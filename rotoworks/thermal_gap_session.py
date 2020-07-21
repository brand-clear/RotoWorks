import sys
import os.path
from PyQt4 import QtGui
from pyqtauto.widgets import Dialog, DialogButtonBox, ExceptionMessageBox
from inspection import ThermalGap
from core import setup_logger
import logging
import csv


setup_logger()


class ThermalGapView(Dialog):
	"""
	Displays the Thermal Gap inspection window.

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
		self._value_map = {}
		self._headers = ['Name', 'Meas']
		super(ThermalGapView, self).__init__('Thermal Gap Session')
		self.layout.setSpacing(10)
		self._display_widget = QtGui.QWidget()
		self._form_layout = QtGui.QFormLayout(self._display_widget)
		self._add_new(1)
		self._scroll_area = QtGui.QScrollArea()
		self._scroll_area.setWidgetResizable(True)
		self._scroll_area.setMaximumHeight(400)
		self._scroll_area.setFrameShape(QtGui.QFrame.NoFrame)
		self._scroll_area.setWidget(self._display_widget)
		self.layout.addWidget(self._scroll_area)
		self.btns = DialogButtonBox(self.layout, 'okcancel')

	def _add_new(self, count):
		"""Insert next row into layout.

		Parameters
		----------
		count : int
			Number of existing inputs.

		"""
		label = 'TG%s' % count
		self._value_map[label] = QtGui.QLineEdit()
		self._value_map[label].setValidator(QtGui.QDoubleValidator(0.0, 1.0, 4))
		self._value_map[label].returnPressed.connect(self._on_press_return)
		self._form_layout.addRow(label, self._value_map[label])
		self._value_map[label].setFocus()

	def _on_press_return(self):
		count = len(self._value_map)
		self._add_new(count + 1)

	def get_input_data(self):
		"""Returns the 2D list of data headers, labels, and values."""
		data = [self._headers]
		for label in self._value_map.keys():
			data.append([label, str(self._value_map[label].text())])
		return data


class ThermalGapController(object):
	"""
	Provides a functional GUI for defining and serializing thermal gap 
	dimensions.

	Parameters
	----------
	data : Data

	Attributes
	----------
	view : ThermalGapView

	"""
	def __init__(self, data):
		self._tg = ThermalGap(data.path)
		self.view = ThermalGapView(data.path)
		self.view.btns.accepted.connect(self._save)
		self.view.btns.rejected.connect(self.view.close)

	def _save(self):
		"""Write user input to CSV file and close view."""
		input_data = self.view.get_input_data()
		try:
			with open(self._tg.OUTPUT_FILE, 'wb') as csvfile:
				csvwriter = csv.writer(csvfile)
				csvwriter.writerows(input_data)
		except IOError as error:
			logging.warning(error)
			ExceptionMessageBox(error).exec_()
		self.view.close()


if __name__ == '__main__':
	pass

	

