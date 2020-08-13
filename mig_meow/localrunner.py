
import os
import time
import shutil
import re
import fnmatch
import threading
import multiprocessing

# This code is heavily based off the 'mig/server/grid_events.py' file
# contained in the MiG source code at: https://sourceforge.net/projects/migrid/

from .constants import RUNNER_DATA, PATTERNS, RECIPES, RUNNER_RECIPES, \
    RUNNER_PATTERNS, NAME, SOURCE, CHAR_LOWERCASE, CHAR_UPPERCASE, CHAR_NUMERIC
from .logging import create_localrunner_logfile, write_to_log
from .fileio import write_dir_pattern, write_dir_recipe, make_dir, \
    read_dir_recipe, read_dir_pattern

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

LOGGER = 'logger'
RULES = 'rules'
RULE_ID = 'id'
RULE_PATH = 'path'
RULE_PATTERN = 'pattern'
RULE_RECIPE = 'recipe'
ADMIN = 'admin'
MONITOR = 'monitor'
DATA = 'data'
JOBS = 'jobs'

QUEUED = 'queued'

recent_jobs = {}
_recent_jobs_lock = threading.Lock()


def generate_rule_id():
    charset = CHAR_UPPERCASE + CHAR_LOWERCASE + CHAR_NUMERIC
    return ''.join(SystemRandom().choice(charset) for _ in range(16))


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


