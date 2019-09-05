from setuptools import setup

from .mig_meow.info import name as module_name
from .mig_meow.info import version as module_version

with open('README.md', 'r') as readme:
    long_description = readme.read()

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
            'bqplot'
      ],
      classifiers=[
            'Programming Language :: Python :: 3',
            'License :: OSI Approved :: GNU General Public License (GPL)',
            'Operating System :: OS Independent'
      ])
