#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import sys
from PyQt4 import QtGui
from pyqtauto.widgets import Dialog, DialogButtonBox
from sulzer.extract import Extract, ProjectsFolderRootError
from view import InputListView
from core import Image, Path


__author__ = 'Brandon McCleary'


class HistoryView(Dialog):
	"""
	Displays an interface for querying historical project data.
	
	Attributes
	----------
	job_num : str
	input_view : InputListView
	btns : DialogButtonBox

	"""
	def __init__(self):
		super(HistoryView, self).__init__('Open Project')
		self._build_gui()

	def _build_gui(self):
		"""Display widgets."""
		self.input_view = InputListView(self.layout, 'Job Number:', Image.SEARCH)
		self.input_view.listbox.setSelectionMode(
			QtGui.QAbstractItemView.SingleSelection
		)
		self.btns = DialogButtonBox(self.layout, 'okcancel')

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
		self.view = HistoryView()
		self.view.input_view.input_le.returnPressed.connect(self._on_click_search)
		self.view.input_view.enter_btn.clicked.connect(self._on_click_search)
		self.view.input_view.listbox.itemDoubleClicked.connect(self.view.accept)
		self.view.btns.accepted.connect(self.view.accept)
		self.view.btns.rejected.connect(self.view.close)

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
			for folder in os.listdir(top_level):
				folder_path = os.path.join(top_level, folder)
				for filename in os.listdir(folder_path):
					if filename[-3:] == '.rw':
						project_dict[filename] = folder_path

		except WindowsError as error:
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

