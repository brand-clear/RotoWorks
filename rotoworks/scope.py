#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import sys
from collections import OrderedDict
from PyQt4 import QtGui
from pyqtauto.widgets import (
	Dialog, 
	TableItem, 
	TableImageButton, 
	Table, 
	DialogButtonBox, 
	TableCheckBox,
	ExceptionMessageBox
)
from machine import Rotor
from core import Path
from data import Data


__author__ = 'Brandon McCleary'


class ScopeView(Dialog):
	"""
	Displays the project workscope window.

	Attributes
	----------
	filename_lb : QLabel
	stage_le : QLineEdit
	table : Table
	ok : DialogButtonBox

	"""

	# Manipulations of the table rows should avoid select-all Checkboxes
	# (top row) and the textual column (first column).
	SELECT_ALL_ROW_OFFSET = 1
	STAGE_COLUMN_OFFSET = 1

	def __init__(self):
		super(ScopeView, self).__init__('Project Scope')
		self._build_gui()

	def _build_gui(self):
		"""Display widgets."""
		self._form_layout = QtGui.QFormLayout()
		self.filename_lb = QtGui.QLabel()
		self.stage_le = QtGui.QLineEdit()
		self.stage_le.setFixedWidth(50)
		self.stage_le.setValidator(QtGui.QIntValidator())
		self.stage_le.setMaxLength(2)
		self.table = Table()
		self.table.verticalHeader().hide()
		self._form_layout.addRow(QtGui.QLabel('Definition:'), self.filename_lb)
		self._form_layout.addRow(QtGui.QLabel('Stage Count:'), self.stage_le)
		self.layout.addLayout(self._form_layout)
		self.layout.addWidget(self.table)
		self.ok = DialogButtonBox(self.layout)

	def _select_all(self, checkbox, state):
		"""Changes the checked state of multiple ``TableCheckboxes`` at once.

		Parameters
		----------
		checkbox : TableCheckbox
			The designated select/deselect-all widget.
		state : bool
			True to select, False to deselect.

		"""
		parent_col = self.table.indexAt(checkbox.parent().pos()).column()
		# Set state for all checkboxes in parent_col
		for check in self.table.findChildren(QtGui.QCheckBox):
			if self.table.indexAt(check.parent().pos()).column() == parent_col:
				check.setChecked(state)

	def _top_row_clicked(self):
		"""Call the select-all ``TableCheckbox`` functionality."""
		checkbox = self.sender()
		if checkbox.isChecked():
			self._select_all(checkbox, True)
		else:
			self._select_all(checkbox, False)

	def _insert_select_all_row(self, col_count):
		"""Insert a select-all ``TableCheckbox`` at the top of each column.

		Parameters
		----------
		col_count : int

		"""
		for col in range(self.STAGE_COLUMN_OFFSET, col_count):
			self.table.setCellWidget(
				0, col, 
				TableCheckBox(response=self._top_row_clicked).widget
			)

	def _insert_feature_rows(self, table_map, col_count):
		"""Insert a ``TableCheckbox`` for all feature table cells.

		Parameters
		----------
		table_map : OrderedDict
		col_count : int

		"""
		row = self.SELECT_ALL_ROW_OFFSET
		for stage in table_map:
			self.table.setItem(row, 0, TableItem(stage))
			for col in range(self.STAGE_COLUMN_OFFSET, col_count):
				self.table.setCellWidget(
					row, col, 
					table_map[stage][col-1].widget
				)
			row += 1

	def set_rows(self, table_map, col_count):
		"""Update table rows.

		Parameters
		----------
		table_map : OrderedDict
		col_count : int

		"""
		self.table.setRowCount(len(table_map) + self.SELECT_ALL_ROW_OFFSET)
		self._insert_select_all_row(col_count)
		self._insert_feature_rows(table_map, col_count)


