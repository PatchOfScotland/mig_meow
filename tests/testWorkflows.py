import unittest

from mig_meow.meow import Pattern, check_patterns_dict, build_workflow_object
from mig_meow.constants import NO_OUTPUT_SET_WARNING, MEOW_MODE, CWL_MODE, \
    DEFAULT_WORKFLOW_TITLE, DEFAULT_CWL_IMPORT_EXPORT_DIR, PATTERNS, RECIPES, \
    WORKFLOWS, STEPS, SETTINGS
from mig_meow.workflow_widget import WorkflowWidget


class WorkflowTest(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

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

        invalid_recipes_dict = {
            'name': 'dict_pattern',
            'input_paths': ['dir/literal.path'],
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
                'boolean': True
            }
        }

        with self.assertRaises(Exception):
            Pattern(invalid_recipes_dict)

        invalid_variables = {
            'name': 'dict_pattern',
            'input_paths': ['dir/literal.path'],
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

        with self.assertRaises(Exception):
            Pattern(invalid_variables)

        invalid_paths = {
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

        with self.assertRaises(Exception):
            Pattern(invalid_paths)

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

