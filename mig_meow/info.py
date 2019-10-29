
module_name = 'mig_meow'
module_fullname = 'Managing Event-Oriented_workflows'
module_version = '0.2.1'


def info():
    """Debug function to check that mig_meow has been imported correctly.
    Prints message about the current build"""
    message = 'ver: %s\n' \
              '%s has been imported ' \
              'correctly. \n%s is a package used for defining event based ' \
              'workflows. It is designed primarily to work with a MiG ' \
              'system.' % (module_version, module_fullname, module_name)
    print(message)
