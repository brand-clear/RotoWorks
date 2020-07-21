import sys
import os.path
from collections import OrderedDict
from PyQt4 import QtGui, QtCore
from pyqtauto.widgets import ComboBox, DialogButtonBox, ExceptionMessageBox
from sulzer.extract import ProjectsFolderRootError
from inspection import Inspection
from machine import Rotor
from project import Project
from core import setup_logger
import logging


setup_logger()


class DefinitionView(QtGui.QWidget):
	"""
	Displays project definition GUI.

	Attributes
	----------
	job_num : str

	phase : str

	machine_type : str

	machine_sub_type : str

	nickname : str

	is_curtis : bool

	btn : DialogButtonBox
		Clicked to create new project.

	"""
	def __init__(self):
		super(DefinitionView, self).__init__()
		self._main_layout = QtGui.QVBoxLayout(self)
		self._form_layout = QtGui.QFormLayout()
		self._form_layout.setSpacing(20)
		# Init widgets
		self._job_le = QtGui.QLineEdit()
		self._phase_cb = ComboBox(Inspection.PHASES)
		self._machine_cb = ComboBox(Rotor.get_machine_types())
		self._sub_cb = ComboBox(Rotor.get_machine_sub_types())
		self._name_le = QtGui.QLineEdit()
		# Configure widgets
		self._job_le.setValidator(QtGui.QIntValidator())
		self._job_le.setMaxLength(6)
		self._name_le.setValidator(
			QtGui.QRegExpValidator(QtCore.QRegExp("[a-z-A-Z_0-9]+"), self)
		)
		self._machine_cb.activated.connect(self._on_select_machine)
		# Add widgets to layout
		self._form_layout.addRow(QtGui.QLabel('Job Number:'), self._job_le)
		self._form_layout.addRow(QtGui.QLabel('Phase:'), self._phase_cb)
		self._form_layout.addRow(QtGui.QLabel('Machine:'), self._machine_cb)
		self._form_layout.addRow(QtGui.QLabel('Sub Type:'), self._sub_cb)
		self._form_layout.addRow(QtGui.QLabel('Nickname:'), self._name_le)
		self._main_layout.addLayout(self._form_layout)
		self.btn = DialogButtonBox(self._main_layout)

	def _on_select_machine(self):
		"""Respond to machine selection with appropriate GUI."""
		if str(self._machine_cb.currentText()) == 'Steam Turbine':
			self._display_context_gui()
		else:
			self._remove_context_gui()

	def _display_context_gui(self):
		self._curtis_lb = QtGui.QLabel('Curtis Stage')
		self._curtis_chk = QtGui.QCheckBox()
		self._form_layout.insertRow(3, self._curtis_lb, self._curtis_chk)

	def _remove_context_gui(self):
		try:
			self._curtis_chk.deleteLater()
			self._curtis_lb.deleteLater()
		except (RuntimeError, AttributeError):
			pass

	def clear(self):
		"""Reset all inputs to default values."""
		self._job_le.setText('')
		self._phase_cb.setCurrentIndex(0)
		self._machine_cb.setCurrentIndex(0)
		self._sub_cb.setCurrentIndex(0)
		self._name_le.setText('')

	def focus(self):
		self._job_le.setFocus()

	@property
	def job_num(self):
		"""str: The 6-digit job number."""
		return str(self._job_le.text())

	@property
	def phase(self):
		"""str: The selected inspection phase."""
		return str(self._phase_cb.currentText())

	@property
	def machine_type(self):
		"""str: The selected machine type."""
		return str(self._machine_cb.currentText())

	@property
	def machine_sub_type(self):
		"""str: The selected machine sub type."""
		return str(self._sub_cb.currentText())

	@property
	def nickname(self):
		"""str: The nickname input."""
		return str(self._name_le.text())

	@property
	def is_curtis(self):
		"""bool : Refers to the machine having a Curtis Stage.

		Notes
		-----
		Curtis stages are only valid for Steam Turbines.

		"""
		try:
			return self._curtis_chk.isChecked()
		except AttributeError:
			return False


class DefinitionController(object):
	"""
	Provides a functional GUI for creating a project data file.

	Attributes
	----------
	view : DefinitionView
		Provides GUI.

	view.btn : DialogButtonBox
		Clicked to initiate creation of new project.

	"""
	def __init__(self):
		self.view = DefinitionView()

	def create(self):
		"""Setup filepaths and serialize data model.

		Returns
		-------
		data : Data
			Project data model.

		"""
		# Get inputs from view
		job_num = self.view.job_num
		phase = self.view.phase
		machine_type = self.view.machine_type
		subtype = self.view.machine_sub_type
		is_curtis = self.view.is_curtis
		nickname = self.view.nickname

		try:
			# Setup filepath
			filepath = Project.filepath(
				job_num, phase, machine_type, subtype, nickname
			)

			if os.path.exists(filepath):
				if ExistingProjectError.proceed(self.view) != QtGui.QMessageBox.Yes:
					return

			# Save data to file
			data = Project.init_data(
				job_num, phase, machine_type, is_curtis, filepath
			)
		except (IOError, ProjectsFolderRootError, WindowsError) as error:
			logging.warning(error)
			ExceptionMessageBox(error).exec_()
		else:
			return data


class ExistingProjectError(object):
	"""
	A QMessageBox warning for project conflicts.

	"""

	MESSAGE = 'The project you are trying to create already exists.\n'
	MESSAGE += 'Do you want to override the existing project?'

	@classmethod
	def proceed(cls, parent):
		"""Request project override input from the user.

		Parameters
		----------
		parent : QWidget subclass

		Returns
		-------
		QtGui.QMessageBox.Yes
			If user decides to override an existing project.
			
		QtGui.QMessageBox.Yes
			If user decides to cancel a project override.
		
		"""
		return QtGui.QMessageBox.warning(
			parent,
			cls.__name__,
			cls.MESSAGE,
			QtGui.QMessageBox.Yes | QtGui.QMessageBox.No
		)


if __name__ == '__main__':
	pass