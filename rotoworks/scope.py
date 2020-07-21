from PyQt4 import QtGui
from pyqtauto.widgets import (TableItem, Table, DialogButtonBox, TableCheckBox, 
	ExceptionMessageBox)
from data import TableMap
from core import setup_logger
import logging


setup_logger()


class ScopeView(QtGui.QWidget):
	"""
	Displays project workscope GUI.

	Attributes
	----------
	stage_le : QLineEdit
		Accepts the number of stages in a machine.

	btn : DialogButtonBox
		Clicked to serialize the updated data model.

	"""

	_SELECT_ALL_ROW_OFFSET = 1
	_STAGE_COLUMN_OFFSET = 1

	def __init__(self):
		super(ScopeView, self).__init__()
		self._main_layout = QtGui.QVBoxLayout(self)
		self._main_layout.setSpacing(20)
		self._form_layout = QtGui.QFormLayout()
		# Init widgets
		self._filename_lb = QtGui.QLabel()
		self.stage_le = QtGui.QLineEdit()
		self.table = Table()
		# Configure widgets
		self.stage_le.setFixedWidth(50)
		self.stage_le.setValidator(QtGui.QIntValidator())
		self.stage_le.setMaxLength(2)
		self.table.verticalHeader().hide()
		# Add widgets to layout
		self._form_layout.addRow(QtGui.QLabel('Project:'), self._filename_lb)
		self._form_layout.addRow(QtGui.QLabel('Stage Count:'), self.stage_le)
		self._main_layout.addLayout(self._form_layout)
		self._main_layout.addWidget(self.table)
		self.btn = DialogButtonBox(self._main_layout)

	def _select_all(self, checkbox, state):
		"""Change the checked state of an entire column.

		Parameters
		----------
		checkbox : TableCheckBox
			The top row widget that was clicked.

		state : bool

		"""
		parent_col = self.table.indexAt(checkbox.parent().pos()).column()
		for check in self.table.findChildren(QtGui.QCheckBox):
			if self.table.indexAt(check.parent().pos()).column() == parent_col:
				check.setChecked(state)

	def _on_click_top_row(self):
		"""Initiate select-all functionality on the ``Table`` object."""
		checkbox = self.sender()
		self._select_all(checkbox, checkbox.isChecked())

	def _insert_select_all_row(self, col_count):
		"""
		Parameters
		----------
		col_count : int

		"""
		for col in range(self._STAGE_COLUMN_OFFSET, col_count):
			self.table.setCellWidget(0, col, TableCheckBox(
				response=self._on_click_top_row).widget
			)
		
	def _insert_feature_rows(self, table_map, col_count):
		"""
		Parameters
		----------
		table_map : TableMap

		col_count : int

		"""
		row = self._SELECT_ALL_ROW_OFFSET
		for stage in table_map.data.keys():
			self.table.setItem(row, 0, TableItem(stage))
			for col in range(self._STAGE_COLUMN_OFFSET, col_count):
				self.table.setCellWidget(row, col, 
					table_map.data[stage][col-1].widget)
			row += 1

	def set_state(self, filename, col_headers, stage_count):
		"""		
		Parameters
		----------
		filename : str
			Name of the data file.

		col_headers : list
			Table column header names.

		stage_count : int
			The number of stages in a machine.

		"""
		self._filename_lb.setText(filename)
		self.table.update(col_headers)
		self.stage_le.setText(str(stage_count))

	def set_rows(self, table_map, col_count):
		"""Update ``Table`` rows.

		Parameters
		----------
		table_map : TableMap

		col_count : int

		"""
		row_count = len(table_map.data) + self._SELECT_ALL_ROW_OFFSET
		if row_count > 1:
			self.table.setRowCount(row_count)
			self._insert_select_all_row(col_count)
			self._insert_feature_rows(table_map, col_count)


class ScopeController(object):
	"""
	Provides a functional GUI for establishing a project workscope.

	A project workscope contains the action items for axial inspections and is
	saved in the project data file.

	Attributes
	----------
	view : ScopeView
		Provides GUI.

	"""
	def __init__(self):
		self._data = None
		self.view = ScopeView()

	def init_state(self, data):
		"""Set view state at startup.

		Parameters
		----------
		data : Data
			Instance data model.

		"""
		# Initialize instance data
		stage_count = len(data.scope.data)
		self._data = data
		self._col_count = len(self._data.features)
		self.table_map = TableMap(
			self._data.is_curtis, 
			len(self._data.features)
		)
		self.table_map.init(stage_count)

		# Update TableMap to existing scope
		if stage_count > 0:
			self.table_map.update(self._data.scope)

		# Set view state
		self.view.setMinimumWidth(90 * self._col_count)
		self.view.set_state(
			self._data.filename, 
			self._data.features, 
			stage_count
		)
		self.view.set_rows(self.table_map, self._col_count)
		self.view.stage_le.textChanged.connect(self._on_edit_stage_count)
		
	def _on_edit_stage_count(self, stage_count):
		"""Update the view ``Table``.

		Parameters
		----------
		stage_count : str

		"""
		try:
			if stage_count == str(0):
				raise ValueError
			self.table_map.init(int(stage_count))
			self.view.set_rows(self.table_map, self._col_count)
		except ValueError:
			# Invalid literal for int() with base 10; called when no input or
			# when input is 0.
			self.view.table.setRowCount(0)	

	def save(self):
		"""Save updates to the project file.
		
		Returns
		-------
		Data
			Instance data model.

		"""
		try:
			self._data.scope.update(self.table_map)
			self._data.save()
		except IOError as error:
			logging.warning(error)
			ExceptionMessageBox(error).exec_()
		else:
			return self._data


if __name__ == '__main__':
	pass