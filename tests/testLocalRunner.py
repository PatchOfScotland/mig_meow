import unittest
import os
import shutil
import time
import numpy as np
import pytest
import pkg_resources

from multiprocessing import Process, Pipe
from watchdog.events import FileCreatedEvent
from watchdog.observers import Observer

from mig_meow.constants import PATTERNS, RECIPES, KEYWORD_DIR, KEYWORD_JOB, \
    KEYWORD_VGRID, KEYWORD_EXTENSION, KEYWORD_PREFIX, KEYWORD_FILENAME, \
    KEYWORD_REL_DIR, KEYWORD_REL_PATH, KEYWORD_PATH, SOURCE, NAME, RECIPE
from mig_meow.fileio import read_dir, read_dir_pattern, read_dir_recipe, \
    make_dir, write_yaml, write_dir_pattern, write_dir_recipe, \
    patten_to_yaml_dict, recipe_to_yaml_dict, read_yaml, write_notebook
from mig_meow.localrunner import WorkflowRunner, RUNNER_DATA, RULE_PATH, \
    RULE_PATTERN, RULE_RECIPE, replace_keywords, worker_timer, job_processor, \
    JOB_DIR, OUTPUT_DATA, job_queue, LocalWorkflowFileMonitor, \
    LocalWorkflowStateMonitor, administrator, OP_CREATE, OP_DELETED, \
    META_FILE, BASE_FILE, PARAMS_FILE
from mig_meow.meow import Pattern

TESTING_VGRID = 'testing_directory'

STANDARD_RULES = [
    {
        'pattern': 'adder',
        'recipe': 'add',
        'path': 'initial_data/*'
    },
    {
        'pattern': 'second_mult',
        'recipe': 'mult',
        'path': 'data_1/data_*.npy'
    },
    {
        'pattern': 'first_mult',
        'recipe': 'mult',
        'path': 'initial_data/*'
    },
    {
        'pattern': 'third_choo',
        'recipe': 'choo',
        'path': 'data_2/*'
    }
]


def check_logger_input(tester, logger_input, title, message):
    tester.assertIsInstance(logger_input, tuple)
    tester.assertEqual(len(logger_input), 2)
    tester.assertEqual(logger_input[0], title)
    tester.assertEqual(logger_input[1], message)


