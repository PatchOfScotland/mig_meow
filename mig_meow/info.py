
module_name = 'mig_meow'
module_fullname = 'Managing Event-Oriented_workflows'
module_version = '0.13'


def info():
    """
    Debug function to check that mig_meow has been imported correctly.
    Prints message about the current build.
    
    :return: (str) debug message.  
    """
    message = 'ver: %s\n' \
              '%s has been imported correctly. \n' \
              '%s is a paradigm used for defining event based ' \
              'workflows. It is designed primarily to work with IDMC, a MiG ' \
              'implementation available at the University of Copenhagen. ' \
              % (module_version, module_name, module_fullname)
    print(message)
