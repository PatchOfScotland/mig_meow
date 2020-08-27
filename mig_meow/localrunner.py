
# This code is heavily based off the 'mig/server/grid_events.py' file
# contained in the MiG source code at: https://sourceforge.net/projects/migrid/

import copy
import glob
import os
import time
import shutil
import re
import fnmatch
import threading
import multiprocessing

from .constants import PATTERNS, RECIPES, NAME, SOURCE, CHAR_LOWERCASE, \
    CHAR_UPPERCASE, CHAR_NUMERIC, RECIPE, KEYWORD_DIR, KEYWORD_EXTENSION, \
    KEYWORD_FILENAME, KEYWORD_JOB, KEYWORD_PATH, KEYWORD_PREFIX, \
    KEYWORD_REL_DIR, KEYWORD_REL_PATH, KEYWORD_VGRID, VGRID
from .logging import create_localrunner_logfile, write_to_log
from .fileio import write_dir_pattern, write_dir_recipe, make_dir, \
    read_dir_recipe, read_dir_pattern, write_notebook, write_yaml, read_yaml
from .meow import get_parameter_sweep_values

from datetime import datetime
from random import SystemRandom
from watchdog.observers import Observer
from watchdog.events import PatternMatchingEventHandler, FileCreatedEvent, \
    FileModifiedEvent, FileDeletedEvent, DirCreatedEvent, DirModifiedEvent, \
    DirDeletedEvent

rule_hits = {}
_hits_lock = threading.Lock()

(_rate_limit_field, _settle_time_field) = ('rate_limit', 'settle_time')
_default_period = 'm'
_default_time = '0'
_unit_periods = {
    's': 1,
    'm': 60,
    'h': 60 * 60,
    'd': 24 * 60 * 60,
    'w': 7 * 24 * 60 * 60,
}

_trigger_event = '_trigger_event'

RUNNER_DATA = '.workflow_data'
RUNNER_PATTERNS = os.path.join(RUNNER_DATA, PATTERNS)
RUNNER_RECIPES = os.path.join(RUNNER_DATA, RECIPES)

JOB_DIR = '.workflow_processing'

LOGGER = 'logger'
RULES = 'rules'
RULE_ID = 'id'
RULE_PATH = 'path'
RULE_PATTERN = 'pattern'
RULE_RECIPE = 'recipe'
ADMIN = 'admin'
MONITOR = 'monitor'
WORKERS = 'workers'
JOBS = 'jobs'
QUEUE = 'queue'
DATA_DIR = 'data_dir'
JOBS_DIR = 'jobs_dir'
RETRO_ACTIVE = 'retro'
PRINT = 'print'

QUEUED = 'queued'
RUNNING = 'running'
FAILED = 'failed'
DONE = 'done'

JOB_ID = 'id'
JOB_PATTERN = 'pattern'
JOB_RECIPE = 'recipe'
JOB_RULE = 'rule'
JOB_PATH = 'path'
JOB_STATUS = 'status'
JOB_CREATE_TIME = 'create'
JOB_START_TIME = 'start'
JOB_END_TIME = 'end'
JOB_ERROR = 'error'

META_FILE = 'job.yml'
BASE_FILE = 'base.ipynb'
PARAMS_FILE = 'params.yml'
JOB_FILE = 'job.ipynb'
RESULT_FILE = 'result.ipynb'

recent_jobs = {}
_recent_jobs_lock = threading.Lock()
_job_lock = threading.Lock()
_queue_lock = threading.Lock()
_worker_lock = threading.Lock()


def generate_id(length=16):
    """
    Generates a random id by using randomly generated alphanumeric strings.
    Uniqueness is not guaranteed, but is a reasonable assumption.

    :param length: (int) [optional] The length of the id to be generated.
    Default is 16

    :return: (str) A random collection of alphanumeric characters.
    """
    charset = CHAR_UPPERCASE + CHAR_LOWERCASE + CHAR_NUMERIC
    return ''.join(SystemRandom().choice(charset) for _ in range(length))


