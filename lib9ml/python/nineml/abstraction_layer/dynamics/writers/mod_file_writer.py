"""
docstring needed

:copyright: Copyright 2010-2013 by the Python lib9ML team, see AUTHORS.
:license: BSD-3, see LICENSE for details.
"""

import os


class ModFileWriter(object):

    @classmethod
    def write(cls, component, filename):

        from nineml2nmodl import write_nmodl, write_nmodldirect
        write_nmodldirect(component=component, mod_filename=filename,
                          weight_variables={})

    @classmethod
    def compile_modfiles(cls, directory):

        cwd = os.getcwd()
        os.chdir(directory)
        print 'Compile_modfiles:', os.getcwd()

        try:
            os.system('nrnivmodl')
        finally:
            os.chdir(cwd)
