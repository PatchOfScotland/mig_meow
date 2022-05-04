
# This code is heavily based off the 'mig/server/grid_events.py' file
# contained in the MiG source code at: https://sourceforge.net/projects/migrid/

import copy
import glob
import os
import time
import re
import fnmatch
import shutil
import socket
import subprocess
import stat
import threading
import paramiko
import pkg_resources

from cryptography.hazmat.primitives import serialization as cryptography_serialisation
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend as cryptography_default_backend
from datetime import datetime
from multiprocessing import Process, Pipe, current_process
from multiprocessing.connection import wait
from random import SystemRandom
from watchdog.observers import Observer
from watchdog.events import PatternMatchingEventHandler, FileCreatedEvent, \
    FileModifiedEvent, FileDeletedEvent, DirCreatedEvent, DirModifiedEvent, \
    DirDeletedEvent

from .constants import PATTERNS, RECIPES, NAME, SOURCE, CHAR_LOWERCASE, \
    CHAR_UPPERCASE, CHAR_NUMERIC, RECIPE, KEYWORD_DIR, KEYWORD_EXTENSION, \
    KEYWORD_FILENAME, KEYWORD_JOB, KEYWORD_PATH, KEYWORD_PREFIX, \
    KEYWORD_REL_DIR, KEYWORD_REL_PATH, KEYWORD_VGRID, VGRID, ENVIRONMENTS
from .logging import create_localrunner_logfile, write_to_log
from .fileio import write_dir_pattern, write_dir_recipe, make_dir, \
    read_dir_recipe, read_dir_pattern, write_notebook, write_yaml, read_yaml, \
    delete_dir_pattern, delete_dir_recipe, rmtree
from .meow import get_parameter_sweep_values, is_valid_pattern_object, Pattern
from .validation import valid_dir_path, check_input, is_valid_recipe_dict, \
    is_valid_local_environment, valid_runner_workers, is_valid_ssh_worker

_trigger_event = '_trigger_event'

RUNNER_DATA = '.workflow_runner_data'
OUTPUT_DATA = 'job_output'

JOB_DIR = '.workflow_processing'

OP_CREATE = 'Created'
OP_MODIFIED = 'Modified'
OP_DELETED = 'Removed'
OP_EVENT = 'Event'

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
OUTPUT_DIR = 'output_dir'
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
JOB_REQUIREMENTS = 'requirements'

META_FILE = 'job.yml'
BASE_FILE = 'base.ipynb'
PARAMS_FILE = 'params.yml'
JOB_FILE = 'job.ipynb'
RESULT_FILE = 'result.ipynb'


def get_runner_patterns(runner_data):
    return os.path.join(runner_data, PATTERNS)


def get_runner_recipes(runner_data):
    return os.path.join(runner_data, RECIPES)


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


def replace_keywords(old_dict, job_id, src_path, vgrid):
    """
    Replaces MiG trigger keywords with with actual values.

    :param old_dict: (dict) A values dict potentially containing MiG keywords.

    :param job_id: (str) The appropriate job ID, corresponding to old_dict.

    :param src_path: (str) The triggering path for the event generating the
    job_id job

    :param vgrid: (str) The vgrid to replace

    :return: (dict) A dict corresponding to old_dict, with the MiG keywords
    replaced with appropriate values.
    """
    new_dict = {}

    filename = os.path.basename(src_path)
    dirname = os.path.dirname(src_path)
    relpath = os.path.relpath(src_path, vgrid)
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
            val = val.replace(KEYWORD_VGRID, vgrid)
            val = val.replace(KEYWORD_EXTENSION, extension)
            val = val.replace(KEYWORD_JOB, job_id)

            new_dict[var] = val
        else:
            new_dict[var] = val

    return new_dict


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


