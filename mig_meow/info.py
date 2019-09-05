
name = 'mig_meow'
fullname = 'Managing Event-Oriented_workflows'
version = '0.1.8'


def info():
    """Debug function to check that mig_meow has been imported correctly.
    Prints message about the current build"""
    message = 'ver: %s\n' \
              '%s has been imported ' \
              'correctly. \nMEOW is a package used for defining event based ' \
              'workflows. It is designed primarily to work with the MiG ' \
              'system.' % (version, fullname)
    print(message)
