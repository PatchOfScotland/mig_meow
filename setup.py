from setuptools import setup

with open('README.md', 'r') as readme:
    long_description = readme.read()

module_name = 'mig_meow'
module_fullname = 'Managing Event-Oriented_workflows'
module_version = '0.13'

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
            #'pillow==7.0.0',
            'graphviz>=0.13.2',
            'bqplot>=0.12.12',
            'IPython>=7.9.0',
            'requests>=2.22.0',
            'ipywidgets>=7.5.1',
            'PyYAML>=5.3',
            'nbformat>=4.4.0'
      ],
      classifiers=[
            'Programming Language :: Python :: 3',
            'License :: OSI Approved :: GNU General Public License (GPL)',
            'Operating System :: OS Independent'
      ])