class ScopeController(object):
	"""
	Provides a functional GUI for establishing a project workscope.

	A project workscope contains the action items for axial inspections and is
	saved in the project definition file.

	Parameters
	----------
	data : Data
		The active data source.

	Attributes
	----------
	view : Dialog

	"""
	def __init__(self, data):
		self._data = data
		self._definition = self._data.definition
		self._scope = self._data.scope
		self._table_map = None
		self._machine = Rotor.get_machine_type_as_object(
			self._definition['Machine Type']
		)
		self._col_headers = self._machine.FEATURES
		self._col_count = len(self._col_headers)
		self.view = ScopeView()
		self._data_col_count = self._col_count - self.view.STAGE_COLUMN_OFFSET
		self._startup()
		self.view.setMinimumWidth(90 * len(self._col_headers))
		self.view.stage_le.textChanged.connect(self._on_edit_stage_count)
		self.view.ok.accepted.connect(self._on_click_ok)

	def _startup(self):
		"""Load and display initial view state.
		
		Notes
		-----
		This must be called prior to connecting the view.stage_le callback
		function. This structure prevents existing scopes from being reset.
		
		"""
		self.view.filename_lb.setText(self._definition['Filename'])
		self.view.table.update(self._col_headers)
		if self.scope is not None:
			stage_count = len(self.scope)
			self.view.stage_le.setText(str(stage_count))
			self._on_edit_stage_count(stage_count)
		else:
			self.view.stage_le.setText('0')

	@property
	def scope(self):
		"""OrderedDict: A mapping of axial features to be measured during inspection.

		Notes
		-----
		Keys 	>>> ``str``	: stage number
		Values 	>>> ``list``: binary values corresponding to machine type features.

		"""
		return self._scope

	@scope.setter
	def scope(self, factor):
		"""
		Parameters
		----------
		factor : int or OrderedDict

		"""
		if type(factor) == int:
			# factor is the new stage count.
			# The scope is reset to stage labels and zeros.
			self._scope = self._reset_scope(factor)
			
		elif type(factor) == OrderedDict:
			# factor is the current table_map.
			# The scope will convert its values to match the table_map.
			table_map = factor
			for key in table_map:
				for i in range(self._data_col_count):
					if table_map[key][i].isChecked():
						self._scope[key][i] = 1
					else:
						self._scope[key][i] = 0

	def _reset_scope(self, stage_count):
		"""Returns an ``OrderedDict``of zeroes in scope format.

		Parameters
		----------
		stage_count : int

		"""
		scope = OrderedDict()
		stage_labels = Rotor.stage_names(
			stage_count, 
			self._definition['Curtis Stage'] == 1
		)
		stage_labels = [i.replace('Stage ', '') for i in stage_labels]
		for label in stage_labels:
			scope[label] = [0] * self._data_col_count
		return scope

	@property
	def table_map(self):
		"""OrderedDict: A map of ``TableCheckboxes`` that correspond to the 
		project scope.

		Example
		-------
		scope 		>>> {'1' : [0, 1]}
		table_map	>>> {'1' : [TableCheckbox(checked=False), TableCheckbox(checked=True)]}

		"""
		return self._table_map

	@table_map.setter
	def table_map(self, scope):
		"""
		Parameters
		----------
		scope : OrderedDict

		"""
		table_map = OrderedDict()
		for stage in self.scope:
			table_map[stage] = []
			for item in self.scope[stage]:
				if item == 1:
					table_map[stage].append(TableCheckBox(checked=True))
				else:
					table_map[stage].append(TableCheckBox())
		self._table_map = table_map

	def _on_edit_stage_count(self, stage_count):
		"""Update the view table per user input.

		Parameters
		----------
		stage_count : int or str

		"""
		try:
			# - When called at startup -
			# This is structured so that existing scopes are not modified prior
			# to filling the view Table.
			if type(stage_count) is int:
				self.table_map = self.scope
				self.view.set_rows(self.table_map, self._col_count)

			else:
				# - When input is changed by user -
				stage_count = int(stage_count) if int(stage_count) > 0 else int('')
				self.scope = stage_count
				self.table_map = self.scope
				self.view.set_rows(self.table_map, self._col_count)

		except ValueError:
			# Invalid literal for int() with base 10
			self.view.table.setRowCount(0)

	def _on_click_ok(self):
		"""Save ``Table`` data to the project file."""
		try:
			self.scope = self.table_map
			self._data.scope = self.scope
			self._data.save_project()
		except IOError as error:
			ExceptionMessageBox(error).exec_()
		else:
			self.view.accept()


if __name__ == '__main__':
	# For test
	app = QtGui.QApplication(sys.argv)


	# Get test data
	test_dir = 'C:\\Users\\mcclbra\\Desktop\\development\\rotoworks\\tests'
	# test_file = '123123_Phase1_CentrifugalCompressor.rw'
	test_file = '123123_Phase1_SteamTurbine.rw'
	data = Data()
	data.open_project(os.path.join(test_dir, test_file))
	# print data.definition, data.scope


	# Test ScopeView
	# -------------------
	# view = ScopeView()
	# view.exec_()


	# Test ScopeController
	# -------------------------
	controller = ScopeController(data)
	controller.view.exec_()