import os

from setuptools import setup

current_dir = os.path.abspath(os.path.dirname(__file__))


def read_file(path):
    with open(path, "r") as _file:
        return _file.read()


def read_requirements(filename):
    path = os.path.join(current_dir, filename)
    return [req.strip() for req in read_file(path).splitlines() if req.strip()]


with open('README.md', 'r') as readme:
    long_description = readme.read()

module_data = {}
with open(os.path.join(current_dir, "mig_meow", "version.py")) as f:
    exec(f.read(), {}, module_data)

setup(name=module_data['__name__'],
      version=module_data['__version__'],
      author='David Marchant',
      author_email='d.marchant@ed-alumni.net',
      description='MiG based manager for event oriented workflows',
      long_description=long_description,
      url='https://github.com/PatchOfScotland/mig_meow',
      packages=['mig_meow'],
      install_requires=read_requirements("requirements.txt"),
      extras_require={
                "test": read_requirements("requirements-testing.txt"),
      },
      classifiers=[
            'Programming Language :: Python :: 3',
            'License :: OSI Approved :: GNU General Public License (GPL)',
            'Operating System :: OS Independent'
      ])
