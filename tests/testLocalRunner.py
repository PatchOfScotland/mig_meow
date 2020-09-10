import unittest
import os
import shutil
import time
import numpy as np

from mig_meow.constants import PATTERNS, RECIPES, KEYWORD_DIR, KEYWORD_JOB, \
    KEYWORD_VGRID, KEYWORD_EXTENSION, KEYWORD_PREFIX, KEYWORD_FILENAME, \
    KEYWORD_REL_DIR, KEYWORD_REL_PATH, KEYWORD_PATH, VGRID, SOURCE
from mig_meow.fileio import read_dir, read_dir_pattern, read_dir_recipe
from mig_meow.localrunner import WorkflowRunner, RUNNER_DATA, \
    get_runner_recipes, get_runner_patterns, RULE_PATH, RULE_PATTERN, \
    RULE_RECIPE, replace_keywords

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
            raise Exception(
                "Required testing location '%s' is already in use"
                % TESTING_VGRID
            )

    def tearDown(self):
        if os.path.exists(TESTING_VGRID):
            shutil.rmtree(TESTING_VGRID)
        if os.path.exists(RUNNER_DATA):
            shutil.rmtree(RUNNER_DATA)

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

    def testWorklflowRunnerRecipeImports(self):
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

    def testWorkflowRunnerPatternIdentification(self):
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

        target_path = os.path.join(RUNNER_DATA, PATTERNS, 'late_adder')
        self.assertFalse(os.path.exists(target_path))

        shutil.copyfile(base_path, target_path)
        self.assertTrue(os.path.exists(target_path))

        # Small pause here as we need to allow daemon processes to work
        time.sleep(3)

        self.assertIsNotNone(runner.check_patterns())
        self.assertIsInstance(runner.check_patterns(), dict)
        self.assertIn('late_adder', runner.check_patterns())

    def testWorklflowRunnerRecipeIdentification(self):
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

        target_path = os.path.join(RUNNER_DATA, RECIPES, 'late_add')
        self.assertFalse(os.path.exists(target_path))

        shutil.copyfile(base_path, target_path)
        self.assertTrue(os.path.exists(target_path))

        # Small pause here as we need to allow daemon processes to work
        time.sleep(3)

        self.assertIsNotNone(runner.check_recipes())
        self.assertIsInstance(runner.check_recipes(), dict)
        self.assertIn('late_add', runner.check_recipes())

    def testWorkflowRunnerRuleCreation(self):
        data = read_dir(directory='examples/meow_directory')
        patterns = data[PATTERNS]
        recipes = data[RECIPES]

        runner = WorkflowRunner(
            TESTING_VGRID,
            0,
            patterns=patterns,
            recipes=recipes,
            daemon=True,
            retro_active_jobs=False,
            print_logging=False
        )

        # Small pause here as we need to allow daemon processes to work
        time.sleep(3)

        self.assertIsNotNone(runner.check_rules())
        self.assertIsInstance(runner.check_rules(), list)
        self.assertEqual(len(runner.check_rules()), 4)
        idless_rules = [{
            RULE_PATH: r[RULE_PATH],
            RULE_PATTERN: r[RULE_PATTERN],
            RULE_RECIPE: r[RULE_RECIPE]
        } for r in runner.check_rules()]
        for rule in STANDARD_RULES:
            self.assertIn(rule, idless_rules)

        self.assertTrue(runner.stop_runner(clear_jobs=True))

    def testWorkflowRunnerPatternRemoval(self):
        data = read_dir(directory='examples/meow_directory')
        patterns = data[PATTERNS]
        recipes = data[RECIPES]

        runner = WorkflowRunner(
            TESTING_VGRID,
            0,
            patterns=patterns,
            recipes=recipes,
            daemon=True,
            retro_active_jobs=False,
            print_logging=False
        )

        # Small pause here as we need to allow daemon processes to work
        time.sleep(3)

        idless_rules = [{
            RULE_PATH: r[RULE_PATH],
            RULE_PATTERN: r[RULE_PATTERN],
            RULE_RECIPE: r[RULE_RECIPE]
        } for r in runner.check_rules()]
        for rule in STANDARD_RULES:
            self.assertIn(rule, idless_rules)

        os.remove(os.path.join(RUNNER_DATA, PATTERNS, 'adder'))

        # Small pause here as we need to allow daemon processes to work
        time.sleep(3)

        self.assertEqual(len(runner.check_rules()), 3)
        idless_rules = [{
            RULE_PATH: r[RULE_PATH],
            RULE_PATTERN: r[RULE_PATTERN],
            RULE_RECIPE: r[RULE_RECIPE]
        } for r in runner.check_rules()]
        for rule in STANDARD_RULES[1:]:
            self.assertIn(rule, idless_rules)

        self.assertTrue(runner.stop_runner(clear_jobs=True))

    def testWorkflowRunnerRecipeRemoval(self):
        data = read_dir(directory='examples/meow_directory')
        patterns = data[PATTERNS]
        recipes = data[RECIPES]

        runner = WorkflowRunner(
            TESTING_VGRID,
            0,
            patterns=patterns,
            recipes=recipes,
            daemon=True,
            retro_active_jobs=False,
            print_logging=False
        )

        # Small pause here as we need to allow daemon processes to work
        time.sleep(3)

        idless_rules = [{
            RULE_PATH: r[RULE_PATH],
            RULE_PATTERN: r[RULE_PATTERN],
            RULE_RECIPE: r[RULE_RECIPE]
        } for r in runner.check_rules()]
        for rule in STANDARD_RULES:
            self.assertIn(rule, idless_rules)

        os.remove(os.path.join(RUNNER_DATA, RECIPES, 'mult'))

        # Small pause here as we need to allow daemon processes to work
        time.sleep(3)

        self.assertEqual(len(runner.check_rules()), 2)
        idless_rules = [{
            RULE_PATH: r[RULE_PATH],
            RULE_PATTERN: r[RULE_PATTERN],
            RULE_RECIPE: r[RULE_RECIPE]
        } for r in runner.check_rules()]
        for rule in [STANDARD_RULES[0], STANDARD_RULES[3]]:
            self.assertIn(rule, idless_rules)

        self.assertTrue(runner.stop_runner(clear_jobs=True))

    def testWorkflowRunnerEventIdentification(self):
        data = read_dir(directory='examples/meow_directory')
        patterns = data[PATTERNS]
        recipes = data[RECIPES]

        runner = WorkflowRunner(
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

        self.assertIsNotNone(runner.check_jobs())
        self.assertIsInstance(runner.check_jobs(), list)
        self.assertEqual(len(runner.check_jobs()), 0)

        data_directory = os.path.join(TESTING_VGRID, 'initial_data')
        os.mkdir(data_directory)
        self.assertTrue(os.path.exists(data_directory))

        data = np.random.randint(100, size=(5, 5))
        data_filename = os.path.join(data_directory, 'datafile.npy')
        self.assertFalse(os.path.exists(data_filename))
        np.save(data_filename, data)

        # Small pause here as we need to allow daemon processes to work
        time.sleep(3)

        self.assertEqual(len(runner.check_jobs()), 4)

        incorrect_directory = os.path.join(TESTING_VGRID, 'init_data')
        os.mkdir(incorrect_directory)
        self.assertTrue(os.path.exists(incorrect_directory))

        incorrect_filename = \
            os.path.join(TESTING_VGRID, 'init_data', 'datafile.npy')
        np.save(incorrect_filename, data)

        # Small pause here as we need to allow daemon processes to work
        time.sleep(3)

        self.assertEqual(len(runner.check_jobs()), 4)

        self.assertTrue(runner.stop_runner(clear_jobs=True))

    def testWorkflowRunnerJobExecution(self):
        data = read_dir(directory='examples/meow_directory')
        patterns = data[PATTERNS]
        recipes = data[RECIPES]

        runner = WorkflowRunner(
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

        self.assertIsNotNone(runner.check_jobs())
        self.assertIsInstance(runner.check_jobs(), list)
        self.assertEqual(len(runner.check_jobs()), 0)

        data_directory = os.path.join(TESTING_VGRID, 'initial_data')
        os.mkdir(data_directory)
        self.assertTrue(os.path.exists(data_directory))

        data = np.random.randint(100, size=(5, 5))
        data_filename = os.path.join(data_directory, 'datafile.npy')
        self.assertFalse(os.path.exists(data_filename))
        np.save(data_filename, data)

        # Small pause here as we need to allow daemon processes to work
        time.sleep(3)

        self.assertEqual(len(runner.check_jobs()), 4)

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
        patterns = data[PATTERNS]
        recipes = data[RECIPES]

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