def administrator(
        from_user, to_user, from_state, from_file, to_queue, from_queue,
        to_worker_writers, from_worker_readers, to_logger, vgrid, job_data,
        meow_data, retro_active, workers_start):

    def add_pattern(pattern):
        op = OP_CREATE
        if pattern.name in patterns:
            if patterns[pattern.name] == pattern:
                return
            else:
                remove_pattern(pattern.name)
                op = OP_MODIFIED
        patterns[pattern.name] = pattern
        identify_rules(new_pattern=pattern)
        to_logger.send(
            (
                'administrator.add_pattern',
                '%s pattern %s' % (op, pattern)
            )
        )

    def add_recipe(recipe):
        op = OP_CREATE
        if recipe[NAME] in recipes:
            if recipes[recipe[NAME]] == recipe:
                return
            else:
                remove_recipe(recipe[NAME])
                op = OP_MODIFIED
        recipes[recipe[NAME]] = recipe
        identify_rules(new_recipe=recipe)
        to_logger.send(
            (
                'administrator.add_recipe',
                '%s recipe %s from source %s'
                % (op, recipe[NAME], recipe[SOURCE])
            )
        )

    def remove_pattern(pattern_name):
        if pattern_name in patterns:
            patterns.pop(pattern_name)
            remove_rules(deleted_pattern_name=pattern_name)
            to_logger.send(
                (
                    'administrator.remove_pattern',
                    'Removed pattern %s' % pattern_name
                )
            )
        else:
            to_logger.send(
                (
                    'administrator.remove_pattern',
                    'Pattern %s was not present in the pattern list to be '
                    'removed' % pattern_name
                )
            )

    def remove_recipe(recipe_name):
        if recipe_name in recipes:
            recipes.pop(recipe_name)
            remove_rules(deleted_recipe_name=recipe_name)
            to_logger.send(
                (
                    'administrator.remove_recipe',
                    'Removed recipe %s' % recipe_name
                )
            )
        else:
            to_logger.send(
                (
                    'administrator.remove_recipe',
                    'Recipe %s was not present in the recipe list to be '
                    'removed' % recipe_name
                )
            )

    def create_new_rule(pattern_name, recipe_name, path):
        rule = {
            RULE_ID: generate_id(),
            RULE_PATTERN: pattern_name,
            RULE_RECIPE: recipe_name,
            RULE_PATH: path
        }
        rules.append(rule)

        to_logger.send(
            (
                'administrator.create_new_rule',
                'Created rule for path: %s with id %s.'
                % (path, rule[RULE_ID])
            )
        )

        pattern = patterns[rule[RULE_PATTERN]]

        yaml_dict = {}
        for var, val in pattern.variables.items():
            yaml_dict[var] = val
        for var, val in pattern.outputs.items():
            yaml_dict[var] = val
        yaml_dict[pattern.trigger_file] = path

        if retro_active:
            testing_path = os.path.join(vgrid, path)

            globbed = glob.glob(testing_path)

            for globble in globbed:
                yaml_dict[pattern.trigger_file] = globble

                local_path = globble[globble.find(os.path.sep)+1:]

                if not pattern.sweep:
                    schedule_job(
                        rule,
                        local_path,
                        yaml_dict
                    )
                else:
                    for var, val in pattern.sweep.items():
                        values = get_parameter_sweep_values(val)
                        for value in values:
                            yaml_dict[var] = value
                            schedule_job(
                                rule,
                                local_path,
                                yaml_dict
                            )

    def identify_rules(new_pattern=None, new_recipe=None):
        if new_pattern:
            if len(new_pattern.recipes) > 1:
                to_logger.send(
                    (
                        'administrator.identify_rules-pattern',
                        'Rule creation aborted. Currently only supports one '
                        'recipe per pattern.'
                    )
                )
            recipe_name = new_pattern.recipes[0]
            if recipe_name in recipes:
                for input_path in new_pattern.trigger_paths:
                    create_new_rule(
                        new_pattern.name,
                        recipe_name,
                        input_path
                    )

        if new_recipe:
            for name, pattern in patterns.items():
                if len(pattern.recipes) > 1:
                    to_logger.send(
                        (
                            'administrator.identify_rules-recipe',
                            'Rule creation avoided for %s. Currently only '
                            'supports one recipe per pattern.' % name
                        )
                    )
                recipe_name = pattern.recipes[0]
                if recipe_name == new_recipe[NAME]:
                    for input_path in pattern.trigger_paths:
                        create_new_rule(
                            name,
                            recipe_name,
                            input_path
                        )

    def remove_rules(deleted_pattern_name=None, deleted_recipe_name=None):
        to_delete = []
        for rule in rules:
            if deleted_pattern_name:
                if rule[RULE_PATTERN] == deleted_pattern_name:
                    to_delete.append(rule)
            if deleted_recipe_name:
                if rule[RULE_RECIPE] == deleted_recipe_name:
                    to_delete.append(rule)
        for delete in to_delete:
            rules.remove(delete)
            to_logger.send(
                (
                    'administrator.remove_rules',
                    'Removing rule: %s.' % delete
                )
            )

    def schedule_job(rule, src_path, yaml_dict):
        """
        Schedules a new job in the workflow runner. This creates the
        appropriate job files in a shared directory, adds the job to the
        queue, and add it to the list of all jobs.

        :param rule: (dict) The rule causing this job to be scheduled.

        :param src_path: (str) The path which generated the triggering event.

        :param yaml_dict: (dict) Any variables to be applied.

        :return: No return.
        """
        recipe = recipes[rule[RULE_RECIPE]]

        environments = {}
        if ENVIRONMENTS in recipe \
                and 'local' in recipe[ENVIRONMENTS] \
                and is_valid_local_environment(recipe[ENVIRONMENTS]['local']):
            environments = recipe[ENVIRONMENTS]['local']

        job_dict = {
            JOB_ID: generate_id(),
            JOB_PATTERN: rule[RULE_PATTERN],
            JOB_RECIPE: rule[RULE_RECIPE],
            JOB_RULE: rule[RULE_ID],
            JOB_PATH: src_path,
            JOB_STATUS: QUEUED,
            JOB_CREATE_TIME: datetime.now(),
            JOB_REQUIREMENTS: environments
        }

        yaml_dict = replace_keywords(
            yaml_dict,
            job_dict[JOB_ID],
            src_path,
            vgrid
        )

        job_dir = os.path.join(job_data, job_dict[JOB_ID])
        make_dir(job_dir)

        meta_file = os.path.join(job_dir, META_FILE)
        write_yaml(job_dict, meta_file)

        base_file = os.path.join(job_dir, BASE_FILE)
        write_notebook(recipe[RECIPE], base_file)

        yaml_file = os.path.join(job_dir, PARAMS_FILE)
        write_yaml(yaml_dict, yaml_file)

        jobs.append(job_dict[JOB_ID])

        to_queue.send(job_dict[JOB_ID])

        to_logger.send(
            (
                'administrator.schedule_job',
                'Scheduled new job %s from rule %s and pattern %s'
                % (job_dict[JOB_ID], rule[RULE_ID], rule[RULE_PATTERN])
            )
        )

    def handle_event(event):
        src_path = event.src_path
        event_type = event.event_type

        handle_path = src_path.replace(vgrid, '', 1)
        while handle_path.startswith(os.path.sep):
            handle_path = handle_path[1:]

        to_logger.send(
            (
                'administrator.handle_event',
                'Handling a %s event at %s' % (event_type, handle_path)
            )
        )

        for rule in rules:
            target_path = rule[RULE_PATH]
            recursive_regexp = fnmatch.translate(target_path)
            direct_regexp = recursive_regexp.replace('.*', '[^/]*')
            recursive_hit = re.match(recursive_regexp, handle_path)
            direct_hit = re.match(direct_regexp, handle_path)

            if direct_hit or recursive_hit:
                pattern = patterns[rule[RULE_PATTERN]]

                to_logger.send(
                    (
                        'administrator.handle_event',
                        'Starting new job for %s using rule %s'
                        % (src_path, rule)
                    )
                )

                yaml_dict = {}
                for var, val in pattern.variables.items():
                    yaml_dict[var] = val
                for var, val in pattern.outputs.items():
                    yaml_dict[var] = val
                yaml_dict[pattern.trigger_file] = src_path

                if not pattern.sweep:
                    schedule_job(
                        rule,
                        src_path,
                        yaml_dict
                    )
                else:
                    for var, val in pattern.sweep.items():
                        values = get_parameter_sweep_values(val)
                        for value in values:
                            yaml_dict[var] = value
                            schedule_job(
                                rule,
                                src_path,
                                yaml_dict
                            )
            else:
                to_logger.send(
                    (
                        'administrator.handle_event',
                        'No matching rule for %s.' % src_path
                    )
                )

    def start_workers():
        for to_worker in to_worker_writers:
            to_worker.send('start')

        return True

    def stop_workers():
        for to_worker in to_worker_writers:
            to_worker.send('stop')

        return True

    def check_running_status():
        running, total = get_running_status()
        if running == total:
            return True, 'All workers are running. '
        else:
            return False, '%d workers are not running. ' % (total - running)

    def get_running_status():
        total = len(to_worker_writers)
        running = 0

        for i in range(len(to_worker_writers)):
            to_worker = to_worker_writers[i]
            to_worker.send('check')

            from_worker = from_worker_readers[i]
            status = from_worker.recv()
            if status == 'running':
                running += 1
        return running, total

    def stop_runner(clear_jobs=False):
        stop_workers()

        if os.path.exists(meow_data) \
                and os.path.isdir(meow_data) \
                and meow_data == RUNNER_DATA:
            rmtree(meow_data)

        if clear_jobs and os.path.exists(job_data):
            for job in jobs:
                job_dir = os.path.join(job_data, job)
                if os.path.exists(job_dir):
                    rmtree(job_dir)
            if len(os.listdir(job_data)) == 0:
                os.rmdir(job_data)
        return True

    def get_all_jobs():
        jobs_queue = copy.deepcopy(jobs)
        return jobs_queue

    def get_queued_jobs():
        to_queue.send('get_queue')
        queue = from_queue.recv()
        return queue

    def get_all_input_paths():
        input_paths = []
        for rule in rules:
            input_paths.append(rule[RULE_PATH])
        return input_paths

    def check_status():
        queued_jobs = len(get_queued_jobs())
        all_jobs = len(get_all_jobs())
        input_paths = get_all_input_paths()

        status = "[%s/%s] %s" % (queued_jobs, all_jobs, input_paths)

        return status

    def add_pattern_dir(pattern):
        status, msg = is_valid_pattern_object(pattern)
        if not status:
            to_logger.send(
                (
                    'administrator.add_pattern',
                    'Could not add pattern. %s' % msg
                )
            )

            return False
        else:
            write_dir_pattern(pattern, directory=meow_data)

            to_logger.send(
                (
                    'administrator.add_pattern',
                    'Added pattern: %s' % msg
                )
            )

            return True

    def modify_pattern_dir(pattern):
        status, msg = is_valid_pattern_object(pattern)
        if not status:
            to_logger.send(
                (
                    'administrator.modify_pattern',
                    'Could not modify pattern. %s' % msg
                )
            )

            return False
        else:
            write_dir_pattern(pattern, directory=meow_data)

            to_logger.send(
                (
                    'administrator.modify_pattern',
                    'Modified pattern: %s' % msg
                )
            )

            return True

    def remove_pattern_dir(pattern):
        if isinstance(pattern, str):
            name = pattern
        elif isinstance(pattern, Pattern):
            name = pattern.name
        else:
            to_logger.send(
                (
                    'administrator.remove_pattern',
                    'Invalid pattern parameter. Must be either Pattern '
                    'object, or a str name. '
                )
            )
            return False

        delete_dir_pattern(name, directory=meow_data)
        to_logger.send(
            (
                'administrator.remove_pattern',
                'Removed pattern: %s' % name
            )
        )

        return True

    def add_recipe_dir(recipe):
        status, msg = is_valid_recipe_dict(recipe)
        if not status:
            to_logger.send(
                (
                    'administrator.add_recipe',
                    'Could not add recipe. %s' % msg
                )
            )
            return False
        else:
            write_dir_recipe(recipe, directory=meow_data)

            to_logger.send(
                (
                    'administrator.add_recipe',
                    'Added user recipe: %s' % msg
                )
            )
            return True

    def modify_recipe_dir(recipe):
        status, msg = is_valid_recipe_dict(recipe)
        if not status:
            to_logger.send(
                (
                    'administrator.modify_recipe',
                    'Could not modify recipe. %s' % msg
                )
            )
            return False
        else:
            write_dir_recipe(recipe, directory=meow_data)

            to_logger.send(
                (
                    'administrator.modify_recipe',
                    'Modified recipe: %s' % msg
                )
            )
            return True

    def remove_recipe_dir(recipe):
        if isinstance(recipe, str):
            name = recipe
        elif isinstance(recipe, dict):
            name = recipe[NAME]
        else:
            to_logger.send(
                (
                    'administrator.remove_recipe',
                    'Invalid recipe parameter. Must be either recipe dict, '
                    'or a str name. '
                )
            )
            return False

        delete_dir_recipe(name, directory=meow_data)
        to_logger.send(
            (
                'administrator.remove_recipe',
                'Removed recipe: %s' % name
            )
        )
        return True

    def check_recipes():
        recipes_dict = copy.deepcopy(recipes)
        return recipes_dict

    def check_patterns():
        patterns_dict = copy.deepcopy(patterns)
        return patterns_dict

    def check_rules():
        rules_list = copy.deepcopy(rules)
        return rules_list

    def check_jobs():
        jobs_list = copy.deepcopy(jobs)
        return jobs_list

    def check_queue():
        return get_queued_jobs()

    # Start of administrator

    patterns = {}
    recipes = {}
    rules = []
    jobs = []

    if workers_start:
        start_workers()

    while True:
        ready = wait([
            from_state,
            from_user,
            from_file
        ])

        if from_state in ready:
            input_message = from_state.recv()
            operation = input_message['operation']
            if 'pattern' in input_message:
                if operation == OP_CREATE:
                    add_pattern(input_message['pattern'])
                elif operation == OP_DELETED:
                    remove_pattern(input_message['pattern'])
            elif 'recipe' in input_message:
                if operation == OP_CREATE:
                    add_recipe(input_message['recipe'])
                elif operation == OP_DELETED:
                    remove_recipe(input_message['recipe'])

        elif from_user in ready:
            input_message = from_user.recv()
            operation = input_message[0]
            args = input_message[1]

            if operation == 'start_workers':
                result = start_workers()
                to_user.send(result)

            elif operation == 'stop_workers':
                result = stop_workers()
                to_user.send(result)

            elif operation == 'check_running_status':
                result = check_running_status()
                to_user.send(result)

            elif operation == 'get_running_status':
                result = get_running_status()
                to_user.send(result)

            elif operation == 'stop_runner':
                result = stop_runner(clear_jobs=args)
                to_user.send(result)

            elif operation == 'get_all_jobs':
                result = get_all_jobs()
                to_user.send(result)

            elif operation == 'get_queued_jobs':
                result = get_queued_jobs()
                to_user.send(result)

            elif operation == 'get_all_input_paths':
                result = get_all_input_paths()
                to_user.send(result)

            elif operation == 'check_status':
                result = check_status()
                to_user.send(result)

            elif operation == 'add_pattern':
                result = add_pattern_dir(args)
                to_user.send(result)

            elif operation == 'modify_pattern':
                result = modify_pattern_dir(args)
                to_user.send(result)

            elif operation == 'remove_pattern':
                result = remove_pattern_dir(args)
                to_user.send(result)

            elif operation == 'add_recipe':
                result = add_recipe_dir(args)
                to_user.send(result)

            elif operation == 'modify_recipe':
                result = modify_recipe_dir(args)
                to_user.send(result)

            elif operation == 'remove_recipe':
                result = remove_recipe_dir(args)
                to_user.send(result)

            elif operation == 'check_recipes':
                result = check_recipes()
                to_user.send(result)

            elif operation == 'check_patterns':
                result = check_patterns()
                to_user.send(result)

            elif operation == 'check_rules':
                result = check_rules()
                to_user.send(result)

            elif operation == 'check_jobs':
                result = check_jobs()
                to_user.send(result)

            elif operation == 'check_queue':
                result = check_queue()
                to_user.send(result)

            elif operation == 'kill':
                to_user.send('dead')
                return

            else:
                raise Exception('Unknown message format: %s' % input_message)

        elif from_file in ready:
            input_message = from_file.recv()
            handle_event(input_message)


