import unittest
import os
import shutil
import time
import numpy as np

from mig_meow.constants import PATTERNS, RECIPES
from mig_meow.fileio import read_dir
from mig_meow.localrunner import WorkflowRunner, RULES, JOBS, RUNNER_DATA, \
    RUNNER_RECIPES, RUNNER_PATTERNS, RULE_PATH, RULE_PATTERN, RULE_RECIPE, \
    RULE_ID, WORKERS, QUEUE

VGRID = 'testing_directory'

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
        if os.path.exists(VGRID):
            raise Exception("Required testing location '%s' is already in use")

    def tearDown(self):
        if os.path.exists(VGRID):
            shutil.rmtree(VGRID)
        if os.path.exists(RUNNER_DATA):
            shutil.rmtree(RUNNER_DATA)

    def testWorkflowRunnerCreation(self):
        runner = WorkflowRunner(logging=False)
        runner.run_local_workflow(
            VGRID,
            0,
            daemon=True
        )

        self.assertTrue(runner.check_running_status())

        self.assertTrue(os.path.exists(RUNNER_DATA))
        self.assertTrue(os.path.isdir(RUNNER_DATA))

        self.assertTrue(os.path.exists(VGRID))
        self.assertTrue(os.path.isdir(VGRID))

        self.assertTrue(runner.stop_runner(clear_jobs=True))

        self.assertFalse(os.path.exists(RUNNER_DATA))
        self.assertTrue(os.path.exists(VGRID))
        self.assertTrue(os.path.isdir(VGRID))

    def testWorkflowRunnerPatternImports(self):
        data = read_dir(directory='examples/meow_directory')
        patterns = data[PATTERNS]

        runner = WorkflowRunner(logging=False)
        runner.run_local_workflow(
            VGRID,
            0,
            patterns=patterns,
            daemon=True
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
            VGRID,
            0,
            recipes=recipes,
            daemon=True
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
            VGRID,
            0,
            daemon=True
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
            VGRID,
            0,
            daemon=True
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
            VGRID,
            0,
            patterns=patterns,
            recipes=recipes,
            daemon=True
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
            VGRID,
            0,
            patterns=patterns,
            recipes=recipes,
            daemon=True
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
            VGRID,
            0,
            patterns=patterns,
            recipes=recipes,
            daemon=True
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
            VGRID,
            0,
            patterns=patterns,
            recipes=recipes,
            daemon=True,
            reuse_vgrid=False
        )

        # Small pause here as we need to allow daemon processes to work
        time.sleep(3)

        self.assertIsNotNone(runner.runner_state[JOBS])
        self.assertIsInstance(runner.runner_state[JOBS], list)
        self.assertEqual(len(runner.runner_state[JOBS]), 0)

        data_directory = os.path.join(VGRID, 'initial_data')
        os.mkdir(data_directory)
        self.assertTrue(os.path.exists(data_directory))

        data = np.random.randint(100, size=(5, 5))
        data_filename = os.path.join(data_directory, 'datafile')
        self.assertFalse(os.path.exists(data_filename))
        np.save(data_filename, data)

        # Small pause here as we need to allow daemon processes to work
        time.sleep(3)

        self.assertEqual(len(runner.runner_state[JOBS]), 4)

        incorrect_directory = os.path.join(VGRID, 'init_data')
        os.mkdir(incorrect_directory)
        self.assertTrue(os.path.exists(incorrect_directory))

        incorrect_filename = os.path.join(VGRID, 'init_data', 'datafile')
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
            VGRID,
            0,
            patterns=patterns,
            recipes=recipes,
            daemon=True,
            reuse_vgrid=False
        )

        # Small pause here as we need to allow daemon processes to work
        time.sleep(3)

        self.assertIsNotNone(runner.runner_state[JOBS])
        self.assertIsInstance(runner.runner_state[JOBS], list)
        self.assertEqual(len(runner.runner_state[JOBS]), 0)

        data_directory = os.path.join(VGRID, 'initial_data')
        os.mkdir(data_directory)
        self.assertTrue(os.path.exists(data_directory))

        data = np.random.randint(100, size=(5, 5))
        data_filename = os.path.join(data_directory, 'datafile')
        self.assertFalse(os.path.exists(data_filename))
        np.save(data_filename, data)

        # Small pause here as we need to allow daemon processes to work
        time.sleep(3)

        self.assertEqual(len(runner.runner_state[JOBS]), 4)

        self.assertTrue(runner.stop_runner(clear_jobs=True))
