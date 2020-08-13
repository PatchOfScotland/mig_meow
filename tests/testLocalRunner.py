import unittest
import os
import shutil
import time
import numpy as np

from mig_meow.constants import PATTERNS, RECIPES, RUNNER_DATA, \
    RUNNER_RECIPES, RUNNER_PATTERNS
from mig_meow.fileio import read_dir
from mig_meow.localrunner import WorkflowRunner, RULES, JOBS

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
            daemon=True
        )

        self.assertTrue(runner.check_running_status())

        self.assertTrue(os.path.exists(RUNNER_DATA))
        self.assertTrue(os.path.isdir(RUNNER_DATA))

        self.assertTrue(os.path.exists(VGRID))
        self.assertTrue(os.path.isdir(VGRID))

        self.assertTrue(runner.stop_runner())

        self.assertFalse(os.path.exists(RUNNER_DATA))
        self.assertTrue(os.path.exists(VGRID))
        self.assertTrue(os.path.isdir(VGRID))

    def testWorkflowRunnerPatternImports(self):
        data = read_dir(directory='examples/meow_directory')
        patterns = data[PATTERNS]

        runner = WorkflowRunner(logging=False)
        runner.run_local_workflow(
            VGRID,
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

        self.assertTrue(runner.stop_runner())

    def testWorklflowRunnerRecipeImports(self):
        data = read_dir(directory='examples/meow_directory')
        recipes = data[RECIPES]

        runner = WorkflowRunner(logging=False)
        runner.run_local_workflow(
            VGRID,
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

        self.assertTrue(runner.stop_runner())

    def testWorkflowRunnerPatternIdentification(self):
        runner = WorkflowRunner(logging=False)
        runner.run_local_workflow(
            VGRID,
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
            patterns=patterns,
            recipes=recipes,
            daemon=True
        )

        # Small pause here as we need to allow daemon processes to work
        time.sleep(3)

        self.assertIsNotNone(runner.runner_state[RULES])
        self.assertIsInstance(runner.runner_state[RULES], list)
        self.assertEqual(len(runner.runner_state[RULES]), 4)
        for rule in STANDARD_RULES:
            self.assertIn(rule, runner.runner_state[RULES])

        self.assertTrue(runner.stop_runner())

    def testWorkflowRunnerPatternRemoval(self):
        data = read_dir(directory='examples/meow_directory')
        patterns = data[PATTERNS]
        recipes = data[RECIPES]

        runner = WorkflowRunner(logging=False)
        runner.run_local_workflow(
            VGRID,
            patterns=patterns,
            recipes=recipes,
            daemon=True
        )

        # Small pause here as we need to allow daemon processes to work
        time.sleep(3)

        for rule in STANDARD_RULES:
            self.assertIn(rule, runner.runner_state[RULES])

        os.remove(os.path.join(RUNNER_PATTERNS, 'adder'))

        # Small pause here as we need to allow daemon processes to work
        time.sleep(3)

        self.assertEqual(len(runner.runner_state[RULES]), 3)
        for rule in STANDARD_RULES[1:]:
            self.assertIn(rule, runner.runner_state[RULES])

        self.assertTrue(runner.stop_runner())

    def testWorkflowRunnerRecipeRemoval(self):
        data = read_dir(directory='examples/meow_directory')
        patterns = data[PATTERNS]
        recipes = data[RECIPES]

        runner = WorkflowRunner(logging=False)
        runner.run_local_workflow(
            VGRID,
            patterns=patterns,
            recipes=recipes,
            daemon=True
        )

        # Small pause here as we need to allow daemon processes to work
        time.sleep(3)

        for rule in STANDARD_RULES:
            self.assertIn(rule, runner.runner_state[RULES])

        os.remove(os.path.join(RUNNER_RECIPES, 'mult'))

        # Small pause here as we need to allow daemon processes to work
        time.sleep(3)

        self.assertEqual(len(runner.runner_state[RULES]), 2)
        for rule in [STANDARD_RULES[0], STANDARD_RULES[3]]:
            self.assertIn(rule, runner.runner_state[RULES])

        self.assertTrue(runner.stop_runner())

    def testWorkflowRunnerEventIdentification(self):
        data = read_dir(directory='examples/meow_directory')
        patterns = data[PATTERNS]
        recipes = data[RECIPES]

        runner = WorkflowRunner(logging=False)
        runner.run_local_workflow(
            VGRID,
            patterns=patterns,
            recipes=recipes,
            daemon=True
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
        np.save(data_filename, data)

        # Small pause here as we need to allow daemon processes to work
        time.sleep(3)

        self.assertEqual(len(runner.runner_state[JOBS]), 2)

        incorrect_filename = os.path.join(VGRID, 'init_data', 'datafile')
        np.save(data_filename, data)

        # Small pause here as we need to allow daemon processes to work
        time.sleep(3)

        self.assertEqual(len(runner.runner_state[JOBS]), 2)

        self.assertTrue(runner.stop_runner())

