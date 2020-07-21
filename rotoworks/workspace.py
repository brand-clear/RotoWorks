import sys
import os.path
from PyQt4 import QtGui, QtCore
from pyqtauto.widgets import (Spacer, DialogButtonBox, ExceptionMessageBox, 
	ListBox)
from turbodoc import (AxialDoc, DiameterDoc, ThermalGapDoc, RotorWeightDoc, 
	CADOpenError, CADLayerError, CADDocError)
from diameter_session import DiameterSessionController
from axial_session import AxialSessionController
from thermal_gap_session import ThermalGapController
from rotor_weights_session import RotorWeightsController
from template import ComparisonController
from core import Path, Image, setup_logger
from inspection import Inspection
from datetime import datetime
import logging


setup_logger()


class WorkspaceView(QtGui.QWidget):
	"""
	Displays project workspace GUI.

	Attributes
	----------
	project_lb : QLabel
		Displays the project filename.

	listbox : ListBox
		Displays a list of inspections.

	meas_btn : QPushButton
		Clicked to launch measurement session.

	doc_btn : QPushButton
		Clicked to launch documentation session.

	compare_btn : QPushButton
		Clicked to launch comparison session.

	selection : str
		The selected inspection.

	"""
	def __init__(self):
		super(WorkspaceView, self).__init__()
		self._main_layout = QtGui.QVBoxLayout(self)
		self._main_layout.setSpacing(10)
		self._grid_layout = QtGui.QGridLayout()
		# Init widgets
		self.project_lb = QtGui.QLabel()
		self._main_layout.addWidget(self.project_lb)
		self.listbox = ListBox(
			self._main_layout, 
			Inspection.get_inspection_types()
		)
		self.listbox.setSelectionMode(QtGui.QAbstractItemView.SingleSelection)
		self.meas_btn = QtGui.QPushButton('Measure')
		self.doc_btn = QtGui.QPushButton('Document')
		self.compare_btn = QtGui.QPushButton('Compare')
		self._meas_stat_lb = QtGui.QLabel()
		self._doc_stat_lb = QtGui.QLabel()
		self._compare_stat_lb = QtGui.QLabel()
		self._meas_stat_lb.setAlignment(QtCore.Qt.AlignCenter)
		self._doc_stat_lb.setAlignment(QtCore.Qt.AlignCenter)
		self._compare_stat_lb.setAlignment(QtCore.Qt.AlignCenter)
		# Add widgets to layout
		self._grid_layout.addWidget(self.meas_btn, 0, 0)
		self._grid_layout.addWidget(self._meas_stat_lb, 1, 0)
		self._grid_layout.addWidget(self.doc_btn, 0, 1)
		self._grid_layout.addWidget(self._doc_stat_lb, 1, 1)
		self._grid_layout.addWidget(self.compare_btn, 0, 2)
		self._grid_layout.addWidget(self._compare_stat_lb, 1, 2)
		self._main_layout.addLayout(self._grid_layout)
		self._main_layout.addItem(Spacer())
		self.btns = QtGui.QDialogButtonBox()
		self.btns.addButton('OK', QtGui.QDialogButtonBox.AcceptRole)
		self.btns.addButton('Back', QtGui.QDialogButtonBox.HelpRole)
		self._main_layout.addWidget(self.btns)
		# Map processes to status labels
		self._status_map = {
			'Measure': self._meas_stat_lb, 
			'Document': self._doc_stat_lb, 
			'Compare': self._compare_stat_lb
		}

	@property
	def selection(self):
		"""str: The selected ``ListBox`` item."""
		return self.listbox.selected_items[0]

	def set_process_status(self, process, mod_time):
		"""Display process status.

		Parameters
		----------
		process : {'Measure', 'Document', 'Compare'}
		mod_time : str
			Date and time that process file was last modified.

		"""
		if mod_time is None:
			self._status_map[process].setText('N/A')
		else:
			self._status_map[process].setText(mod_time)


class WorkspaceController(object):
	"""Provides a functional GUI for launching various project processes.

	The project workspace allows the user to launch measurement, documentation, 
	and comparison sessions for each listed inspection.

	Attributes
	----------
	view : WorkspaceView
		Provides GUI.

	data : Data

	"""
	def __init__(self):
		self._data = None
		self._filetype_map = {'Measure': '.csv', 'Document': 'Doc.txt'}
		self._meas_session_map = {
			'Axial': AxialSessionController, 
			'Diameter': DiameterSessionController,
			'Thermal Gap': ThermalGapController,
			'Rotor Weight': RotorWeightsController
		}
		self._doc_session_map = {
			'Axial': AxialDoc,	
			'Diameter': DiameterDoc,
			'Thermal Gap': ThermalGapDoc,
			'Rotor Weight': RotorWeightDoc
		}
		self.view = WorkspaceView()
		self.view.listbox.itemClicked.connect(self._on_click_listbox)
		self.view.meas_btn.clicked.connect(self._on_click_meas_btn)
		self.view.doc_btn.clicked.connect(self._on_click_doc_btn)
		self.view.compare_btn.clicked.connect(self._on_click_compare_btn)

	@property
	def data(self):
		"""Data: The instance data model."""
		return self._data

	def init_state(self, data):
		self._data = data
		self.view.project_lb.setText('Project: %s' % self._data.filename)

	def _format_time(self, time):
		return time.strftime("%m-%d-%y %I:%M %p")

	def _get_mod_date(self, inspection, process):
		"""Get the date and time that a file was last modified.

		Parameters
		----------
		inspection : {'Axial', 'Diameter', 'Thermal Gap', 'Rotor Weight'}
			Dictates the process filename to be evaluated.

		process : {'Measure', 'Document'}
			Dictates the file extension to be evaluated.

		Returns
		-------
		str or None

		"""
		inspection = inspection.replace(' ', '')
		filename = os.path.join(
			self._data.path, inspection + self._filetype_map[process]
		)
		try:
			mtime = os.path.getmtime(filename)
		except OSError:
			return
		else:
			return self._format_time(datetime.fromtimestamp(mtime))

	def _on_click_listbox(self):
		"""Set completion status for inspection processes."""
		inspection = self.view.selection
		meas_status = self._get_mod_date(inspection, 'Measure')
		self.view.set_process_status('Measure', meas_status)

		doc_status = self._get_mod_date(inspection, 'Document')
		self.view.set_process_status('Document', doc_status)

		if meas_status is not None:
			self.view.set_process_status('Compare', 'Ready')
		else:
			self.view.set_process_status('Compare', meas_status)

	def _on_click_meas_btn(self):
		"""Launch a measurement session."""
		inspection = self.view.selection
		try:
			meas = self._meas_session_map[inspection](self._data)
		except KeyError as error:
			logging.warning(error)
			pass
		else:
			meas.view.exec_()
		self._on_click_listbox()

	def _on_click_doc_btn(self):
		"""Launch a documentation session."""
		inspection = self.view.selection
		try:
			doc = self._doc_session_map[inspection](self._data)
			doc.start()
		except (CADOpenError, CADDocError, CADLayerError, 
				AttributeError, IOError) as error:
			logging.warning(error)
			ExceptionMessageBox(error).exec_()
			
		self._on_click_listbox()

	def _on_click_compare_btn(self):
		"""Launch a comparison session."""
		inspection = self.view.selection
		if self._get_mod_date(inspection, 'Measure') is not None:
			comparison = ComparisonController(self._data, inspection)
			comparison.start()


if __name__ == '__main__':
	pass