import unittest
import copy
import nbformat
import os

from mig_meow.meow import Pattern, check_patterns_dict, build_workflow_object
from mig_meow.constants import NO_OUTPUT_SET_WARNING, MEOW_MODE, CWL_MODE, \
    DEFAULT_WORKFLOW_TITLE, DEFAULT_CWL_IMPORT_EXPORT_DIR, PATTERNS, RECIPES, \
    WORKFLOWS, STEPS, SETTINGS, MEOW_NEW_RECIPE_BUTTON, \
    MEOW_EDIT_RECIPE_BUTTON, MEOW_EDIT_PATTERN_BUTTON, \
    MEOW_IMPORT_VGRID_BUTTON, MEOW_EXPORT_VGRID_BUTTON, \
    MEOW_NEW_PATTERN_BUTTON, MEOW_IMPORT_CWL_BUTTON, DEFAULT_JOB_NAME, \
    NO_NAME_SET_ERROR, NO_RECIPES_SET_ERROR, NO_INPUT_PATH_SET_ERROR, \
    NO_INPUT_FILE_SET_ERROR, PLACEHOLDER_ERROR, \
    OUTPUT_NOT_VARIABLE_ERROR, TRIGGER_NOT_VARIABLE_ERROR, \
    INVALID_INPUT_PATH_ERROR, PLACEHOLDER
from mig_meow.workflow_widget import WorkflowWidget