def job_queue(from_admin, to_admin, from_worker_readers, to_worker_writers,
              to_logger, job_home):
    queue = []
    worker_module_lists = []

    all_inputs = [from_admin]

    for channel_reader in from_worker_readers:
        all_inputs.append(channel_reader)
        worker_module_lists.append([])

    while True:
        ready = wait(all_inputs)

        if from_admin in ready:
            input_message = from_admin.recv()
            if input_message == 'get_queue':
                current_queue = copy.deepcopy(queue)
                to_admin.send(current_queue)

            elif input_message == 'kill':
                to_admin.send('dead')
                return

            # submitting new job
            else:
                queue.append(input_message)

        # Is from worker
        else:
            for i in range(len(from_worker_readers)):
                if from_worker_readers[i] in ready:
                    input_message = from_worker_readers[i].recv()
                    to_worker = to_worker_writers[i]
                    # Is module list
                    if isinstance(input_message, list):
                        worker_module_lists[i] = input_message
                    if input_message == 'request':
                        assigned_job = None
                        for job_id in queue:
                            job_dir = os.path.join(job_home, job_id)
                            meta_path = os.path.join(job_dir, META_FILE)
                            job_data = read_yaml(meta_path)

                            requirements = job_data[JOB_REQUIREMENTS]
                            missing_requirement = False
                            if 'dependencies' in requirements:
                                for requirement in \
                                        requirements['dependencies']:
                                    if requirement not in \
                                            worker_module_lists[i]:
                                        missing_requirement = True
                            if not missing_requirement:
                                assigned_job = job_id
                                break
                            else:
                                to_logger.send(
                                    (
                                        'job_queue.queue request',
                                        "Could not assign job %s to worker "
                                        "%s as missing one or more "
                                        "requirement from %s."
                                        % (job_id, i, requirements)
                                    )
                                )
                        if assigned_job:
                            queue.remove(assigned_job)

                            to_logger.send(
                                (
                                    'job_queue.queue request',
                                    "Assigning job %s" % assigned_job
                                )
                            )
                        to_worker.send(assigned_job)


