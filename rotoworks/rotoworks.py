#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
from os import startfile
from os.path import join as osjoin
from PyQt4 import QtGui, QtCore
from pyqtauto.widgets import ExceptionMessageBox
from view import HomeView
from core import Image, Path
from data import Data
from definition import DefinitionController
from scope import ScopeController
from workspace import WorkspaceController
from history import HistoryController


__author__ 	= 'Brandon McCleary'
__version__ = '1.0'
__status__ 	= 'Production'


class RotoWorks(QtGui.QMainWindow):
	"""
	RotoWorks aims to simplify shop inspections and automate customer 
	documentation. 

	The inspections are carried out with a portable CMM via PolyWorks Inspector 
	and are validated in real-time per established metrics (see PolyWorks 
	macros). The inspection data is used to auto-populate a pre-built AutoCAD 
	form.

	The standard RotoWorks workflow is the following:
		+ Create a new project
		+ Define project attributes
		+ Build project workscope
		+ Initiate measurement session
		+ Initiate documentation session

	"""
	def __init__(self):
		super(RotoWorks, self).__init__()
		self.setWindowTitle('RotoWorks | Sulzer RES')
		self._central_widget = QtGui.QWidget()
		self._central_widget.setStyleSheet('background-color:white;')
		self._central_widget.setContentsMargins(20,20,20,20)
		self.setCentralWidget(self._central_widget)
		self._view = HomeView(self._central_widget)
		self._view.new_btn.clicked.connect(self._on_click_new)
		self._view.open_btn.clicked.connect(self._on_click_open)
		self._view.info_btn.clicked.connect(self._on_click_info)

	def _on_click_new(self):
		"""Start a new project."""
		data = Data()
		definition = DefinitionController(data)
		if definition.view.exec_():
			scope = ScopeController(data)
			if scope.view.exec_():
				workspace = WorkspaceController(data, self._modify_scope)
				workspace.view.exec_()

	def _on_click_open(self):
		"""Open an existing project."""
		history = HistoryController()
		if history.view.exec_():
			data = Data()
			if history.project is not None:
				data.open_project(history.project)
				workspace = WorkspaceController(data, self._modify_scope)
				workspace.view.exec_()

	def _modify_scope(self, workspace, data):
		"""Allow the user to retroactively modify a project's workscope.

		Parameters
		----------
		workspace : WorkspaceController
			The active ``WorkspaceController`` object.
		data : Data
			The active data source.

		"""
		workspace.view.hide()
		scope = ScopeController(data)
		if scope.view.exec_():
			# Update active data source
			workspace.data = data
		workspace.view.show()

	def _on_click_info(self):
		"""Open the user guide."""
		try:
			startfile(osjoin(Path.DOCS, 'RotoWorks User Guide.pdf'))
		except OSError as error:
			ExceptionMessageBox(error).exec_()
		

if __name__ == '__main__':
	# Run RotoWorks app
	app = QtGui.QApplication(sys.argv)
	app.setWindowIcon(QtGui.QIcon(QtGui.QPixmap(Image.ICON)))
	app.setStyle(QtGui.QStyleFactory.create('cleanlooks'))
	roto = RotoWorks()
	roto.show()
	sys.exit(app.exec_())
