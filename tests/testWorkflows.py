import unittest
import copy
import nbformat
import os

from mig_meow.constants import NO_OUTPUT_SET_WARNING, MEOW_MODE, CWL_MODE, \
    DEFAULT_WORKFLOW_TITLE, DEFAULT_CWL_IMPORT_EXPORT_DIR, PATTERNS, RECIPES, \
    WORKFLOWS, STEPS, SETTINGS, MEOW_NEW_RECIPE_BUTTON, \
    MEOW_EDIT_RECIPE_BUTTON, MEOW_EDIT_PATTERN_BUTTON, \
    MEOW_IMPORT_VGRID_BUTTON, MEOW_EXPORT_VGRID_BUTTON, \
    MEOW_NEW_PATTERN_BUTTON, MEOW_IMPORT_CWL_BUTTON, DEFAULT_JOB_NAME, \
    NO_NAME_SET_ERROR, NO_RECIPES_SET_ERROR, NO_INPUT_PATH_SET_ERROR, \
    NO_INPUT_FILE_SET_ERROR, PLACEHOLDER_ERROR, \
    OUTPUT_NOT_VARIABLE_ERROR, TRIGGER_NOT_VARIABLE_ERROR, \
    INVALID_INPUT_PATH_ERROR, PLACEHOLDER, NAME, INPUT_FILE, TRIGGER_PATHS, \
    TRIGGER_RECIPES, OUTPUT, VARIABLES, SOURCE, RECIPE, CWL_NAME, \
    CWL_REQUIREMENTS, CWL_CWL_VERSION, CWL_CLASS, CWL_BASE_COMMAND, \
    CWL_INPUTS, CWL_OUTPUTS, CWL_STEPS, CWL_STDOUT, CWL_ARGUMENTS, CWL_HINTS, \
    CWL_VARIABLES, TRIGGER_OUTPUT, NOTEBOOK_OUTPUT
from mig_meow.inputs import is_valid_recipe_dict, is_valid_pattern_dict
from mig_meow.meow import Pattern, check_patterns_dict, \
    build_workflow_object, create_recipe_dict
from mig_meow.workflow_widget import WorkflowWidget

EMPTY_NOTEBOOK = 'test_notebook.ipynb'

VALID_PATTERN_DICT = {
    NAME: 'test_pattern',
    TRIGGER_PATHS: ['dir/literal.path'],
    TRIGGER_RECIPES: {
        'trigger_id': {
            'recipe_id': {
                'name': 'test_recipe',
                'source': 'source.ipynb',
                'recipe': {}
            }
        }
    },
    INPUT_FILE: 'trigger_file_name',
    OUTPUT: {
        'outfile_1': 'dir_1/out.path',
        'outfile_2': 'dir_2/out.path',
        DEFAULT_JOB_NAME: 'notebook/output.path',
        'trigger_file_name': 'trigger/file/output.path'
    },
    VARIABLES: {
        'int': 0,
        'float': 3.5,
        'array': [0, 1],
        'dict': {1: 1, 2: 2},
        'set': {1, 2},
        'char': 'c',
        'string': "String",
        'boolean': True
    }
}

VALID_RECIPE_DICT = {
    NAME: 'test_recipe',
    SOURCE: 'test_notebook.ipynb',
    RECIPE: {
        'cells': [],
        'metadata': {},
        'nbformat': 4,
        'nbformat_minor': 2
    }
}

VALID_WORKFLOW_DICT = {
    CWL_NAME: 'workflow_name',
    CWL_CWL_VERSION: 'v1.0',
    CWL_CLASS: 'workflow',
    CWL_INPUTS: {},
    CWL_OUTPUTS: {},
    CWL_STEPS: {},
    CWL_REQUIREMENTS: {}
}

VALID_STEP_DICT = {
    CWL_NAME: 'step_name',
    CWL_CWL_VERSION: 'v1.0',
    CWL_CLASS: 'commandLineTool',
    CWL_BASE_COMMAND: '',
    CWL_STDOUT: '',
    CWL_INPUTS: {},
    CWL_OUTPUTS: {},
    CWL_ARGUMENTS: [],
    CWL_REQUIREMENTS: {},
    CWL_HINTS: {}
}

VALID_SETTINGS_DICT = {
    CWL_NAME: 'variables_name',
    CWL_VARIABLES: {}
}

VALID_PATTERN_FORM_VALUES = {
    NAME: 'test_pattern',
    TRIGGER_PATHS: ['dir/literal.path'],
    RECIPES: [
        'test_recipe'
    ],
    INPUT_FILE: 'trigger_file_name',
    TRIGGER_OUTPUT: 'trigger/file/output.path',
    NOTEBOOK_OUTPUT: 'notebook/output.path',
    OUTPUT: [
        {
            'Name': 'outfile_1',
            'Value': 'dir_1/out.path'
        },
        {
            'Name': 'outfile_2',
            'Value': 'dir_2/out.path'
        }
    ],
    VARIABLES: [
        {
            'Name': 'int',
            'Value': 0
        },
        {
            'Name': 'float',
            'Value': 3.5
        },
        {
            'Name': 'array',
            'Value': [0, 1]
        },
        {
            'Name': 'dict',
            'Value': {1: 1, 2: 2}
        },
        {
            'Name': 'set',
            'Value': {1, 2}
        },
        {
            'Name': 'char',
            'Value': 'c'
        },
        {
            'Name': 'string',
            'Value': "String"
        },
        {
            'Name': 'boolean',
            'Value': True
        }
    ]
}


