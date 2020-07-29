import os


def info():
    """
    Debug function to check that mig_meow has been imported correctly.
    Prints message about the current build.
    
    :return: (str) debug message.  
    """
    msg = "No version data available"

    current_dir = os.path.abspath(os.path.dirname(__file__))
    version_path = os.path.join(
        current_dir[:current_dir.rfind(os.path.sep)],
        'version.py'
    )

    module_data = {}
    try:
        module_data = {}
        with open(version_path) as f:
            exec(f.read(), {}, module_data)
    except:
        pass

    if module_data:
        msg = 'ver: %s\n' \
              '%s has been imported correctly. \n' \
              '%s is a paradigm used for defining event based ' \
              'workflows. It is designed primarily to work with IDMC, a MiG ' \
              'implementation available at the University of Copenhagen. ' \
              % (module_data['__version__'],
                 module_data['__name__'],
                 module_data['__fullname__'])
    print(msg)
