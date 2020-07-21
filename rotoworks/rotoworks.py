import os
import sys
from PyQt4 import QtGui
from pyqtauto.widgets import ToolBar, ExceptionMessageBox
from pyqtauto.setters import set_uniform_margins
from definition import DefinitionController
from workspace import WorkspaceController
from history import HistoryController
from scope import ScopeController
from core import Image, Path, setup_logger
from data import get_data_source
from view import HomeView
import logging


class RotoWorks(object):
	"""
	RotoWorks is an application that aims to simplify shop inspections and 
	automate customer documentation.

	Technologists will use this program to assist with measuring mechanical
	dimensions, documenting measurement sessions, and optionally, comparing to
	other mechanical systems.

	Inspections are carried out with a Portable CMM device, such as a Faro Arm, 
	via PolyWorks Inspector. Customer documentation is carried out through 
	Autodesk AutoCAD. Comparison reports are saved as CSV.

	"""
	def __init__(self):
		self.window = QtGui.QMainWindow()
		self.window.setWindowTitle('RotoWorks')
		# Toolbar
		self.toolbar = ToolBar(self.window, 'Tool Bar')
		self.toolbar.add_action(Image.NEW, 'New', self.on_click_new)
		self.toolbar.add_action(Image.OPEN, 'Open', self.on_click_open)
		self.toolbar.add_action(Image.INFO, 'Help', self.on_click_help)
		# Main views
		self.home_view = HomeView()
		self.definition = DefinitionController()
		self.definition.view.btn.accepted.connect(self.create_project)
		self.scope = ScopeController()
		self.scope.view.btn.accepted.connect(self.enter_workspace)
		self.workspace = WorkspaceController()
		self.workspace.view.btns.helpRequested.connect(self.retro_scope_mod)
		self.workspace.view.btns.accepted.connect(self.on_workspace_finish)
		# Stack views
		self.interfaces = QtGui.QStackedWidget()
		self.interfaces.addWidget(self.home_view)
		self.interfaces.addWidget(self.definition.view)
		self.interfaces.addWidget(self.scope.view)
		self.interfaces.addWidget(self.workspace.view)
		set_uniform_margins(self.interfaces, 10)
		self.window.setCentralWidget(self.interfaces)

	def on_click_new(self):
		self.definition.view.clear()
		self.interfaces.setCurrentWidget(self.definition.view)
		self.definition.view._job_le.setFocus()

	def create_project(self):
		data = self.definition.create()
		if data is not None:
			self.enter_workscope(data)

	def enter_workscope(self, data):
		"""Display project workscope interface.

		Parameters
		----------
		data : Data
			The active data model.

		"""
		col_headers = data.features
		self.scope.init_state(data)
		self.interfaces.setCurrentWidget(self.scope.view)

	def enter_workspace(self):
		"""Display project workspace interface."""
		data = self.scope.save()
		self.workspace.init_state(data)
		self.interfaces.setCurrentWidget(self.workspace.view)

	def retro_scope_mod(self):
		"""Allow user to retroactively modify ``ScopeModel`` instance."""
		self.enter_workscope(self.workspace.data)
		
	def on_workspace_finish(self):
		self.interfaces.setCurrentWidget(self.home_view)

	def on_click_help(self):
		"""Open user guide."""
		try:
			os.startfile(os.path.join(Path.DOCS, 'RotoWorks User Guide.pdf'))
		except OSError as error:
			logging.warning(error)
			ExceptionMessageBox(error).exec_()

	def on_click_open(self):
		"""Prompt user to open an existing project."""
		history = HistoryController()
		if history.view.exec_():
			if history.project is not None:
				try:
					data = get_data_source(history.project)
				except IOError as error:
					logging.warning(error)
					ExceptionMessageBox(error).exec_()
				else:
					self.enter_workscope(data)
					# self.workspace.init_state(data)
					# self.interfaces.setCurrentWidget(self.workspace.view)


if __name__ == '__main__':
	setup_logger()
	# Run RotoWorks app
	app = QtGui.QApplication(sys.argv)
	app.setWindowIcon(QtGui.QIcon(QtGui.QPixmap(Image.ICON)))
	rotoworks = RotoWorks()
	rotoworks.window.show()
	sys.exit(app.exec_())