def make_fake_event(path, state, is_directory=False):
    """Create a fake state change event for path. Looks up path to see if the
    change is a directory or file.
    """

    file_map = {'modified': FileModifiedEvent,
                'created': FileCreatedEvent,
                'deleted': FileDeletedEvent}
    dir_map = {'modified': DirModifiedEvent,
               'created': DirCreatedEvent, 'deleted': DirDeletedEvent}
    if is_directory or os.path.isdir(path):
        fake = dir_map[state](path)
    else:
        fake = file_map[state](path)

    # mark it a trigger event
    setattr(fake, _trigger_event, True)
    return fake


def is_fake_event(event):
    """Check if event came from our trigger-X rules rather than a real file
    system change.
    """

    return getattr(event, _trigger_event, False)


def get_job_dir(state, job_id):
    """
    Gets the path of a jobs directory.

    :param state: (dict) The shared state.

    :param job_id: (str) The job id.

    :return: (str) The path to the jobs directory.
    """
    return os.path.join(state[JOBS_DIR], job_id)


def replace_keywords(old_dict, state, job_id, src_path):
    """
    Replaces MiG trigger keywords with with actual values.

    :param old_dict: (dict) A values dict potentially containing MiG keywords.

    :param state: (dict) The shared runner state

    :param job_id: (str) The appropriate job ID, corresponding to old_dict.

    :param src_path: (str) The triggering path for the event generating the
    job_id job

    :return: (dict) A dict corresponding to old_dict, with the MiG keywords
    replaced with appropriate values.
    """
    new_dict = {}

    filename = os.path.basename(src_path)
    dirname = os.path.dirname(src_path)
    relpath = os.path.relpath(src_path, state[VGRID])
    reldirname = os.path.dirname(relpath)
    (prefix, extension) = os.path.splitext(filename)

    for var, val in old_dict.items():
        if isinstance(val, str):
            val = val.replace(KEYWORD_PATH, src_path)
            val = val.replace(KEYWORD_REL_PATH, relpath)
            val = val.replace(KEYWORD_DIR, dirname)
            val = val.replace(KEYWORD_REL_DIR, reldirname)
            val = val.replace(KEYWORD_FILENAME, filename)
            val = val.replace(KEYWORD_PREFIX, prefix)
            val = val.replace(KEYWORD_VGRID, state[VGRID])
            val = val.replace(KEYWORD_EXTENSION, extension)
            val = val.replace(KEYWORD_JOB, job_id)

            new_dict[var] = val

    return new_dict


def schedule_job(runner_state, rule, src_path, recipe_code, yaml_dict):
    """
    Schedules a new job in the workflow runner. This creates the appropriate
    job files in a shared directory, adds the job to the queue, and add it to
    the list of all jobs.

    :param runner_state: (dict) The shared runner state.

    :param rule: (dict) The rule causing this job to be scheduled.

    :param src_path: (str) The path which generated the triggering event.

    :param recipe_code: (dict) The recipe code to be run through.

    :param yaml_dict: (dict) Any variables to be applied.

    :return: No return.
    """
    job_dict = {
        JOB_ID: generate_id(),
        JOB_PATTERN: rule[RULE_PATTERN],
        JOB_RECIPE: rule[RULE_RECIPE],
        JOB_RULE: rule[RULE_ID],
        JOB_PATH: src_path,
        JOB_STATUS: QUEUED,
        JOB_CREATE_TIME: datetime.now()
    }

    yaml_dict = replace_keywords(
        yaml_dict,
        runner_state,
        job_dict[JOB_ID],
        src_path
    )

    job_dir = get_job_dir(runner_state, job_dict[JOB_ID])
    make_dir(job_dir)

    meta_file = os.path.join(job_dir, META_FILE)
    write_yaml(job_dict, meta_file)

    base_file = os.path.join(job_dir, BASE_FILE)
    write_notebook(recipe_code, base_file)

    yaml_file = os.path.join(job_dir, PARAMS_FILE)
    write_yaml(yaml_dict, yaml_file)

    _job_lock.acquire()
    _queue_lock.acquire()
    try:
        runner_state[JOBS].append(job_dict[JOB_ID])
        runner_state[QUEUE].append(job_dict[JOB_ID])
    except Exception as ex:
        _job_lock.release()
        _queue_lock.release()
        raise Exception(ex)
    _job_lock.release()
    _queue_lock.release()