def job_processor(processing_method, processing_method_args, from_timer,
                  to_timer, from_admin, to_admin, to_queue, from_queue,
                  to_logger, processor_id, job_home, output_data):
    state = 'stopped'

    to_timer.send('sleep')

    module_list = [p.project_name for p in pkg_resources.working_set]
    to_queue.send(module_list)

    while True:
        ready = wait([from_admin, from_timer])

        if from_admin in ready:
            input_message = from_admin.recv()

            if input_message == 'start':
                state = 'running'

            elif input_message == 'check':
                to_admin.send(state)

            elif input_message == 'stop':
                state = 'stopped'

            elif input_message == 'kill':
                to_timer.send('kill')
                to_admin.send('dead')
                return

        elif from_timer in ready:
            input_message = from_timer.recv()

            if input_message == 'done' and state == 'running':
                to_queue.send('request')

                job_id = from_queue.recv()

                if job_id:
                    to_logger.send(
                        (
                            'job_processor.worker %s' % processor_id,
                            "Found job %s" % job_id
                        )
                    )

                    processing_method_args["job_id"] = job_id
                    processing_method_args["job_home"] = job_home
                    processing_method_args["output_data"] = output_data

                    status, msg = processing_method(processing_method_args)

                    if not status:
                        to_logger.send(
                            (
                                'job_processor.worker %s' % processor_id,
                                "Job worker encountered an error. %s" % msg
                            )
                        )

                    to_logger.send(
                        (
                            'job_processor.worker %s' % processor_id,
                            "Completed job %s" % job_id
                        )
                    )
                else:
                    to_logger.send(
                        (
                            'job_processor.worker %s' % processor_id,
                            "Worker %s found no job in queue" % processor_id
                        )
                    )

            to_timer.send('sleep')


def local_processing(processing_method_args):
    job_id = processing_method_args["job_id"]
    job_home = processing_method_args["job_home"]
    output_data = processing_method_args["output_data"]

    job_dir = os.path.join(job_home, job_id)
    meta_path = os.path.join(job_dir, META_FILE)
    base_path = os.path.join(job_dir, BASE_FILE)
    param_path = os.path.join(job_dir, PARAMS_FILE)
    job_path = os.path.join(job_dir, JOB_FILE)
    result_path = os.path.join(job_dir, RESULT_FILE)

    job_data = read_yaml(meta_path)

    job_data[JOB_STATUS] = RUNNING
    job_data[JOB_START_TIME] = datetime.now()

    write_yaml(job_data, meta_path)

    error = False
    cmd = 'notebook_parameterizer ' \
          + base_path + ' ' \
          + param_path + ' ' \
          + '-o ' + job_path
    try:
        sub = subprocess.Popen(cmd,
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE,
                               shell=True)
        # TODO: implement a timeout (max simulation time)
        (stdout, stderr) = sub.communicate()
        if stderr:
            error = stderr

    except Exception as ex:
        error = ex

    if not os.path.exists(job_path) or error:
        job_data[JOB_STATUS] = FAILED
        job_data[JOB_END_TIME] = datetime.now()
        msg = 'Job file %s was not created successfully' \
              % job_id
        if error:
            msg += '. %s' % error
        job_data[JOB_ERROR] = msg
        write_yaml(job_data, meta_path)
        return False, msg

    cmd = 'papermill ' \
          + job_path + ' ' \
          + result_path
    try:
        sub = subprocess.Popen(cmd,
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE,
                               shell=True)
        # TODO: implement a timeout (max simulation time)
        (stdout, stderr) = sub.communicate()
    except Exception as ex:
        error = ex

    if not os.path.exists(result_path) or error:
        job_data[JOB_STATUS] = FAILED
        job_data[JOB_END_TIME] = datetime.now()
        msg = 'Result file %s was not created successfully'
        if error:
            msg += '. %s' % error
        job_data[JOB_ERROR] = msg
        write_yaml(job_data, meta_path)
        return False, msg

    job_data[JOB_STATUS] = DONE
    job_data[JOB_END_TIME] = datetime.now()
    write_yaml(job_data, meta_path)

    job_output_dir = os.path.join(output_data, job_id)

    shutil.move(job_dir, job_output_dir)

    return True, ''


