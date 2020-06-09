import os
import sys
from PyQt4 import QtGui
from pyqtauto.widgets import Dialog, DialogButtonBox
from sulzer.extract import Extract, ProjectsFolderRootError
from view import InputListView
from core import Image, Path


class HistoryView(Dialog):
	"""
	Displays an interface for querying historical project data.

	Parameters
	----------
	search_callback : callable
	
	Attributes
	----------
	job_num : str
	input_view : InputListView
	btns : DialogButtonBox

	"""
	def __init__(self, search_callback):
		self._search_callback = search_callback
		super(HistoryView, self).__init__('Open Project')
		self._build_gui()

	def _build_gui(self):
		"""Display widgets."""
		self.input_view = InputListView(self.layout, 'Job Number:', Image.SEARCH)
		self.input_view.listbox.setSelectionMode(
			QtGui.QAbstractItemView.SingleSelection
		)
		self.input_view.input_le.returnPressed.connect(self._search_callback)
		self.input_view.enter_btn.clicked.connect(self._search_callback)
		self.input_view.listbox.itemDoubleClicked.connect(self.accept)
		self.btns = DialogButtonBox(self.layout, 'okcancel')
		self.btns.accepted.connect(self.accept)
		self.btns.rejected.connect(self.close)

	@property
	def job_num(self):
		"""str: QLineEdit input text."""
		return str(self.input_view.input_le.text())


class HistoryController(object):
	"""
	Provides a functional GUI for querying historical project data.

	Attributes
	----------
	project : str or None
	projects : dict or None
	view : HistoryView

	"""
	def __init__(self):
		self._projects = {}
		self.view = HistoryView(self._on_click_search)

	@property
	def project(self):
		"""str or None: The absolute path of the selected filename."""
		try:
			selection = self.view.input_view.selected_items[0]
			return os.path.join(self.projects[selection], selection)
		except (IndexError, KeyError, TypeError):
			return

	@property
	def projects(self):
		"""dict: The relevant filenames and their corresponding paths."""
		return self._projects

	@projects.setter
	def projects(self, top_level):
		"""
		Parameters
		----------
		top_level : str
			Absolute path to a top-level job directory.

		"""
		project_dict = {}

		try:
			for root, dirs, files in os.walk(top_level):
				for filename in files:
					if filename.endswith('.rw'):
						project_dict[filename] = root
			if len(project_dict.keys()) == 0:
				project_dict['No projects found'] = None
		finally:
			self._projects = project_dict

	def _on_click_search(self):
		"""Process user input and update view."""

		job_num = self.view.job_num
		try:
			job_root = os.path.basename(
				Extract.projects_folder_root(job_num)
			)
			self.projects = os.path.join(Path.JOBS, job_root, job_num)
		except ProjectsFolderRootError:
			self.view.input_view.set_listbox(['No PROJECTS FOLDER found'])
		else:
			self.view.input_view.set_listbox(self.projects.keys())


if __name__ == '__main__':
	# For test
	app = QtGui.QApplication(sys.argv)
	app.setStyle(QtGui.QStyleFactory.create('cleanlooks'))


	# Test HistoryView
	# -------------------
	# view = HistoryView()
	# view.exec_()


	# Test HistoryController
	# -------------------------
	controller = HistoryController()
	controller.view.exec_()
	print controller.project

