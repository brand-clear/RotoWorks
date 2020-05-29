#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import sys
from collections import OrderedDict
from PyQt4 import QtGui, QtCore
from pyqtauto.widgets import (
	Dialog, ComboBox, 
	DialogButtonBox, 
	ExceptionMessageBox
)
from sulzer.extract import Extract, ProjectsFolderRootError
from pywinscript.win import create_folder
from inspection import Inspection
from machine import Rotor
from core import Path
from data import Data


__author__ = 'Brandon McCleary'


class DefinitionView(Dialog):
	"""
	Displays the project definition window.

	Parameters
	----------
	phases : list
	machine_types : list
	machine_sub_types : list

	Attributes
	----------
	machine_cb : ComboBox
	ok : DialogButtonBox
	job_num : str
	phase : str
	machine_type : str
	machine_sub_type : str
	nickname : str
	is_curtis : bool

	"""
	def __init__(self, phases, machine_types, machine_sub_types):
		super(DefinitionView, self).__init__('Project Definition')
		self._build_gui(phases, machine_types, machine_sub_types)

	def _build_gui(self, phases, machine_types, machine_sub_types):
		"""Fill and display widgets.

		Parameters
		----------
		phases : list
		machine_types : list
		sub_types : list

		"""
		# Init widgets
		self._form = QtGui.QFormLayout()
		self._job_le = QtGui.QLineEdit()
		self._job_le.setValidator(QtGui.QIntValidator())
		self._job_le.setMaxLength(6)
		self._phase_cb = ComboBox(phases)
		self.machine_cb = ComboBox(machine_types)
		self._sub_cb = ComboBox(machine_sub_types)
		self._name_le = QtGui.QLineEdit()
		self._name_le.setValidator(
			QtGui.QRegExpValidator(QtCore.QRegExp("[a-z-A-Z_0-9]+"), self)
		)
		# Place widgets
		self._form.addRow(QtGui.QLabel('Job Number:'), self._job_le)
		self._form.addRow(QtGui.QLabel('Phase:'), self._phase_cb)
		self._form.addRow(QtGui.QLabel('Machine:'), self.machine_cb)
		self._form.addRow(QtGui.QLabel('Sub Type:'), self._sub_cb)
		self._form.addRow(QtGui.QLabel('Nickname:'), self._name_le)
		self.layout.addLayout(self._form)
		self.ok = DialogButtonBox(self.layout)

	def display_optional_gui(self):
		# Optional widgets are only valid for Steam Turbine machines.
		self._curtis_chk = QtGui.QCheckBox()
		self._curtis_lb = QtGui.QLabel('Curtis Stage:')
		self._form.insertRow(3, self._curtis_lb, self._curtis_chk)

	def remove_optional_gui(self):
		# Optional widgets are only valid for Steam Turbine machines.
		try:
			self._curtis_chk.deleteLater()
			self._curtis_lb.deleteLater()
		except (RuntimeError, AttributeError):
			pass

	@property
	def job_num(self):
		"""str: The 6-digit job number."""
		return str(self._job_le.text())

	@property
	def phase(self):
		"""str: The inspection phase for this project."""
		return str(self._phase_cb.currentText())

	@property
	def machine_type(self):
		"""str: The type of machine for this project."""
		return str(self.machine_cb.currentText())

	@property
	def machine_sub_type(self):
		"""str: A sub-type of the machine for this project."""
		return str(self._sub_cb.currentText())

	@property
	def nickname(self):
		"""str: A name used to help distinguish this project from others."""
		return str(self._name_le.text())

	@property
	def is_curtis(self):
		"""bool : True if this machine has a curtis stage.

		Notes
		-----
		Curtis stages are only valid for Steam Turbine machines.

		"""
		try:
			return self._curtis_chk.isChecked()
		except AttributeError:
			return False