def ssh_processing(processing_method_args):
    job_id = processing_method_args["job_id"]
    job_home = processing_method_args["job_home"]
    output_data = processing_method_args["output_data"]

    resource_hostname = "localhost"
    resource_username = "patch_of_scotland"
    resource_rsa = "/home/patch_of_scotland/.ssh/id_rsa_skimbleshanks.pub"
    resource_mount_point = "test_tmp_dir/mountpoint"

    server_hostname = socket.getfqdn()
    server_username = os.getlogin()
    server_rsa_private = "/home/patch_of_scotland/.ssh/id_rsa_sshfs_testing"
    server_rsa_public = "/home/patch_of_scotland/.ssh/id_rsa_sshfs_testing.pub"
    server_known_hosts = "/home/patch_of_scotland/.ssh/known_hosts_sshfs_testing"
    server_authorised_keys = "/home/patch_of_scotland/.ssh/authorized_keys"
    server_mount_target = "/home/patch_of_scotland/TestSpace/sshfs/onHost"

    ssh_client = paramiko.SSHClient()
    # This will do for now but should be more rigorous in future
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh_client.connect(
        hostname=resource_hostname,
        username=resource_username,
        key_filename=resource_rsa,
    )
    sftp_client = ssh_client.open_sftp()

    ssh_client.exec_command(f"mkdir -p {resource_mount_point}")

    sftp_client.put("/home/patch_of_scotland/.ssh/id_rsa_skimbleshanks test_tmp_dir/id_rsa_skimbleshanks")

    ssh_client.exec_command(f"mkdir {resource_mount_point}")

    _, stdout, stderr = ssh_client.exec_command(f"sshfs {server_username}@{server_hostname}:{server_mount_target} {resource_mount_point} -oIdentityFile={server_rsa_private} -oUserKnownHostsFile={server_known_hosts} -o reconnect -C")

    print(stdout.readlines())
    print(stderr.readlines())

    _, stdout, stderr = ssh_client.exec_command(f"fusermount -u {resource_mount_point}")

    print(stdout.readlines())
    print(stderr.readlines())

    ssh_client.exec_command("rm -rf test_tmp_dir")

    sftp_client.close()
    ssh_client.close()


def setup_ssh_files():
    key = rsa.generate_private_key(
        backend=cryptography_default_backend(),
        public_exponent=65537,
        key_size=2048
    )
    private_key = key.private_bytes(
        cryptography_serialisation.Encoding.PEM,
        cryptography_serialisation.PrivateFormat.PKCS8,
        cryptography_serialisation.NoEncryption()
    )
    public_key = key.public_key().public_bytes(
        cryptography_serialisation.Encoding.OpenSSH,
        cryptography_serialisation.PublicFormat.OpenSSH
    )
    with open(server_rsa_private, 'xb') as private_key_file:
        private_key_file.write(private_key)
    os.chmod(server_rsa_private, stat.S_IRUSR | stat.S_IWUSR)

    with open(server_rsa_public, 'xb') as public_key_file:
        public_key_file.write(public_key)
    os.chmod(server_rsa_public,
             stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IROTH)

    with open(server_authorised_keys, 'ab') as authorised_keys_file:
        authorised_keys_file.write(public_key)
        authorised_keys_file.write(bytes("\n", 'utf-8'))

    cmd = f"ssh-keyscan -H localhost"
    process = subprocess.Popen(cmd.split(), stdout=subprocess.PIPE)
    output, error = process.communicate()
    with open(server_known_hosts, 'xb') as known_hosts_file:
        known_hosts_file.write(output)


def clean_up_ssh():
    try:
        if os.path.exists(server_rsa_private):
            os.remove(server_rsa_private)
    except NameError:
        pass
    try:
        if os.path.exists(server_rsa_public):
            os.remove(server_rsa_public)
    except NameError:
        pass
    try:
        if os.path.exists(server_known_hosts):
            os.remove(server_known_hosts)
    except NameError:
        pass

    authorised_keys_lines = []
    try:
        with open(server_authorised_keys, 'r') as authorised_keys_file:
            authorised_keys_lines = authorised_keys_file.readlines()
    except NameError:
        pass
    try:
        with open(server_authorised_keys, 'w') as authorised_keys_file:
            for line in authorised_keys_lines:
                if line.strip("\n") != public_key.decode('utf-8'):
                    authorised_keys_file.write(line)
    except NameError:
        pass


def worker_timer(from_worker, to_worker, worker_id, wait_time=10):
    while True:
        msg = from_worker.recv()

        if msg == 'sleep':
            time.sleep(wait_time + (worker_id % wait_time))

            to_worker.send('done')
        elif msg == 'kill':
            to_worker.send('dead')
            return


def logger(all_input_channel_readers, print_logging=True, file_logging=False):
    runner_log_file = create_localrunner_logfile(debug_mode=file_logging)

    while True:
        ready = wait(all_input_channel_readers)

        for reader in all_input_channel_readers:
            if reader in ready:
                input_message = reader.recv()

                write_to_log(
                    runner_log_file,
                    input_message[0],
                    input_message[1]
                )

                if print_logging:
                    print(str(input_message[0]) + ': ' + str(input_message[1]))

                continue