class WorkflowTest(unittest.TestCase):
    def setUp(self):
        if os.path.exists(EMPTY_NOTEBOOK):
            raise Exception(
                "Required test location '%s' is already in use"
                % EMPTY_NOTEBOOK
            )
        notebook = nbformat.v4.new_notebook()
        nbformat.write(notebook, EMPTY_NOTEBOOK)

    def tearDown(self):
        os.remove(EMPTY_NOTEBOOK)

    def testPatternDictCheck(self):
        # Test valid pattern dict is accepted
        valid, msg = is_valid_pattern_dict(VALID_PATTERN_DICT)
        self.assertTrue(valid)
        self.assertEqual(msg, '')

        # Test that 'output' is optional.
        no_output_dict = copy.deepcopy(VALID_PATTERN_DICT)
        no_output_dict.pop(OUTPUT)
        valid, msg = is_valid_pattern_dict(no_output_dict)
        self.assertTrue(valid)
        self.assertEqual(msg, '')

        # Test that 'variables' is optional.
        no_variables_dict = copy.deepcopy(VALID_PATTERN_DICT)
        no_variables_dict.pop(VARIABLES)
        valid, msg = is_valid_pattern_dict(no_variables_dict)
        self.assertTrue(valid)
        self.assertEqual(msg, '')

        # Test non-dict is rejected
        valid, msg = is_valid_pattern_dict(1)
        self.assertFalse(valid)
        self.assertIsNotNone(msg)

        # Test invalid 'name' type is rejected
        incorrect_name_dict = copy.deepcopy(VALID_PATTERN_DICT)
        incorrect_name_dict[NAME] = 1
        valid, msg = is_valid_pattern_dict(incorrect_name_dict)
        self.assertFalse(valid)
        self.assertIsNotNone(msg)

        # Test invalid 'input_paths' type is rejected
        incorrect_paths_dict = copy.deepcopy(VALID_PATTERN_DICT)
        incorrect_paths_dict[TRIGGER_PATHS] = 1
        valid, msg = is_valid_pattern_dict(incorrect_paths_dict)
        self.assertFalse(valid)
        self.assertIsNotNone(msg)

        # Test invalid 'trigger_recipes' type is rejected
        incorrect_recipes_dict = copy.deepcopy(VALID_PATTERN_DICT)
        incorrect_recipes_dict[TRIGGER_RECIPES] = 1
        valid, msg = is_valid_pattern_dict(incorrect_recipes_dict)
        self.assertFalse(valid)
        self.assertIsNotNone(msg)

        # Test invalid 'input_file' type is rejected
        incorrect_file_dict = copy.deepcopy(VALID_PATTERN_DICT)
        incorrect_file_dict[INPUT_FILE] =1
        valid, msg = is_valid_pattern_dict(incorrect_file_dict)
        self.assertFalse(valid)
        self.assertIsNotNone(msg)

        # Test invalid 'output' type is rejected.
        incorrect_output_dict = copy.deepcopy(VALID_PATTERN_DICT)
        incorrect_output_dict[OUTPUT] =1
        valid, msg = is_valid_pattern_dict(incorrect_output_dict)
        self.assertFalse(valid)
        self.assertIsNotNone(msg)

        # Test invalid 'variables' type is rejected.
        incorrect_variables_dict = copy.deepcopy(VALID_PATTERN_DICT)
        incorrect_variables_dict[VARIABLES] = 1
        valid, msg = is_valid_pattern_dict(incorrect_variables_dict)
        self.assertFalse(valid)
        self.assertIsNotNone(msg)

        # Test missing 'name' key is rejected.
        no_name_dict = copy.deepcopy(VALID_PATTERN_DICT)
        no_name_dict.pop(NAME)
        valid, msg = is_valid_pattern_dict(no_name_dict)
        self.assertFalse(valid)
        self.assertIsNotNone(msg)

        # Test missing 'input_paths' key is rejected.
        no_paths_dict = copy.deepcopy(VALID_PATTERN_DICT)
        no_paths_dict.pop(TRIGGER_PATHS)
        valid, msg = is_valid_pattern_dict(no_paths_dict)
        self.assertFalse(valid)
        self.assertIsNotNone(msg)

        # Test missing 'trigger_recipes' key is rejected.
        no_recipes_dict = copy.deepcopy(VALID_PATTERN_DICT)
        no_recipes_dict.pop(TRIGGER_RECIPES)
        valid, msg = is_valid_pattern_dict(no_recipes_dict)
        self.assertFalse(valid)
        self.assertIsNotNone(msg)

        # Test missing 'input_file' key is rejected.
        no_file_dict = copy.deepcopy(VALID_PATTERN_DICT)
        no_file_dict.pop(INPUT_FILE)
        valid, msg = is_valid_pattern_dict(no_file_dict)
        self.assertFalse(valid)
        self.assertIsNotNone(msg)

        # Test extra keys do not fail, if 'strict' is left False.
        extra_values_dict = copy.deepcopy(VALID_PATTERN_DICT)
        extra_values_dict['extra'] = 'extra'
        valid, msg = is_valid_pattern_dict(extra_values_dict)
        self.assertTrue(valid)
        self.assertEqual(msg, '')

        # Test extra keys fail if 'strict set to True.
        valid, msg = is_valid_pattern_dict(extra_values_dict, strict=True)
        self.assertFalse(valid)
        self.assertIsNotNone(msg)

    def testNewPatternCreation(self):
        test_pattern = Pattern('standard_pattern')

        # Test that pattern with only a name is not valid.
        valid, _ = test_pattern.integrity_check()
        self.assertFalse(valid)

        test_pattern.add_single_input('input_file', 'dir/regex.path')
        # Test that we cannot add a 'single input' once one has already been
        # defined
        with self.assertRaises(Exception):
            test_pattern.add_single_input('another_input', 'dir/regex.path')

        # Test that pattern is not valid without recipe.
        valid, msg = test_pattern.integrity_check()
        self.assertFalse(valid)

        test_pattern.add_recipe('recipe')
        test_pattern.add_recipe('recipe')

        # Test that both recipes have been added.
        self.assertEqual(len(test_pattern.recipes), 2)

        # Test that pattern is now valid, but that it returns a no output
        # warning.
        valid, msg = test_pattern.integrity_check()
        self.assertTrue(valid)
        self.assertEqual(msg, NO_OUTPUT_SET_WARNING)

        test_pattern.add_output('output_file', 'dir/regex.path')
        test_pattern.add_output('another_output', 'dir/regex.path')
        # Test that we cannot define two outputs with the same name.
        with self.assertRaises(Exception):
            test_pattern.add_output('another_output', 'dir/regex.path')

        test_pattern.return_notebook('dir/notebook.path')

        test_pattern.add_variable('int', 0)
        test_pattern.add_variable('float', 3.5)
        test_pattern.add_variable('array', [0, 1])
        test_pattern.add_variable('dict', {1: 1, 2: 2})
        test_pattern.add_variable('set', {1, 2})
        test_pattern.add_variable('char', 'c')
        test_pattern.add_variable('string', "String")
        test_pattern.add_variable('boolean', True)

        # Test that pattern is still valid with added variables
        valid, msg = test_pattern.integrity_check()
        self.assertTrue(valid)
        self.assertEqual(msg, '')

        # Test that we cannot add a variable that already has been defined.
        with self.assertRaises(Exception):
            test_pattern.add_variable('int', 1)
        # Test that we cannot add a variable that shares a name with the
        # 'input_file'.
        with self.assertRaises(Exception):
            test_pattern.add_variable('input_file', 1)
        # Test that we cannot add a variable that shares a name with an output
        # file
        with self.assertRaises(Exception):
            test_pattern.add_variable('output_file', 1)

        # Test that pattern is still valid and the 3 above tests have not
        # invalidated the pattern.
        valid, msg = test_pattern.integrity_check()
        self.assertTrue(valid)
        self.assertEqual(msg, '')

    def testDictPatternCreation(self):
        # Test pattern is valid with valid dictionary input. This simulates a
        # dictionary provided by the MiG, with an already registered recipe.
        test_pattern = Pattern(VALID_PATTERN_DICT)
        valid, msg = test_pattern.integrity_check()
        self.assertTrue(valid)
        self.assertEqual(msg, '')

        alt_pattern_dict = {
            NAME: 'alt_dict_pattern',
            TRIGGER_PATHS: ['dir/literal.path'],
            TRIGGER_RECIPES: {
                'trigger_id': {
                    'recipe_name': {}
                }
            },
            INPUT_FILE: 'trigger_file_name',
            OUTPUT: {
                'outfile_1': 'dir_1/outpath.txt',
                'outfile_2': 'dir_2/outpath.txt',
            },
            VARIABLES: {
                'int': 0,
                'float': 3.5,
                'array': [0, 1],
                'dict': {1: 1, 2: 2},
                'set': {1, 2},
                'char': 'c',
                'string': "String",
                'boolean': True
            }
        }

        # Test pattern is valid with valid dictionary input. This simulates a
        # dictionary provided by the MiG, with a recipe not yet registered.
        test_alt_pattern = Pattern(alt_pattern_dict)
        valid, msg = test_alt_pattern.integrity_check()
        self.assertTrue(valid)
        self.assertEqual(msg, '')

        # Test that no 'name' value is rejected.
        test_alt_pattern.name = None
        valid, msg = test_alt_pattern.integrity_check()
        self.assertFalse(valid)
        self.assertEqual(msg, NO_NAME_SET_ERROR)

        # Test that an empty 'name' value is rejected.
        test_alt_pattern.name = ''
        valid, msg = test_alt_pattern.integrity_check()
        self.assertFalse(valid)
        self.assertEqual(msg, NO_NAME_SET_ERROR)

        invalid_recipes = {
            NAME: 'invalid_recipes',
            TRIGGER_PATHS: ['dir/literal.path'],
            TRIGGER_RECIPES: {
                'recipe_name': {}
            },
            INPUT_FILE: 'trigger_file_name',
            OUTPUT: {
                'outfile_1': 'dir_1/outpath.txt',
                'outfile_2': 'dir_2/outpath.txt',
            },
            VARIABLES: {
                'int': 0,
                'float': 3.5,
                'array': [0, 1],
                'dict': {1: 1, 2: 2},
                'set': {1, 2},
                'char': 'c',
                'string': "String",
                'boolean': True
            }
        }

        # Test that incorrectly formatted 'trigger_recipes' values is rejected.
        invalid_recipes_pattern = Pattern(invalid_recipes)
        valid, msg = invalid_recipes_pattern.integrity_check()
        self.assertFalse(valid)
        self.assertEqual(msg, NO_RECIPES_SET_ERROR)

        no_paths = {
            NAME: 'dict_pattern',
            TRIGGER_PATHS: [],
            TRIGGER_RECIPES: {
                'recipe_id': {
                    'name': 'recipe',
                    'source': 'source.ipynb',
                    'recipe': {}
                }
            },
            INPUT_FILE: 'trigger_file_name',
            OUTPUT: {
                'outfile_1': 'dir_1/outpath.txt',
                'outfile_2': 'dir_2/outpath.txt',
            },
            VARIABLES: {
                'int': 0,
                'float': 3.5,
                'array': [0, 1],
                'dict': {1: 1, 2: 2},
                'set': {1, 2},
                'char': 'c',
                'string': "String",
                'boolean': True,
                'outfile_1': 'something'
            }
        }

        # Test that empty 'input_paths' list is rejected.
        no_paths_pattern = Pattern(no_paths)
        valid, msg = no_paths_pattern.integrity_check()
        self.assertFalse(valid)
        self.assertEqual(msg, NO_INPUT_PATH_SET_ERROR)

        invalid_paths = {
            NAME: 'dict_pattern',
            TRIGGER_PATHS: [''],
            TRIGGER_RECIPES: {
                'recipe_id': {
                    'name': 'recipe',
                    'source': 'source.ipynb',
                    'recipe': {}
                }
            },
            INPUT_FILE: 'trigger_file_name',
            OUTPUT: {
                'outfile_1': 'dir_1/outpath.txt',
                'outfile_2': 'dir_2/outpath.txt',
            },
            VARIABLES: {
                'int': 0,
                'float': 3.5,
                'array': [0, 1],
                'dict': {1: 1, 2: 2},
                'set': {1, 2},
                'char': 'c',
                'string': "String",
                'boolean': True,
                'outfile_1': 'something'
            }
        }

        # Test that empty 'input_path' list entry is rejected.
        invalid_paths_pattern = Pattern(invalid_paths)
        valid, msg = invalid_paths_pattern.integrity_check()
        self.assertFalse(valid)
        self.assertIn(INVALID_INPUT_PATH_ERROR, msg)

        invalid_in_file = {
            NAME: 'dict_pattern',
            TRIGGER_PATHS: ['path'],
            TRIGGER_RECIPES: {
                'recipe_id': {
                    'name': 'recipe',
                    'source': 'source.ipynb',
                    'recipe': {}
                }
            },
            INPUT_FILE: '',
            OUTPUT: {
                'outfile_1': 'dir_1/outpath.txt',
                'outfile_2': 'dir_2/outpath.txt',
            },
            VARIABLES: {
                'int': 0,
                'float': 3.5,
                'array': [0, 1],
                'dict': {1: 1, 2: 2},
                'set': {1, 2},
                'char': 'c',
                'string': "String",
                'boolean': True,
                'outfile_1': 'something'
            }
        }

        # Test that empty 'input_file' value is rejected.
        with self.assertRaises(Exception):
            Pattern(invalid_in_file)

        # Test that no pattern 'trigger_file' is rejected.
        no_infile_pattern = Pattern(VALID_PATTERN_DICT)
        no_infile_pattern.trigger_file = None
        valid, msg = no_infile_pattern.integrity_check()
        self.assertFalse(valid)
        self.assertEqual(msg, NO_INPUT_FILE_SET_ERROR)

        # Test that empty pattern 'trigger_file is rejected.
        no_infile_pattern.trigger_file = ''
        valid, msg = no_infile_pattern.integrity_check()
        self.assertFalse(valid)
        self.assertEqual(msg, NO_INPUT_FILE_SET_ERROR)

        # Test that a pattern output not being in 'variables' is rejected.
        output_not_variable_pattern = Pattern(VALID_PATTERN_DICT)
        output_not_variable_pattern.variables.pop('outfile_1')
        valid, msg = output_not_variable_pattern.integrity_check()
        self.assertFalse(valid)
        self.assertIn(OUTPUT_NOT_VARIABLE_ERROR, msg)

        # Test that a pattern 'input_file' not being in 'variables' is
        # rejected.
        trigger_not_variable_pattern = Pattern(VALID_PATTERN_DICT)
        trigger_not_variable_pattern.variables.pop('trigger_file_name')
        valid, msg = trigger_not_variable_pattern.integrity_check()
        self.assertFalse(valid)
        self.assertEqual(msg, TRIGGER_NOT_VARIABLE_ERROR)

    def testPatternPlaceholderCheck(self):
        # Test that pattern is valid with valid dictionary.
        test_pattern = Pattern(VALID_PATTERN_DICT)
        valid, msg = test_pattern.integrity_check()
        self.assertTrue(valid)
        self.assertEqual(msg, '')

        # Test that placeholder name value is invalid.
        placeholder_name_pattern = Pattern(VALID_PATTERN_DICT)
        placeholder_name_pattern.name = PLACEHOLDER
        valid, msg = placeholder_name_pattern.integrity_check()
        self.assertFalse(valid)
        self.assertEqual(msg, PLACEHOLDER_ERROR)

        # Test that placeholder 'input_file' is invalid.
        placeholder_trigger_file_pattern = Pattern(VALID_PATTERN_DICT)
        placeholder_trigger_file_pattern.trigger_file = PLACEHOLDER
        placeholder_trigger_file_pattern.variables[PLACEHOLDER] = PLACEHOLDER
        valid, msg = placeholder_trigger_file_pattern.integrity_check()
        self.assertFalse(valid)
        self.assertEqual(msg, PLACEHOLDER_ERROR)

        # Test that placeholder 'trigger_paths' is invalid.
        placeholder_trigger_paths_pattern = Pattern(VALID_PATTERN_DICT)
        placeholder_trigger_paths_pattern.trigger_paths = PLACEHOLDER
        valid, msg = placeholder_trigger_paths_pattern.integrity_check()
        self.assertFalse(valid)
        self.assertEqual(msg, PLACEHOLDER_ERROR)

        # Test that placeholder 'recipes' is invalid.
        placeholder_recipes_pattern = Pattern(VALID_PATTERN_DICT)
        placeholder_recipes_pattern.recipes = PLACEHOLDER
        valid, msg = placeholder_recipes_pattern.integrity_check()
        self.assertFalse(valid)
        self.assertEqual(msg, PLACEHOLDER_ERROR)

        # Test that placeholder being in 'trigger_paths' list is invalid.
        placeholder_in_path_entries_pattern = Pattern(VALID_PATTERN_DICT)
        placeholder_in_path_entries_pattern.trigger_paths[0] = PLACEHOLDER
        valid, msg = placeholder_in_path_entries_pattern.integrity_check()
        self.assertFalse(valid)
        self.assertEqual(msg, PLACEHOLDER_ERROR)

        # Test that placeholder being in 'recipes' list is invalid.
        placeholder_recipe_entries_pattern = Pattern(VALID_PATTERN_DICT)
        placeholder_recipe_entries_pattern.recipes[0] = PLACEHOLDER
        valid, msg = placeholder_recipe_entries_pattern.integrity_check()
        self.assertFalse(valid)
        self.assertEqual(msg, PLACEHOLDER_ERROR)

        # Test that placeholder being in 'variables' keys is invalid.
        placeholder_variable_key_pattern = Pattern(VALID_PATTERN_DICT)
        placeholder_variable_key_pattern.variables[PLACEHOLDER] = 'value'
        valid, msg = placeholder_variable_key_pattern.integrity_check()
        self.assertFalse(valid)
        self.assertEqual(msg, PLACEHOLDER_ERROR)

        # Test that placeholder being in 'variables' values is invalid.
        placeholder_variable_value_pattern = Pattern(VALID_PATTERN_DICT)
        placeholder_variable_value_pattern.variables['extra'] = PLACEHOLDER
        valid, msg = placeholder_variable_value_pattern.integrity_check()
        self.assertFalse(valid)
        self.assertEqual(msg, PLACEHOLDER_ERROR)

        # Test that placeholder being in 'output' keys is invalid.
        placeholder_output_key_pattern = Pattern(VALID_PATTERN_DICT)
        placeholder_output_key_pattern.outputs[PLACEHOLDER] = 'path'
        placeholder_output_key_pattern.variables[PLACEHOLDER] = PLACEHOLDER
        valid, msg = placeholder_output_key_pattern.integrity_check()
        self.assertFalse(valid)
        self.assertEqual(msg, PLACEHOLDER_ERROR)

        # Test that placeholder being in 'output' values is invalid.
        placeholder_output_value_pattern = Pattern(VALID_PATTERN_DICT)
        placeholder_output_value_pattern.outputs['extra'] = PLACEHOLDER
        placeholder_output_value_pattern.variables['extra'] = 'extra'
        valid, msg = placeholder_output_value_pattern.integrity_check()
        self.assertFalse(valid)
        self.assertEqual(msg, PLACEHOLDER_ERROR)

    def testPatternIdentify(self):
        test_pattern_1 = Pattern('identical_pattern')

        test_pattern_1.add_single_input('trigger_file_name', 'dir/regex.path')

        test_pattern_1.add_output('outfile_1', 'dir_1/outpath.txt')
        test_pattern_1.add_output('outfile_2', 'dir_2/outpath.txt')

        test_pattern_1.add_recipe('recipe')

        test_pattern_1.add_variable('int', 0)
        test_pattern_1.add_variable('float', 3.5)
        test_pattern_1.add_variable('array', [0, 1])
        test_pattern_1.add_variable('dict', {1: 1, 2: 2})
        test_pattern_1.add_variable('set', {1, 2})
        test_pattern_1.add_variable('char', 'c')
        test_pattern_1.add_variable('string', "String")
        test_pattern_1.add_variable('boolean', True)

        # Test that first pattern is valid.
        valid, msg = test_pattern_1.integrity_check()
        self.assertTrue(valid)

        pattern_dict = {
            NAME: 'identical_pattern',
            TRIGGER_PATHS: ['dir/regex.path'],
            TRIGGER_RECIPES: {
                'trigger_id': {
                    'recipe_id': {
                        'name': 'recipe',
                        'source': 'source.ipynb',
                        'recipe': {}
                    }
                }
            },
            INPUT_FILE: 'trigger_file_name',
            OUTPUT: {
                'outfile_1': 'dir_1/outpath.txt',
                'outfile_2': 'dir_2/outpath.txt',
            },
            VARIABLES: {
                'int': 0,
                'float': 3.5,
                'array': [0, 1],
                'dict': {1: 1, 2: 2},
                'set': {1, 2},
                'char': 'c',
                'string': "String",
                'boolean': True
            }
        }

        # Test that second pattern is valid.
        test_pattern_2 = Pattern(pattern_dict)
        valid, msg = test_pattern_2.integrity_check()
        self.assertTrue(valid)

        pattern_dict['persistence_id'] = '12345678910'

        # Test that third pattern is valid
        test_pattern_3 = Pattern(pattern_dict)
        valid, msg = test_pattern_3.integrity_check()
        self.assertTrue(valid)

        # Test that first and second patterns are equal
        self.assertTrue(test_pattern_1 == test_pattern_2)

        # Test that first and third patterns are not equal
        self.assertFalse(test_pattern_1 == test_pattern_3)

        # Test that second and third patterns are not equal
        self.assertFalse(test_pattern_2 == test_pattern_3)

    def testPatternsDictCheck(self):
        # Test that check on patterns dict is acceptable
        pass

    def testRecipeDictCheck(self):
        # Test that valid dict is valid.
        valid, msg = is_valid_recipe_dict(VALID_RECIPE_DICT)
        self.assertTrue(valid)
        self.assertEqual(msg, '')

        # Test that non-dict type is rejected.
        valid, msg = is_valid_recipe_dict(1)
        self.assertFalse(valid)
        self.assertIsNotNone(msg)

        # Test that invalid 'name' type is rejected.
        incorrect_name_dict = copy.deepcopy(VALID_RECIPE_DICT)
        incorrect_name_dict[NAME] = 1
        valid, msg = is_valid_recipe_dict(incorrect_name_dict)
        self.assertFalse(valid)
        self.assertIsNotNone(msg)

        # Test that invalid 'source' type is rejected.
        incorrect_source_dict = copy.deepcopy(VALID_RECIPE_DICT)
        incorrect_source_dict[SOURCE] = 1
        valid, msg = is_valid_recipe_dict(incorrect_source_dict)
        self.assertFalse(valid)
        self.assertIsNotNone(msg)

        # Test that invalid 'recipe' type is rejected.
        incorrect_recipe_dict = copy.deepcopy(VALID_RECIPE_DICT)
        incorrect_recipe_dict[RECIPE] = 1
        valid, msg = is_valid_recipe_dict(incorrect_recipe_dict)
        self.assertFalse(valid)
        self.assertIsNotNone(msg)

        # Test that no 'name' key is rejected.
        no_name_dict = copy.deepcopy(VALID_RECIPE_DICT)
        no_name_dict.pop(NAME)
        valid, msg = is_valid_recipe_dict(no_name_dict)
        self.assertFalse(valid)
        self.assertIsNotNone(msg)

        # Test that no 'source' key is rejected.
        no_source_dict = copy.deepcopy(VALID_RECIPE_DICT)
        no_source_dict.pop(SOURCE)
        valid, msg = is_valid_recipe_dict(no_source_dict)
        self.assertFalse(valid)
        self.assertIsNotNone(msg)

        # Test that extra keys are still valid when 'strict' left set to False.
        extra_values_dict = copy.deepcopy(VALID_RECIPE_DICT)
        extra_values_dict['extra'] = 'extra'
        valid, msg = is_valid_recipe_dict(extra_values_dict)
        self.assertTrue(valid)
        self.assertEqual(msg, '')

        # Test that extra keys are rejected when 'strict' set to True.
        valid, msg = is_valid_recipe_dict(extra_values_dict, strict=True)
        self.assertFalse(valid)
        self.assertIsNotNone(msg)

    def testRecipeCreation(self):
        notebook_dict = nbformat.read(EMPTY_NOTEBOOK, nbformat.NO_CONVERT)

        recipe_dict = \
            create_recipe_dict(notebook_dict, 'test_recipe', EMPTY_NOTEBOOK)

        expected_dict = {
            NAME: 'test_recipe',
            SOURCE: 'test_notebook.ipynb',
            RECIPE: {
                'cells': [],
                'metadata': {},
                'nbformat': 4,
                'nbformat_minor': 2
            }
        }

        # Test that created recipe has expected values.
        self.assertTrue(recipe_dict == expected_dict)

    def testRecipesDictCheck(self):
        # Test that check on recipes dict is acceptable
        pass

    def testMeowWorkflow(self):
        pattern_one_dict = {
            NAME: 'first_pattern',
            TRIGGER_PATHS: ['start'],
            TRIGGER_RECIPES: {
                'trigger_id': {
                    'recipe_id': {
                        'name': 'recipe',
                        'source': 'source.ipynb',
                        'recipe': {}
                    }
                }
            },
            INPUT_FILE: 'trigger_file_name',
            OUTPUT: {
                'outfile_1': 'first/one',
                'outfile_2': 'first/two',
            },
            VARIABLES: {}
        }

        # Test pattern_one is valid. This should have no ancestors and pattern
        # two and three and descendants.
        pattern_one = Pattern(pattern_one_dict)
        valid, msg = pattern_one.integrity_check()
        self.assertTrue(valid)
        self.assertEqual(msg, '')

        pattern_two_dict = {
            'name': 'second_pattern',
            'input_paths': ['first/one'],
            'trigger_recipes': {
                'trigger_id': {
                    'recipe_id': {
                        'name': 'recipe',
                        'source': 'source.ipynb',
                        'recipe': {}
                    }
                }
            },
            'input_file': 'trigger_file_name',
            'output': {},
            'variables': {}
        }

        # Test pattern_two is valid but has a no output warning. This should
        # have pattern one as an ancestor and no descendants.
        pattern_two = Pattern(pattern_two_dict)
        valid, msg = pattern_two.integrity_check()
        self.assertTrue(valid)
        self.assertEqual(msg, NO_OUTPUT_SET_WARNING)

        pattern_three_dict = {
            'name': 'third_pattern',
            'input_paths': ['first/two'],
            'trigger_recipes': {
                'trigger_id': {
                    'recipe_id': {
                        'name': 'recipe',
                        'source': 'source.ipynb',
                        'recipe': {}
                    }
                }
            },
            'input_file': 'trigger_file_name',
            'output': {
                'outfile': 'third/one'
            },
            'variables': {}
        }

        # Test pattern_three is valid. This should have pattern one and five
        # as ancestors and pattern 4 as a descendant.
        pattern_three = Pattern(pattern_three_dict)
        valid, msg = pattern_three.integrity_check()
        self.assertTrue(valid)
        self.assertEqual(msg, '')

        pattern_four_dict = {
            'name': 'fourth_pattern',
            'input_paths': ['third/one'],
            'trigger_recipes': {
                'trigger_id': {
                    'recipe_id': {
                        'name': 'recipe',
                        'source': 'source.ipynb',
                        'recipe': {}
                    }
                }
            },
            'input_file': 'trigger_file_name',
            'output': {
                'outfile': 'four/one'
            },
            'variables': {}
        }

        # Test pattern_four is valid. This should have pattern three as an
        # ancestor and pattern five as a descendant.
        pattern_four = Pattern(pattern_four_dict)
        valid, msg = pattern_four.integrity_check()
        self.assertTrue(valid)
        self.assertEqual(msg, '')

        pattern_five_dict = {
            'name': 'fifth_pattern',
            'input_paths': ['four/one'],
            'trigger_recipes': {
                'trigger_id': {
                    'recipe_id': {
                        'name': 'recipe',
                        'source': 'source.ipynb',
                        'recipe': {}
                    }
                }
            },
            'input_file': 'trigger_file_name',
            'output': {
                'outfile': 'first/two'
            },
            'variables': {}
        }

        # Test pattern_five is valid. This should have pattern four as an
        # ancestor and pattern three as a descendant.
        pattern_five = Pattern(pattern_five_dict)
        valid, msg = pattern_five.integrity_check()
        self.assertTrue(valid)
        self.assertEqual(msg, '')

        pattern_six_dict = {
            'name': 'sixth_pattern',
            'input_paths': ['unlinked'],
            'trigger_recipes': {
                'trigger_id': {
                    'recipe_id': {
                        'name': 'recipe',
                        'source': 'source.ipynb',
                        'recipe': {}
                    }
                }
            },
            'input_file': 'trigger_file_name',
            'output': {},
            'variables': {}
        }

        # Test pattern_six is valid but has a no output warning. This should
        # have no descendants or ancestors.
        pattern_six = Pattern(pattern_six_dict)
        valid, msg = pattern_six.integrity_check()
        self.assertTrue(valid)
        self.assertEqual(msg, NO_OUTPUT_SET_WARNING)

        patterns = {
            pattern_one.name: pattern_one,
            pattern_two.name: pattern_two,
            pattern_three.name: pattern_three,
            pattern_four.name: pattern_four,
            pattern_five.name: pattern_five,
            pattern_six.name: pattern_six
        }

        # Test that all patterns stored correctly.
        valid, msg = check_patterns_dict(patterns)
        self.assertTrue(valid)

        # Test that valid workflow is valid.
        valid, workflow = build_workflow_object(patterns)
        self.assertTrue(valid)

        # Test that returned workflow object is valid
        self.assertIsInstance(workflow, dict)
        self.assertEqual(len(workflow), len(patterns))
        for node_key, node in workflow.items():
            self.assertIsInstance(node, dict)
            self.assertIn('ancestors', node)
            self.assertIn('descendants', node)
            self.assertIn('workflow inputs', node)
            self.assertIn('workflow outputs', node)

        # Test that first pattern node has been correctly setup.
        self.assertEqual(workflow['first_pattern']['ancestors'], {})
        self.assertIn(
            'second_pattern', workflow['first_pattern']['descendants']
        )
        self.assertIn(
            'third_pattern', workflow['first_pattern']['descendants']
        )
        self.assertEqual(len(workflow['first_pattern']['descendants']), 2)

        # Test that second pattern node has been correctly setup.
        self.assertIn('first_pattern', workflow['second_pattern']['ancestors'])
        self.assertEqual(len(workflow['second_pattern']['ancestors']), 1)
        self.assertEqual(workflow['second_pattern']['descendants'], {})

        # Test that third pattern node has been correctly setup.
        self.assertIn('first_pattern', workflow['third_pattern']['ancestors'])
        self.assertIn('fifth_pattern', workflow['third_pattern']['ancestors'])
        self.assertEqual(len(workflow['third_pattern']['ancestors']), 2)
        self.assertIn(
            'fourth_pattern', workflow['third_pattern']['descendants']
        )
        self.assertEqual(len(workflow['third_pattern']['descendants']), 1)

        # Test that fourth pattern node has been correctly setup.
        self.assertIn('third_pattern', workflow['fourth_pattern']['ancestors'])
        self.assertEqual(len(workflow['fourth_pattern']['ancestors']), 1)
        self.assertIn(
            'fifth_pattern', workflow['fourth_pattern']['descendants']
        )
        self.assertEqual(len(workflow['fourth_pattern']['descendants']), 1)

        # Test that fifth pattern node has been correctly setup.
        self.assertIn('fourth_pattern', workflow['fifth_pattern']['ancestors'])
        self.assertEqual(len(workflow['fifth_pattern']['ancestors']), 1)
        self.assertIn(
            'third_pattern', workflow['fifth_pattern']['descendants']
        )
        self.assertEqual(len(workflow['fifth_pattern']['descendants']), 1)

        # Test that sixth pattern node has been correctly setup.
        self.assertEqual(workflow['sixth_pattern']['ancestors'], {})
        self.assertEqual(workflow['sixth_pattern']['descendants'], {})

    def testWorkflowWidgetCreation(self):
        workflow_widget = WorkflowWidget()

        # Test that default setup arguments are correct.
        self.assertEqual(workflow_widget.mode, MEOW_MODE)
        self.assertFalse(workflow_widget.auto_import)
        self.assertEqual(
            workflow_widget.workflow_title, DEFAULT_WORKFLOW_TITLE
        )
        self.assertEqual(
            workflow_widget.cwl_import_export_dir,
            DEFAULT_CWL_IMPORT_EXPORT_DIR
        )
        self.assertEqual(workflow_widget.meow[PATTERNS], {})
        self.assertEqual(workflow_widget.meow[RECIPES], {})
        self.assertEqual(workflow_widget.cwl[WORKFLOWS], {})
        self.assertEqual(workflow_widget.cwl[STEPS], {})
        self.assertEqual(workflow_widget.cwl[SETTINGS], {})
        self.assertIsNone(workflow_widget.vgrid)

        # Test that valid pattern is valid.
        pattern = Pattern(VALID_PATTERN_DICT)
        valid, msg = pattern.integrity_check()
        self.assertTrue(valid)
        self.assertEqual(msg, '')

        args = {
            'mode': 'CWL',
            'auto_import': True,
            'export_name': 'example_name',
            'cwl_dir': 'test_dir',
            PATTERNS: {
                pattern.name: pattern
            },
            RECIPES: {
                VALID_RECIPE_DICT[NAME]: VALID_RECIPE_DICT
            },
            WORKFLOWS: {
                VALID_WORKFLOW_DICT[NAME]: VALID_WORKFLOW_DICT
            },
            STEPS: {
                VALID_STEP_DICT[NAME]: VALID_STEP_DICT
            },
            SETTINGS: {
                VALID_SETTINGS_DICT[NAME]: VALID_SETTINGS_DICT
            },
            'vgrid': 'sample_vgrid'
        }

        workflow_widget = WorkflowWidget(**args)

        # Test that provided keyword arguments are implemented correctly.
        self.assertEqual(workflow_widget.mode, CWL_MODE)
        self.assertTrue(workflow_widget.auto_import)
        self.assertEqual(workflow_widget.workflow_title, 'example_name')
        self.assertEqual(workflow_widget.cwl_import_export_dir, 'test_dir')
        self.assertEqual(len(workflow_widget.meow[PATTERNS]), 1)
        self.assertIn(pattern.name, workflow_widget.meow[PATTERNS])
        self.assertEqual(len(workflow_widget.meow[RECIPES]), 1)
        self.assertIn(VALID_RECIPE_DICT[NAME], workflow_widget.meow[RECIPES])
        self.assertEqual(len(workflow_widget.cwl[WORKFLOWS]), 1)
        self.assertIn(VALID_WORKFLOW_DICT[NAME], workflow_widget.cwl[WORKFLOWS])
        self.assertEqual(len(workflow_widget.cwl[STEPS]), 1)
        self.assertIn(VALID_STEP_DICT[NAME], workflow_widget.cwl[STEPS])
        self.assertEqual(len(workflow_widget.cwl[SETTINGS]), 1)
        self.assertIn(VALID_SETTINGS_DICT[NAME], workflow_widget.cwl[SETTINGS])
        self.assertEqual(workflow_widget.vgrid, 'sample_vgrid')

        superfluous_args = {
            'extra': 0
        }
        # Test that unsupported keyword arguments are rejected.
        with self.assertRaises(ValueError):
            WorkflowWidget(**superfluous_args)

        # Test that invalid 'mode' is rejected.
        invalid_mode = {
            'mode': 'Unknown'
        }
        with self.assertRaises(AttributeError):
            WorkflowWidget(**invalid_mode)

        # Test that incorrect 'patterns' type is rejected.
        unformatted_pattern_args = {
            PATTERNS: 5
        }
        #
        with self.assertRaises(TypeError):
            WorkflowWidget(**unformatted_pattern_args)

        # Test that incorrect 'recipes' type is rejected.
        unformatted_recipe_args = {
            RECIPES: 5
        }
        #
        with self.assertRaises(TypeError):
            WorkflowWidget(**unformatted_recipe_args)

        # Test that incorrect 'workflows' type is rejected.
        unformatted_workflows_args = {
            WORKFLOWS: 5
        }
        #
        with self.assertRaises(TypeError):
            WorkflowWidget(**unformatted_workflows_args)

        # Test that incorrect 'steps' type is rejected.
        unformatted_step_args = {
            STEPS: 5
        }
        #
        with self.assertRaises(TypeError):
            WorkflowWidget(**unformatted_step_args)

        # Test that incorrect 'settings' type is rejected.
        unformatted_settings_args = {
            SETTINGS: 5
        }
        #
        with self.assertRaises(TypeError):
            WorkflowWidget(**unformatted_settings_args)

        # Test that incorrect 'vgrid' type is rejected.
        unformatted_vgrid_args = {
            'vgrid': 5
        }
        #
        with self.assertRaises(TypeError):
            WorkflowWidget(**unformatted_vgrid_args)

        # Test that incorrect 'auto_import' type is rejected.
        unformatted_auto_import_args = {
            'auto_import': 5
        }
        #
        with self.assertRaises(TypeError):
            WorkflowWidget(**unformatted_auto_import_args)

        # Test that incorrect 'cwl_dir' type is rejected.
        unformatted_cwl_dir_args = {
            'cwl_dir': 5
        }
        #
        with self.assertRaises(TypeError):
            WorkflowWidget(**unformatted_cwl_dir_args)

        # Test that incorrect 'export_name' type is rejected.
        unformatted_export_name_args = {
            'export_name': 5
        }
        #
        with self.assertRaises(TypeError):
            WorkflowWidget(**unformatted_export_name_args)

    def testWorkflowWidgetPatternInteractions(self):
        workflow_widget = WorkflowWidget()

        workflow_widget.construct_widget()

        # Test that no patterns or recipes at setup.
        self.assertEqual(workflow_widget.meow[PATTERNS], {})
        self.assertEqual(workflow_widget.meow[RECIPES], {})

        # Test that valid pattern dict is accepted.
        completed = \
            workflow_widget.process_new_pattern(VALID_PATTERN_FORM_VALUES)
        self.assertTrue(completed)

        # Test that two patterns cannot be added with same name
        same_name_values = copy.deepcopy(VALID_PATTERN_FORM_VALUES)
        completed = workflow_widget.process_new_pattern(same_name_values)
        self.assertFalse(completed)

        # Test that pattern with incomplete values is rejected.
        incomplete_values = copy.deepcopy(VALID_PATTERN_FORM_VALUES)
        incomplete_values.pop(TRIGGER_PATHS)
        completed = workflow_widget.process_new_pattern(incomplete_values)
        self.assertFalse(completed)

        # Test that pattern has been recorded in widget database.
        self.assertEqual(len(workflow_widget.meow[PATTERNS]), 1)
        self.assertIn(
            VALID_PATTERN_FORM_VALUES[NAME],
            workflow_widget.meow[PATTERNS]
        )

        # Test that stored pattern is valid.
        extracted_pattern = \
            workflow_widget.meow[PATTERNS][VALID_PATTERN_FORM_VALUES[NAME]]
        valid, msg = extracted_pattern.integrity_check()
        self.assertTrue(valid)
        self.assertEqual(msg, '')

        # Test that baseline tester pattern is valid.
        tester_pattern = Pattern(VALID_PATTERN_DICT)
        valid, msg = tester_pattern.integrity_check()
        self.assertTrue(valid)
        self.assertEqual(msg, '')

        # Test that the stored pattern has the expected values.
        self.assertTrue(tester_pattern == extracted_pattern)

        updated_pattern_values = copy.deepcopy(VALID_PATTERN_FORM_VALUES)
        updated_pattern_values[VARIABLES] = [
            {
                'Name': 'int',
                'Value': 45
            },
            {
                'Name': 'string',
                'Value': "Word"
            }
        ]

        updated_pattern_dict = copy.deepcopy(VALID_PATTERN_DICT)
        updated_pattern_dict[VARIABLES] = {
            'int': 45,
            'string': "Word"
        }

        workflow_widget.process_editing_pattern(updated_pattern_values)

        # Test that pattern is still present after update, and that it is the
        # only pattern.
        self.assertEqual(len(workflow_widget.meow[PATTERNS]), 1)
        self.assertIn(
            VALID_PATTERN_FORM_VALUES[NAME],
            workflow_widget.meow[PATTERNS]
        )

        # Test that updated pattern is still valid.
        updated_pattern = \
            workflow_widget.meow[PATTERNS][VALID_PATTERN_FORM_VALUES[NAME]]
        valid, msg = updated_pattern.integrity_check()
        self.assertTrue(valid)
        self.assertEqual(msg, '')

        # Test that baseline tester pattern is valid
        updated_tester_pattern = Pattern(updated_pattern_dict)
        valid, msg = updated_tester_pattern.integrity_check()
        self.assertTrue(valid)
        self.assertEqual(msg, '')

        # Test that updated pattern has expected values.
        self.assertTrue(updated_pattern == updated_tester_pattern)

        # Test that updated pattern differs from its previous version.
        self.assertFalse(extracted_pattern == updated_pattern)

        # Test that updated base tester pattern differs from its previous
        # version.
        self.assertFalse(tester_pattern == updated_tester_pattern)

        # Test that pattern is still only pattern in widget database.
        self.assertEqual(len(workflow_widget.meow[PATTERNS]), 1)
        self.assertIn(
            VALID_PATTERN_FORM_VALUES[NAME],
            workflow_widget.meow[PATTERNS]
        )

        # Test that editing pattern with incomplete values fails.
        complete = workflow_widget.process_editing_pattern(incomplete_values)
        self.assertFalse(complete)

        # Test pattern is still valid and has not been updated by previous
        # failed update.
        self.assertEqual(len(workflow_widget.meow[PATTERNS]), 1)
        self.assertIn(
            VALID_PATTERN_FORM_VALUES[NAME],
            workflow_widget.meow[PATTERNS]
        )
        updated_pattern = \
            workflow_widget.meow[PATTERNS][VALID_PATTERN_FORM_VALUES[NAME]]
        valid, msg = updated_pattern.integrity_check()
        self.assertTrue(valid)
        self.assertEqual(msg, '')
        self.assertTrue(updated_pattern == updated_tester_pattern)
        self.assertFalse(extracted_pattern == updated_pattern)
        self.assertFalse(tester_pattern == updated_tester_pattern)

        # Test that pattern that has not been registered cannot be deleted,
        # and that patterns that are registered are not deleted instead.
        completed = workflow_widget.process_delete_pattern('unregistered_name')
        self.assertFalse(completed)
        self.assertEqual(len(workflow_widget.meow[PATTERNS]), 1)
        self.assertIn(
            VALID_PATTERN_FORM_VALUES[NAME],
            workflow_widget.meow[PATTERNS]
        )

        # Test that registered pattern can be deleted.
        completed = workflow_widget.process_delete_pattern(
            VALID_PATTERN_FORM_VALUES[NAME]
        )
        self.assertTrue(completed)
        self.assertEqual(workflow_widget.meow[PATTERNS], {})

    def testWorkflowWidgetRecipeInteractions(self):
        pass

    # TODO come back to this once we've test creation and deleting.
    def testWorkflowWidgetButtonEnabling(self):
        # Test that valid pattern is valid.
        pattern = Pattern(VALID_PATTERN_DICT)
        valid, msg = pattern.integrity_check()
        self.assertTrue(valid)
        self.assertEqual(msg, '')

        args = {
            PATTERNS: {
                pattern.name: pattern
            },
            RECIPES: {
                VALID_RECIPE_DICT[NAME]: VALID_RECIPE_DICT
            }
        }

        workflow_widget = WorkflowWidget(**args)

        # Test that keyword arguments passes successfully
        self.assertEqual(len(workflow_widget.meow[PATTERNS]), 1)
        self.assertIn(pattern.name, workflow_widget.meow[PATTERNS])
        self.assertEqual(len(workflow_widget.meow[RECIPES]), 1)
        self.assertIn(VALID_RECIPE_DICT[NAME], workflow_widget.meow[RECIPES])

        workflow_widget.construct_widget()

        for key, button in workflow_widget.button_elements.items():
            if key == MEOW_NEW_PATTERN_BUTTON:
                # Test that new pattern button is not disabled.
                self.assertFalse(button.disabled)
            if key == MEOW_EDIT_PATTERN_BUTTON:
                # Test that edit pattern button is not disabled.
                self.assertFalse(button.disabled)
            if key == MEOW_NEW_RECIPE_BUTTON:
                # Test that new recipe button is not disabled.
                self.assertFalse(button.disabled)
            if key == MEOW_EDIT_RECIPE_BUTTON:
                # Test that edit recipe button is not disabled.
                self.assertFalse(button.disabled)
            if key == MEOW_IMPORT_CWL_BUTTON:
                # Test that cwl import button is disabled.
                self.assertTrue(button.disabled)
            if key == MEOW_IMPORT_VGRID_BUTTON:
                # Test that vgrid import button is disabled.
                self.assertTrue(button.disabled)
            if key == MEOW_EXPORT_VGRID_BUTTON:
                # Test that vgrid export button is disabled.
                self.assertTrue(button.disabled)