class DefinitionController(object):
	"""
	Provides a functional GUI for creating a project definition file.

	Parameters
	----------
	data : Data
		Active data model.

	Attributes
	----------
	view : DefinitionView

	"""
	def __init__(self, data):
		self._data = data
		self.view = DefinitionView(
			Inspection.PHASES, 
			Rotor.get_machine_types(), 
			Rotor.get_machine_sub_types()
		)
		self.view.machine_cb.activated.connect(self._on_select_machine)
		self.view.ok.accepted.connect(self._on_click_ok)

	def _on_select_machine(self):
		"""Handle optional GUI."""
		if self.view.machine_type == 'Steam Turbine':
			self.view.display_optional_gui()
		else:
			self.view.remove_optional_gui()

	def _get_project_folder(self, job_num, phase):
		"""Get the absolute path to a ROTOWORKS project folder.

		Parameters
		----------
		job_num : str
		phase : str
		
		Returns
		-------
		rw_project_folder : str

		Raises
		------
		ProjectsFolderRoot
			If the PROJECTS FOLDER root cannot be found. This path is used to 
			help determine the ROTOWORKS path.
		WindowsError
			If a ROTOWORKS folder could not be created due to a missing link.

		"""
		# Search for the PROJECTS FOLDER root
		try:
			pfolder_root = Extract.projects_folder_root(job_num)
		except ProjectsFolderRootError as error:
			msg = 'Make sure this job has a valid PROJECTS FOLDER and try again'
			error.message = "%s\n%s." % (error.message, msg)
			raise error

		# Create the ROTOWORKS project folder
		try:
			rw_job_root = create_folder(
				os.path.join(Path.JOBS, os.path.basename(pfolder_root))
			)
			rw_job_folder = create_folder(os.path.join(rw_job_root, job_num))
			rw_project_folder = create_folder(os.path.join(rw_job_folder, phase))
		except WindowsError as error:
			raise error

		return rw_project_folder

	def _get_definition_filename(
			self, job_num, phase, machine_type, machine_sub_type, nickname
		):
		"""Get the filename that will store a ROTOWORKS project.

		Parameters
		----------
		job_num : str
		phase : str
		machine_type : str
		machine_sub_type : str
		nickname : str

		Returns
		-------
		filename : str

		"""
		filename = '%s_%s_%s_%s_%s.rw' % (
			job_num,
			phase,
			machine_type,
			machine_sub_type,
			nickname
		)
		# Strip whitespace and duplicate underscores
		filename = filename.replace(' ', '')
		filename = filename.replace('__', '_')
		filename = filename.replace('_.', '.')
		return filename

	def _on_click_ok(self):
		"""Process project definition request."""
		# Set up directory
		try:
			folder = self._get_project_folder(
				self.view.job_num, 
				self.view.phase
			)
		except (ProjectsFolderRootError, WindowsError) as error:
			ExceptionMessageBox(error).exec_()
			return

		# Get project filepath
		filename = self._get_definition_filename(
			self.view.job_num,
			self.view.phase,
			self.view.machine_type,
			self.view.machine_sub_type,
			self.view.nickname
		)
		filepath = os.path.join(folder, filename)

		# Prompt user if project conflict is found
		if os.path.exists(filepath):
			if ExistingProjectError.proceed(self.view) != QtGui.QMessageBox.Yes:
				return

		# Build definition
		self._data.definition = OrderedDict([
			('Job Number', self.view.job_num),
			('Phase', self.view.phase),
			('Machine Type', self.view.machine_type),
			('Curtis Stage', self.view.is_curtis),
			('Path to Filename', folder),
			('Filename', filename),
			('Ref Filename', None)
		])

		# Save definition to file
		try:
			self._data.save_project()
		except IOError as error:
			ExceptionMessageBox(error).exec_()
		else:
			self.view.accept()


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
		parent : Dialog

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
	# For test
	app = QtGui.QApplication(sys.argv)


	# Test DefinitionView
	# -------------------
	# view = DefinitionView(
	# 	Inspection.PHASES, 
	# 	Rotor.get_machine_types(), 
	# 	Rotor.get_machine_sub_types()
	# )
	# view.exec_()


	# Test DefinitionController
	# -------------------------
	controller = DefinitionController(Data())
	controller.view.exec_()


	# Test ExistingProjectError
	# ExistingProjectError.proceed(None)