class WorkflowRunner:
    def __init__(self, path, workers, patterns=None, recipes=None,
                 meow_data=RUNNER_DATA, job_data=JOB_DIR,
                 output_data=OUTPUT_DATA, daemon=False, reuse_vgrid=True,
                 start_workers=True, retro_active_jobs=True,
                 print_logging=True, file_logging=False, wait_time=10):

        valid_dir_path(path, 'path')
        valid_runner_workers(workers)
        check_input(patterns, dict, PATTERNS, or_none=True)
        check_input(recipes, dict, RECIPES, or_none=True)
        valid_dir_path(meow_data, 'meow_data')
        valid_dir_path(job_data, 'job_data')
        valid_dir_path(output_data, 'output_data')
        check_input(daemon, bool, 'daemon')
        check_input(reuse_vgrid, bool, 'reuse_vgrid')
        check_input(start_workers, bool, 'start_workers')
        check_input(retro_active_jobs, bool, 'retro_active_jobs')
        check_input(print_logging, bool, 'print_logging')
        check_input(file_logging, bool, 'file_logging')
        check_input(wait_time, int, 'wait_time')

        make_dir(path, can_exist=reuse_vgrid)
        make_dir(job_data)
        if meow_data == RUNNER_DATA:
            make_dir(meow_data, ensure_clean=True)
        else:
            make_dir(meow_data)
        make_dir(output_data)
        make_dir(get_runner_patterns(meow_data), ensure_clean=True)
        make_dir(get_runner_recipes(meow_data), ensure_clean=True)

        user_to_admin_reader, user_to_admin_writer = Pipe(duplex=False)
        admin_to_user_reader, admin_to_user_writer = Pipe(duplex=False)
        user_to_logger_reader, user_to_logger_writer = Pipe(duplex=False)

        self.user_to_admin = user_to_admin_writer
        self.admin_to_user = admin_to_user_reader

        state_to_admin_reader, state_to_admin_writer = Pipe(duplex=False)
        state_to_logger_reader, state_to_logger_writer = Pipe(duplex=False)

        file_to_admin_reader, file_to_admin_writer = Pipe(duplex=False)
        file_to_logger_reader, file_to_logger_writer = Pipe(duplex=False)

        admin_to_queue_reader, admin_to_queue_writer = Pipe(duplex=False)
        queue_to_admin_reader, queue_to_admin_writer = Pipe(duplex=False)
        admin_to_logger_reader, admin_to_logger_writer = Pipe(duplex=False)

        queue_to_logger_reader, queue_to_logger_writer = Pipe(duplex=False)

        all_logger_inputs = [
            user_to_logger_reader,
            state_to_logger_reader,
            file_to_logger_reader,
            admin_to_logger_reader,
            queue_to_logger_reader,
        ]

        workers_and_timers_list = []
        admin_to_workers = []
        worker_to_admins = []
        worker_to_queues = []
        queue_to_workers = []
        if isinstance(workers, int):
            workers = [{}] * workers
        for processor_id, worker_type in enumerate(workers):
            worker_to_timer_reader, worker_to_timer_writer = Pipe(duplex=False)
            timer_to_worker_reader, timer_to_worker_writer = Pipe(duplex=False)
            admin_to_worker_reader, admin_to_worker_writer = Pipe(duplex=False)
            worker_to_admin_reader, worker_to_admin_writer = Pipe(duplex=False)
            worker_to_queue_reader, worker_to_queue_writer = Pipe(duplex=False)
            queue_to_worker_reader, queue_to_worker_writer = Pipe(duplex=False)
            worker_to_logger_reader, worker_to_logger_writer = Pipe(duplex=False)

            # Defaults, used in local processing
            processing_type = local_processing
            processing_arguments = {}

            if is_valid_ssh_worker(worker_type)[0]:
                processing_type = ssh_processing
                processing_arguments = {}

            worker = Process(
                target=job_processor,
                args=(
                    processing_type,
                    processing_arguments,
                    timer_to_worker_reader,
                    worker_to_timer_writer,
                    admin_to_worker_reader,
                    worker_to_admin_writer,
                    worker_to_queue_writer,
                    queue_to_worker_reader,
                    worker_to_logger_writer,
                    processor_id,
                    job_data,
                    output_data
                )
            )

            timer = Process(
                target=worker_timer,
                args=(
                    worker_to_timer_reader,
                    timer_to_worker_writer,
                    processor_id,
                    wait_time
                )
            )

            workers_and_timers_list.append(worker)
            workers_and_timers_list.append(timer)
            admin_to_workers.append(admin_to_worker_writer)
            worker_to_admins.append(worker_to_admin_reader)
            worker_to_queues.append(worker_to_queue_reader)
            queue_to_workers.append(queue_to_worker_writer)
            all_logger_inputs.append(worker_to_logger_reader)

        administrator_process = Process(
            target=administrator,
            args=(
                user_to_admin_reader,
                admin_to_user_writer,
                state_to_admin_reader,
                file_to_admin_reader,
                admin_to_queue_writer,
                queue_to_admin_reader,
                admin_to_workers,
                worker_to_admins,
                admin_to_logger_writer,
                path,
                job_data,
                meow_data,
                retro_active_jobs,
                start_workers
            )
        )

        job_queue_process = Process(
            target=job_queue,
            args=(
                admin_to_queue_reader,
                queue_to_admin_writer,
                worker_to_queues,
                queue_to_workers,
                queue_to_logger_writer,
                job_data
            )
        )

        logger_process = Process(
            target=logger,
            args=(
                all_logger_inputs,
                print_logging,
                file_logging
            )
        )

        self.process_list = [
            job_queue_process,
            administrator_process,
        ]

        self.logger_process = logger_process
        for worker_or_timer in workers_and_timers_list:
            self.process_list.append(worker_or_timer)

        # Start all non-monitoring processes
        self.run()

        state_monitor = LocalWorkflowStateMonitor(
            state_to_admin_writer, state_to_logger_writer, meow_data)
        self.state_monitor_process = Observer()
        self.state_monitor_process.schedule(
            state_monitor,
            meow_data,
            recursive=True
        )

        file_monitor = LocalWorkflowFileMonitor(
            file_to_admin_writer, file_to_logger_writer)
        self.file_monitor_process = Observer()
        self.file_monitor_process.schedule(
            file_monitor,
            path,
            recursive=True
        )


        self.state_monitor_process.start()
        self.file_monitor_process.start()

        admin_to_logger_writer.send(
            (
                'WorkflowRunner._init',
                 'Started WorkflowRunner processes. '
            )
        )

        if patterns:
            for name, pattern in patterns.items():
                admin_to_logger_writer.send(
                    (
                        'WorkflowRunner._init',
                        "Adding pattern %s. " % name
                    )
                )

                write_dir_pattern(pattern, directory=meow_data)

        admin_to_logger_writer.send(
            (
                'WorkflowRunner._init',
                'Added all predefined patterns. '
            )
        )

        if recipes:
            for name, recipe in recipes.items():
                admin_to_logger_writer.send(
                    (
                        'WorkflowRunner._init',
                        "Adding recipe %s. " % name
                    )
                )

                write_dir_recipe(recipe, directory=meow_data)

        admin_to_logger_writer.send(
            (
                'WorkflowRunner._init',
                 'Added all predefined recipes. '
            )
        )

        if not daemon:
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                self.stop_runner()

    def __del__(self):
        clean_up_ssh()

    def run(self):
        self.logger_process.start()
        for my_process in self.process_list:
            my_process.start()

    def join(self):
        self.file_monitor_process.join()
        self.state_monitor_process.join()
        for my_process in self.process_list:
            my_process.join()
        self.logger_process.join()

    def stop(self):
        self.file_monitor_process.stop()
        self.file_monitor_process.join()
        self.state_monitor_process.stop()
        self.state_monitor_process.join()
        for my_process in self.process_list:
            if hasattr(my_process, 'terminate'):
                my_process.terminate()
            else:
                my_process.stop()
            my_process.join()
        self.logger_process.terminate()
        self.logger_process.join()

    def start_workers(self):
        self.user_to_admin.send(
            (
                'start_workers',
                None
            )
        )
        result = self.admin_to_user.recv()
        return result

    def stop_workers(self):
        self.user_to_admin.send(
            (
                'stop_workers',
                None
            )
        )
        result = self.admin_to_user.recv()
        return result

    def check_running_status(self):
        self.user_to_admin.send(
            (
                'check_running_status',
                None
            )
        )
        result = self.admin_to_user.recv()
        return result

    def get_running_status(self):
        self.user_to_admin.send(
            (
                'get_running_status',
                None
            )
        )
        result = self.admin_to_user.recv()
        return result

    def stop_runner(self, clear_jobs=False):
        self.user_to_admin.send(
            (
                'stop_runner',
                clear_jobs
            )
        )
        result = self.admin_to_user.recv()
        self.stop()
        self.join()
        return result

    def get_all_jobs(self):
        self.user_to_admin.send(
            (
                'get_all_jobs',
                None
            )
        )
        result = self.admin_to_user.recv()
        return result

    def get_queued_jobs(self):
        self.user_to_admin.send(
            (
                'get_queued_jobs',
                None
            )
        )
        result = self.admin_to_user.recv()
        return result

    def get_all_input_paths(self):
        self.user_to_admin.send(
            (
                'get_all_input_paths',
                None
            )
        )
        result = self.admin_to_user.recv()
        return result

    def check_status(self):
        self.user_to_admin.send(
            (
                'check_status',
                None
            )
        )
        result = self.admin_to_user.recv()
        return result

    def add_pattern(self, pattern):
        self.user_to_admin.send(
            (
                'add_pattern',
                pattern
            )
        )
        result = self.admin_to_user.recv()
        return result

    def modify_pattern(self, pattern):
        self.user_to_admin.send(
            (
                'modify_pattern',
                pattern
            )
        )
        result = self.admin_to_user.recv()
        return result

    def remove_pattern(self, pattern):
        self.user_to_admin.send(
            (
                'remove_pattern',
                pattern
            )
        )
        result = self.admin_to_user.recv()
        return result

    def add_recipe(self, recipe):
        self.user_to_admin.send(
            (
                'add_recipe',
                recipe
            )
        )
        result = self.admin_to_user.recv()
        return result

    def modify_recipe(self, recipe):
        self.user_to_admin.send(
            (
                'modify_recipe',
                recipe
            )
        )
        result = self.admin_to_user.recv()
        return result

    def remove_recipe(self, recipe):
        self.user_to_admin.send(
            (
                'remove_recipe',
                recipe
            )
        )
        result = self.admin_to_user.recv()
        return result

    def check_recipes(self):
        self.user_to_admin.send(
            (
                'check_recipes',
                None
            )
        )
        result = self.admin_to_user.recv()
        return result

    def check_patterns(self):
        self.user_to_admin.send(
            (
                'check_patterns',
                None
            )
        )
        result = self.admin_to_user.recv()
        return result

    def check_rules(self):
        self.user_to_admin.send(
            (
                'check_rules',
                None
            )
        )
        result = self.admin_to_user.recv()
        return result

    def check_jobs(self):
        self.user_to_admin.send(
            (
                'check_jobs',
                None
            )
        )
        result = self.admin_to_user.recv()
        return result

    def check_queue(self):
        self.user_to_admin.send(
            (
                'check_queue',
                None
            )
        )
        result = self.admin_to_user.recv()
        return result


