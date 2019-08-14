
import json
import ipywidgets as widgets
import os

from IPython.display import display

from .input import check_input, valid_path, valid_string
from .constants import INPUT_NAME, INPUT_OUTPUT, INPUT_RECIPES, \
    INPUT_TRIGGER_PATH, INPUT_VARIABLES, INPUT_TRIGGER_FILE, \
    INPUT_TRIGGER_OUTPUT, INPUT_NOTEBOOK_OUTPUT, ALL_PATTERN_INPUTS, \
    DEFAULT_WORKFLOW_FILENAME, WORKFLOW_IMAGE_EXTENSION, INPUT_SOURCE, \
    NOTEBOOK_EXTENSIONS, PATTERN, RECIPE, NAME
from .pattern import Pattern, is_valid_pattern_object
from .recipe import is_valid_recipe_dict, create_recipe_from_notebook
from .workflows import build_workflow_object, create_workflow_image
from .notebook import list_current_recipes


def create_widget(patterns=None, recipes=None, filename=None):
    # TODO update this
    """Displays a widget for workflow defitions. Can optionally take a
    predefined workflow as input"""

    widget = WorkflowWidget(patterns=patterns,
                            recipes=recipes,
                            filename=filename)
    return widget.display_widget()


class WorkflowWidget:
    def __init__(self, patterns={}, recipes={}, filename=None):

        if not isinstance(patterns, dict):
            raise Exception('The provided patterns were not in a dict')
        for pattern in patterns.values():
            valid, feedback = is_valid_pattern_object(pattern)
            if not valid:
                raise Exception('Pattern %s was not valid. %s'
                                % (pattern, feedback))
        self.patterns = patterns

        if not isinstance(recipes, dict):
            raise Exception('The provided recipes were not in a dict')
        for recipe in recipes.values():
            valid, feedback = is_valid_recipe_dict(recipe)
            if not valid:
                raise Exception('Recipe %s was not valid. %s'
                                % (recipe, feedback))
        self.recipes = recipes

        if filename:
            check_input(filename, str, 'filename')
            valid_string(filename, 'filename')
        else:
            filename = DEFAULT_WORKFLOW_FILENAME

        self.filename = filename
        extended_filename = filename + WORKFLOW_IMAGE_EXTENSION
        if patterns and recipes:
            self.workflow = build_workflow_object(patterns, recipes)
        else:
            self.workflow = {}

        create_workflow_image(self.workflow, self.patterns, self.recipes, filename=filename)

        if os.path.isfile(extended_filename):
            file = open(extended_filename, "rb")
            image = file.read()
            self.workflow_display = widgets.Image(
                value=image,
                format='png'
            )
            file.close()
        else:
            # TODO don't show anything here at all if no input defined?
            self.workflow_display = widgets.Image()

        self.display_area = widgets.Output()

        self.new_pattern_button = widgets.Button(
            value=False,
            description="New Pattern",
            disabled=False,
            button_style='',
            tooltip='Define a new pattern'
        )
        self.new_pattern_button.on_click(self.on_new_pattern_clicked)

        self.edit_pattern_button = widgets.Button(
            value=False,
            description="Edit Pattern",
            disabled=False,
            button_style='',
            tooltip='Edit an existing pattern'
        )
        self.edit_pattern_button.on_click(self.on_edit_pattern_clicked)

        self.new_recipe_button = widgets.Button(
            value=False,
            description="Add Recipe",
            disabled=False,
            button_style='',
            tooltip='Import a new recipe'
        )
        self.new_recipe_button.on_click(self.on_new_recipe_clicked)

        self.edit_recipe_button = widgets.Button(
            value=False,
            description="Edit Recipe",
            disabled=False,
            button_style='',
            tooltip='Edit an existing recipe'
        )
        self.edit_recipe_button.on_click(self.on_edit_recipe_clicked)

        self.import_from_vgrid_button = widgets.Button(
            value=False,
            description="Read VGrid",
            disabled=True,
            button_style='',
            tooltip='Here is a tooltip for this button'
        )
        self.import_from_vgrid_button.on_click(
            self.on_import_from_vgrid_clicked
        )

        self.export_to_vgrid_button = widgets.Button(
            value=False,
            description="Export Workflow",
            disabled=True,
            button_style='',
            tooltip='Here is a tooltip for this button'
        )
        self.export_to_vgrid_button.on_click(self.on_export_to_vgrid_clicked)

        self.feedback = widgets.HTML()

        self.display_area = widgets.Output()

        # TODO update so all forms use this?
        self.current_form = {}

        self.pattern_form = {}
        self.pattern_form_line_counts = {}
        self.pattern_form_rows = {}
        self.pattern_form_old_values = {}

        self.recipe_form = {}
        self.recipe_form_rows = {}
        self.recipe_form_old_values = {}

        self.displayed_form = None
        self.editting_area = None
        self.editting = None

    def disable_top_buttons(self):
        self.new_pattern_button.disabled = True
        self.edit_pattern_button.disabled = True
        self.new_recipe_button.disabled = True
        self.edit_recipe_button.disabled = True
        self.import_from_vgrid_button.disabled = True
        self.export_to_vgrid_button.disabled = True

    def enable_top_buttons(self):
        self.new_pattern_button.disabled = False
        if self.patterns:
            self.edit_pattern_button.disabled = False
        else:
            self.edit_pattern_button.disabled = True
        self.new_recipe_button.disabled = False
        if self.recipes:
            self.edit_recipe_button.disabled = False
        else:
            self.edit_recipe_button.disabled = True
        self.import_from_vgrid_button.disabled = False
        self.export_to_vgrid_button.disabled = False

    def populate_new_pattern_form(self, form, form_rows, form_old_values,
                                  form_line_counts, population_function,
                                  done_function):
        form[INPUT_NAME] = self._create_form_single_input(
            "Name",
            "Pattern Name. This is used to identify the pattern and so "
            "should be a unique string."
            "<br/>"
            "Example: <b>pattern_1</b>"
            "<br/>"
            "In this example this pattern is given the name 'pattern_1'.",
            INPUT_NAME,
            form_rows,
            form_old_values
        )
        form[INPUT_TRIGGER_PATH] = self._create_form_single_input(
            "Trigger path",
            "Triggering path for file events which are used to schedule "
            "jobs. This is expressed as a regular expression against which "
            "file events are matched. It can be as broad or specific as "
            "required. Any matches between file events and the path given "
            "will cause a scheduled job. File paths are taken relative to the "
            "vgrid home directory. "
            "<br/>"
            "Example: <b>dir/input_file_*\\.txt</b>"
            "<br/>"
            "In this example pattern jobs will trigger on an '.txt' files "
            "whose file name starts with 'input_file_' and is located in "
            "the 'dir' directory. The 'dir' directory in this case should be "
            "located in he vgrid home directory. So if you are operating in "
            "the 'test' vgrid, the structure should be 'test/dir'.",
            INPUT_TRIGGER_PATH,
            form_rows,
            form_old_values
        )
        form[INPUT_TRIGGER_FILE] = self._create_form_single_input(
            "Trigger file",
            "This is the variable name used to identify the triggering file "
            "within the job processing."
            "<br/>"
            "Example: <b>input_file</b>"
            "<br/>"
            "In this the triggering file will be copied into the job as "
            "'input_file'. This can then be opened or manipulated as "
            "necessary by the job processing.",
            INPUT_TRIGGER_FILE,
            form_rows,
            form_old_values
        )
        form[
            INPUT_TRIGGER_OUTPUT] = self._create_form_single_input(
            "Trigger output",
            "Trigger output is an optional parameter used to define if the "
            "triggering file is returned. This is defined by the path for the "
            "file to be copied to at job completion. If it is not provided "
            "then any changes made to it are lost, but other output may still "
            "be saved if defined in the output parameter."
            "<br/>"
            "Example: <b>dir/*_output.txt</b>"
            "<br/>"
            "In this example data file is saved within the 'dir' directory. "
            "If the job was triggered on 'test.txt' then the output file "
            "would be called 'test_output.txt",
            INPUT_TRIGGER_OUTPUT,
            form_rows,
            form_old_values,
            optional=True
        )
        form[
            INPUT_NOTEBOOK_OUTPUT] = self._create_form_single_input(
            "Notebook output",
            "Notebook output is an optional parameter used to define if the "
            "notebook used for job processing is returned. This is defined as "
            "a path for the notebook to be copied to at job completion. If it "
            "is not provided then the notebook is destroyed, but other output "
            "may still be saved if defined in the output parameter."
            "<br/>"
            "Example: <b>dir/*_output.ipynb</b>"
            "<br/>"
            "In this example the job notebook is saved within the 'dir' "
            "directory. If the job was triggered on 'test.txt' then the "
            "output notebook would be called 'test_output.ipynb",
            INPUT_NOTEBOOK_OUTPUT,
            form_rows,
            form_old_values,
            optional=True
        )
        form[INPUT_OUTPUT] = self._create_form_multi_input(
            "Output",
            "Output data to be saved after job completion. Anything not "
            "saved will be lost. Zero or more files can be copied and should "
            "be expressed in two parts as a variable declaration. The "
            "variable name is the name of the output file within the job, "
            "whilst the value is the file location to which it shall be "
            "copied. In the output string a '*' character can be used to "
            "dynamically create file names, with the * being replaced at "
            "runtime by the triggering files filename. Each output should be "
            "defined in its own text box, and the 'Add output file' button "
            "can be used to create additional text boxes as needed."
            "<br/>"
            "Example: <b>job_output = dir/some_output/*.ipynb</b>"
            "<br/>"
            "In this example, the file 'job_output' is created by the job and "
            "copied to the 'some_output' directory in 'dir'. If 'some_output' "
            "does not already exist it is created. The file will be named "
            "according to the triggering file, and given the '.ipynb' file "
            "extension. If the triggering file was 'sample.txt' then the "
            "output will be called 'sample.ipynb'.",
            INPUT_OUTPUT,
            form,
            form_rows,
            form_old_values,
            form_line_counts,
            population_function,
            done_function,
            optional=True
        )
        form[INPUT_RECIPES] = self._create_form_multi_input(
            "Recipe",
            "Recipe(s) to be used for job definition. These should be recipe "
            "names and may be recipes already defined in the system or "
            "additional ones yet to be added. Each recipe should be defined "
            "in its own text box, and the 'Add recipe' button can be used to "
            "create additional text boxes as needed."
            "<br/>"
            "Example: <b>recipe_1</b>"
            "<br/>"
            "In this example, the recipe 'recipe_1' is used as the definition "
            "of any job processing.",
            INPUT_RECIPES,
            form,
            form_rows,
            form_old_values,
            form_line_counts,
            population_function,
            done_function,
            extra_text="<br/>Current defined recipes are: ",
            extra_func=list_current_recipes()
        )
        form[INPUT_VARIABLES] = self._create_form_multi_input(
            "Variable",
            "Variable(s) accessible to the job at runtime. These are passed "
            "to the job using papermill to run a parameterised notebook. Zero "
            "or more variables can be defined and should be declared as "
            "variable definitions. The variable name will be used as the "
            "variable name within the job notebook, and the vraiable value "
            "will be its value. Any Python data structure can be defined as "
            "long as it can be declared in a single line."
            "<br/>"
            "Example: <b>list_a=[1,2,3]</b>"
            "<br/>"
            "In this example a list of numbers is created and named 'list_a'."
            ,
            INPUT_VARIABLES,
            form,
            form_rows,
            form_old_values,
            form_line_counts,
            population_function,
            done_function,
            optional=True
        )

    def populate_new_recipe_form(self, form, form_rows, form_old_values,
                                 form_line_counts, population_function,
                                  done_function):
        form[INPUT_SOURCE] = self._create_form_single_input(
            "Source",
            "The Jupyter Notebook to be used as a source for the recipe. This "
            "should be expressed as a path to the notebook. Note that if a "
            "name is not provided below then the notebook filename will be "
            "used as the recipe name"
            "<br/>"
            "Example: <b>dir/notebook_1.ipynb</b>"
            "<br/>"
            "In this example this notebook 'notebook_1' in the 'dir' ."
            "directory is imported as a recipe. ",
            INPUT_SOURCE,
            form_rows,
            form_old_values,
            extra_text="<br/>Current defined recipes are: ",
            extra_func=list_current_recipes()
        )
        form[INPUT_NAME] = self._create_form_single_input(
            "Name",
            "Optional recipe name. This is used to identify the recipe and so "
            "must be unique. If not provided then the notebook filename is "
            "taken as the name. "
            "<br/>"
            "Example: <b>recipe_1</b>"
            "<br/>"
            "In this example this recipe is given the name 'recipe_1', "
            "regardless of the name of the source notebook.",
            INPUT_NAME,
            form_rows,
            form_old_values,
            optional=True,
            extra_text="<br/>Current defined recipes are: ",
            extra_func=list_current_recipes()
        )

    def process_pattern_values(self, values):
        try:
            pattern = Pattern(values[INPUT_NAME])
            if values[INPUT_NAME] in self.patterns:
                msg = "Pattern name is not valid as another pattern is " \
                      "already registered with that name. "
                self.feedback.value = msg
                return
            file_name = values[INPUT_TRIGGER_FILE]
            trigger_path = values[INPUT_TRIGGER_PATH]
            trigger_output = values[INPUT_TRIGGER_OUTPUT]
            if trigger_output:
                pattern.add_single_input(file_name,
                                         trigger_path,
                                         output_path=trigger_output)
            else:
                pattern.add_single_input(file_name, trigger_path)
            notebook_return = values[INPUT_NOTEBOOK_OUTPUT]
            if notebook_return:
                pattern.return_notebook(notebook_return)
            for recipe in values[INPUT_RECIPES]:
                pattern.add_recipe(recipe)
            for variable in values[INPUT_VARIABLES]:
                if variable:
                    if '=' in variable:
                        name = variable[:variable.index('=')]
                        value = variable[variable.index('=') + 1:]
                        pattern.add_variable(name, value)
                    else:
                        raise Exception("Variable needs to be declared with a "
                                        "name and a value in the form "
                                        "'name=value', but no '=' is present "
                                        "in %s" % variable)
            for output in values[INPUT_OUTPUT]:
                if output:
                    if '=' in output:
                        name = output[:output.index('=')]
                        value = output[output.index('=') + 1:]
                        pattern.add_output(name, value)
                    else:
                        raise Exception("Output needs to be declared with a "
                                        "name and a value in the form "
                                        "'name=value', but no '=' is present "
                                        "in %s" % output)
            valid, warnings = pattern.integrity_check()
            if valid:
                if pattern.name in self.patterns:
                    word = 'updated'
                else:
                    word = 'created'
                self.patterns[pattern.name] = pattern
                msg = "pattern %s %s. " % (pattern.name, word)
                if warnings:
                    msg += "\n%s" % warnings
                self.feedback.value = msg
                self.update_workflow_image()
                self.close_form()
                return True
            else:
                msg = "pattern is not valid. "
                if warnings:
                    msg += "\n%s" % warnings
                self.feedback.value = msg
                return False
        except Exception as e:
            self.feedback.value = str(e)
            return False

    def process_recipe_values(self, values, ignore_conflicts=False):
        try:
            source = values[INPUT_SOURCE]
            name = values[INPUT_NAME]

            valid_path(source,
                       'Source',
                       extensions=NOTEBOOK_EXTENSIONS
                       )
            if os.path.sep in source:
                filename = \
                    source[source.index('/') + 1:source.index('.')]
            else:
                filename = source[:source.index('.')]
            if not name:
                name = filename
            if not os.path.isfile(source):
                self.feedback.value = "Source %s was not found. " % source
                return
            if name:
                valid_string(name, 'Name')
                if not ignore_conflicts:
                    if name in self.recipes:
                        msg = "recipe name is not valid as another recipe " \
                              "is already registered with that name. Please " \
                              "try again using a different name. "
                        self.feedback.value = msg
                        return
            self.feedback.value = "Everything seems in order. "

            with open(source, "r") as read_file:
                notebook = json.load(read_file)
                recipe = create_recipe_from_notebook(notebook, name)
                if name in self.recipes:
                    word = 'updated'
                else:
                    word = 'created'
                self.recipes[name] = recipe
                self.feedback.value = "Recipe %s %s. " % (name, word)
            self.update_workflow_image()
            self.close_form()
            return True
        except Exception as e:
            self.feedback.value = "Something went wrong with recipe " \
                                  "generation. %s " % str(e)
            return False

    def on_new_pattern_clicked(self, button):
        self.disable_top_buttons()
        self._refresh_new_form(self.pattern_form, self.pattern_form_old_values, self.pattern_form_rows, self.pattern_form_line_counts, self.populate_new_pattern_form, self.process_pattern_values)
        self.clear_feedback()

    def on_edit_pattern_clicked(self, button):
        self.disable_top_buttons()
        self._refresh_edit_form(self.pattern_form, PATTERN, self.patterns)
        self.clear_feedback()

    def on_new_recipe_clicked(self, button):
        self.disable_top_buttons()
        self._refresh_new_form(self.recipe_form, self.recipe_form_old_values, self.recipe_form_rows, {}, self.populate_new_recipe_form, self.process_recipe_values)
        self.clear_feedback()

    def on_edit_recipe_clicked(self, button):
        self.disable_top_buttons()
        self._refresh_edit_form(self.recipe_form, RECIPE, self.recipes)
        self.clear_feedback()

    def _refresh_new_form(self, form, form_old_values, form_rows,
                          form_line_counts, population_function,
                          done_function, wait=False):

        if form:
            form_old_values = {}
            for key in form_rows.keys():
                form_old_values[key] = form_rows[key]
        form = {}
        # if self.displayed_form:
        #     self.displayed_form.close()
        self.display_area.clear_output(wait=wait)

        population_function(form,
                            form_rows,
                            form_old_values,
                            form_line_counts,
                            population_function,
                            done_function)

        items = []
        for key in form.keys():
            items.append(form[key])

        form["done_button"] = widgets.Button(
            value=False,
            description="Done",
            disabled=False,
            button_style='',
            tooltip='Here is a tooltip for this button'
        )

        def done_button_click(button):
            values = {}
            for key in form_rows.keys():
                row = form_rows[key]
                if isinstance(row, list):
                    values_list = []
                    for element in row:
                        values_list.append(element.value)
                    values[key] = values_list
                else:
                    values[key] = form_rows[key].value

            done_function(values)

        form["done_button"].on_click(done_button_click)

        form["cancel_button"] = widgets.Button(
            value=False,
            description="Cancel",
            disabled=False,
            button_style='',
            tooltip='Here is a tooltip for this button'
        )

        def cancel_button_click(button):
            if isinstance(self.displayed_form, widgets.VBox):
                self.close_form()
                form_old_values = {}
                for text_key in form_rows.keys():
                    form_old_values[text_key] = form_rows[text_key]
                self.clear_feedback()

        form["cancel_button"].on_click(cancel_button_click)

        bottom_row_items = [
            form["done_button"],
            form["cancel_button"]
        ]
        bottom_row = widgets.HBox(bottom_row_items)
        items.append(bottom_row)

        self.displayed_form = widgets.VBox(items)

        with self.display_area:
            form_id = display(self.displayed_form, display_id=True)

    def _refresh_edit_form(self, form, editting, display_dict):
        form = {}
        # if self.displayed_form:
        #     self.displayed_form.close()
        self.display_area.clear_output()

        options = []
        for key in display_dict:
            options.append(key)

        dropdown = widgets.Dropdown(
            options=options,
            value=None,
            description="%s: " % editting,
            disabled=False,
        )

        def on_dropdown_select(change):
            if change['type'] == 'change' and change['name'] == 'value':
                to_edit = display_dict[change['new']]
                if editting is RECIPE:
                    self.editting = (editting, to_edit)
                    self.recipe_editor()
                elif editting is PATTERN:
                    self.pattern_editor(to_edit)

        dropdown.observe(on_dropdown_select)

        top_row_items = [
            dropdown
        ]
        top_row = widgets.HBox(top_row_items)

        items = [
            top_row
        ]

        self.displayed_form = widgets.VBox(items)

        with self.display_area:
            form_id = display(self.displayed_form, display_id=True)

    def recipe_editor(self):
        if not self.editting_area:
            label = widgets.Label(
                value='Update source:'
            )
            source = widgets.Text()
            self.current_form = {
                INPUT_SOURCE: source
            }
            input_items = [
                label,
                source
            ]
            input_row = widgets.HBox(input_items)

            apply = widgets.Button(
                value=False,
                description="Apply Changes",
                disabled=False,
                button_style='',
                tooltip='TODO'
            )
            apply.on_click(self.on_apply_recipe_changes_clicked)

            delete = widgets.Button(
                value=False,
                description="Delete recipe",
                disabled=False,
                button_style='',
                tooltip='TODO'
            )
            delete.on_click(self.on_delete_recipe_clicked)

            cancel = widgets.Button(
                value=False,
                description="Cancel",
                disabled=False,
                button_style='',
                tooltip='TODO'
            )
            cancel.on_click(self.on_cancel_clicked)

            button_items = [
                apply,
                delete,
                cancel
            ]
            button_row = widgets.HBox(button_items)

            editting_items = [
                input_row,
                button_row
            ]

            self.editting_area = widgets.VBox(editting_items)

            with self.display_area:
                display(self.editting_area)

    def pattern_editor(self, to_edit_object):
        pass

    def on_apply_recipe_changes_clicked(self, button):
        values = {
            INPUT_NAME: self.editting[1][NAME],
            INPUT_SOURCE: self.current_form[INPUT_SOURCE].value
        }
        if self.process_recipe_values(values, ignore_conflicts=True):
            self.done_editting()

    def on_delete_recipe_clicked(self, button):
        to_delete = self.editting[1][NAME]
        if to_delete in self.recipes.keys():
            self.recipes.pop(to_delete)
        self.feedback.value = "Recipe %s deleted. " % to_delete
        self.update_workflow_image()
        self.done_editting()


    # TODO poss also use this in recipe form
    def on_cancel_clicked(self, button):
        if isinstance(self.displayed_form, widgets.VBox):
            self.done_editting()
            self.clear_feedback()

    def done_editting(self):
        self.close_form()
        self.editting_area = None
        self.editting = None

    def make_help_button(self, help_text, extra_text, extra_func):
        help_button = widgets.Button(
            value=False,
            description="Toggle help",
            disabled=False,
            button_style='',
            tooltip='Here is a tooltip for this button'
        )
        help_html = widgets.HTML(
            value=""
        )
        def help_button_click(button):
            if help_html.value is "":
                message = help_text
                if extra_text:
                    message += extra_text
                if extra_func:
                    message += extra_func
                help_html.value = message
            else:
                help_html.value = ""

        help_button.on_click(help_button_click)

        return help_button, help_html

    def _create_form_single_input(self, text, help_text, key, form,
                                  old_values, extra_text=None,
                                  extra_func=None, optional=False):
        msg = text
        if optional:
            msg += " (optional)"
        label = widgets.Label(
            value="%s: " % msg
        )

        input = widgets.Text()
        if key in old_values:
            input.value = old_values[key].value
            old_values.pop(key, None)
        form[key] = input

        help_button, help_text = self.make_help_button(help_text,
                                                       extra_text=extra_text,
                                                       extra_func=extra_func)

        top_row_items = [
            label,
            input,
            help_button
        ]

        top_row = widgets.HBox(top_row_items)

        items = [
            top_row,
            help_text
        ]

        input_widget = widgets.VBox(items)
        return input_widget

    def _create_form_multi_input(self, text, help, key, form, rows, old_values,
                                 line_counts, population_function,
                                 done_function, extra_text=None,
                                 extra_func=None, optional=False):
        msg = text
        if optional:
            msg += " (optional)"
        label = widgets.Label(
            value="%s(s): " % msg
        )
        input = widgets.Text()

        help_button, help_text = self.make_help_button(help,
                                                       extra_text=extra_text,
                                                       extra_func=extra_func)

        input_old_values = []
        if key in old_values:
            input_old_values = old_values[key]
        if input_old_values:
            input.value = input_old_values[0].value
            del input_old_values[0]

        rows[key] = [input]

        add_button = widgets.Button(
            value=False,
            description="Add %s" % text.lower(),
            disabled=False,
            button_style='',
            tooltip='Here is a tooltip for this button'
        )

        def add_button_click(button):
            if key in line_counts.keys():
                line_counts[key] += 1
            else:
                line_counts[key] = 1
            self._refresh_new_form(form,
                                   old_values,
                                   rows,
                                   line_counts,
                                   population_function,
                                   done_function,
                                   wait=True)

        add_button.on_click(add_button_click)

        remove_button = widgets.Button(
            value=False,
            description="Remove %s" % text.lower(),
            disabled=False,
            button_style='',
            tooltip='Here is a tooltip for this button'
        )

        def remove_button_click(button):
            if key in line_counts.keys():
                line_counts[key] -= 1
            self._refresh_new_form(form,
                                   old_values,
                                   rows,
                                   line_counts,
                                   population_function,
                                   done_function,
                                   wait=True)

        if key in line_counts.keys():
            if line_counts[key] == 0:
                remove_button.disabled = True
        else:
            remove_button.disabled = True

        remove_button.on_click(remove_button_click)

        top_row_items = [
            label,
            input,
            help_button
        ]
        top_row = widgets.HBox(top_row_items)

        extra_rows = []
        if key in line_counts.keys():
            extra_rows_count = line_counts[key]
            for x in range(0, extra_rows_count):
                extra_input = widgets.Text()
                if input_old_values:
                    extra_input.value = input_old_values[0].value
                    del input_old_values[0]
                extra_row_items = [
                    extra_input
                ]
                extra_row = widgets.HBox(extra_row_items)
                extra_rows.append(extra_row)

                rows[key].append(extra_input)

                # if key in form:
                #     form[key].append(extra_input)

        if key in old_values:
            old_values.pop(key, None)

        bottom_row_items = [
            add_button,
            remove_button
        ]
        bottom_row = widgets.HBox(bottom_row_items)

        form_items = [
            top_row,
        ]
        for row in extra_rows:
            form_items.append(row)
        form_items.append(bottom_row)
        form_items.append(help_text)

        form_row = widgets.VBox(form_items)

        return form_row

    def on_import_from_vgrid_clicked(self, button):
        # status, patterns, message = retrieve_current_patterns()
        #
        # print(message)
        # if not status:
        #     return
        #
        # print('Found %d patterns' % len(patterns))
        # for pattern in patterns:
        #     print('%s (%s), inputs: %s, outputs: %s'
        #           % (pattern[NAME], pattern[PERSISTENCE_ID],
        #              pattern[TRIGGER_PATHS], pattern[OUTPUT]))
        #
        # print(message)
        # if not status:
        #     return
        #
        # print('displaying nodes:')
        # for key, value in workflow.items():
        #     print('node: %s, ancestors: %s, descendents: %s'
        #           % (key, value[ANCESTORS].keys(), value[DESCENDENTS].keys()))
        print("Goes nowhere, does nothing")

    def on_export_to_vgrid_clicked(self, button):
        print("Goes nowhere, does nothing")

    def clear_feedback(self):
        self.feedback.value = ""

    def close_form(self):
        # self.displayed_form.close()
        self.displayed_form = None
        self.display_area.clear_output()
        self.enable_top_buttons()

    def update_workflow_image(self):
        try:
            self.workflow = build_workflow_object(self.patterns, self.recipes)
        except:
            self.workflow = {}
        create_workflow_image(self.workflow, self.patterns, self.recipes,
                              filename=self.filename)
        extended_filename = self.filename + WORKFLOW_IMAGE_EXTENSION
        file = open(extended_filename, "rb")
        image = file.read()
        self.workflow_display.value = image
        file.close()

    def display_widget(self):
        # TODO update this
        """Displays a widget for workflow defitions. Can optionally take a
        predefined workflow as input"""

        workflow_image = [self.workflow_display]
        image_row = widgets.HBox(workflow_image)

        button_row_items = [self.new_pattern_button,
                            self.edit_pattern_button,
                            self.new_recipe_button,
                            self.edit_recipe_button,
                            self.import_from_vgrid_button,
                            self.export_to_vgrid_button]
        button_row = widgets.HBox(button_row_items)

        feedback_items = [
            self.feedback
        ]
        feedback_row = widgets.HBox(feedback_items)

        display_items = [
            self.display_area
        ]
        display_row = widgets.HBox(display_items)

        widget = widgets.VBox(
            [
                image_row,
                button_row,
                display_row,
                feedback_row
            ]
        )
        self.enable_top_buttons()
        return widget