import os
import shutil
import time

print(os.getcwd())

os.chdir('..')

print(os.getcwd())

import mig_meow as meow

base_dir = 'local_workflow_base'
file_base = os.path.join(base_dir, 'files')
processing_dir = os.path.join(base_dir, 'jobs')
state_dir = os.path.join(base_dir, 'state')
examples_dir = 'examples'
meow_dir = os.path.join(examples_dir, 'meow_directory')
data_dir = os.path.join(examples_dir, 'example_data')
initial_dir = 'initial_data'

meow.info()

if os.path.exists(base_dir):
    if os.path.isdir(base_dir):
        shutil.rmtree(base_dir)
        print('Removing directory %s' % base_dir)
    else:
        os.remove(base_dir)
        print('Removing %s' % base_dir)
print('Creating %s' % base_dir)
os.mkdir(base_dir)

patterns = {
#    'adder': meow.read_dir_pattern('adder', directory=meow_dir),
    'first_mult': meow.read_dir_pattern('first_mult', directory=meow_dir),
    'second_mult': meow.read_dir_pattern('second_mult', directory=meow_dir),
    'third_choo': meow.read_dir_pattern('third_choo', directory=meow_dir)
}

recipes = {
    'add': meow.read_dir_recipe('add', directory=meow_dir),
    'choo': meow.read_dir_recipe('choo', directory=meow_dir),
    'mult': meow.read_dir_recipe('mult', directory=meow_dir)
}

# runner = meow.WorkflowRunner(
#     file_base,
#     3,
#     patterns=patterns,
#     recipes=recipes,
#     daemon=True,
#     job_data=processing_dir,
#     meow_data=state_dir
# )
#
# time.sleep(3)
#
# os.mkdir(os.path.join(file_base, initial_dir))
# for file_name in os.listdir(data_dir):
#     source_path = os.path.join(data_dir, file_name)
#     target_path = os.path.join(file_base, initial_dir, file_name)
#     shutil.copy(source_path, target_path)
