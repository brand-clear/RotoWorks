import sys
import py2exe
import pyautocad
import matplotlib
from distutils.core import setup


sys.argv.append('py2exe')
setup(
    windows=[{"script":"L:\\Division2\\DRAFTING\\Applications\\rotoworks\\rotoworks\\rotoworks.py"}],
    options={"py2exe":{"includes":["pyautocad", "sip", "PyQt4.QtXml", 'pandas._libs.tslibs.np_datetime','pandas._libs.tslibs.nattype','pandas._libs.skiplist']}},
    data_files=matplotlib.get_py2exe_datafiles()
)
