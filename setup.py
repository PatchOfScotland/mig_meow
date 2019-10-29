from setuptools import setup

with open('README.md', 'r') as readme:
    long_description = readme.read()

module_name = 'mig_meow'
module_fullname = 'Managing Event-Oriented_workflows'
module_version = '0.2'

setup(name=module_name,
      version=module_version,
      author='David Marchant',
      author_email='d.marchant@ed-alumni.net',
      description='MiG based manager for event oriented workflows',
      long_description=long_description,
      # long_description_content_type='text/markdown',
      url='https://github.com/PatchOfScotland/mig_meow',
      packages=['mig_meow'],
      install_requires=[
            'pillow',
            'graphviz',
            'bqplot',
            'IPython',
            'requests',
            'ipywidgets',
            'PyYAML'
      ],
      classifiers=[
            'Programming Language :: Python :: 3',
            'License :: OSI Approved :: GNU General Public License (GPL)',
            'Operating System :: OS Independent'
      ])