class WorkflowRunner:
    def __init__(self, logging=True):
        runner_log_file = create_localrunner_logfile(debug_mode=logging)

        self.runner_state = {
            PATTERNS: {},
            RECIPES: {},
            RULES: [],
            JOBS: [],
            QUEUE: [],
            LOGGER: runner_log_file,
            ADMIN: None,
            MONITOR: None,
            WORKERS: [],
            DATA_DIR: None,
            JOBS_DIR: None,
            VGRID: None,
            RETRO_ACTIVE: True,
            PRINT: True
        }

        write_to_log(
            self.runner_state[LOGGER],
            'run_local_workflow',
            'created new log at %s' % self.runner_state[LOGGER],
            to_print=self.runner_state[PRINT]
        )

    def run_local_workflow(
            self, path, workers, patterns=None, recipes=None,
            meow_data=RUNNER_DATA, job_data=JOB_DIR, daemon=False,
            reuse_vgrid=True, start_workers=False, retro_active_jobs=True,
            print_logging=True
    ):
        make_dir(path, can_exist=reuse_vgrid)
        make_dir(job_data)
        make_dir(meow_data, can_exist=False)
        make_dir(RUNNER_PATTERNS, can_exist=False)
        make_dir(RUNNER_RECIPES, can_exist=False)

        self.runner_state[VGRID] = path

        write_to_log(
            self.runner_state[LOGGER],
            'run_local_workflow',
            'Starting file monitor',
            to_print=print_logging
        )

        workflow_monitor = LocalWorkflowMonitor(
            runner_state=self.runner_state
        )
        monitor_observer = Observer()
        self.runner_state[MONITOR] = monitor_observer
        monitor_observer.schedule(
            workflow_monitor,
            path,
            recursive=True
        )
        monitor_observer.start()

        write_to_log(
            self.runner_state[LOGGER],
            'run_local_workflow',
            'Starting MEOW monitor',
            to_print=print_logging
        )

        self.runner_state[DATA_DIR] = meow_data
        self.runner_state[JOBS_DIR] = job_data
        self.runner_state[RETRO_ACTIVE] = retro_active_jobs
        self.runner_state[PRINT] = print_logging

        workflow_administrator = LocalWorkflowAdministrator(
            runner_state=self.runner_state
        )
        administrator_observer = Observer()
        self.runner_state[ADMIN] = administrator_observer
        administrator_observer.schedule(
            workflow_administrator,
            meow_data,
            recursive=print_logging
        )
        administrator_observer.start()

        write_to_log(
            self.runner_state[LOGGER],
            'run_local_workflow',
            'Monitor setup complete',
            to_print=print_logging
        )

        if patterns:
            for name, pattern in patterns.items():
                write_dir_pattern(pattern, directory=RUNNER_DATA)

        if recipes:
            for name, recipe in recipes.items():
                write_dir_recipe(recipe, directory=RUNNER_DATA)

        write_to_log(
            self.runner_state[LOGGER],
            'run_local_workflow',
            'Initial Pattern and Recipe definitions complete',
            to_print=print_logging
        )

        _worker_lock.acquire()
        try:
            for id in range(0, workers):
                worker = JobProcessor(id, self.runner_state)
                self.runner_state[WORKERS].append(worker)
        except Exception as ex:
            _worker_lock.release()
            raise Exception(ex)
        _worker_lock.release()

        if start_workers:
            self.start_workers()

        if not daemon:
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                self.stop_runner()

    def start_workers(self):
        _worker_lock.acquire()
        try:
            workers = self.runner_state[WORKERS]

            for worker in workers:
                write_to_log(
                    self.runner_state[LOGGER],
                    'start_workers',
                    "Starting worker %s" % worker.worker_id,
                    to_print=self.runner_state[PRINT]
                )

                worker.start()
        except Exception as ex:
            _worker_lock.release()
            raise Exception(ex)
        _worker_lock.release()

    def check_running_status(self):
        if not self.runner_state[ADMIN]:
            return (False, 'The Workflow Admin is not running. You should '
                           'start another workflow runner. ')
        if not self.runner_state[MONITOR]:
            return (False, 'The Workflow Monitor is not running. You should '
                           'start another workflow runner. ')
        _worker_lock.acquire()
        try:
            for worker in self.runner_state[WORKERS]:
                if not worker.isalive():
                    return (False, "Worker %s is not running. You may be able"
                                   "to fix this by running the 'start_workers'"
                                   "function. ")
        except Exception as ex:
            _worker_lock.release()
            raise Exception(ex)
        _worker_lock.release()
        return (True, 'All systems are running. ')

    def stop_runner(self, clear_jobs=False):

        _worker_lock.acquire()
        try:
            monitor_observer = self.runner_state[MONITOR]
            administrator_observer = self.runner_state[ADMIN]
            workers = self.runner_state[WORKERS]

            to_join = []

            if monitor_observer.is_alive():
                to_join.append(monitor_observer)
                monitor_observer.stop()

            if administrator_observer.is_alive():
                to_join.append(administrator_observer)
                administrator_observer.stop()
            for worker in workers:
                if worker.is_alive():
                    to_join.append(worker)
                    worker.stop()

            for thread in to_join:
                thread.join()

            self.runner_state[MONITOR] = None
            self.runner_state[ADMIN] = None
            self.runner_state[WORKERS] = []
        except Exception as ex:
            _worker_lock.release()
            raise Exception(ex)
        _worker_lock.release()

        meow_data = self.runner_state[DATA_DIR]
        if os.path.exists(meow_data) and os.path.isdir(meow_data):
            shutil.rmtree(meow_data)

        job_data = self.runner_state[JOBS_DIR]
        if clear_jobs and os.path.exists(job_data):
            for job in self.runner_state[JOBS]:
                job_dir = get_job_dir(self.runner_state, job)
                if os.path.exists(job_dir):
                    shutil.rmtree(job_dir)
            if len(os.listdir(job_data)) == 0:
                os.rmdir(job_data)
        return True

    def get_all_jobs(self):
        job_queue = []

        _job_lock.acquire()
        try:
            job_queue = copy.deepcopy(self.runner_state[JOBS])
        except:
            pass
        _job_lock.release()

        return job_queue

    def get_queued_jobs(self):
        job_queue = []

        _job_lock.acquire()
        try:
            job_queue = copy.deepcopy(self.runner_state[QUEUE])
        except:
            pass
        _job_lock.release()

        return job_queue


