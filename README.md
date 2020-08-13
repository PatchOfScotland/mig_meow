# mig_meow
MEOW is a Manager for Event Oriented Workflows.

## Introduction
mig_meow provides a way for MEOW Workflows to be defined using Patterns and 
Recipes. These can be sent to the MiG 
(https://sourceforge.net/projects/migrid/), which is used for actual job 
processing and data storage.

Currently this package does very little on its own.

## Installation
mig_meow can be installed from pypi using pip using:
```
pip install mig_meow
```

## Jupyter
mig_meow is designed primarily to be used within Jupyter notebooks, either as a
standard notebook or within Jupyter Lab. If you are running it within Jupyter 
Lab it will require the labextensions:

- jupyterlab-manager (https://github.com/jupyter-widgets/ipywidgets)
- bqplot (https://github.com/bqplot/bqplot)

## Examples
Some example patterns and recipes are included in the 'examples' directory. 
These can be worked through in the 'workflow_examples.ipynb' notebook.

## Testing
Automatic testing is available though it will require a numpy install to work 
correctly.