class WorkflowTest(unittest.TestCase):
    def setUp(self):
        if os.path.exists(TESTING_VGRID):
            raise Exception(
                "Required testing location '%s' is already in use"
                % TESTING_VGRID
            )

    def tearDown(self):
        if os.path.exists(TESTING_VGRID):
            shutil.rmtree(TESTING_VGRID)
        if os.path.exists(RUNNER_DATA):
            shutil.rmtree(RUNNER_DATA)
        if os.path.exists(JOB_DIR):
            shutil.rmtree(JOB_DIR)
        if os.path.exists(OUTPUT_DATA):
            shutil.rmtree(OUTPUT_DATA)

    @pytest.mark.timeout(5)
    def testTimerProcess(self):
        to_timer_reader, to_timer_writer = Pipe(duplex=False)
        from_timer_reader, from_timer_writer = Pipe(duplex=False)

        timer = Process(
            target=worker_timer,
            args=(
                to_timer_reader,
                from_timer_writer,
                0,
                3
            )
        )

        start_time = time.time()

        timer.start()
        self.assertTrue(timer.is_alive())

        to_timer_writer.send('sleep')
        msg = from_timer_reader.recv()
        finish_time = time.time()

        self.assertTrue(finish_time - start_time >= 3)
        self.assertEqual(msg, 'done')

        to_timer_writer.send('kill')
        msg = from_timer_reader.recv()

        timer.join()
        self.assertEqual(msg, 'dead')
        self.assertFalse(timer.is_alive())

    @pytest.mark.timeout(5)
    def testWorkerProcessAdminInteractions(self):
        make_dir(JOB_DIR)
        make_dir(OUTPUT_DATA)

        worker_to_timer_reader, worker_to_timer_writer = Pipe(duplex=False)
        timer_to_worker_reader, timer_to_worker_writer = Pipe(duplex=False)
        admin_to_worker_reader, admin_to_worker_writer = Pipe(duplex=False)
        worker_to_admin_reader, worker_to_admin_writer = Pipe(duplex=False)
        worker_to_queue_reader, worker_to_queue_writer = Pipe(duplex=False)
        queue_to_worker_reader, queue_to_worker_writer = Pipe(duplex=False)
        worker_to_logger_reader, worker_to_logger_writer = Pipe(duplex=False)

        worker = Process(
            target=job_processor,
            args=(
                timer_to_worker_reader,
                worker_to_timer_writer,
                admin_to_worker_reader,
                worker_to_admin_writer,
                worker_to_queue_writer,
                queue_to_worker_reader,
                worker_to_logger_writer,
                0,
                JOB_DIR,
                OUTPUT_DATA
            )
        )

        worker.start()
        self.assertTrue(worker.is_alive())

        msg = worker_to_timer_reader.recv()
        self.assertEqual(msg, 'sleep')

        admin_to_worker_writer.send('check')
        msg = worker_to_admin_reader.recv()
        self.assertEqual(msg, 'stopped')

        admin_to_worker_writer.send('start')
        admin_to_worker_writer.send('check')
        msg = worker_to_admin_reader.recv()
        self.assertEqual(msg, 'running')

        admin_to_worker_writer.send('stop')
        admin_to_worker_writer.send('check')
        msg = worker_to_admin_reader.recv()
        self.assertEqual(msg, 'stopped')

        admin_to_worker_writer.send('kill')
        msg = worker_to_admin_reader.recv()
        self.assertEqual(msg, 'dead')

        worker.join()
        self.assertFalse(worker.is_alive())

    @pytest.mark.timeout(5)
    def testQueueProcessAdminInteractions(self):
        admin_to_queue_reader, admin_to_queue_writer = Pipe(duplex=False)
        queue_to_admin_reader, queue_to_admin_writer = Pipe(duplex=False)
        queue_to_logger_reader, queue_to_logger_writer = Pipe(duplex=False)

        worker_to_queues = []
        queue_to_workers = []

        job_queue_process = Process(
            target=job_queue,
            args=(
                admin_to_queue_reader,
                queue_to_admin_writer,
                worker_to_queues,
                queue_to_workers,
                queue_to_logger_writer,
                JOB_DIR
            )
        )

        job_queue_process.start()
        self.assertTrue(job_queue_process.is_alive())

        admin_to_queue_writer.send('get_queue')
        msg = queue_to_admin_reader.recv()
        self.assertEqual(msg, [])

        admin_to_queue_writer.send('0123456789')
        admin_to_queue_writer.send('get_queue')
        msg = queue_to_admin_reader.recv()
        self.assertEqual(msg, ['0123456789'])

        admin_to_queue_writer.send('kill')
        msg = queue_to_admin_reader.recv()
        self.assertEqual(msg, 'dead')

        job_queue_process.join()
        self.assertFalse(job_queue_process.is_alive())

    @pytest.mark.timeout(5)
    def testFileMonitorProcess(self):
        make_dir(TESTING_VGRID)

        file_to_admin_reader, file_to_admin_writer = Pipe(duplex=False)
        file_to_logger_reader, file_to_logger_writer = Pipe(duplex=False)

        file_monitor = LocalWorkflowFileMonitor(
            file_to_admin_writer, file_to_logger_writer)
        file_monitor_process = Observer()
        file_monitor_process.schedule(
            file_monitor,
            TESTING_VGRID,
            recursive=True
        )

        file_monitor_process.start()
        self.assertTrue(file_monitor_process.is_alive())

        data = {
            'key': 'value'
        }
        file_path = os.path.join(TESTING_VGRID, 'data')
        write_yaml(data, file_path)
        self.assertTrue(os.path.exists(file_path))

        msg = file_to_admin_reader.recv()
        print(msg)
        self.assertIsInstance(msg, FileCreatedEvent)
        self.assertEqual(msg.src_path, file_path)

        file_monitor_process.stop()
        file_monitor_process.join()
        self.assertFalse(file_monitor_process.is_alive())

    @pytest.mark.timeout(5)
    def testStateMonitorProcess(self):
        make_dir(RUNNER_DATA)
        make_dir(os.path.join(RUNNER_DATA, PATTERNS))
        make_dir(os.path.join(RUNNER_DATA, RECIPES))

        state_to_admin_reader, state_to_admin_writer = Pipe(duplex=False)
        state_to_logger_reader, state_to_logger_writer = Pipe(duplex=False)

        state_monitor = LocalWorkflowStateMonitor(
            state_to_admin_writer, state_to_logger_writer, RUNNER_DATA)
        state_monitor_process = Observer()
        state_monitor_process.schedule(
            state_monitor,
            RUNNER_DATA,
            recursive=True
        )

        state_monitor_process.start()
        self.assertTrue(state_monitor_process.is_alive())

        data = read_dir(directory='examples/meow_directory')
        pattern = data['patterns']['adder']
        recipe = data['recipes']['add']

        write_dir_pattern(pattern, directory=RUNNER_DATA)
        pattern_path = os.path.join(RUNNER_DATA, PATTERNS, 'adder')
        self.assertTrue(os.path.exists(pattern_path))

        msg = state_to_admin_reader.recv()
        self.assertIsInstance(msg, dict)
        self.assertIn('operation', msg)
        self.assertEqual(msg['operation'], OP_CREATE)
        self.assertIn('pattern', msg)
        self.assertIsInstance(msg['pattern'], Pattern)
        self.assertEqual(pattern, msg['pattern'])

        os.remove(pattern_path)
        self.assertFalse(os.path.exists(pattern_path))

        msg = state_to_admin_reader.recv()
        self.assertIsInstance(msg, dict)
        self.assertIn('operation', msg)
        self.assertEqual(msg['operation'], OP_DELETED)
        self.assertIn('pattern', msg)
        self.assertIsInstance(msg['pattern'], str)
        self.assertEqual(msg['pattern'], 'adder')

        write_dir_recipe(recipe, directory=RUNNER_DATA)
        recipe_path = os.path.join(RUNNER_DATA, RECIPES, 'add')
        self.assertTrue(os.path.exists(recipe_path))

        msg = state_to_admin_reader.recv()
        self.assertIsInstance(msg, dict)
        self.assertIn('operation', msg)
        self.assertEqual(msg['operation'], OP_CREATE)
        self.assertIn('recipe', msg)
        self.assertIsInstance(msg['recipe'], dict)
        self.assertEqual(recipe, msg['recipe'])

        os.remove(recipe_path)
        self.assertFalse(os.path.exists(recipe_path))

        msg = state_to_admin_reader.recv()
        self.assertIsInstance(msg, dict)
        self.assertIn('operation', msg)
        self.assertEqual(msg['operation'], OP_DELETED)
        self.assertIn('recipe', msg)
        self.assertIsInstance(msg['recipe'], str)
        self.assertEqual(msg['recipe'], 'add')

        state_monitor_process.stop()
        state_monitor_process.join()
        self.assertFalse(state_monitor_process.is_alive())

    @pytest.mark.timeout(5)
    def testAdminProcessUserInteractions(self):
        data = read_dir(directory='examples/meow_directory')
        pattern = data['patterns']['adder']
        recipe = data['recipes']['add']

        user_to_admin_reader, user_to_admin_writer = Pipe(duplex=False)
        admin_to_user_reader, admin_to_user_writer = Pipe(duplex=False)
        state_to_admin_reader, state_to_admin_writer = Pipe(duplex=False)
        file_to_admin_reader, file_to_admin_writer = Pipe(duplex=False)
        admin_to_queue_reader, admin_to_queue_writer = Pipe(duplex=False)
        queue_to_admin_reader, queue_to_admin_writer = Pipe(duplex=False)
        admin_to_logger_reader, admin_to_logger_writer = Pipe(duplex=False)
        admin_to_workers = []
        worker_to_admins = []

        admin_to_worker_reader, admin_to_worker_writer = Pipe(duplex=False)
        worker_to_admin_reader, worker_to_admin_writer = Pipe(duplex=False)

        admin_to_workers.append(admin_to_worker_writer)
        worker_to_admins.append(worker_to_admin_reader)

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
                TESTING_VGRID,
                JOB_DIR,
                RUNNER_DATA,
                True,
                False
            )
        )

        administrator_process.start()
        self.assertTrue(administrator_process.is_alive())

        user_to_admin_writer.send(('start_workers', None))
        msg = admin_to_worker_reader.recv()
        self.assertEqual(msg, 'start')
        msg = admin_to_user_reader.recv()
        self.assertTrue(msg)

        user_to_admin_writer.send(('stop_workers', None))
        msg = admin_to_worker_reader.recv()
        self.assertEqual(msg, 'stop')
        msg = admin_to_user_reader.recv()
        self.assertTrue(msg)

        user_to_admin_writer.send(('get_running_status', None))
        msg = admin_to_worker_reader.recv()
        self.assertEqual(msg, 'check')
        worker_to_admin_writer.send('running')
        msg = admin_to_user_reader.recv()
        self.assertEqual(msg, (1, 1))

        user_to_admin_writer.send(('check_running_status', None))
        msg = admin_to_worker_reader.recv()
        self.assertEqual(msg, 'check')
        worker_to_admin_writer.send('running')
        msg = admin_to_user_reader.recv()
        self.assertEqual(msg, (True, 'All workers are running. '))

        user_to_admin_writer.send(('stop_runner', None))
        msg = admin_to_worker_reader.recv()
        self.assertEqual(msg, 'stop')
        msg = admin_to_user_reader.recv()
        self.assertTrue(msg)

        user_to_admin_writer.send(('get_all_jobs', None))
        msg = admin_to_user_reader.recv()
        self.assertEqual(msg, [])

        user_to_admin_writer.send(('get_queued_jobs', None))
        msg = admin_to_queue_reader.recv()
        self.assertEqual(msg, 'get_queue')
        queue_to_admin_writer.send(['1234567890'])
        msg = admin_to_user_reader.recv()
        self.assertEqual(msg, ['1234567890'])

        user_to_admin_writer.send(('get_all_input_paths', None))
        msg = admin_to_user_reader.recv()
        self.assertEqual(msg, [])

        user_to_admin_writer.send(('check_status', None))
        msg = admin_to_queue_reader.recv()
        self.assertEqual(msg, 'get_queue')
        queue_to_admin_writer.send([])
        msg = admin_to_user_reader.recv()
        self.assertEqual(msg, '[0/0] []')

        user_to_admin_writer.send(('add_pattern', pattern))
        msg = admin_to_user_reader.recv()
        self.assertTrue(msg)

        user_to_admin_writer.send(('modify_pattern', pattern))
        msg = admin_to_user_reader.recv()
        self.assertTrue(msg)

        user_to_admin_writer.send(('remove_pattern', pattern))
        msg = admin_to_user_reader.recv()
        self.assertTrue(msg)

        user_to_admin_writer.send(('add_recipe', recipe))
        msg = admin_to_user_reader.recv()
        self.assertTrue(msg)

        user_to_admin_writer.send(('modify_recipe', recipe))
        msg = admin_to_user_reader.recv()
        self.assertTrue(msg)

        user_to_admin_writer.send(('remove_recipe', recipe))
        msg = admin_to_user_reader.recv()
        self.assertTrue(msg)

        user_to_admin_writer.send(('check_recipes', None))
        msg = admin_to_user_reader.recv()
        self.assertEqual(msg, {})

        user_to_admin_writer.send(('check_patterns', None))
        msg = admin_to_user_reader.recv()
        self.assertEqual(msg, {})

        user_to_admin_writer.send(('check_rules', None))
        msg = admin_to_user_reader.recv()
        self.assertEqual(msg, [])

        user_to_admin_writer.send(('check_jobs', None))
        msg = admin_to_user_reader.recv()
        self.assertEqual(msg, [])

        user_to_admin_writer.send(('check_queue', None))
        msg = admin_to_queue_reader.recv()
        self.assertEqual(msg, 'get_queue')
        queue_to_admin_writer.send(['1234567890'])
        msg = admin_to_user_reader.recv()
        self.assertEqual(msg, ['1234567890'])

        user_to_admin_writer.send(('kill', None))
        msg = admin_to_user_reader.recv()
        self.assertEqual(msg, 'dead')

        administrator_process.join()
        self.assertFalse(administrator_process.is_alive())

    @pytest.mark.timeout(5)
    def testAdminMonitorInteractions(self):
        make_dir(TESTING_VGRID)
        make_dir(os.path.join(TESTING_VGRID, 'start'))
        make_dir(RUNNER_DATA)
        make_dir(os.path.join(RUNNER_DATA, PATTERNS))
        make_dir(os.path.join(RUNNER_DATA, RECIPES))
        make_dir(JOB_DIR)

        data = read_dir(directory='examples/meow_directory')
        pattern = data['patterns']['pAppend']
        recipe = data['recipes']['rAppend']

        file_to_admin_reader, file_to_admin_writer = Pipe(duplex=False)
        file_to_logger_reader, file_to_logger_writer = Pipe(duplex=False)
        state_to_admin_reader, state_to_admin_writer = Pipe(duplex=False)
        state_to_logger_reader, state_to_logger_writer = Pipe(duplex=False)
        user_to_admin_reader, user_to_admin_writer = Pipe(duplex=False)
        admin_to_user_reader, admin_to_user_writer = Pipe(duplex=False)
        admin_to_queue_reader, admin_to_queue_writer = Pipe(duplex=False)
        queue_to_admin_reader, queue_to_admin_writer = Pipe(duplex=False)
        admin_to_logger_reader, admin_to_logger_writer = Pipe(duplex=False)
        admin_to_workers = []
        worker_to_admins = []
        admin_to_worker_reader, admin_to_worker_writer = Pipe(duplex=False)
        worker_to_admin_reader, worker_to_admin_writer = Pipe(duplex=False)
        admin_to_workers.append(admin_to_worker_writer)
        worker_to_admins.append(worker_to_admin_reader)

        file_monitor = LocalWorkflowFileMonitor(
            file_to_admin_writer, file_to_logger_writer)
        file_monitor_process = Observer()
        file_monitor_process.schedule(
            file_monitor,
            TESTING_VGRID,
            recursive=True
        )

        state_monitor = LocalWorkflowStateMonitor(
            state_to_admin_writer, state_to_logger_writer, RUNNER_DATA)
        state_monitor_process = Observer()
        state_monitor_process.schedule(
            state_monitor,
            RUNNER_DATA,
            recursive=True
        )

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
                TESTING_VGRID,
                JOB_DIR,
                RUNNER_DATA,
                True,
                False
            )
        )

        file_monitor_process.start()
        self.assertTrue(file_monitor_process.is_alive())

        state_monitor_process.start()
        self.assertTrue(state_monitor_process.is_alive())

        administrator_process.start()
        self.assertTrue(administrator_process.is_alive())

        write_dir_pattern(pattern, directory=RUNNER_DATA)
        pattern_path = os.path.join(RUNNER_DATA, PATTERNS, pattern.name)
        msg = admin_to_logger_reader.recv()
        check_logger_input(
            self,
            msg,
            'add_pattern',
            "%s pattern %s" % (OP_CREATE, pattern)
        )

        os.remove(pattern_path)
        msg = admin_to_logger_reader.recv()
        check_logger_input(
            self,
            msg,
            'remove_pattern',
            "%s pattern %s" % (OP_DELETED, pattern.name)
        )

        write_dir_recipe(recipe, directory=RUNNER_DATA)
        recipe_path = os.path.join(RUNNER_DATA, RECIPES, recipe[NAME])
        msg = admin_to_logger_reader.recv()
        check_logger_input(
            self,
            msg,
            'add_recipe',
            "%s recipe %s from source %s"
            % (OP_CREATE, recipe[NAME], recipe[SOURCE])
        )

        os.remove(recipe_path)
        msg = admin_to_logger_reader.recv()
        check_logger_input(
            self,
            msg,
            'remove_recipe',
            "%s recipe %s" % (OP_DELETED, recipe[NAME])
        )

        write_dir_pattern(pattern, directory=RUNNER_DATA)
        write_dir_recipe(recipe, directory=RUNNER_DATA)
        msg = admin_to_logger_reader.recv()
        check_logger_input(
            self,
            msg,
            'add_pattern',
            "%s pattern %s" % (OP_CREATE, pattern)
        )
        msg = admin_to_logger_reader.recv()
        self.assertEqual(len(msg), 2)
        self.assertEqual(msg[0], 'create_new_rule')
        self.assertIn("Created rule for path: %s" % pattern.trigger_paths[0],
                      msg[1])
        rule_id = msg[1][msg[1].index(' with id ')+9:-1]

        msg = admin_to_logger_reader.recv()
        check_logger_input(
            self,
            msg,
            'add_recipe',
            "%s recipe %s from source %s"
            % (OP_CREATE, recipe[NAME], recipe[SOURCE])
        )

        user_to_admin_writer.send(('get_all_input_paths', None))
        msg = admin_to_user_reader.recv()
        self.assertEqual(msg, [pattern.trigger_paths[0]])

        user_to_admin_writer.send(('check_recipes', None))
        msg = admin_to_user_reader.recv()
        self.assertEqual(msg, {recipe[NAME]: recipe})

        user_to_admin_writer.send(('check_patterns', None))
        msg = admin_to_user_reader.recv()
        self.assertEqual(msg, {pattern.name: pattern})

        expected_rule = {
            'id': rule_id,
            'pattern': pattern.name,
            'recipe': recipe[NAME],
            'path': pattern.trigger_paths[0]
        }
        user_to_admin_writer.send(('check_rules', None))
        msg = admin_to_user_reader.recv()
        self.assertEqual(msg, [expected_rule])

        base_path = 'examples/textfile.txt'
        self.assertTrue(os.path.exists(base_path))
        target_path = os.path.join(TESTING_VGRID, 'start', 'data.txt')
        self.assertFalse(os.path.exists(target_path))

        shutil.copyfile(base_path, target_path)
        self.assertTrue(os.path.exists(target_path))

        msg = admin_to_logger_reader.recv()
        check_logger_input(
            self,
            msg,
            'handle_event',
            'Handling a created event at start/data.txt'
        )

        msg = admin_to_logger_reader.recv()
        check_logger_input(
            self,
            msg,
            'run_handler',
            'Starting new job for %s using rule %s'
            % (target_path, expected_rule))

        msg = admin_to_logger_reader.recv()
        job_id = msg[1][18:34]
        check_logger_input(
            self,
            msg,
            'handle_event',
            'Scheduled new job %s from rule %s and pattern %s'
            % (job_id, rule_id, pattern.name))

        msg = admin_to_queue_reader.recv()
        self.assertEqual(msg, job_id)
        job_dir = os.path.join(JOB_DIR, job_id)
        self.assertTrue(os.path.exists(job_dir))
        self.assertTrue(os.path.isdir(job_dir))
        meta_path = os.path.join(job_dir, META_FILE)
        self.assertTrue(os.path.exists(meta_path))
        base_path = os.path.join(job_dir, BASE_FILE)
        self.assertTrue(os.path.exists(base_path))
        params_path = os.path.join(job_dir, PARAMS_FILE)
        self.assertTrue(os.path.exists(params_path))

        expected_params = {
            'extra': 'Appended by pAppend',
            'infile': 'testing_directory/start/data.txt',
            'outfile': 'testing_directory/end/data.txt'
        }

        params = read_yaml(params_path)
        self.assertEqual(params, expected_params)

        user_to_admin_writer.send(('get_all_jobs', None))
        msg = admin_to_user_reader.recv()
        self.assertEqual(msg, [job_id])

        user_to_admin_writer.send(('check_status', None))
        msg = admin_to_queue_reader.recv()
        self.assertEqual(msg, 'get_queue')
        queue_to_admin_writer.send([])
        msg = admin_to_user_reader.recv()
        self.assertEqual(msg, "[0/1] ['%s']" % pattern.trigger_paths[0])

        file_monitor_process.stop()
        file_monitor_process.join()
        self.assertFalse(file_monitor_process.is_alive())

        state_monitor_process.stop()
        state_monitor_process.join()
        self.assertFalse(state_monitor_process.is_alive())

        user_to_admin_writer.send(('kill', None))
        msg = admin_to_user_reader.recv()
        self.assertEqual(msg, 'dead')

        administrator_process.join()
        self.assertFalse(administrator_process.is_alive())

    @pytest.mark.timeout(30)
    def testJobProcessing(self):
        make_dir(JOB_DIR)
        make_dir(OUTPUT_DATA)
        job_id = '1234567890'
        job_dir = os.path.join(JOB_DIR, job_id)
        make_dir(job_dir)

        params = {
            'extra': 'Appended by pAppend',
            'infile': 'testing_directory/start/data.txt',
            'outfile': 'testing_directory/end/data.txt'
        }
        params_path = os.path.join(job_dir, 'params.yml')
        write_yaml(params, params_path)

        job = {
            'create': '2021-05-21 09:14: 10.740050',
            'id': job_id,
            'path': 'start/data.txt',
            'pattern': 'pAppend',
            'recipe': 'rAppend',
            'rule': 'alJ7vPFkYp9hSK2A',
            'status': 'queed'
        }
        job_path = os.path.join(job_dir, 'job.yml')
        write_yaml(job, job_path)

        recipe = read_dir_recipe(
            'rAppend',
            directory='examples/meow_directory'
        )
        base_path = os.path.join(job_dir, 'base.ipynb')
        write_notebook(recipe[RECIPE], base_path)

        worker_to_timer_reader, worker_to_timer_writer = Pipe(duplex=False)
        timer_to_worker_reader, timer_to_worker_writer = Pipe(duplex=False)
        admin_to_worker_reader, admin_to_worker_writer = Pipe(duplex=False)
        worker_to_admin_reader, worker_to_admin_writer = Pipe(duplex=False)
        worker_to_queue_reader, worker_to_queue_writer = Pipe(duplex=False)
        queue_to_worker_reader, queue_to_worker_writer = Pipe(duplex=False)
        worker_to_logger_reader, worker_to_logger_writer = Pipe(duplex=False)

        worker = Process(
            target=job_processor,
            args=(
                timer_to_worker_reader,
                worker_to_timer_writer,
                admin_to_worker_reader,
                worker_to_admin_writer,
                worker_to_queue_writer,
                queue_to_worker_reader,
                worker_to_logger_writer,
                0,
                JOB_DIR,
                OUTPUT_DATA
            )
        )

        worker.start()
        self.assertTrue(worker.is_alive())

        msg = worker_to_timer_reader.recv()
        self.assertEqual(msg, 'sleep')

        msg = worker_to_queue_reader.recv()
        self.assertTrue(isinstance(msg, list))
        module_list = [p.project_name for p in pkg_resources.working_set]
        self.assertEqual(msg, module_list)

        timer_to_worker_writer.send('done')
        msg = worker_to_timer_reader.recv()
        self.assertEqual(msg, 'sleep')

        admin_to_worker_writer.send('start')
        admin_to_worker_writer.send('check')
        msg = worker_to_admin_reader.recv()
        self.assertEqual(msg, 'running')

        timer_to_worker_writer.send('done')
        msg = worker_to_queue_reader.recv()
        self.assertEqual(msg, 'request')
        queue_to_worker_writer.send(None)
        msg = worker_to_logger_reader.recv()
        check_logger_input(
            self,
            msg,
            'worker 0',
            "Worker 0 found no job in queue"
        )

        timer_to_worker_writer.send('done')
        msg = worker_to_queue_reader.recv()
        self.assertEqual(msg, 'request')
        queue_to_worker_writer.send(job_id)
        msg = worker_to_logger_reader.recv()
        check_logger_input(
            self,
            msg,
            'worker 0',
            "Found job %s" % job_id
        )
        msg = worker_to_logger_reader.recv()
        check_logger_input(
            self,
            msg,
            'worker 0',
            "Completed job %s" % job_id
        )

        admin_to_worker_writer.send('kill')
        msg = worker_to_admin_reader.recv()
        self.assertEqual(msg, 'dead')

        worker.join()
        self.assertFalse(worker.is_alive())

    @pytest.mark.timeout(30)
    def testJobAssignment(self):
        admin_to_queue_reader, admin_to_queue_writer = Pipe(duplex=False)
        queue_to_admin_reader, queue_to_admin_writer = Pipe(duplex=False)
        queue_to_logger_reader, queue_to_logger_writer = Pipe(duplex=False)

        make_dir(JOB_DIR)
        make_dir(OUTPUT_DATA)
        job_id = '1234567890'
        job_dir = os.path.join(JOB_DIR, job_id)
        make_dir(job_dir)

        params = {
            'extra': 'Appended by pAppend',
            'infile': 'testing_directory/start/data.txt',
            'outfile': 'testing_directory/end/data.txt'
        }
        params_path = os.path.join(job_dir, 'params.yml')
        write_yaml(params, params_path)

        job = {
            'create': '2021-05-21 09:14: 10.740050',
            'id': job_id,
            'path': 'start/data.txt',
            'pattern': 'pAppend',
            'recipe': 'rAppend',
            'rule': 'alJ7vPFkYp9hSK2A',
            'status': 'queued',
            'requirements': {
                'dependencies': [
                    'watchdog'
                ]
            }
        }
        job_path = os.path.join(job_dir, 'job.yml')
        write_yaml(job, job_path)

        recipe = read_dir_recipe(
            'rAppend',
            directory='examples/meow_directory'
        )
        base_path = os.path.join(job_dir, 'base.ipynb')
        write_notebook(recipe[RECIPE], base_path)

        worker_to_queues = []
        queue_to_workers = []

        worker_to_queue_reader, worker_to_queue_writer = Pipe(duplex=False)
        queue_to_worker_reader, queue_to_worker_writer = Pipe(duplex=False)

        worker_to_queues.append(worker_to_queue_reader)
        queue_to_workers.append(queue_to_worker_writer)

        job_queue_process = Process(
            target=job_queue,
            args=(
                admin_to_queue_reader,
                queue_to_admin_writer,
                worker_to_queues,
                queue_to_workers,
                queue_to_logger_writer,
                JOB_DIR
            )
        )

        job_queue_process.start()
        self.assertTrue(job_queue_process.is_alive())

        module_list = [p.project_name for p in pkg_resources.working_set]
        worker_to_queue_writer.send(module_list)

        admin_to_queue_writer.send('get_queue')
        msg = queue_to_admin_reader.recv()
        self.assertEqual(msg, [])

        admin_to_queue_writer.send(job_id)
        admin_to_queue_writer.send('get_queue')
        msg = queue_to_admin_reader.recv()
        self.assertEqual(msg, [job_id])

        worker_to_queue_writer.send('request')
        msg = queue_to_worker_reader.recv()
        self.assertEqual(msg, job_id)
        msg = queue_to_logger_reader.recv()
        check_logger_input(
            self,
            msg,
            'queue request',
            'Assigning job %s' % job_id
        )

        admin_to_queue_writer.send('get_queue')
        msg = queue_to_admin_reader.recv()
        self.assertEqual(msg, [])

        job['requirements']['dependencies'] = ['watchdog', 'doesnotexist']
        write_yaml(job, job_path)

        admin_to_queue_writer.send(job_id)
        admin_to_queue_writer.send('get_queue')
        msg = queue_to_admin_reader.recv()
        self.assertEqual(msg, [job_id])

        worker_to_queue_writer.send('request')
        msg = queue_to_worker_reader.recv()
        self.assertEqual(msg, None)
        msg = queue_to_logger_reader.recv()
        check_logger_input(
            self,
            msg,
            'queue request',
            "Could not assign job %s to worker 0 as missing one or more "
            "requirement from %s." % (job_id, job['requirements'])
        )

        admin_to_queue_writer.send('kill')
        msg = queue_to_admin_reader.recv()
        self.assertEqual(msg, 'dead')

        job_queue_process.join()
        self.assertFalse(job_queue_process.is_alive())

    @pytest.mark.timeout(30)
    def testJobLifetime(self):
        make_dir(TESTING_VGRID)
        make_dir(os.path.join(TESTING_VGRID, 'start'))
        make_dir(RUNNER_DATA)
        make_dir(os.path.join(RUNNER_DATA, PATTERNS))
        make_dir(os.path.join(RUNNER_DATA, RECIPES))
        make_dir(JOB_DIR)

        data = read_dir(directory='examples/meow_directory')
        pattern = data['patterns']['pAppend']
        recipe = data['recipes']['rAppend']

        file_to_admin_reader, file_to_admin_writer = Pipe(duplex=False)
        file_to_logger_reader, file_to_logger_writer = Pipe(duplex=False)
        state_to_admin_reader, state_to_admin_writer = Pipe(duplex=False)
        state_to_logger_reader, state_to_logger_writer = Pipe(duplex=False)
        user_to_admin_reader, user_to_admin_writer = Pipe(duplex=False)
        admin_to_user_reader, admin_to_user_writer = Pipe(duplex=False)
        admin_to_queue_reader, admin_to_queue_writer = Pipe(duplex=False)
        queue_to_admin_reader, queue_to_admin_writer = Pipe(duplex=False)
        admin_to_logger_reader, admin_to_logger_writer = Pipe(duplex=False)
        queue_to_logger_reader, queue_to_logger_writer = Pipe(duplex=False)

        admin_to_workers = []
        worker_to_admins = []
        worker_to_queues = []
        queue_to_workers = []

        admin_to_worker_reader, admin_to_worker_writer = Pipe(duplex=False)
        worker_to_admin_reader, worker_to_admin_writer = Pipe(duplex=False)
        worker_to_timer_reader, worker_to_timer_writer = Pipe(duplex=False)
        timer_to_worker_reader, timer_to_worker_writer = Pipe(duplex=False)
        worker_to_queue_reader, worker_to_queue_writer = Pipe(duplex=False)
        queue_to_worker_reader, queue_to_worker_writer = Pipe(duplex=False)
        worker_to_logger_reader, worker_to_logger_writer = Pipe(
            duplex=False)

        admin_to_workers.append(admin_to_worker_writer)
        worker_to_admins.append(worker_to_admin_reader)
        worker_to_queues.append(worker_to_queue_reader)
        queue_to_workers.append(queue_to_worker_writer)

        file_monitor = LocalWorkflowFileMonitor(
            file_to_admin_writer, file_to_logger_writer)
        file_monitor_process = Observer()
        file_monitor_process.schedule(
            file_monitor,
            TESTING_VGRID,
            recursive=True
        )

        state_monitor = LocalWorkflowStateMonitor(
            state_to_admin_writer, state_to_logger_writer, RUNNER_DATA)
        state_monitor_process = Observer()
        state_monitor_process.schedule(
            state_monitor,
            RUNNER_DATA,
            recursive=True
        )

        worker = Process(
            target=job_processor,
            args=(
                timer_to_worker_reader,
                worker_to_timer_writer,
                admin_to_worker_reader,
                worker_to_admin_writer,
                worker_to_queue_writer,
                queue_to_worker_reader,
                worker_to_logger_writer,
                0,
                JOB_DIR,
                OUTPUT_DATA
            )
        )

        timer = Process(
            target=worker_timer,
            args=(
                worker_to_timer_reader,
                timer_to_worker_writer,
                0
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
                JOB_DIR
            )
        )

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
                TESTING_VGRID,
                JOB_DIR,
                RUNNER_DATA,
                True,
                True
            )
        )

        file_monitor_process.start()
        self.assertTrue(file_monitor_process.is_alive())

        state_monitor_process.start()
        self.assertTrue(state_monitor_process.is_alive())

        administrator_process.start()
        self.assertTrue(administrator_process.is_alive())

        worker.start()
        self.assertTrue(administrator_process.is_alive())

        job_queue_process.start()
        self.assertTrue(administrator_process.is_alive())

        timer.start()
        self.assertTrue(administrator_process.is_alive())

        write_dir_pattern(pattern, directory=RUNNER_DATA)
        write_dir_recipe(recipe, directory=RUNNER_DATA)
        base_path = 'examples/textfile.txt'
        target_path = os.path.join(TESTING_VGRID, 'start', 'data.txt')
        shutil.copyfile(base_path, target_path)

        msg = queue_to_logger_reader.recv()
        self.assertIsInstance(msg, tuple)
        self.assertEqual(len(msg), 2)
        self.assertEqual(msg[0], 'queue request')
        job_id = msg[1][14:]
        self.assertEqual(msg[1], "Assigning job %s" % job_id)

        msg = worker_to_logger_reader.recv()
        check_logger_input(self, msg, 'worker 0', "Found job %s" % job_id)

        msg = worker_to_logger_reader.recv()
        check_logger_input(self, msg, 'worker 0',
                           "Completed job %s" % job_id)

        output_path = os.path.join(TESTING_VGRID, 'end', 'data.txt')
        self.assertTrue(os.path.exists(output_path))

        expected_contents = """This is the starting text file.
It has 3 lines of text.
It has 16 words.
Appended by pAppend"""

        with open(output_path, 'r') as output_file:
            data = output_file.read()
        self.assertEqual(expected_contents, data)

        admin_to_worker_writer.send('kill')
        msg = worker_to_admin_reader.recv()
        self.assertEqual(msg, 'dead')

        worker.join()
        self.assertFalse(worker.is_alive())
        timer.join()
        self.assertFalse(timer.is_alive())

        admin_to_queue_writer.send('kill')
        msg = queue_to_admin_reader.recv()
        self.assertEqual(msg, 'dead')

        job_queue_process.join()
        self.assertFalse(job_queue_process.is_alive())

        file_monitor_process.stop()
        file_monitor_process.join()
        self.assertFalse(file_monitor_process.is_alive())

        state_monitor_process.stop()
        state_monitor_process.join()
        self.assertFalse(state_monitor_process.is_alive())

        user_to_admin_writer.send(('kill', None))
        msg = admin_to_user_reader.recv()
        self.assertEqual(msg, 'dead')

        administrator_process.join()
        self.assertFalse(administrator_process.is_alive())

    ###############################################################################

    def testWorkflowRunnerCreation(self):
        runner = WorkflowRunner(
            TESTING_VGRID,
            0,
            daemon=True,
            retro_active_jobs=False,
            print_logging=False
        )

        self.assertTrue(runner.check_running_status())

        self.assertTrue(os.path.exists(RUNNER_DATA))
        self.assertTrue(os.path.isdir(RUNNER_DATA))

        self.assertTrue(os.path.exists(TESTING_VGRID))
        self.assertTrue(os.path.isdir(TESTING_VGRID))

        self.assertTrue(runner.stop_runner(clear_jobs=True))

        self.assertFalse(os.path.exists(RUNNER_DATA))
        self.assertTrue(os.path.exists(TESTING_VGRID))
        self.assertTrue(os.path.isdir(TESTING_VGRID))

    def testWorkflowRunnerPatternImports(self):
        data = read_dir(directory='examples/meow_directory')
        patterns = data[PATTERNS]

        runner = WorkflowRunner(
            TESTING_VGRID,
            0,
            patterns=patterns,
            daemon=True,
            retro_active_jobs=False,
            print_logging=False
        )

        # Small pause here as we need to allow daemon processes to work
        time.sleep(3)

        self.assertIsNotNone(runner.check_patterns())
        self.assertIsInstance(runner.check_patterns(), dict)
        self.assertIn('adder', patterns)
        self.assertIn('adder', runner.check_patterns())
        self.assertIn('first_mult', patterns)
        self.assertIn('first_mult', runner.check_patterns())
        self.assertIn('second_mult', patterns)
        self.assertIn('second_mult', runner.check_patterns())
        self.assertIn('third_choo', patterns)
        self.assertIn('third_choo', runner.check_patterns())

        self.assertTrue(runner.stop_runner(clear_jobs=True))

    def testWorkflowRunnerRecipeImports(self):
        data = read_dir(directory='examples/meow_directory')
        recipes = data[RECIPES]

        runner = WorkflowRunner(
            TESTING_VGRID,
            0,
            recipes=recipes,
            daemon=True,
            retro_active_jobs=False,
            print_logging=False
        )

        # Small pause here as we need to allow daemon processes to work
        time.sleep(3)

        self.assertIsNotNone(runner.check_recipes())
        self.assertIsInstance(runner.check_recipes(), dict)
        self.assertIn('add', recipes)
        self.assertIn('add', runner.check_recipes())
        self.assertIn('mult', recipes)
        self.assertIn('mult', runner.check_recipes())
        self.assertIn('choo', recipes)
        self.assertIn('choo', runner.check_recipes())

        self.assertTrue(runner.stop_runner(clear_jobs=True))

    # def testWorkflowRunnerPatternIdentification(self):
    #     runner = WorkflowRunner(
    #         TESTING_VGRID,
    #         0,
    #         daemon=True,
    #         retro_active_jobs=False,
    #         print_logging=False
    #     )
    #
    #     self.assertEqual(runner.check_patterns(), {})
    #
    #     base_path = 'examples/meow_directory/patterns/adder'
    #     self.assertTrue(os.path.exists(base_path))
    #
    #     target_path = os.path.join(RUNNER_DATA, PATTERNS, 'late_adder')
    #     self.assertFalse(os.path.exists(target_path))
    #
    #     shutil.copyfile(base_path, target_path)
    #     self.assertTrue(os.path.exists(target_path))
    #
    #     # Small pause here as we need to allow daemon processes to work
    #     time.sleep(3)
    #
    #     self.assertIsNotNone(runner.check_patterns())
    #     self.assertIsInstance(runner.check_patterns(), dict)
    #     self.assertIn('late_adder', runner.check_patterns())
    #
    #     self.assertTrue(runner.stop_runner(clear_jobs=True))

    # def testWorkflowRunnerRecipeIdentification(self):
    #     runner = WorkflowRunner(
    #         TESTING_VGRID,
    #         0,
    #         daemon=True,
    #         retro_active_jobs=False,
    #         print_logging=True
    #     )
    #
    #     self.assertEqual(runner.check_recipes(), {})
    #
    #     base_path = 'examples/meow_directory/recipes/add'
    #     self.assertTrue(os.path.exists(base_path))
    #
    #     target_path = os.path.join(RUNNER_DATA, RECIPES, 'late_add')
    #     self.assertFalse(os.path.exists(target_path))
    #
    #     shutil.copyfile(base_path, target_path)
    #     self.assertTrue(os.path.exists(target_path))
    #
    #     # Small pause here as we need to allow daemon processes to work
    #     time.sleep(3)
    #
    #     self.assertIsNotNone(runner.check_recipes())
    #     self.assertIsInstance(runner.check_recipes(), dict)
    #     self.assertIn('late_add', runner.check_recipes())
    #
    #     self.assertTrue(runner.stop_runner(clear_jobs=True))

    # def testWorkflowRunnerRuleCreation(self):
    #     data = read_dir(directory='examples/meow_directory')
    #     patterns = data[PATTERNS]
    #     recipes = data[RECIPES]
    #
    #     runner = WorkflowRunner(
    #         TESTING_VGRID,
    #         0,
    #         patterns=patterns,
    #         recipes=recipes,
    #         daemon=True,
    #         retro_active_jobs=False,
    #         print_logging=False
    #     )
    #
    #     # Small pause here as we need to allow daemon processes to work
    #     time.sleep(3)
    #
    #     self.assertIsNotNone(runner.check_rules())
    #     self.assertIsInstance(runner.check_rules(), list)
    #     self.assertEqual(len(runner.check_rules()), 4)
    #     idless_rules = [{
    #         RULE_PATH: r[RULE_PATH],
    #         RULE_PATTERN: r[RULE_PATTERN],
    #         RULE_RECIPE: r[RULE_RECIPE]
    #     } for r in runner.check_rules()]
    #     for rule in STANDARD_RULES:
    #         self.assertIn(rule, idless_rules)
    #
    #     self.assertTrue(runner.stop_runner(clear_jobs=True))

    # def testWorkflowRunnerPatternRemoval(self):
    #     data = read_dir(directory='examples/meow_directory')
    #     patterns = data[PATTERNS]
    #     recipes = data[RECIPES]
    #
    #     runner = WorkflowRunner(
    #         TESTING_VGRID,
    #         0,
    #         patterns=patterns,
    #         recipes=recipes,
    #         daemon=True,
    #         retro_active_jobs=False,
    #         print_logging=False
    #     )
    #
    #     # Small pause here as we need to allow daemon processes to work
    #     time.sleep(3)
    #
    #     idless_rules = [{
    #         RULE_PATH: r[RULE_PATH],
    #         RULE_PATTERN: r[RULE_PATTERN],
    #         RULE_RECIPE: r[RULE_RECIPE]
    #     } for r in runner.check_rules()]
    #     for rule in STANDARD_RULES:
    #         self.assertIn(rule, idless_rules)
    #
    #     os.remove(os.path.join(RUNNER_DATA, PATTERNS, 'adder'))
    #
    #     # Small pause here as we need to allow daemon processes to work
    #     time.sleep(3)
    #
    #     self.assertEqual(len(runner.check_rules()), 3)
    #     idless_rules = [{
    #         RULE_PATH: r[RULE_PATH],
    #         RULE_PATTERN: r[RULE_PATTERN],
    #         RULE_RECIPE: r[RULE_RECIPE]
    #     } for r in runner.check_rules()]
    #     for rule in STANDARD_RULES[1:]:
    #         self.assertIn(rule, idless_rules)
    #
    #     self.assertTrue(runner.stop_runner(clear_jobs=True))

    # def testWorkflowRunnerRecipeRemoval(self):
    #     data = read_dir(directory='examples/meow_directory')
    #     patterns = data[PATTERNS]
    #     recipes = data[RECIPES]
    #
    #     runner = WorkflowRunner(
    #         TESTING_VGRID,
    #         0,
    #         patterns=patterns,
    #         recipes=recipes,
    #         daemon=True,
    #         retro_active_jobs=False,
    #         print_logging=False
    #     )
    #
    #     # Small pause here as we need to allow daemon processes to work
    #     time.sleep(3)
    #
    #     idless_rules = [{
    #         RULE_PATH: r[RULE_PATH],
    #         RULE_PATTERN: r[RULE_PATTERN],
    #         RULE_RECIPE: r[RULE_RECIPE]
    #     } for r in runner.check_rules()]
    #     for rule in STANDARD_RULES:
    #         self.assertIn(rule, idless_rules)
    #
    #     os.remove(os.path.join(RUNNER_DATA, RECIPES, 'mult'))
    #
    #     # Small pause here as we need to allow daemon processes to work
    #     time.sleep(3)
    #
    #     self.assertEqual(len(runner.check_rules()), 2)
    #     idless_rules = [{
    #         RULE_PATH: r[RULE_PATH],
    #         RULE_PATTERN: r[RULE_PATTERN],
    #         RULE_RECIPE: r[RULE_RECIPE]
    #     } for r in runner.check_rules()]
    #     for rule in [STANDARD_RULES[0], STANDARD_RULES[3]]:
    #         self.assertIn(rule, idless_rules)
    #
    #     self.assertTrue(runner.stop_runner(clear_jobs=True))

    # def testWorkflowRunnerEventIdentification(self):
    #     data = read_dir(directory='examples/meow_directory')
    #     patterns = data[PATTERNS]
    #     recipes = data[RECIPES]
    #
    #     runner = WorkflowRunner(
    #         TESTING_VGRID,
    #         0,
    #         patterns=patterns,
    #         recipes=recipes,
    #         daemon=True,
    #         reuse_vgrid=False,
    #         retro_active_jobs=False,
    #         print_logging=True
    #     )
    #
    #     # Small pause here as we need to allow daemon processes to work
    #     time.sleep(3)
    #
    #     self.assertIsNotNone(runner.check_jobs())
    #     self.assertIsInstance(runner.check_jobs(), list)
    #     self.assertEqual(len(runner.check_jobs()), 0)
    #
    #     data_directory = os.path.join(TESTING_VGRID, 'initial_data')
    #     os.mkdir(data_directory)
    #     self.assertTrue(os.path.exists(data_directory))
    #
    #     data = np.random.randint(100, size=(5, 5))
    #     data_filename = os.path.join(data_directory, 'datafile.npy')
    #     self.assertFalse(os.path.exists(data_filename))
    #     np.save(data_filename, data)
    #
    #     # Small pause here as we need to allow daemon processes to work
    #     time.sleep(3)
    #
    #     self.assertEqual(len(runner.check_jobs()), 4)
    #
    #     incorrect_directory = os.path.join(TESTING_VGRID, 'init_data')
    #     os.mkdir(incorrect_directory)
    #     self.assertTrue(os.path.exists(incorrect_directory))
    #
    #     incorrect_filename = \
    #         os.path.join(TESTING_VGRID, 'init_data', 'datafile.npy')
    #     np.save(incorrect_filename, data)
    #
    #     # Small pause here as we need to allow daemon processes to work
    #     time.sleep(3)
    #
    #     self.assertEqual(len(runner.check_jobs()), 4)
    #
    #     self.assertTrue(runner.stop_runner(clear_jobs=True))

    # def testWorkflowRunnerJobExecution(self):
    #     data = read_dir(directory='examples/meow_directory')
    #     patterns = data[PATTERNS]
    #     recipes = data[RECIPES]
    #
    #     runner = WorkflowRunner(
    #         TESTING_VGRID,
    #         0,
    #         patterns=patterns,
    #         recipes=recipes,
    #         daemon=True,
    #         reuse_vgrid=False,
    #         retro_active_jobs=False,
    #         print_logging=False
    #     )
    #
    #     # Small pause here as we need to allow daemon processes to work
    #     time.sleep(3)
    #
    #     self.assertIsNotNone(runner.check_jobs())
    #     self.assertIsInstance(runner.check_jobs(), list)
    #     self.assertEqual(len(runner.check_jobs()), 0)
    #
    #     data_directory = os.path.join(TESTING_VGRID, 'initial_data')
    #     os.mkdir(data_directory)
    #     self.assertTrue(os.path.exists(data_directory))
    #
    #     data = np.random.randint(100, size=(5, 5))
    #     data_filename = os.path.join(data_directory, 'datafile.npy')
    #     self.assertFalse(os.path.exists(data_filename))
    #     np.save(data_filename, data)
    #
    #     # Small pause here as we need to allow daemon processes to work
    #     time.sleep(3)
    #
    #     self.assertEqual(len(runner.check_jobs()), 4)
    #
    #     self.assertTrue(runner.stop_runner(clear_jobs=True))

    def testWorkflowKeywordReplacement(self):

        _end = os.path.join('path', 'with', 'ending')

        to_test = {
            1: os.path.join(_end, KEYWORD_PATH),
            2: os.path.join(_end, KEYWORD_REL_PATH),
            3: os.path.join(_end, KEYWORD_DIR),
            4: os.path.join(_end, KEYWORD_REL_DIR),
            5: os.path.join(_end, KEYWORD_FILENAME),
            6: os.path.join(_end, KEYWORD_PREFIX),
            7: os.path.join(_end, KEYWORD_VGRID),
            8: os.path.join(_end, KEYWORD_EXTENSION),
            9: os.path.join(_end, KEYWORD_JOB),
            10: 10
        }

        _vgrid = 'MyVgrid'
        _id = 'abcdefgh123456'
        _dir1 = 'first'
        _dir2 = 'second'
        _prefix = 'file'
        _ext = '.txt'
        _filename = _prefix + _ext
        _src_path = os.path.join(_vgrid, _dir1, _dir2, _filename)

        replaced = replace_keywords(to_test, _id, _src_path, _vgrid)

        self.assertIsInstance(replaced, dict)
        for k in to_test.keys():
            self.assertIn(k, replaced)

        _one = os.path.join(_end, _src_path)
        _two = os.path.join(_end, _dir1, _dir2, _filename)
        _three = os.path.join(_end, _vgrid, _dir1, _dir2)
        _four = os.path.join(_end, _dir1, _dir2)
        _five = os.path.join(_end, _filename)
        _six = os.path.join(_end, _prefix)
        _seven = os.path.join(_end, _vgrid)
        _eight = os.path.join(_end, _ext)
        _nine = os.path.join(_end, _id)
        _ten = 10

        self.assertEqual(_one, replaced[1])
        self.assertEqual(_two, replaced[2])
        self.assertEqual(_three, replaced[3])
        self.assertEqual(_four, replaced[4])
        self.assertEqual(_five, replaced[5])
        self.assertEqual(_six, replaced[6])
        self.assertEqual(_seven, replaced[7])
        self.assertEqual(_eight, replaced[8])
        self.assertEqual(_nine, replaced[9])
        self.assertEqual(_ten, replaced[10])

    def testRetroActiveRules(self):
        data = read_dir(directory='examples/meow_directory')

        patterns = {
            data[PATTERNS]['adder'].name: data[PATTERNS]['adder'],
            data[PATTERNS]['first_mult'].name: data[PATTERNS]['first_mult'],
            data[PATTERNS]['second_mult'].name: data[PATTERNS]['second_mult'],
            data[PATTERNS]['third_choo'].name: data[PATTERNS]['third_choo']
        }
        recipes = {
            data[RECIPES]['add'][NAME]: data[RECIPES]['add'],
            data[RECIPES]['mult'][NAME]: data[RECIPES]['mult'],
            data[RECIPES]['choo'][NAME]: data[RECIPES]['choo']
        }

        retroless_runner = WorkflowRunner(
            TESTING_VGRID,
            0,
            patterns=patterns,
            recipes=recipes,
            daemon=True,
            reuse_vgrid=False,
            retro_active_jobs=False,
            print_logging=False
        )

        # Small pause here as we need to allow daemon processes to work
        time.sleep(3)

        self.assertIsNotNone(retroless_runner.check_rules())
        self.assertIsInstance(retroless_runner.check_rules(), list)
        self.assertEqual(len(retroless_runner.check_rules()), 4)
        self.assertEqual(len(retroless_runner.check_jobs()), 0)

        self.assertTrue(retroless_runner.stop_runner(clear_jobs=True))

        data_directory = os.path.join(TESTING_VGRID, 'initial_data')
        if not os.path.exists(data_directory):
            os.mkdir(data_directory)
        self.assertTrue(os.path.exists(data_directory))

        data = np.random.randint(100, size=(5, 5))
        data_filename = os.path.join(data_directory, 'datafile.npy')
        np.save(data_filename, data)
        self.assertTrue(os.path.exists(data_filename))

        runner = WorkflowRunner(
            TESTING_VGRID,
            0,
            patterns=patterns,
            recipes=recipes,
            daemon=True,
            reuse_vgrid=True,
            retro_active_jobs=True,
            print_logging=False
        )

        # Small pause here as we need to allow daemon processes to work
        time.sleep(3)

        self.assertIsNotNone(runner.check_jobs())
        self.assertIsInstance(runner.check_jobs(), list)

        # Small pause here as we need to allow daemon processes to work
        time.sleep(3)

        self.assertEqual(len(runner.check_jobs()), 4)

        self.assertTrue(runner.stop_runner(clear_jobs=True))

    def testAddPatternFunction(self):
        runner = WorkflowRunner(
            TESTING_VGRID,
            0,
            daemon=True,
            retro_active_jobs=False,
            print_logging=False
        )

        self.assertEqual(runner.check_patterns(), {})

        base_path = 'examples/meow_directory/patterns/adder'
        self.assertTrue(os.path.exists(base_path))

        new_path = os.path.join(RUNNER_DATA, PATTERNS, 'adder')
        self.assertFalse(os.path.exists(new_path))

        pattern = read_dir_pattern(
            'adder',
            directory='examples/meow_directory'
        )

        runner.add_pattern(pattern)

        # Small pause here as we need to allow daemon processes to work
        time.sleep(3)

        self.assertIsNotNone(runner.check_patterns())
        self.assertIsInstance(runner.check_patterns(), dict)
        self.assertIn('adder', runner.check_patterns())

        self.assertTrue(os.path.exists(new_path))

        self.assertTrue(runner.stop_runner(clear_jobs=True))

    def testModifyPatternFunction(self):
        data = read_dir(directory='examples/meow_directory')
        patterns = data[PATTERNS]

        runner = WorkflowRunner(
            TESTING_VGRID,
            0,
            patterns=patterns,
            daemon=True,
            retro_active_jobs=False,
            print_logging=False
        )

        base_path = 'examples/meow_directory/patterns/adder'
        self.assertTrue(os.path.exists(base_path))

        pattern = read_dir_pattern(
            'adder',
            directory='examples/meow_directory'
        )
        new_paths = ['something_new/*']
        pattern.trigger_paths = new_paths

        runner.modify_pattern(pattern)

        # Small pause here as we need to allow daemon processes to work
        time.sleep(3)

        self.assertIsNotNone(runner.check_patterns())
        self.assertIsInstance(runner.check_patterns(), dict)
        self.assertIn('adder', runner.check_patterns())
        self.assertEqual(
            runner.check_patterns()['adder'].trigger_paths,
            new_paths
         )

        self.assertTrue(runner.stop_runner(clear_jobs=True))

    def testRemovePatternFunction(self):
        data = read_dir(directory='examples/meow_directory')
        patterns = data[PATTERNS]

        runner = WorkflowRunner(
            TESTING_VGRID,
            0,
            patterns=patterns,
            daemon=True,
            retro_active_jobs=False,
            print_logging=False
        )

        # Small pause here as we need to allow daemon processes to work
        time.sleep(3)

        self.assertIsNotNone(runner.check_patterns())
        self.assertIsInstance(runner.check_patterns(), dict)
        self.assertIn('adder', runner.check_patterns())

        removed_path = os.path.join(RUNNER_DATA, PATTERNS, 'adder')
        self.assertTrue(os.path.exists(removed_path))

        runner.remove_pattern('adder')

        # Small pause here as we need to allow daemon processes to work
        time.sleep(3)

        self.assertNotIn('adder', runner.check_patterns())

        self.assertFalse(os.path.exists(removed_path))

        self.assertTrue(runner.stop_runner(clear_jobs=True))

    def testAddRecipeFunction(self):
        runner = WorkflowRunner(
            TESTING_VGRID,
            0,
            daemon=True,
            retro_active_jobs=False,
            print_logging=False
        )

        self.assertEqual(runner.check_recipes(), {})

        base_path = 'examples/meow_directory/recipes/add'
        self.assertTrue(os.path.exists(base_path))

        new_path = os.path.join(RUNNER_DATA, RECIPES, 'add')
        self.assertFalse(os.path.exists(new_path))

        recipe = read_dir_recipe(
            'add',
            directory='examples/meow_directory'
        )

        runner.add_recipe(recipe)

        # Small pause here as we need to allow daemon processes to work
        time.sleep(3)

        self.assertIsNotNone(runner.check_recipes())
        self.assertIsInstance(runner.check_recipes(), dict)
        self.assertIn('add', runner.check_recipes())

        self.assertTrue(os.path.exists(new_path))

        self.assertTrue(runner.stop_runner(clear_jobs=True))

    def testModifyRecipeFunction(self):
        data = read_dir(directory='examples/meow_directory')
        recipes = data[RECIPES]

        runner = WorkflowRunner(
            TESTING_VGRID,
            0,
            recipes=recipes,
            daemon=True,
            retro_active_jobs=False,
            print_logging=False
        )

        base_path = 'examples/meow_directory/recipes/add'
        self.assertTrue(os.path.exists(base_path))

        recipe = read_dir_recipe(
            'add',
            directory='examples/meow_directory'
        )
        new_source = 'something_new.ipynb'
        recipe[SOURCE] = new_source

        runner.modify_recipe(recipe)

        # Small pause here as we need to allow daemon processes to work
        time.sleep(3)

        self.assertIsNotNone(runner.check_recipes())
        self.assertIsInstance(runner.check_recipes(), dict)
        self.assertIn('add', runner.check_recipes())
        self.assertEqual(
            runner.check_recipes()['add'][SOURCE],
            new_source
        )

        self.assertTrue(runner.stop_runner(clear_jobs=True))

    def testRemoveRecipeFunction(self):
        data = read_dir(directory='examples/meow_directory')
        recipes = data[RECIPES]

        runner = WorkflowRunner(
            TESTING_VGRID,
            0,
            recipes=recipes,
            daemon=True,
            retro_active_jobs=False,
            print_logging=False
        )

        # Small pause here as we need to allow daemon processes to work
        time.sleep(3)

        self.assertIsNotNone(runner.check_recipes())
        self.assertIsInstance(runner.check_recipes(), dict)
        self.assertIn('add', runner.check_recipes())

        removed_path = os.path.join(RUNNER_DATA, RECIPES, 'add')
        self.assertTrue(os.path.exists(removed_path))

        runner.remove_recipe('add')

        # Small pause here as we need to allow daemon processes to work
        time.sleep(3)

        self.assertNotIn('add', runner.check_recipes())

        removed_path = os.path.join(RUNNER_DATA, RECIPES, 'add')
        self.assertFalse(os.path.exists(removed_path))

        self.assertTrue(runner.stop_runner(clear_jobs=True))