class LocalWorkflowStateMonitor(PatternMatchingEventHandler):
    """
    Event handler to monitor pattern and recipe changes.
    """

    def __init__(
            self, to_admin, to_logger,  meow_data, patterns=None,
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
        self.to_logger = to_logger
        self.to_admin = to_admin
        self.meow_data = meow_data
        self.state_patterns = {}
        self.state_recipes = {}

        self.to_logger.send(
            (
                'LocalWorkflowStateMonitor._init',
                'Setting up new state monitor'
            )
        )

        # Check pre-existing Patterns and Recipes
        runner_patterns = get_runner_patterns(self.meow_data)
        for file_path in os.listdir(runner_patterns):
            try:
                pattern = read_dir_pattern(
                    file_path,
                    directory=self.meow_data
                )

                self.add_pattern(pattern)
            except Exception as exc:
                self.to_logger.send(
                    ('LocalWorkflowStateMonitor._init', str(exc))
                )

        runner_recipes = get_runner_recipes(self.meow_data)
        for file_path in os.listdir(runner_recipes):
            try:
                recipe = read_dir_recipe(
                    file_path,
                    directory=self.meow_data
                )
                # self.to_logger.send(
                #     (
                #         'LocalWorkflowStateMonitor._init',
                #         'Identified pre-existing recipe: %s' % pattern.name
                #     )
                # )
                self.add_recipe(recipe)
            except Exception as exc:
                self.to_logger.send(
                    ('LocalWorkflowStateMonitor._init', str(exc))
                )
        self.to_logger.send(
            (
                'LocalWorkflowStateMonitor._init',
                'Finished identifying pre-existing state'
            )
        )

    def update_rules(self, event):
        """Handle all rule updates"""

        if event.is_directory:
            return

        self.to_logger.send(
            (
                'LocalWorkflowStateMonitor.update_rules',
                "Handling %s rule update at %s"
                % (event.event_type, event.src_path)
            )
        )

        src_path = event.src_path

        try:
            valid_dir_path(src_path, 'src_path')
        except ValueError as ve:
            self.to_logger.send(
                (
                    'LocalWorkflowStateMonitor.update_rules',
                    "Ignoring events at %s. %s" % (src_path, ve)
                )
            )
            return

        event_type = event.event_type
        file_type = ''
        file_path = ''
        try:
            runner_patterns = get_runner_patterns(self.meow_data)
            runner_recipes = get_runner_recipes(self.meow_data)
            if runner_patterns in src_path:
                file_path = src_path[
                            src_path.find(runner_patterns)
                            + len(runner_patterns)+1:]
                file_type = PATTERNS
            elif runner_recipes in src_path:
                file_path = src_path[
                            src_path.find(runner_recipes)
                            + len(runner_recipes)+1:]
                file_type = RECIPES
        except Exception as exc:
            self.to_logger.send(
                (
                    'LocalWorkflowStateMonitor.update_rules-pattern',
                    'Cannot process event at %s due to error: %s'
                    % (src_path, exc)
                )
            )
            return
        if os.path.sep in file_path:
            self.to_logger.send(
                (
                    'LocalWorkflowStateMonitor.update_rules-pattern',
                    'Cannot process nested event at %s' % src_path
                )
            )
            return

        if event_type in ['created', 'modified']:
            if file_type == PATTERNS:
                try:
                    pattern = read_dir_pattern(
                        file_path,
                        directory=self.meow_data
                    )
                    self.to_logger.send(
                        (
                            'LocalWorkflowStateMonitor.update_rules-pattern',
                            "Found pattern: '%s'" % pattern
                        )
                    )
                except Exception as exc:
                    self.to_logger.send(
                        (
                            'LocalWorkflowStateMonitor.update_rules-pattern',
                            str(exc)
                        )
                    )
                    return
                self.add_pattern(pattern)
            elif file_type == RECIPES:
                try:
                    recipe = read_dir_recipe(
                        file_path,
                        directory=self.meow_data
                    )
                except Exception as exc:
                    self.to_logger.send(
                        (
                            'LocalWorkflowStateMonitor.update_rules-recipe',
                            str(exc)
                        )
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
        op = OP_CREATE
        if pattern.name in self.state_patterns:
            if self.state_patterns[pattern.name] == pattern:
                return
            else:
                self.remove_pattern(pattern.name)
                op = OP_MODIFIED
        self.state_patterns[pattern.name] = pattern

        msg = {
            'operation': OP_CREATE,
            'pattern': pattern
        }
        self.to_admin.send(msg)

        self.to_logger.send(
            (
                'LocalWorkflowStateMonitor.add_pattern',
                '%s pattern %s' % (op, pattern)
            )
        )

    def add_recipe(self, recipe):
        op = OP_CREATE
        if recipe[NAME] in self.state_recipes:
            if self.state_recipes[recipe[NAME]] == recipe:
                return
            else:
                self.remove_recipe(recipe[NAME])
                op = OP_MODIFIED
        self.state_recipes[recipe[NAME]] = recipe

        msg = {
            'operation': OP_CREATE,
            'recipe': recipe
        }
        self.to_admin.send(msg)

        self.to_logger.send(
            (
                'LocalWorkflowStateMonitor.add_recipe',
                '%s recipe %s from source %s'
                % (op, recipe[NAME], recipe[SOURCE])
            )
        )

    def remove_pattern(self, pattern_name):
        if pattern_name in self.state_patterns:
            self.state_patterns.pop(pattern_name)

            msg = {
                'operation': OP_DELETED,
                'pattern': pattern_name
            }
            self.to_admin.send(msg)

            self.to_logger.send(
                (
                    'LocalWorkflowStateMonitor.remove_pattern',
                    'Removed pattern %s' % pattern_name
                )
            )
        else:
            self.to_logger.send(
                (
                    'LocalWorkflowStateMonitor.remove_pattern',
                    'Pattern %s was not present in the pattern list to be '
                    'removed' % pattern_name
                )
            )

    def remove_recipe(self, recipe_name):
        if recipe_name in self.state_recipes:
            self.state_recipes.pop(recipe_name)

            msg = {
                'operation': OP_DELETED,
                'recipe': recipe_name
            }
            self.to_admin.send(msg)

            self.to_logger.send(
                (
                    'LocalWorkflowStateMonitor.remove_recipe',
                    'Removed recipe %s' % recipe_name
                )
            )
        else:
            self.to_logger.send(
                (
                    'LocalWorkflowStateMonitor.remove_recipe',
                    'Recipe %s was not present in the recipe list to be '
                    'removed' % recipe_name
                )
            )


class LocalWorkflowFileMonitor(PatternMatchingEventHandler):
    """
    Event handler to schedule jobs according to file events.
    """

    def __init__(
            self, to_admin, to_logger, patterns=None,
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
        self.to_logger = to_logger
        self.to_admin = to_admin
        self.recent_jobs = {}
        self._recent_jobs_lock = threading.Lock()

        self.to_logger.send(
            (
                'LocalWorkflowFileMonitor.__init__',
                'Setting up new file monitor'
            )
        )

    def __handle_trigger(self, event):
        pid = current_process().pid
        event_type = event.event_type
        src_path = event.src_path
        time_stamp = event.time_stamp

        self.to_logger.send(
            (
                'LocalWorkflowFileMonitor.__handle_trigger',
                'Running threaded handler at (%s) to handle %s event at %s at '
                '%s' % (pid, event_type, src_path, time_stamp)
            )
        )

        # This will prevent some job spamming
        self._recent_jobs_lock.acquire()
        try:
            if src_path in self.recent_jobs:
                recent_timestamp = self.recent_jobs[src_path]
                difference = time_stamp - recent_timestamp

                if difference <= 1:
                    self.recent_jobs[src_path] = \
                        max(recent_timestamp, time_stamp)
                    # self.to_logger.send(
                    #     (
                    #         'LocalWorkflowFileMonitor.__handle_trigger',
                    #         'Skipping due to recent hit'
                    #     )
                    # )
                    self._recent_jobs_lock.release()
                    return
                else:
                    self.recent_jobs[src_path] = time_stamp
            else:
                self.recent_jobs[src_path] = time_stamp
        except Exception as ex:
            self._recent_jobs_lock.release()
            raise Exception(ex)
        self._recent_jobs_lock.release()

        self.to_logger.send(
            (
                'LocalWorkflowFileMonitor.__handle_trigger',
                'Event at (%s) sent to admin.' % src_path
            )
        )

        self.to_admin.send(event)

    def run_handler(self, event):
        waiting_for_threaded_resources = True
        while waiting_for_threaded_resources:
            try:
                worker = threading.Thread(
                    target=self.__handle_trigger,
                    args=[event])
                worker.daemon = True
                worker.start()
                waiting_for_threaded_resources = False
            except threading.ThreadError:
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