class JobProcessor(threading.Thread):
    def __init__(self, worker_id, runner_state):
        threading.Thread.__init__(self)
        self.worker_id = worker_id
        self._stop = threading.Event()
        self.runner_state = runner_state

    def run(self):
        while True:
            if self._stop.isSet():
                return
            _queue_lock.acquire()
            try:
                queue = self.runner_state[JOBS]

                write_to_log(
                    self.runner_state[LOGGER],
                    'worker %s' % self.worker_id,
                    "There are %d jobs in the queue" % len(queue),
                    to_print=self.runner_state[PRINT]
                )

                running_job = None
                running_data = None
                for job in queue:
                    job_dir = get_job_dir(self.runner_state, job)
                    meta_path = os.path.join(job_dir, META_FILE)

                    job_data = read_yaml(meta_path)

                    if job_data[JOB_STATUS] == QUEUED:
                        running_job = job
                        running_data = job_data
                        job_data[JOB_STATUS] = RUNNING
                        job_data[JOB_START_TIME] = datetime.now()

                        write_yaml(job_data, meta_path)

                        write_to_log(
                            self.runner_state[LOGGER],
                            'worker %s' % self.worker_id,
                            "Found job %s" % job_data[JOB_ID],
                            to_print=self.runner_state[PRINT]
                        )
                        break
            except Exception as ex:
                _queue_lock.release()
                raise Exception(ex)
            if running_job:
                self.runner_state[JOBS].remove(running_job)
                _queue_lock.release()
            else:
                _queue_lock.release()
                time.sleep(10 + (self.worker_id % 10))
                continue

            job_dir = get_job_dir(self.runner_state, running_job)
            meta_path = os.path.join(job_dir, META_FILE)
            base_path = os.path.join(job_dir, BASE_FILE)
            param_path = os.path.join(job_dir, PARAMS_FILE)
            job_path = os.path.join(job_dir, JOB_FILE)
            result_path = os.path.join(job_dir, RESULT_FILE)

            error = False
            cmd = 'notebook_parameterizer ' \
                  + base_path + ' ' \
                  + param_path + ' ' \
                  + '-o ' + job_path
            try:
                os.system(cmd)
            except Exception as ex:
                error = ex

            if not os.path.exists(job_path) or error:
                running_data[JOB_STATUS] = FAILED
                running_data[JOB_END_TIME] = datetime.now()
                msg = 'Job file %s was not created successfully'
                if error:
                    msg += '. %s' % error
                running_data[JOB_ERROR] = msg
                write_yaml(running_data, meta_path)
                write_to_log(
                    self.runner_state[LOGGER],
                    'worker %s' % self.worker_id,
                    "Job worker encountered and error. %s" % msg,
                    to_print=self.runner_state[PRINT]
                )
                time.sleep(10 + (self.worker_id % 10))
                continue

            cmd = 'papermill ' \
                  + job_path + ' ' \
                  + result_path
            try:
                os.system(cmd)
            except Exception as ex:
                error = ex

            if not os.path.exists(result_path) or error:
                running_data[JOB_STATUS] = FAILED
                running_data[JOB_END_TIME] = datetime.now()
                msg = 'Result file %s was not created successfully'
                if error:
                    msg += '. %s' % error
                running_data[JOB_ERROR] = msg
                write_yaml(running_data, meta_path)
                write_to_log(
                    self.runner_state[LOGGER],
                    'worker %s' % self.worker_id,
                    "Job worker encountered and error. %s" % msg,
                    to_print=self.runner_state[PRINT]
                )
                time.sleep(10 + (self.worker_id % 10))
                continue

            running_data[JOB_STATUS] = DONE
            running_data[JOB_END_TIME] = datetime.now()
            write_yaml(running_data, meta_path)

            time.sleep(10 + (self.worker_id % 10))

    def stop(self):
        self._stop.set()