EMPTY_NOTEBOOK = 'test_notebook.ipynb'


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

    def testNewPatternCreation(self):
        test_pattern = Pattern('standard_pattern')

        valid, _ = test_pattern.integrity_check()
        self.assertFalse(valid)

        test_pattern.add_single_input('input_file', 'dir/regex.path')
        with self.assertRaises(Exception):
            test_pattern.add_single_input('another_input', 'dir/regex.path')

        valid, msg = test_pattern.integrity_check()
        self.assertFalse(valid)

        test_pattern.add_recipe('recipe')
        test_pattern.add_recipe('recipe')

        valid, msg = test_pattern.integrity_check()
        self.assertTrue(valid)
        self.assertEqual(msg, NO_OUTPUT_SET_WARNING)

        test_pattern.add_output('output_file', 'dir/regex.path')
        test_pattern.add_output('another_output', 'dir/regex.path')
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

        with self.assertRaises(Exception):
            test_pattern.add_variable('int', 1)
        with self.assertRaises(Exception):
            test_pattern.add_variable('input_file', 1)
        with self.assertRaises(Exception):
            test_pattern.add_variable('output_file', 1)

        valid, msg = test_pattern.integrity_check()
        self.assertTrue(valid)
        self.assertEqual(msg, '')

    def testDictPatternCreation(self):
        pattern_dict = {
            'name': 'dict_pattern',
            'input_paths': ['dir/literal.path'],
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
                'outfile_1': 'dir_1/outpath.txt',
                'outfile_2': 'dir_2/outpath.txt',
            },
            'variables': {
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

        test_pattern = Pattern(pattern_dict)

        valid, msg = test_pattern.integrity_check()
        self.assertTrue(valid)
        self.assertEqual(msg, '')

        alt_pattern_dict = {
            'name': 'alt_dict_pattern',
            'input_paths': ['dir/literal.path'],
            'trigger_recipes': {
                'trigger_id': {
                    'recipe_name': {}
                }
            },
            'input_file': 'trigger_file_name',
            'output': {
                'outfile_1': 'dir_1/outpath.txt',
                'outfile_2': 'dir_2/outpath.txt',
            },
            'variables': {
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

        test_alt_pattern = Pattern(alt_pattern_dict)

        valid, msg = test_alt_pattern.integrity_check()
        self.assertTrue(valid)
        self.assertEqual(msg, '')

        test_alt_pattern.name = None
        valid, msg = test_alt_pattern.integrity_check()
        self.assertFalse(valid)
        self.assertEqual(msg, NO_NAME_SET_ERROR)

        test_alt_pattern.name = ''
        valid, msg = test_alt_pattern.integrity_check()
        self.assertFalse(valid)
        self.assertEqual(msg, NO_NAME_SET_ERROR)

        invalid_recipes = {
            'name': 'invalid_recipes',
            'input_paths': ['dir/literal.path'],
            'trigger_recipes': {
                'recipe_name': {}
            },
            'input_file': 'trigger_file_name',
            'output': {
                'outfile_1': 'dir_1/outpath.txt',
                'outfile_2': 'dir_2/outpath.txt',
            },
            'variables': {
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

        invalid_recipes_pattern = Pattern(invalid_recipes)
        valid, msg = invalid_recipes_pattern.integrity_check()
        self.assertFalse(valid)
        self.assertEqual(msg, NO_RECIPES_SET_ERROR)

        no_paths = {
            'name': 'dict_pattern',
            'input_paths': [],
            'trigger_recipes': {
                'recipe_id': {
                    'name': 'recipe',
                    'source': 'source.ipynb',
                    'recipe': {}
                }
            },
            'input_file': 'trigger_file_name',
            'output': {
                'outfile_1': 'dir_1/outpath.txt',
                'outfile_2': 'dir_2/outpath.txt',
            },
            'variables': {
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

        no_paths_pattern = Pattern(no_paths)
        valid, msg = no_paths_pattern.integrity_check()
        self.assertFalse(valid)
        self.assertEqual(msg, NO_INPUT_PATH_SET_ERROR)

        invalid_paths = {
            'name': 'dict_pattern',
            'input_paths': [''],
            'trigger_recipes': {
                'recipe_id': {
                    'name': 'recipe',
                    'source': 'source.ipynb',
                    'recipe': {}
                }
            },
            'input_file': 'trigger_file_name',
            'output': {
                'outfile_1': 'dir_1/outpath.txt',
                'outfile_2': 'dir_2/outpath.txt',
            },
            'variables': {
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

        invalid_paths_pattern = Pattern(invalid_paths)
        valid, msg = invalid_paths_pattern.integrity_check()
        self.assertFalse(valid)
        self.assertIn(INVALID_INPUT_PATH_ERROR, msg)

        invalid_in_file = {
            'name': 'dict_pattern',
            'input_paths': ['path'],
            'trigger_recipes': {
                'recipe_id': {
                    'name': 'recipe',
                    'source': 'source.ipynb',
                    'recipe': {}
                }
            },
            'input_file': '',
            'output': {
                'outfile_1': 'dir_1/outpath.txt',
                'outfile_2': 'dir_2/outpath.txt',
            },
            'variables': {
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

        with self.assertRaises(Exception):
            Pattern(invalid_in_file)

        no_infile_pattern = Pattern(pattern_dict)
        valid, msg = no_infile_pattern.integrity_check()
        self.assertTrue(valid)
        self.assertEqual(msg, '')
        no_infile_pattern.trigger_file = None
        valid, msg = no_infile_pattern.integrity_check()
        self.assertFalse(valid)
        self.assertEqual(msg, NO_INPUT_FILE_SET_ERROR)
        no_infile_pattern.trigger_file = ''
        valid, msg = no_infile_pattern.integrity_check()
        self.assertFalse(valid)
        self.assertEqual(msg, NO_INPUT_FILE_SET_ERROR)

        output_not_variable_pattern = Pattern(pattern_dict)
        valid, msg = output_not_variable_pattern.integrity_check()
        self.assertTrue(valid)
        self.assertEqual(msg, '')
        output_not_variable_pattern.variables.pop('outfile_1')
        valid, msg = output_not_variable_pattern.integrity_check()
        self.assertFalse(valid)
        self.assertIn(OUTPUT_NOT_VARIABLE_ERROR, msg)

        trigger_not_variable_pattern = Pattern(pattern_dict)
        valid, msg = trigger_not_variable_pattern.integrity_check()
        self.assertTrue(valid)
        self.assertEqual(msg, '')
        trigger_not_variable_pattern.variables.pop('trigger_file_name')
        valid, msg = trigger_not_variable_pattern.integrity_check()
        self.assertFalse(valid)
        self.assertEqual(msg, TRIGGER_NOT_VARIABLE_ERROR)

    def testPatternPlaceholderCheck(self):
        pattern_dict = {
            'name': 'dict_pattern',
            'input_paths': ['dir/literal.path'],
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
                'outfile_1': 'dir_1/outpath.txt',
                'outfile_2': 'dir_2/outpath.txt',
            },
            'variables': {
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

        test_pattern = Pattern(pattern_dict)
        valid, msg = test_pattern.integrity_check()
        self.assertTrue(valid)
        self.assertEqual(msg, '')

        placeholder_name_pattern = Pattern(pattern_dict)
        placeholder_name_pattern.name = PLACEHOLDER
        valid, msg = placeholder_name_pattern.integrity_check()
        self.assertFalse(valid)
        self.assertEqual(msg, PLACEHOLDER_ERROR)

        placeholder_trigger_file_pattern = Pattern(pattern_dict)
        placeholder_trigger_file_pattern.trigger_file = PLACEHOLDER
        placeholder_trigger_file_pattern.variables[PLACEHOLDER] = PLACEHOLDER
        valid, msg = placeholder_trigger_file_pattern.integrity_check()
        self.assertFalse(valid)
        self.assertEqual(msg, PLACEHOLDER_ERROR)

        placeholder_trigger_paths_pattern = Pattern(pattern_dict)
        placeholder_trigger_paths_pattern.trigger_paths = PLACEHOLDER
        valid, msg = placeholder_trigger_paths_pattern.integrity_check()
        self.assertFalse(valid)
        self.assertEqual(msg, PLACEHOLDER_ERROR)

        placeholder_recipes_pattern = Pattern(pattern_dict)
        placeholder_recipes_pattern.recipes = PLACEHOLDER
        valid, msg = placeholder_recipes_pattern.integrity_check()
        self.assertFalse(valid)
        self.assertEqual(msg, PLACEHOLDER_ERROR)

        placeholder_in_paths_pattern = Pattern(pattern_dict)
        placeholder_in_paths_pattern.trigger_paths[0] = PLACEHOLDER
        valid, msg = placeholder_in_paths_pattern.integrity_check()
        self.assertFalse(valid)
        self.assertEqual(msg, PLACEHOLDER_ERROR)

        placeholder_recipes_pattern = Pattern(pattern_dict)
        placeholder_recipes_pattern.recipes[0] = PLACEHOLDER
        valid, msg = placeholder_recipes_pattern.integrity_check()
        self.assertFalse(valid)
        self.assertEqual(msg, PLACEHOLDER_ERROR)

        placeholder_variable_key_pattern = Pattern(pattern_dict)
        placeholder_variable_key_pattern.variables[PLACEHOLDER] = 'value'
        valid, msg = placeholder_variable_key_pattern.integrity_check()
        self.assertFalse(valid)
        self.assertEqual(msg, PLACEHOLDER_ERROR)

        placeholder_variable_value_pattern = Pattern(pattern_dict)
        placeholder_variable_value_pattern.variables['extra'] = PLACEHOLDER
        valid, msg = placeholder_variable_value_pattern.integrity_check()
        self.assertFalse(valid)
        self.assertEqual(msg, PLACEHOLDER_ERROR)

        placeholder_output_key_pattern = Pattern(pattern_dict)
        placeholder_output_key_pattern.outputs[PLACEHOLDER] = 'path'
        placeholder_output_key_pattern.variables[PLACEHOLDER] = PLACEHOLDER
        valid, msg = placeholder_output_key_pattern.integrity_check()
        self.assertFalse(valid)
        self.assertEqual(msg, PLACEHOLDER_ERROR)

        placeholder_output_value_pattern = Pattern(pattern_dict)
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

        valid, msg = test_pattern_1.integrity_check()
        self.assertTrue(valid)

        pattern_dict = {
            'name': 'identical_pattern',
            'input_paths': ['dir/regex.path'],
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
                'outfile_1': 'dir_1/outpath.txt',
                'outfile_2': 'dir_2/outpath.txt',
            },
            'variables': {
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

        test_pattern_2 = Pattern(pattern_dict)
        valid, msg = test_pattern_2.integrity_check()
        self.assertTrue(valid)

        pattern_dict['persistence_id'] = '12345678910'

        test_pattern_3 = Pattern(pattern_dict)
        valid, msg = test_pattern_3.integrity_check()
        self.assertTrue(valid)

        self.assertTrue(test_pattern_1 == test_pattern_2)
        self.assertFalse(test_pattern_1 == test_pattern_3)
        self.assertFalse(test_pattern_2 == test_pattern_3)

    def testMeowWorkflow(self):
        pattern_one_dict = {
            'name': 'first_pattern',
            'input_paths': ['start'],
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
                'outfile_1': 'first/one',
                'outfile_2': 'first/two',
            },
            'variables': {}
        }

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

        valid, msg = check_patterns_dict(patterns)
        self.assertTrue(valid)

        valid, workflow = build_workflow_object(patterns)
        self.assertTrue(valid)

        self.assertIsInstance(workflow, dict)
        self.assertEqual(len(workflow), len(patterns))

        for node_key, node in workflow.items():
            self.assertIsInstance(node, dict)
            self.assertIn('ancestors', node)
            self.assertIn('descendants', node)
            self.assertIn('workflow inputs', node)
            self.assertIn('workflow outputs', node)

        self.assertEqual(workflow['first_pattern']['ancestors'], {})
        self.assertIn(
            'second_pattern', workflow['first_pattern']['descendants']
        )
        self.assertIn(
            'third_pattern', workflow['first_pattern']['descendants']
        )
        self.assertEqual(len(workflow['first_pattern']['descendants']), 2)

        self.assertIn('first_pattern', workflow['second_pattern']['ancestors'])
        self.assertEqual(len(workflow['second_pattern']['ancestors']), 1)
        self.assertEqual(workflow['second_pattern']['descendants'], {})

        self.assertIn('first_pattern', workflow['third_pattern']['ancestors'])
        self.assertIn('fifth_pattern', workflow['third_pattern']['ancestors'])
        self.assertEqual(len(workflow['third_pattern']['ancestors']), 2)
        self.assertIn(
            'fourth_pattern', workflow['third_pattern']['descendants']
        )
        self.assertEqual(len(workflow['third_pattern']['descendants']), 1)

        self.assertIn('third_pattern', workflow['fourth_pattern']['ancestors'])
        self.assertEqual(len(workflow['fourth_pattern']['ancestors']), 1)
        self.assertIn(
            'fifth_pattern', workflow['fourth_pattern']['descendants']
        )
        self.assertEqual(len(workflow['fourth_pattern']['descendants']), 1)

        self.assertIn('fourth_pattern', workflow['fifth_pattern']['ancestors'])
        self.assertEqual(len(workflow['fifth_pattern']['ancestors']), 1)
        self.assertIn(
            'third_pattern', workflow['fifth_pattern']['descendants']
        )
        self.assertEqual(len(workflow['fifth_pattern']['descendants']), 1)

        self.assertEqual(workflow['sixth_pattern']['ancestors'], {})
        self.assertEqual(workflow['sixth_pattern']['descendants'], {})

    def testWorkflowWidgetCreation(self):
        workflow_widget = WorkflowWidget()

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

        pattern_dict = {
            'name': 'dict_pattern',
            'input_paths': ['dir/literal.path'],
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
                'outfile_1': 'dir_1/outpath.txt',
                'outfile_2': 'dir_2/outpath.txt',
            },
            'variables': {
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
        pattern = Pattern(pattern_dict)
        valid, msg = pattern.integrity_check()
        self.assertTrue(valid)
        self.assertEqual(msg, '')

        recipe_dict = {
            'name': 'recipe_name',
            'source': 'recipe_source',
            'recipe': {}
        }

        workflow_dict = {
            'name': 'workflow_name',
            'cwlVersion': 'v1.0',
            'class': 'workflow',
            'inputs': {},
            'outputs': {},
            'steps': {},
            'requirements': {}
        }

        step_dict = {
            'name': 'step_name',
            'cwlVersion': 'v1.0',
            'class': 'commandLineTool',
            'baseCommand': '',
            'stdout': '',
            'inputs': {},
            'outputs': {},
            'arguments': [],
            'requirements': {},
            'hints': {}
        }

        variable_dict = {
            'name': 'variables_name',
            'arguments': {}
        }

        args = {
            'mode': 'CWL',
            'auto_import': True,
            'export_name': 'example_name',
            'cwl_dir': 'test_dir',
            PATTERNS: {
                pattern.name: pattern
            },
            RECIPES: {
                'recipe_name': recipe_dict
            },
            WORKFLOWS: {
                'workflow_name': workflow_dict
            },
            STEPS: {
                'step_name': step_dict
            },
            SETTINGS: {
                'variables_name': variable_dict
            },
            'vgrid': 'sample_vgrid'
        }

        workflow_widget = WorkflowWidget(**args)

        self.assertEqual(workflow_widget.mode, CWL_MODE)
        self.assertTrue(workflow_widget.auto_import)
        self.assertEqual(workflow_widget.workflow_title, 'example_name')
        self.assertEqual(workflow_widget.cwl_import_export_dir, 'test_dir')
        self.assertEqual(len(workflow_widget.meow[PATTERNS]), 1)
        self.assertIn(pattern.name, workflow_widget.meow[PATTERNS])
        self.assertEqual(len(workflow_widget.meow[RECIPES]), 1)
        self.assertIn('recipe_name', workflow_widget.meow[RECIPES])
        self.assertEqual(len(workflow_widget.cwl[WORKFLOWS]), 1)
        self.assertIn('workflow_name', workflow_widget.cwl[WORKFLOWS])
        self.assertEqual(len(workflow_widget.cwl[STEPS]), 1)
        self.assertIn('step_name', workflow_widget.cwl[STEPS])
        self.assertEqual(len(workflow_widget.cwl[SETTINGS]), 1)
        self.assertIn('variables_name', workflow_widget.cwl[SETTINGS])
        self.assertEqual(workflow_widget.vgrid, 'sample_vgrid')

        superfluous_args = {
            'extra': 0
        }
        with self.assertRaises(ValueError):
            WorkflowWidget(**superfluous_args)

        unformated_args = {
            'export_name': 5
        }
        with self.assertRaises(TypeError):
            WorkflowWidget(**unformated_args)

        invalid_mode = {
            'mode': 'Unknown'
        }
        with self.assertRaises(AttributeError):
            WorkflowWidget(**invalid_mode)

    def testWorkflowWidgetPatternInteractions(self):
        workflow_widget = WorkflowWidget()

        workflow_widget.construct_widget()

        self.assertEqual(workflow_widget.meow[PATTERNS], {})
        self.assertEqual(workflow_widget.meow[RECIPES], {})

        pattern_values = {
            'name': 'value_pattern',
            'input_paths': ['dir/literal.path'],
            'recipes': {
                'recipe_name': {
                    'name': 'recipe_name',
                    'source': 'source.ipynb',
                    'recipe': {}
                }
            },
            'input_file': 'trigger_file_name',
            'trigger_output': 'in_file_output',
            'notebook_output': 'notebook_output',
            'output': [
                {
                    'Name': 'outfile_1',
                    'Value': 'out_1.path'
                },
                {
                    'Name': 'outfile_2',
                    'Value': 'out_2.path'
                }
            ],
            'variables': [
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

        completed = workflow_widget.process_new_pattern(pattern_values)
        self.assertTrue(completed)

        same_name_values = copy.deepcopy(pattern_values)
        completed = workflow_widget.process_new_pattern(same_name_values)
        self.assertFalse(completed)

        incomplete_values = copy.deepcopy(pattern_values)
        incomplete_values.pop('variables')
        completed = workflow_widget.process_new_pattern(incomplete_values)
        self.assertFalse(completed)

        self.assertEqual(len(workflow_widget.meow[PATTERNS]), 1)
        self.assertIn('value_pattern', workflow_widget.meow[PATTERNS])

        extracted_pattern = workflow_widget.meow[PATTERNS]['value_pattern']
        valid, msg = extracted_pattern.integrity_check()
        self.assertTrue(valid)
        self.assertEqual(msg, '')

        pattern_dict = {
            'name': 'value_pattern',
            'input_paths': ['dir/literal.path'],
            'trigger_recipes': {
                'trigger_id': {
                    'recipe_id': {
                        'name': 'recipe_name',
                        'source': 'source.ipynb',
                        'recipe': {}
                    }
                }
            },
            'input_file': 'trigger_file_name',
            'output': {
                'outfile_1': 'out_1.path',
                'outfile_2': 'out_2.path',
                'trigger_file_name': 'in_file_output',
                DEFAULT_JOB_NAME: 'notebook_output'
            },
            'variables': {
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
        tester_pattern = Pattern(pattern_dict)
        valid, msg = tester_pattern.integrity_check()
        self.assertTrue(valid)
        self.assertEqual(msg, '')

        self.assertTrue(tester_pattern == extracted_pattern)

        updated_pattern_values = copy.deepcopy(pattern_values)
        updated_pattern_values['variables'] = [
            {
                'Name': 'int',
                'Value': 45
            },
            {
                'Name': 'string',
                'Value': "Word"
            }
        ]

        updated_pattern_dict = copy.deepcopy(pattern_dict)
        updated_pattern_dict['variables'] = {
            'int': 45,
            'string': "Word"
        }

        workflow_widget.process_editing_pattern(updated_pattern_values)

        self.assertEqual(len(workflow_widget.meow[PATTERNS]), 1)
        self.assertIn('value_pattern', workflow_widget.meow[PATTERNS])

        updated_pattern = workflow_widget.meow[PATTERNS]['value_pattern']
        valid, msg = updated_pattern.integrity_check()
        self.assertTrue(valid)
        self.assertEqual(msg, '')

        updated_tester_pattern = Pattern(updated_pattern_dict)
        valid, msg = updated_tester_pattern.integrity_check()
        self.assertTrue(valid)
        self.assertEqual(msg, '')

        self.assertTrue(updated_pattern == updated_tester_pattern)
        self.assertFalse(extracted_pattern == updated_pattern)
        self.assertFalse(tester_pattern == updated_tester_pattern)

        self.assertEqual(len(workflow_widget.meow[PATTERNS]), 1)
        self.assertIn('value_pattern', workflow_widget.meow[PATTERNS])

        completed = workflow_widget.process_editing_pattern(incomplete_values)
        self.assertFalse(completed)
        self.assertEqual(len(workflow_widget.meow[PATTERNS]), 1)
        self.assertIn('value_pattern', workflow_widget.meow[PATTERNS])

        updated_pattern = workflow_widget.meow[PATTERNS]['value_pattern']
        valid, msg = updated_pattern.integrity_check()
        self.assertTrue(valid)
        self.assertEqual(msg, '')

        self.assertTrue(updated_pattern == updated_tester_pattern)
        self.assertFalse(extracted_pattern == updated_pattern)
        self.assertFalse(tester_pattern == updated_tester_pattern)

        completed = workflow_widget.process_delete_pattern('unregistered_name')
        self.assertFalse(completed)
        self.assertEqual(len(workflow_widget.meow[PATTERNS]), 1)
        self.assertIn('value_pattern', workflow_widget.meow[PATTERNS])

        completed = workflow_widget.process_delete_pattern('value_pattern')
        self.assertTrue(completed)
        self.assertEqual(workflow_widget.meow[PATTERNS], {})

    # TODO come back to this once we've test creation and deleting.
    def testWorkflowWidgetButtonEnabling(self):
        pattern_dict = {
            'name': 'dict_pattern',
            'input_paths': ['dir/literal.path'],
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
                'outfile_1': 'dir_1/outpath.txt',
                'outfile_2': 'dir_2/outpath.txt',
            },
            'variables': {
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
        pattern = Pattern(pattern_dict)
        valid, msg = pattern.integrity_check()
        self.assertTrue(valid)
        self.assertEqual(msg, '')

        recipe_dict = {
            'name': 'recipe_name',
            'source': 'recipe_source',
            'recipe': {}
        }

        args = {
            PATTERNS: {
                pattern.name: pattern
            },
            RECIPES: {
                'recipe_name': recipe_dict
            }
        }

        workflow_widget = WorkflowWidget(**args)

        self.assertEqual(len(workflow_widget.meow[PATTERNS]), 1)
        self.assertIn(pattern.name, workflow_widget.meow[PATTERNS])
        self.assertEqual(len(workflow_widget.meow[RECIPES]), 1)
        self.assertIn('recipe_name', workflow_widget.meow[RECIPES])

        workflow_widget.construct_widget()

        for key, button in workflow_widget.button_elements.items():
            if key == MEOW_NEW_PATTERN_BUTTON:
                self.assertFalse(button.disabled)
            if key == MEOW_EDIT_PATTERN_BUTTON:
                self.assertFalse(button.disabled)
            if key == MEOW_NEW_RECIPE_BUTTON:
                self.assertFalse(button.disabled)
            if key == MEOW_EDIT_RECIPE_BUTTON:
                self.assertFalse(button.disabled)
            if key == MEOW_IMPORT_CWL_BUTTON:
                self.assertTrue(button.disabled)
            if key == MEOW_IMPORT_VGRID_BUTTON:
                self.assertTrue(button.disabled)
            if key == MEOW_EXPORT_VGRID_BUTTON:
                self.assertTrue(button.disabled)
