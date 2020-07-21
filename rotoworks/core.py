"""
rotoworks.core contains absolute paths to default directories and images.

"""
import sys
import json
import logging
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
	LOG = osjoin(ROOT, 'logging', 'app.log')


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
	IMPORT_LEFT = osjoin(ROOT, 'import-left.png')
	IMPORT_RIGHT = osjoin(ROOT, 'import-right.png')

	
def setup_logger():
	logging.basicConfig(filename=Path.LOG, 
		format='%(name)s - %(levelname)s - %(message)s')


if __name__ == "__main__":
	pass