class LocalWorkflowAdministrator(PatternMatchingEventHandler):
    """
    Event handler to monitor pattern and recipe changes.
    """

    def __init__(
            self, runner_state=None, patterns=None, ignore_patterns=None,
            ignore_directories=False, case_sensitive=False):
        """Constructor"""

        PatternMatchingEventHandler.__init__(
            self,
            patterns,
            ignore_patterns,
            ignore_directories,
            case_sensitive
        )
        self.runner_state = runner_state

    def update_rules(self, event):
        """Handle all rule updates"""

        if event.is_directory:
            return

        write_to_log(
            self.runner_state[LOGGER],
            'update_rules',
            "Handling %s rule update at %s"
            % (event.event_type, event.src_path),
            to_print=self.runner_state[PRINT]
        )

        src_path = event.src_path
        event_type = event.event_type
        file_type = ''
        file_path = ''
        try:
            if RUNNER_PATTERNS in src_path:
                file_path = src_path[
                            src_path.find(RUNNER_PATTERNS)
                            + len(RUNNER_PATTERNS)+1:]
                file_type = PATTERNS
            elif RUNNER_RECIPES in src_path:
                file_path = src_path[
                            src_path.find(RUNNER_RECIPES)
                            + len(RUNNER_RECIPES)+1:]
                file_type = RECIPES
        except Exception as exc:
            write_to_log(
                self.runner_state[LOGGER],
                'update_rules-pattern',
                'Cannot process event at %s due to error: %s'
                % (src_path, exc),
                to_print=self.runner_state[PRINT]
            )
            return
        if os.path.sep in file_path:
            write_to_log(
                self.runner_state[LOGGER],
                'update_rules-pattern',
                'Cannot process nested event at %s' % src_path,
                to_print=self.runner_state[PRINT]
            )
            return

        if event_type in ['created', 'modified']:
            if file_type == PATTERNS:
                try:
                    pattern = read_dir_pattern(
                        file_path,
                        directory=RUNNER_DATA
                    )
                except Exception as exc:
                    write_to_log(
                        self.runner_state[LOGGER],
                        'update_rules-pattern',
                        exc,
                        to_print=self.runner_state[PRINT]
                    )
                    return
                self.add_pattern(pattern)
            elif file_type == RECIPES:
                try:
                    recipe = read_dir_recipe(
                        file_path,
                        directory=RUNNER_DATA
                    )
                except Exception as exc:
                    write_to_log(
                        self.runner_state[LOGGER],
                        'update_rules-recipe',
                        exc,
                        to_print=self.runner_state[PRINT]
                    )
                    return
                self.add_recipe(recipe)
        elif event_type == 'deleted':
            if file_type == PATTERNS:
                self.remove_pattern(file_path)
            elif file_type == RECIPES:
                self.remove_recipe(file_path)

    def on_modified(self, event):
        """Handle modified rule file"""

        self.update_rules(event)

    def on_created(self, event):
        """Handle new rule file"""

        self.update_rules(event)

    def on_deleted(self, event):
        """Handle deleted rule file"""

        self.update_rules(event)

    def add_pattern(self, pattern):
        op = 'Created new'
        if pattern.name in self.runner_state[PATTERNS]:
            if self.runner_state[PATTERNS][pattern.name] == pattern:
                return
            else:
                self.remove_pattern(pattern.name)
                op = 'Modified'
        self.runner_state[PATTERNS][pattern.name] = pattern
        self.identify_rules(new_pattern=pattern)
        write_to_log(
            self.runner_state[LOGGER],
            'add_pattern',
            '%s pattern %s' % (op, pattern),
            to_print=self.runner_state[PRINT]
        )

    def add_recipe(self, recipe):
        op = 'Created new'
        if recipe[NAME] in self.runner_state[RECIPES]:
            if self.runner_state[RECIPES][recipe[NAME]] == recipe:
                return
            else:
                self.remove_recipe(recipe[NAME])
                op = 'Modified'
        self.runner_state[RECIPES][recipe[NAME]] = recipe
        self.identify_rules(new_recipe=recipe)
        write_to_log(
            self.runner_state[LOGGER],
            'add_recipe',
            '%s recipe %s from source %s'
            % (op, recipe[NAME], recipe[SOURCE]),
            to_print=self.runner_state[PRINT]
        )

    def remove_pattern(self, pattern_name):
        if pattern_name in self.runner_state[PATTERNS]:
            self.runner_state[PATTERNS].pop(pattern_name)
        self.remove_rules(deleted_pattern_name=pattern_name)
        write_to_log(
            self.runner_state[LOGGER],
            'remove_pattern',
            'Removed pattern %s' % pattern_name,
            to_print=self.runner_state[PRINT]
        )

    def remove_recipe(self, recipe_name):
        if recipe_name in self.runner_state[RECIPES]:
            self.runner_state[RECIPES].pop(recipe_name)
        self.remove_rules(deleted_recipe_name=recipe_name)
        write_to_log(
            self.runner_state[LOGGER],
            'remove_recipe',
            'Removed recipe %s' % recipe_name,
            to_print=self.runner_state[PRINT]
        )

    def create_new_rule(self, pattern_name, recipe_name, path):
        rule = {
            RULE_ID: generate_id(),
            RULE_PATTERN: pattern_name,
            RULE_RECIPE: recipe_name,
            RULE_PATH: path
        }
        self.runner_state[RULES].append(rule)
        write_to_log(
            self.runner_state[LOGGER],
            'create_new_rule',
            'Created rule for path: %s with id %s.'
            % (path, rule[RULE_ID]),
            to_print=self.runner_state[PRINT]
        )

        notebook_code = self.runner_state[RECIPES][rule[RULE_RECIPE]][RECIPE]

        pattern = self.runner_state[PATTERNS][rule[RULE_PATTERN]]

        yaml_dict = {}
        for var, val in pattern.variables.items():
            yaml_dict[var] = val
        for var, val in pattern.outputs.items():
            yaml_dict[var] = val
        yaml_dict[pattern.trigger_file] = path

        if self.runner_state[RETRO_ACTIVE]:
            testing_path = os.path.join(self.runner_state[VGRID], path)

            globbed = glob.glob(testing_path)

            for globble in globbed:

                local_path = globble[globble.find(os.path.sep)+1:]

                if not pattern.sweep:
                    schedule_job(
                        self.runner_state,
                        rule,
                        local_path,
                        notebook_code,
                        yaml_dict
                    )
                else:
                    for var, val in pattern.sweep.items():
                        values = get_parameter_sweep_values(val)
                        for value in values:
                            yaml_dict[var] = value
                            schedule_job(
                                self.runner_state,
                                rule,
                                local_path,
                                notebook_code,
                                yaml_dict
                            )

    def identify_rules(self, new_pattern=None, new_recipe=None):
        if new_pattern:
            if len(new_pattern.recipes) > 1:
                write_to_log(
                    self.runner_state[LOGGER],
                    'identify_rules-pattern',
                    'Rule creation aborted. Currently only supports one '
                    'recipe per pattern.',
                )
            recipe_name = new_pattern.recipes[0]
            if recipe_name in self.runner_state[RECIPES]:
                for input_path in new_pattern.trigger_paths:
                    self.create_new_rule(
                        new_pattern.name,
                        recipe_name,
                        input_path
                    )

        if new_recipe:
            for name, pattern in self.runner_state[PATTERNS].items():
                if len(pattern.recipes) > 1:
                    write_to_log(
                        self.runner_state[LOGGER],
                        'identify_rules-recipe',
                        'Rule creation avoided for %s. Currently only '
                        'supports one recipe per pattern.' % name,
                    )
                recipe_name = pattern.recipes[0]
                if recipe_name == new_recipe[NAME]:
                    for input_path in pattern.trigger_paths:
                        self.create_new_rule(
                            name,
                            recipe_name,
                            input_path
                        )

    def remove_rules(
            self, deleted_pattern_name=None, deleted_recipe_name=None):
        to_delete = []
        for rule in self.runner_state[RULES]:
            if deleted_pattern_name:
                if rule[RULE_PATTERN] == deleted_pattern_name:
                    to_delete.append(rule)
            if deleted_recipe_name:
                if rule[RULE_RECIPE] == deleted_recipe_name:
                    to_delete.append(rule)
        for delete in to_delete:
            self.runner_state[RULES].remove(delete)
            write_to_log(
                self.runner_state[LOGGER],
                'remove_rules',
                'Removing rule: %s.' % delete,
                to_print=self.runner_state[PRINT]
            )


