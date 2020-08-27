import unittest
import os
import shutil
import time
import numpy as np

from mig_meow.constants import PATTERNS, RECIPES, KEYWORD_DIR, KEYWORD_JOB, \
    KEYWORD_VGRID, KEYWORD_EXTENSION, KEYWORD_PREFIX, KEYWORD_FILENAME, \
    KEYWORD_REL_DIR, KEYWORD_REL_PATH, KEYWORD_PATH, VGRID
from mig_meow.fileio import read_dir
from mig_meow.localrunner import WorkflowRunner, RULES, JOBS, RUNNER_DATA, \
    RUNNER_RECIPES, RUNNER_PATTERNS, RULE_PATH, RULE_PATTERN, RULE_RECIPE, \
    replace_keywords

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


class WorkflowTest(unittest.TestCase):
    def setUp(self):
        if os.path.exists(TESTING_VGRID):
            raise Exception("Required testing location '%s' is already in use")

    def tearDown(self):
        if os.path.exists(TESTING_VGRID):
            shutil.rmtree(TESTING_VGRID)
        if os.path.exists(RUNNER_DATA):
            shutil.rmtree(RUNNER_DATA)

    def testWorkflowRunnerCreation(self):
        runner = WorkflowRunner(logging=False)
        runner.run_local_workflow(
            TESTING_VGRID,
            0,
            daemon=True,
            retro_active_jobs=False
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

        runner = WorkflowRunner(logging=False)
        runner.run_local_workflow(
            TESTING_VGRID,
            0,
            patterns=patterns,
            daemon=True,
            retro_active_jobs=False
        )

        # Small pause here as we need to allow daemon processes to work
        time.sleep(3)

        self.assertIsNotNone(runner.runner_state[PATTERNS])
        self.assertIsInstance(runner.runner_state[PATTERNS], dict)
        self.assertIn('adder', runner.runner_state[PATTERNS])
        self.assertIn('first_mult', runner.runner_state[PATTERNS])
        self.assertIn('second_mult', runner.runner_state[PATTERNS])
        self.assertIn('third_choo', runner.runner_state[PATTERNS])

        self.assertTrue(runner.stop_runner(clear_jobs=True))

    def testWorklflowRunnerRecipeImports(self):
        data = read_dir(directory='examples/meow_directory')
        recipes = data[RECIPES]

        runner = WorkflowRunner(logging=False)
        runner.run_local_workflow(
            TESTING_VGRID,
            0,
            recipes=recipes,
            daemon=True,
            retro_active_jobs=False
        )

        # Small pause here as we need to allow daemon processes to work
        time.sleep(3)

        self.assertIsNotNone(runner.runner_state[RECIPES])
        self.assertIsInstance(runner.runner_state[RECIPES], dict)
        self.assertIn('add', runner.runner_state[RECIPES])
        self.assertIn('mult', runner.runner_state[RECIPES])
        self.assertIn('choo', runner.runner_state[RECIPES])

        self.assertTrue(runner.stop_runner(clear_jobs=True))

    def testWorkflowRunnerPatternIdentification(self):
        runner = WorkflowRunner(logging=False)
        runner.run_local_workflow(
            TESTING_VGRID,
            0,
            daemon=True,
            retro_active_jobs=False
        )

        self.assertEqual(runner.runner_state[PATTERNS], {})

        base_path = 'examples/meow_directory/patterns/adder'
        self.assertTrue(os.path.exists(base_path))

        target_path = os.path.join(RUNNER_PATTERNS, 'late_adder')
        self.assertFalse(os.path.exists(target_path))

        shutil.copyfile(base_path, target_path)
        self.assertTrue(os.path.exists(target_path))

        # Small pause here as we need to allow daemon processes to work
        time.sleep(3)

        self.assertIsNotNone(runner.runner_state[PATTERNS])
        self.assertIsInstance(runner.runner_state[PATTERNS], dict)
        self.assertIn('late_adder', runner.runner_state[PATTERNS])

    def testWorklflowRunnerRecipeIdentification(self):
        runner = WorkflowRunner(logging=False)
        runner.run_local_workflow(
            TESTING_VGRID,
            0,
            daemon=True,
            retro_active_jobs=False
        )

        self.assertEqual(runner.runner_state[RECIPES], {})

        base_path = 'examples/meow_directory/recipes/add'
        self.assertTrue(os.path.exists(base_path))

        target_path = os.path.join(RUNNER_RECIPES, 'late_add')
        self.assertFalse(os.path.exists(target_path))

        shutil.copyfile(base_path, target_path)
        self.assertTrue(os.path.exists(target_path))

        # Small pause here as we need to allow daemon processes to work
        time.sleep(3)

        self.assertIsNotNone(runner.runner_state[RECIPES])
        self.assertIsInstance(runner.runner_state[RECIPES], dict)
        self.assertIn('late_add', runner.runner_state[RECIPES])

    def testWorkflowRunnerRuleCreation(self):
        data = read_dir(directory='examples/meow_directory')
        patterns = data[PATTERNS]
        recipes = data[RECIPES]

        runner = WorkflowRunner(logging=False)
        runner.run_local_workflow(
            TESTING_VGRID,
            0,
            patterns=patterns,
            recipes=recipes,
            daemon=True,
            retro_active_jobs=False
        )

        # Small pause here as we need to allow daemon processes to work
        time.sleep(3)

        self.assertIsNotNone(runner.runner_state[RULES])
        self.assertIsInstance(runner.runner_state[RULES], list)
        self.assertEqual(len(runner.runner_state[RULES]), 4)
        idless_rules = [{
            RULE_PATH: r[RULE_PATH],
            RULE_PATTERN: r[RULE_PATTERN],
            RULE_RECIPE: r[RULE_RECIPE]
        } for r in runner.runner_state[RULES]]
        for rule in STANDARD_RULES:
            self.assertIn(rule, idless_rules)

        self.assertTrue(runner.stop_runner(clear_jobs=True))

    def testWorkflowRunnerPatternRemoval(self):
        data = read_dir(directory='examples/meow_directory')
        patterns = data[PATTERNS]
        recipes = data[RECIPES]

        runner = WorkflowRunner(logging=False)
        runner.run_local_workflow(
            TESTING_VGRID,
            0,
            patterns=patterns,
            recipes=recipes,
            daemon=True,
            retro_active_jobs=False
        )

        # Small pause here as we need to allow daemon processes to work
        time.sleep(3)

        idless_rules = [{
            RULE_PATH: r[RULE_PATH],
            RULE_PATTERN: r[RULE_PATTERN],
            RULE_RECIPE: r[RULE_RECIPE]
        } for r in runner.runner_state[RULES]]
        for rule in STANDARD_RULES:
            self.assertIn(rule, idless_rules)

        os.remove(os.path.join(RUNNER_PATTERNS, 'adder'))

        # Small pause here as we need to allow daemon processes to work
        time.sleep(3)

        self.assertEqual(len(runner.runner_state[RULES]), 3)
        idless_rules = [{
            RULE_PATH: r[RULE_PATH],
            RULE_PATTERN: r[RULE_PATTERN],
            RULE_RECIPE: r[RULE_RECIPE]
        } for r in runner.runner_state[RULES]]
        for rule in STANDARD_RULES[1:]:
            self.assertIn(rule, idless_rules)

        self.assertTrue(runner.stop_runner(clear_jobs=True))

    def testWorkflowRunnerRecipeRemoval(self):
        data = read_dir(directory='examples/meow_directory')
        patterns = data[PATTERNS]
        recipes = data[RECIPES]

        runner = WorkflowRunner(logging=False)
        runner.run_local_workflow(
            TESTING_VGRID,
            0,
            patterns=patterns,
            recipes=recipes,
            daemon=True,
            retro_active_jobs=False
        )

        # Small pause here as we need to allow daemon processes to work
        time.sleep(3)

        idless_rules = [{
            RULE_PATH: r[RULE_PATH],
            RULE_PATTERN: r[RULE_PATTERN],
            RULE_RECIPE: r[RULE_RECIPE]
        } for r in runner.runner_state[RULES]]
        for rule in STANDARD_RULES:
            self.assertIn(rule, idless_rules)

        os.remove(os.path.join(RUNNER_RECIPES, 'mult'))

        # Small pause here as we need to allow daemon processes to work
        time.sleep(3)

        self.assertEqual(len(runner.runner_state[RULES]), 2)
        idless_rules = [{
            RULE_PATH: r[RULE_PATH],
            RULE_PATTERN: r[RULE_PATTERN],
            RULE_RECIPE: r[RULE_RECIPE]
        } for r in runner.runner_state[RULES]]
        for rule in [STANDARD_RULES[0], STANDARD_RULES[3]]:
            self.assertIn(rule, idless_rules)

        self.assertTrue(runner.stop_runner(clear_jobs=True))

    def testWorkflowRunnerEventIdentification(self):
        data = read_dir(directory='examples/meow_directory')
        patterns = data[PATTERNS]
        recipes = data[RECIPES]

        runner = WorkflowRunner(logging=False)
        runner.run_local_workflow(
            TESTING_VGRID,
            0,
            patterns=patterns,
            recipes=recipes,
            daemon=True,
            reuse_vgrid=False,
            retro_active_jobs=False
        )

        # Small pause here as we need to allow daemon processes to work
        time.sleep(3)

        self.assertIsNotNone(runner.runner_state[JOBS])
        self.assertIsInstance(runner.runner_state[JOBS], list)
        self.assertEqual(len(runner.runner_state[JOBS]), 0)

        data_directory = os.path.join(TESTING_VGRID, 'initial_data')
        os.mkdir(data_directory)
        self.assertTrue(os.path.exists(data_directory))

        data = np.random.randint(100, size=(5, 5))
        data_filename = os.path.join(data_directory, 'datafile.npy')
        self.assertFalse(os.path.exists(data_filename))
        np.save(data_filename, data)

        # Small pause here as we need to allow daemon processes to work
        time.sleep(3)

        self.assertEqual(len(runner.runner_state[JOBS]), 4)

        incorrect_directory = os.path.join(TESTING_VGRID, 'init_data')
        os.mkdir(incorrect_directory)
        self.assertTrue(os.path.exists(incorrect_directory))

        incorrect_filename = \
            os.path.join(TESTING_VGRID, 'init_data', 'datafile.npy')
        np.save(incorrect_filename, data)

        # Small pause here as we need to allow daemon processes to work
        time.sleep(3)

        self.assertEqual(len(runner.runner_state[JOBS]), 4)

        self.assertTrue(runner.stop_runner(clear_jobs=True))

    def testWorkflowRunnerJobExecution(self):
        data = read_dir(directory='examples/meow_directory')
        patterns = data[PATTERNS]
        recipes = data[RECIPES]

        runner = WorkflowRunner(logging=False)
        runner.run_local_workflow(
            TESTING_VGRID,
            0,
            patterns=patterns,
            recipes=recipes,
            daemon=True,
            reuse_vgrid=False,
            retro_active_jobs=False
        )

        # Small pause here as we need to allow daemon processes to work
        time.sleep(3)

        self.assertIsNotNone(runner.runner_state[JOBS])
        self.assertIsInstance(runner.runner_state[JOBS], list)
        self.assertEqual(len(runner.runner_state[JOBS]), 0)

        data_directory = os.path.join(TESTING_VGRID, 'initial_data')
        os.mkdir(data_directory)
        self.assertTrue(os.path.exists(data_directory))

        data = np.random.randint(100, size=(5, 5))
        data_filename = os.path.join(data_directory, 'datafile.npy')
        self.assertFalse(os.path.exists(data_filename))
        np.save(data_filename, data)

        # Small pause here as we need to allow daemon processes to work
        time.sleep(3)

        self.assertEqual(len(runner.runner_state[JOBS]), 4)

        self.assertTrue(runner.stop_runner(clear_jobs=True))

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
            9: os.path.join(_end, KEYWORD_JOB)
        }

        _vgrid = 'MyVgrid'
        _id = 'abcdefgh123456'
        _dir1 = 'first'
        _dir2 = 'second'
        _prefix = 'file'
        _ext = '.txt'
        _filename = _prefix + _ext
        _src_path = os.path.join(_vgrid, _dir1, _dir2, _filename)

        state = {
            VGRID: _vgrid
        }

        replaced = replace_keywords(to_test, state, _id, _src_path)

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

        self.assertEqual(_one, replaced[1])
        self.assertEqual(_two, replaced[2])
        self.assertEqual(_three, replaced[3])
        self.assertEqual(_four, replaced[4])
        self.assertEqual(_five, replaced[5])
        self.assertEqual(_six, replaced[6])
        self.assertEqual(_seven, replaced[7])
        self.assertEqual(_eight, replaced[8])
        self.assertEqual(_nine, replaced[9])

    def testRetroActiveRules(self):
        data = read_dir(directory='examples/meow_directory')
        patterns = data[PATTERNS]
        recipes = data[RECIPES]

        retroless_runner = WorkflowRunner(logging=False)
        retroless_runner.run_local_workflow(
            TESTING_VGRID,
            0,
            patterns=patterns,
            recipes=recipes,
            daemon=True,
            reuse_vgrid=False,
            retro_active_jobs=False
        )

        # Small pause here as we need to allow daemon processes to work
        time.sleep(3)

        self.assertIsNotNone(retroless_runner.runner_state[RULES])
        self.assertIsInstance(retroless_runner.runner_state[RULES], list)
        self.assertEqual(len(retroless_runner.runner_state[RULES]), 4)
        self.assertEqual(len(retroless_runner.runner_state[JOBS]), 0)

        self.assertTrue(retroless_runner.stop_runner(clear_jobs=True))

        data_directory = os.path.join(TESTING_VGRID, 'initial_data')
        if not os.path.exists(data_directory):
            os.mkdir(data_directory)
        self.assertTrue(os.path.exists(data_directory))

        data = np.random.randint(100, size=(5, 5))
        data_filename = os.path.join(data_directory, 'datafile.npy')
        np.save(data_filename, data)
        self.assertTrue(os.path.exists(data_filename))

        runner = WorkflowRunner(logging=False)
        runner.run_local_workflow(
            TESTING_VGRID,
            0,
            patterns=patterns,
            recipes=recipes,
            daemon=True,
            reuse_vgrid=True,
            retro_active_jobs=True
        )

        # Small pause here as we need to allow daemon processes to work
        time.sleep(3)

        self.assertIsNotNone(runner.runner_state[JOBS])
        self.assertIsInstance(runner.runner_state[JOBS], list)

        # Small pause here as we need to allow daemon processes to work
        time.sleep(3)

        self.assertEqual(len(runner.runner_state[JOBS]), 4)

        self.assertTrue(runner.stop_runner(clear_jobs=True))
