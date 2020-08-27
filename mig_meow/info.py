from .version import __name__, __version__, __fullname__


def info():
    """
    Debug function to check that mig_meow has been imported correctly.
    Prints message about the current build.
    
    :return: (str) debug message.  
    """

    msg = 'ver: %s\n' \
          '%s has been imported correctly. \n' \
          '%s is a paradigm used for defining event based ' \
          'workflows. It is designed primarily to work with IDMC, a MiG ' \
          'implementation available at the University of Copenhagen. ' \
          % (__version__, __name__, __fullname__)
    print(msg)