class LocalWorkflowMonitor(PatternMatchingEventHandler):
    """
    Event handler to schedule jobs according to file events.
    """

    def __init__(
            self, runner_state=None, patterns=None,
            ignore_patterns=None, ignore_directories=False,
            case_sensitive=False):
        """Constructor"""

        PatternMatchingEventHandler.__init__(
            self,
            patterns,
            ignore_patterns,
            ignore_directories,
            case_sensitive
        )
        self.runner_state = runner_state

        write_to_log(
            runner_state[LOGGER],
            'LocalWorkflowRunner',
            'Starting new workflow runner',
            to_print=self.runner_state[PRINT]
        )

    def __handle_trigger(self, event, handle_path, rule):
        pid = multiprocessing.current_process().pid
        event_type = event.event_type
        src_path = event.src_path
        time_stamp = event.time_stamp

        write_to_log(
            self.runner_state[LOGGER],
            '__handle_trigger',
            'Running threaded handler at (%s) to handle %s event at %s '
            'with rule %s'
            % (pid, event_type, handle_path, rule[RULE_ID]))

        # This will prevent some job spamming
        _recent_jobs_lock.acquire()
        try:
            if src_path in recent_jobs:
                if rule[RULE_ID] in recent_jobs[src_path]:
                    recent_timestamp = recent_jobs[src_path][rule[RULE_ID]]
                    difference = time_stamp - recent_timestamp

                    if difference <= 1:
                        recent_jobs[src_path][RULE_ID] = \
                            max(recent_timestamp, time_stamp)
                        write_to_log(
                            self.runner_state[LOGGER],
                            '__handle_trigger',
                            'Skipping due to recent hit'
                        )
                        _recent_jobs_lock.release()
                        return
                else:
                    recent_jobs[src_path][rule[RULE_ID]] = time_stamp
            else:
                recent_jobs[src_path] = {
                    rule[RULE_ID]: time_stamp
                }
        except Exception as ex:
            _recent_jobs_lock.release()
            raise Exception(ex)
        _recent_jobs_lock.release()

        notebook_code = self.runner_state[RECIPES][rule[RULE_RECIPE]][RECIPE]

        pattern = self.runner_state[PATTERNS][rule[RULE_PATTERN]]

        write_to_log(
            self.runner_state[LOGGER],
            'run_handler',
            'Starting new job for %s using rule %s' % (src_path, rule),
            to_print=self.runner_state[PRINT]
        )

        yaml_dict = {}
        for var, val in pattern.variables.items():
            yaml_dict[var] = val
        for var, val in pattern.outputs.items():
            yaml_dict[var] = val
        yaml_dict[pattern.trigger_file] = src_path

        if not pattern.sweep:
            schedule_job(
                self.runner_state,
                rule,
                src_path,
                notebook_code,
                yaml_dict
            )
        else:
            for var, val in pattern.sweep.items():
                values = get_parameter_sweep_values(val)
                for value in values:
                    yaml_dict[var] = value
                    schedule_job(
                        self.runner_state,
                        rule,
                        src_path,
                        notebook_code,
                        yaml_dict
                    )

    def run_handler(self, event):
        src_path = event.src_path
        event_type = event.event_type

        handle_path = src_path.replace(self.runner_state[VGRID], '', 1)
        while handle_path.startswith(os.path.sep):
            handle_path = handle_path[1:]

        write_to_log(
            self.runner_state[LOGGER],
            'run_handler',
            'Handling %s event at %s' % (event_type, handle_path),
            to_print=self.runner_state[PRINT]
        )

        for rule in self.runner_state[RULES]:
            target_path = rule[RULE_PATH]
            recursive_regexp = fnmatch.translate(target_path)
            direct_regexp = recursive_regexp.replace('.*', '[^/]*')
            recursive_hit = re.match(recursive_regexp, handle_path)
            direct_hit = re.match(direct_regexp, handle_path)

            if direct_hit or recursive_hit:
                waiting_for_thread_resources = True
                while waiting_for_thread_resources:
                    try:
                        worker = threading.Thread(
                            target=self.__handle_trigger,
                            args=(event, handle_path, rule))
                        worker.daemon = True
                        worker.start()
                        waiting_for_thread_resources = False
                    except threading.ThreadError as exc:
                        time.sleep(1)

    def handle_event(self, event):
        if event.is_directory:
            return

        if event.event_type not in ['created', 'modified']:
            return

        event.time_stamp = time.time()

        self.run_handler(event)

    def on_modified(self, event):
        """Handle modified files"""

        self.handle_event(event)

    def on_created(self, event):
        """Handle created files"""

        self.handle_event(event)

    def on_deleted(self, event):
        """Handle deleted files"""

        self.handle_event(event)

    def on_moved(self, event):
        """Handle moved files"""

        fake = make_fake_event(
            event.dest_path,
            'created',
            event.is_directory
        )
        self.handle_event(fake)