class WorkflowRunner:
    def __init__(self, logging=True):
        runner_log_file = create_localrunner_logfile(debug_mode=logging)

        self.runner_state = {
            PATTERNS: {},
            RECIPES: {},
            RULES: [],
            JOBS: [],
            LOGGER: runner_log_file,
            ADMIN: None,
            MONITOR: None,
            DATA: None
        }

        write_to_log(
            self.runner_state[LOGGER],
            'run_local_workflow',
            'created new log at %s' % self.runner_state[LOGGER],
            to_print=True
        )

    def run_local_workflow(
            self, path, patterns=None, recipes=None, meow_data=RUNNER_DATA,
            daemon=False):
        write_to_log(
            self.runner_state[LOGGER],
            'run_local_workflow',
            'Starting file monitor',
            to_print=True
        )

        make_dir(path)

        workflow_monitor = self.LocalWorkflowMonitor(
            base_path=path,
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
            to_print=True
        )

        make_dir(meow_data, can_exist=False)
        make_dir(RUNNER_PATTERNS, can_exist=False)
        make_dir(RUNNER_RECIPES, can_exist=False)
        self.runner_state[DATA] = meow_data

        workflow_administrator = self.LocalWorkflowAdministrator(
            runner_state=self.runner_state
        )
        administrator_observer = Observer()
        self.runner_state[ADMIN] = administrator_observer
        administrator_observer.schedule(
            workflow_administrator,
            meow_data,
            recursive=True
        )
        administrator_observer.start()

        write_to_log(
            self.runner_state[LOGGER],
            'run_local_workflow',
            'Monitor setup complete'
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
            'Initial Pattern and Recipe definitions complete'
        )

        if not daemon:
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                self.stop_runner()

    def check_running_status(self):
        if not self.runner_state[ADMIN]:
            return False
        if not self.runner_state[MONITOR]:
            return False
        return True

    def stop_runner(self):
        monitor_observer = self.runner_state[MONITOR]
        administrator_observer = self.runner_state[ADMIN]

        monitor_observer.stop()
        administrator_observer.stop()

        monitor_observer.join()
        administrator_observer.join()

        self.runner_state[MONITOR] = None
        self.runner_state[ADMIN] = None

        meow_data = self.runner_state[DATA]
        if os.path.exists(meow_data) and os.path.isdir(meow_data):
            shutil.rmtree(meow_data)

        return True

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
                to_print=True
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
                    to_print=True
                )
                return
            if os.path.sep in file_path:
                write_to_log(
                    self.runner_state[LOGGER],
                    'update_rules-pattern',
                    'Cannot process nested event at %s' % src_path,
                    to_print=True
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
                            to_print=True
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
                            to_print=True
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
                to_print=True
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
                to_print=True
            )

        def remove_pattern(self, pattern_name):
            if pattern_name in self.runner_state[PATTERNS]:
                self.runner_state[PATTERNS].pop(pattern_name)
            self.remove_rules(deleted_pattern_name=pattern_name)
            write_to_log(
                self.runner_state[LOGGER],
                'remove_pattern',
                'Removed pattern %s' % pattern_name,
                to_print=True
            )

        def remove_recipe(self, recipe_name):
            if recipe_name in self.runner_state[RECIPES]:
                self.runner_state[RECIPES].pop(recipe_name)
            self.remove_rules(deleted_recipe_name=recipe_name)
            write_to_log(
                self.runner_state[LOGGER],
                'remove_recipe',
                'Removed recipe %s' % recipe_name,
                to_print=True
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
                        rule = {
                            RULE_ID: generate_rule_id(),
                            RULE_PATTERN: new_pattern.name,
                            RULE_RECIPE: recipe_name,
                            RULE_PATH: input_path
                        }
                        self.runner_state[RULES].append(rule)
                        write_to_log(
                            self.runner_state[LOGGER],
                            'identify_rules-pattern',
                            'Created rule for path: %s with id %s.'
                            % (input_path, rule[RULE_ID]),
                            to_print=True
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
                            rule = {
                                RULE_ID: generate_rule_id(),
                                RULE_PATTERN: name,
                                RULE_RECIPE: recipe_name,
                                RULE_PATH: input_path
                            }
                            self.runner_state[RULES].append(rule)
                            write_to_log(
                                self.runner_state[LOGGER],
                                'identify_rules-recipe',
                                'Created rule for path: %s with id %s.'
                                % (input_path, rule[RULE_ID]),
                                to_print=True
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
                    to_print=True
                )

    class LocalWorkflowMonitor(PatternMatchingEventHandler):
        """
        Event handler to schedule jobs according to file events.
        """

        def __init__(
                self, runner_state=None, base_path=None, patterns=None,
                ignore_patterns=None, ignore_directories=False,
                case_sensitive=False):
            """Constructor"""

            write_to_log(
                runner_state[LOGGER],
                'LocalWorkflowRunner',
                'Starting new workflow runner',
                to_print=True
            )

            PatternMatchingEventHandler.__init__(
                self,
                patterns,
                ignore_patterns,
                ignore_directories,
                case_sensitive
            )
            self.runner_state = runner_state
            self.base_path = base_path

        def start_job(self, path, rule):
            write_to_log(
                self.runner_state[LOGGER],
                'run_handler',
                'Starting new job for %s using rule %s' % (path, rule),
                to_print=True
            )

            job_dict = {
                'pattern': rule[RULE_PATTERN],
                'recipe': rule[RULE_RECIPE],
                'rule': rule[RULE_ID],
                'path': path,
                'status': QUEUED
            }

            self.runner_state[JOBS].append(job_dict)

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
                % (pid, event_type, handle_path, rule[RULE_ID])
            )

            # This will prevent some job spamming
            _recent_jobs_lock.acquire()
            if src_path in recent_jobs:
                if rule[RULE_ID] in recent_jobs[src_path]:
                    recent_timestamp = recent_jobs[src_path][RULE_ID]
                    difference = time_stamp - recent_timestamp

                    if difference <= 1:
                        recent_jobs[src_path][RULE_ID] = \
                            max(recent_timestamp, time_stamp)
                        write_to_log(
                            self.runner_state[LOGGER],
                            '__handle_trigger',
                            'Skipping due to recent hit'
                        )
                        return
                else:
                    recent_jobs[src_path][rule[RULE_ID]] = time_stamp
            else:
                recent_jobs[src_path] = {
                    rule[RULE_ID]: time_stamp
                }
            _recent_jobs_lock.release()

            print("hit rule: %s" % rule)
            self.start_job(src_path, rule)

        def run_handler(self, event):
            src_path = event.src_path
            event_type = event.event_type
            time_stamp = event.time_stamp

            handle_path = src_path.replace(self.base_path, '', 1)
            while handle_path.startswith(os.path.sep):
                handle_path = handle_path[1:]

            write_to_log(
                self.runner_state[LOGGER],
                'run_handler',
                'Handling %s event at %s' % (event_type, handle_path),
                to_print=True
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

