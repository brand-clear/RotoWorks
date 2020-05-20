#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import sys
from PyQt4 import QtGui
from pyqtauto.widgets import (
	Spacer, 
	Table, 
	ImageButton, 
	DialogButtonBox, 
	Dialog, 
	TableItem,
	TableImageButton,
	ExceptionMessageBox
)
from machine import Rotor
from core import Path, Image
from data import Data
from inspection import Inspection
from turbodoc import (
	AxialDoc, 
	DiameterDoc, 
	CADOpenError, 
	CADLayerError, 
	CADDocError
)
from diameter_session import DiameterSessionController
from axial_session import AxialSessionController


__author__ = 'Brandon McCleary'


class WorkspaceView(Dialog):
	"""
	Displays the project workspace window.

	Attributes
	----------
	filename_lb : QLabel
	edit_btn : ImageButton
	table : Table
	ok_btn : DialogButtonBox

	"""
	def __init__(self):
		super(WorkspaceView, self).__init__('Project Workspace')
		self._build_gui()

	def _build_gui(self):
		"""Display widgets."""
		self._h_layout = QtGui.QHBoxLayout()
		self.filename_lb = QtGui.QLabel()
		self._h_layout.addWidget(QtGui.QLabel('Definition:'))
		self._h_layout.addWidget(self.filename_lb)
		self._h_layout.addItem(Spacer())
		self.edit_btn = ImageButton(Image.EDIT, self._h_layout, flat=True)
		self.layout.addLayout(self._h_layout)
		self.table = Table(['Inspection', 'Measure', 'Document'])
		self.table.verticalHeader().hide()
		self.layout.addWidget(self.table)
		self.ok_btn = DialogButtonBox(self.layout)

	def set_table(self, callback, filepath):
		"""Update table contents.

		Parameters
		----------
		callback : callable
			Called when a ``TableImageButton`` is clicked.
		filepath : str
			Absolute path to the project directory.

		"""
		self.table.setRowCount(0)
		inspections = Inspection.get_inspection_types()
		inspection_count = len(inspections)
		existing_files = os.listdir(filepath)
		self.table.setRowCount(inspection_count)
		for i in range(inspection_count):
			# Inspection name column
			self.table.setItem(i, 0, TableItem(inspections[i]))
			self.table.setRowHeight(i, 60)
			# Measure button
			# If <inspection>Scope.csv exists, the inspection has been 
			# performed at least once before.
			self._add_table_button(
				inspections[i]+'Scope.csv' in existing_files, 
				callback, 
				i, 1
			)
			# Document button
			# If <inspection>Doc.txt exists, the inspection has been 
			# documented at least once before.
			self._add_table_button(
				inspections[i]+'Doc.txt' in existing_files, 
				callback, 
				i, 2
			)

	def _add_table_button(self, has_worked, callback, row, col):
		"""Insert an ``ImageButton`` into a ``Table`` cell.

		Parameters
		----------
		has_worked : bool
			An indication that the corresponding action has been performed.
		callback : callable
			Called when the ``TableImageButton`` is clicked.
		row : int
		col : int

		"""
		map = {True: Image.REPLAY, False: Image.PLAY}
		self.table.setCellWidget(
			row, col, TableImageButton(map[has_worked], callback).widget
		)

	def get_clicked_intent(self):
		"""Get the requested inspection and action from a button click.

		Returns
		-------
		inspection : str
			{'Axial', 'Diameter'}
		action : str
			{'measure', 'document'}

		"""
		button = self.sender()
		index = self.table.indexAt(button.parent().pos())
		inspection = str(self.table.item(index.row(), 0).text())
		action = 'measure' if index.column() == 1 else 'document'
		return inspection, action


class WorkspaceController(object):
	"""
	Provides a functional GUI for launching measurement and/or documentation
	sessions.

	Parameters
	----------
	data : Data
		The active data source.
	scope_callback : callable
		Method that provides retroactive modifications to the project
		scope.

	Attributes
	----------
	view : WorkspaceView

	"""
	def __init__(self, data, scope_callback):
		self._data = data
		self._scope_callback = scope_callback
		self._definition = self._data.definition
		self._project_path = self._definition['Path to Filename']
		self._machine = Rotor.get_machine_type_as_object(
			self._definition['Machine Type']
		)
		self.view = WorkspaceView()
		self.view.filename_lb.setText(self._definition['Filename'])
		self.view.edit_btn.clicked.connect(
			lambda: self._scope_callback(self, self._data)
		)
		self.view.ok_btn.accepted.connect(self.view.accept)
		self.update_view()

	@property
	def data(self):
		"""Data: The active data source."""
		return self._data
	
	@data.setter
	def data(self, data):
		"""
		Parameters
		----------
		data : Data

		"""
		self._data = data

	def update_view(self):
		"""Refresh widgets."""
		self.view.set_table(self._on_click_table_button, self._project_path)

	def _on_click_table_button(self):
		"""Process table button clicks to launch the appropriate action."""
		inspection, intent = self.view.get_clicked_intent()
		self.view.set_table(
			self._on_click_table_button, 
			self._project_path
		)
		if intent == 'document':
			self._launch_doc_session(inspection)

		elif intent == 'measure':
			self._launch_measurement_session(inspection)

	def _launch_measurement_session(self, inspection):
		"""Start a measurement session.

		Parameters
		----------
		inspection : {'Axial', 'Diameter'}

		"""
		self.view.hide()

		if inspection == 'Axial':
			meas = AxialSessionController(self._data)
			meas.view.exec_()

		elif inspection == 'Diameter':
			meas = DiameterSessionController(self._definition)
			meas.view.exec_()

		self.view.show()
		self.update_view()

	def _launch_doc_session(self, inspection):
		"""Start a documentation session.

		Parameters
		----------
		inspection : {'Axial', 'Diameter'}

		"""
		try:
			if inspection == 'Axial':
				doc = AxialDoc(self._data)
				doc.start()

			elif inspection == 'Diameter':
				doc = DiameterDoc(self._project_path)
				doc.start()
				
		except (
			CADOpenError, CADDocError, CADLayerError, AttributeError, IOError
		) as error:
			ExceptionMessageBox(error).exec_()
		else:
			self.update_view()


if __name__ == '__main__':
	# For test
	app = QtGui.QApplication(sys.argv)
	app.setWindowIcon(QtGui.QIcon(QtGui.QPixmap(Image.ICON)))
	app.setStyle(QtGui.QStyleFactory.create('cleanlooks'))

	# Get test data
	test_dir = 'C:\\Users\\mcclbra\\Desktop\\development\\rotoworks\\tests'
	test_file = '123123_Phase1_CentrifugalCompressor.rw'
	#test_file = '123123_Phase1_SteamTurbine.rw'
	data = Data()
	data.open_project(os.path.join(test_dir, test_file))


	# Test WorkspaceView
	# -------------------
	# view = WorkspaceView()
	# view.exec_()


	# Test WorkspaceController
	# -------------------------
	controller = WorkspaceController(data, lambda: None)
	controller.view.exec_()