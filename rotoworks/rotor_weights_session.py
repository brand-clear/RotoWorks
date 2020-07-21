import sys
import os.path
from collections import OrderedDict
from PyQt4 import QtGui
from pyqtauto.widgets import (Dialog, DialogButtonBox, ExceptionMessageBox, 
	Spacer)
from inspection import RotorWeight
from core import setup_logger
import logging
import csv


setup_logger()


class RotorWeightsView(Dialog):
	"""
	Displays the Rotor Weights inspection window.

	Parameters
	----------
	path : str
		The absolute path to a ROTOWORKS project directory.

	Attributes
	----------
	btns : DialogButtonBox

	"""
	def __init__(self, path):
		self._path = path
		self._headers = ['Name', 'Meas']
		self._te = 'TE Journal'
		self._nte = 'NTE Journal'
		self._oaw = 'Overall Weight (lbs):'
		self._name_map = OrderedDict([
			(self._te, 'TEW'),
			(self._nte, 'NTEW'),
			(self._oaw, 'OAW')
		])
		super(RotorWeightsView, self).__init__('Rotor Weights Session')
		self.layout.setSpacing(10)
		# Init widgets
		self._gui_map = OrderedDict([
			(self._te, QtGui.QLineEdit()),
			(self._nte, QtGui.QLineEdit()),
			(self._oaw, QtGui.QLabel('*')),
		])
		self._form_layout = QtGui.QFormLayout()
		for label in self._gui_map.keys():
			# Configure widgets
			try:
				self._gui_map[label].setValidator(QtGui.QIntValidator())
				self._gui_map[label].textEdited.connect(self._on_edit_text)
			except AttributeError:
				pass
			self._form_layout.addRow(label, self._gui_map[label])
		self.layout.addLayout(self._form_layout)
		self.layout.addItem(Spacer(ypad=30, ypolicy='min'))
		self.btns = DialogButtonBox(self.layout, 'okcancel')
		self.btns.accepted.connect(self.get_input_data)

	def _on_edit_text(self):
		"""Update overall weight value."""
		te = self._assign_zero_to_empty_string(self._gui_map[self._te].text())
		nte = self._assign_zero_to_empty_string(self._gui_map[self._nte].text())
		self._gui_map[self._oaw].setText(str(te + nte))

	def _assign_zero_to_empty_string(self, value):
		"""
		Parameters
		----------
		value : str

		"""
		try:
			return int(value)
		except ValueError:
			return 0

	def _get_weight(self, key):
		"""Get validated weight input from ``QLineEdit``.

		Parameters
		----------
		key : {self._te, self._nte, self.oaw}

		"""
		return str(self._assign_zero_to_empty_string(self._gui_map[key].text()))

	def get_input_data(self):
		"""Returns the 2D list of data headers, labels, and values."""
		data = [self._headers]
		for key in (self._te, self._nte, self._oaw):
			data.append([self._name_map[key], self._get_weight(key)])
		return data


class RotorWeightsController(object):
	"""
	Provides a functional GUI for defining and serializing Rotor Weight 
	dimensions.

	Parameters
	----------
	data : Data

	Attributes
	----------
	view : RotorWeightsView

	"""
	def __init__(self, data):
		self._weight = RotorWeight(data.path)
		self.view = RotorWeightsView(data.path)
		self.view.btns.accepted.connect(self._save)
		self.view.btns.rejected.connect(self.view.close)

	def _save(self):
		"""Write user input to CSV file and close view."""
		input_data = self.view.get_input_data()
		try:
			with open(self._weight.OUTPUT_FILE, 'wb') as csvfile:
				csvwriter = csv.writer(csvfile)
				csvwriter.writerows(input_data)
		except IOError as error:
			logging.warning(error)
			ExceptionMessageBox(error).exec_()
		self.view.close()


if __name__ == '__main__':
	pass




