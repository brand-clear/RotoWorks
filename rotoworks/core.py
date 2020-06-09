"""
rotoworks.core contains absolute paths to default directories and images.

"""
import sys
import json
from os.path import dirname
from os.path import join as osjoin
from os.path import split as ossplit
from collections import OrderedDict
from sulzer.extract import Extract, ProjectsFolderRootError
from pywinscript.win import create_folder


class Path(object):
    """Default network paths."""

    if ossplit(sys.executable)[1] == 'python.exe':
        # Dev mode
        ROOT = dirname(dirname(__file__))

        # Dev mode - testing current build
        # ROOT = 'L:\\Division2\\DRAFTING\\Applications\\rotoworks'
    else:
        # Production mode
        ROOT = 'L:\\Division2\\DRAFTING\\Applications\\rotoworks'

    DATA = osjoin(ROOT, 'data')
    IMAGE = osjoin(DATA, 'images')
    MACROS = osjoin(ROOT, 'macros')
    DOCS = osjoin(ROOT, 'docs')
    BALANCE = "L:\\Division2\\DCC\\1-CAD-FORMS\\BALANCE"
    JOBS = osjoin(DATA, 'jobs')


class Image(object):
    """Default image paths."""
    ROOT = Path.IMAGE
    EDIT = osjoin(ROOT, 'edit.png')
    PLAY = osjoin(ROOT, 'play.png')
    REPLAY = osjoin(ROOT, 'replay.png')
    DOWNLOAD = osjoin(ROOT, 'download.png')
    FORWARD = osjoin(ROOT, 'forward.png')
    BACK = osjoin(ROOT, 'back.png')
    NEW = osjoin(ROOT, 'new.png')
    OPEN = osjoin(ROOT, 'open.png')
    INFO = osjoin(ROOT, 'info.png')
    LOGO = osjoin(ROOT, 'logo.png')
    SEARCH = osjoin(ROOT, 'search.png')
    ICON = osjoin(ROOT, 'sulzer.png')
    CLOUD = osjoin(ROOT, 'cloud.png')
    CLOUD_RIGHT = osjoin(ROOT, 'cloud-right.png')
    COMPARE = osjoin(ROOT, 'compare.png')
    

if __name__ == "__main__":
    print Path.ROOT, Path.MACROS
