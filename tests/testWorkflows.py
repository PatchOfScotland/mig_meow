import unittest

from mig_meow.pattern import Pattern
from mig_meow.constants import NAME, INPUT_FILE, TRIGGER_PATHS, RECIPES, \
    OUTPUT, VARIABLES, TRIGGER_RECIPES

class WorkflowTest(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def testNewPatternCreation(self):
        self.createStandardPattern()

    def testDictPatternCreation(self):
        self.createStandardPatternFromDict()

    def testPatternIdentify(self):
        standard_pattern = self.createStandardPattern()
        standard_dict_pattern = self.createStandardPatternFromDict()

        print(standard_pattern)
        print(standard_dict_pattern)

        self.assertEqual(standard_pattern, standard_dict_pattern)

    def testWorkflow(self):
        pass

    def createStandardPattern(self):
        test_pattern = Pattern('standard_pattern')

        test_pattern.add_single_input('input_file', 'dir/regex.path')
        with self.assertRaises(Exception):
            test_pattern.add_single_input('another_input', 'dir/regex.path')

        test_pattern.add_output('output_file', 'dir/regex.path')
        test_pattern.add_output('another_output', 'dir/regex.path')
        with self.assertRaises(Exception):
            test_pattern.add_output('another_output', 'dir/regex.path')

        test_pattern.add_static_input('static_input', 'dir/regex.path')
        test_pattern.add_static_input('another_static_input', 'dir/regex.path')
        with self.assertRaises(Exception):
            test_pattern.add_static_input('another_static_input',
                                          'dir/regex.path')
        with self.assertRaises(Exception):
            test_pattern.add_static_input('input_file', 'dir/regex.path')

        test_pattern.return_notebook('dir/notebook.path')

        test_pattern.add_recipe('recipe')
        test_pattern.add_recipe('recipe')

        test_pattern.add_variable('int', 0)
        test_pattern.add_variable('float', 3.5)
        test_pattern.add_variable('array', [0, 1])
        test_pattern.add_variable('dict', {1: 1, 2: 2})
        test_pattern.add_variable('set', {1, 2})
        test_pattern.add_variable('char', 'c')
        test_pattern.add_variable('string', "String")
        test_pattern.add_variable('boolean', True)

        with self.assertRaises(Exception):
            test_pattern.add_variable('int', 1)
        with self.assertRaises(Exception):
            test_pattern.add_variable('input_file', 1)
        with self.assertRaises(Exception):
            test_pattern.add_variable('output_file', 1)
        with self.assertRaises(Exception):
            test_pattern.add_variable('static_input', 1)

        valid, _ = test_pattern.integrity_check()
        self.assertTrue(valid)

        return test_pattern

    def createStandardPatternFromDict(self):
        dict = {
            NAME: "standard_pattern",
            INPUT_FILE: "input_file",
            TRIGGER_PATHS: ['dir/regex.path'],
            # TODO improve
            TRIGGER_RECIPES: [],
            # RECIPES: ['recipe', 'recipe'],
            OUTPUT: {
                'output_file': 'dir/regex.path',
                'another_output': 'dir/regex.path',
                'wf_job': 'dir/notebook.path'
            },
            VARIABLES: {
                'input_file': 'input_file',
                'output_file': 'output_file',
                'another_output': 'another_output',
                'static_input': 'static_input',
                'another_static_input': 'another_static_input',
                'int': 0,
                'float': 3.5,
                'array': [0, 1],
                'dict': {1: 1, 2: 2},
                'set': {1, 2},
                'char': 'c',
                'string': "String",
                'boolean': True,
                'wf_job': 'wf_job'
            }
        }

        test_pattern = Pattern(dict)

        valid, _ = test_pattern.integrity_check()
        self.assertTrue(valid)

        return test_pattern