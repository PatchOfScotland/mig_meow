
import ipywidgets as widgets
import os
import json

from .constants import PATTERNS_DIR, ANCESTORS, DESCENDENTS, NAME, \
    PERSISTENCE_ID, TRIGGER_PATHS, OUTPUT
from .workflows import build_workflow
from .pattern import Pattern

def retrieve_current_patterns(debug='False'):
    """Will look within the expected workflow pattern directory and return a
    dict of all found patterns. If debug is set to true will also output
    warning messages"""
    all_patterns = {}
    message = ''
    if os.path.isdir(PATTERNS_DIR):
        for path in os.listdir(PATTERNS_DIR):
            file_path = os.path.join(PATTERNS_DIR, path)
            if os.path.isfile(file_path):
                try:
                    with open(file_path) as file:
                        input_dict = json.load(file)
                        pattern = Pattern(input_dict)
                        all_patterns[pattern.name] = pattern
                except:
                    message += '%s is unreadable, possibly corrupt.' % path
    else:
        if debug:
            return ({}, 'No patterns found to import.')
        return {}
    if debug:
        return (all_patterns, message)
    return all_patterns


def display_widget():
    import_from_vgrid_button = widgets.Button(
        value=False,
        description="Read VGrid",
        disabled=False,
        button_style='',
        tooltip='Here is a tooltip for this button',
        icon='check'
    )

    export_to_vgrid_button = widgets.Button(
        value=False,
        description="Export Workflow",
        disabled=False,
        button_style='',
        tooltip='Here is a tooltip for this button',
        icon='check'
    )

    def on_import_from_vgrid_clicked(button):
        status, patterns, message = retrieve_current_patterns()

        print(message)
        if not status:
            return

        print('Found %d patterns' % len(patterns))
        for pattern in patterns:
            print('%s (%s), inputs: %s, outputs: %s' % (
            pattern[NAME], pattern[PERSISTENCE_ID],
            pattern[TRIGGER_PATHS], pattern[OUTPUT]))

        status, workflow, message = build_workflow(patterns)

        print(message)
        if not status:
            return

        print('displaying nodes:')
        for key, value in workflow.items():
            print('node: %s, ancestors: %s, descendents: %s' % (
            key, value[ANCESTORS].keys(), value[DESCENDENTS].keys()))

    def on_export_to_vgrid_clicked(button):
        print("Goes nowhere, does nothing")

    import_from_vgrid_button.on_click(on_import_from_vgrid_clicked)
    export_to_vgrid_button.on_click(on_export_to_vgrid_clicked)

    items = [import_from_vgrid_button, export_to_vgrid_button]
    return widgets.Box(items)
