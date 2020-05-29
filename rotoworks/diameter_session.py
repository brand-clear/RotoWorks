#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import sys
import string
import itertools
from PyQt4 import QtGui, QtCore
from pyqtauto.widgets import Dialog, ImageButton
from view import InputListView, InspectionCommandView
from core import Image, Path
from machine import Rotor
from data import Data
from template import Template
from inspection import Diameter


__author__ = 'Brandon McCleary'


class DiameterSessionView(Dialog):
	"""
	Displays the diameter inspection window.

	Attributes
	----------
	input : InputListView
	cmd : InspectionCommandView
	label_range : list

	"""
	def __init__(self):
		super(DiameterSessionView, self).__init__('Diameter Session')
		self._build_gui()

	def _build_gui(self):
		"""Display widgets."""
		self.input = InputListView(
			self.layout, 
			'Dimension:', 
			Image.CLOUD
		)
		self.input.input_le.setValidator(
			QtGui.QRegExpValidator(QtCore.QRegExp("[a-z-A-Z-*]+"), self)
		)
		self.input.input_le.setMaxLength(7)
		self.input.enter_btn.setAutoDefault(False)
		self.input.enter_btn.setToolTip('Import')
		self.cmd = InspectionCommandView(self.layout)

	@property
	def label_range(self):
		"""list: QLineEdit input texts in all caps."""
		text = str(self.input.input_le.text()).upper()
		return filter(str.strip, text.split('-'))


class DiameterSessionController(object):
	"""
	Provides a functional GUI for defining a diametrical workscope, initiating 
	the inspection, and exporting the resulting data.

	Parameters
	----------
	definition : OrderedDict

	Attributes
	----------
	MODIFIERS : list
	view : DiameterSessionView

	See Also
	--------
	data.Data.definition

	"""

	# *H is a signal for hand measurements
	# *P is a signal for constraining planes
	MODIFIERS = ['*H', '*P']

	def __init__(self, definition):
		self._definition = definition
		self._machine = Rotor.get_machine_type_as_object(
			self._definition['Machine Type']
		)
		self._diameter = Diameter(self._definition['Path to Filename'])

		# Index _alphabet, the dimension label library, for label ranges
		self._alphabet = list(string.ascii_uppercase)
		self._alphabet.extend(
			[i+b for i in self._alphabet for b in self._alphabet]
		)

		# Initialize view and connect widgets with responsive actions
		self.view = DiameterSessionView()
		self.view.input.input_le.returnPressed.connect(self._on_click_enter)
		self.view.input.enter_btn.clicked.connect(self._on_click_import)
		self.view.cmd.start_btn.clicked.connect(self._on_click_start)
		self.view.cmd.finish_btn.clicked.connect(self._on_click_finish)
		self.view.connect(
			QtGui.QShortcut(
				QtGui.QKeySequence(QtCore.Qt.Key_Delete), 
				self.view.input.listbox
			), 
			QtCore.SIGNAL('activated()'), 
			self._on_click_delete
		)

	def _update_view(self):
		"""Refresh widgets."""
		self.view.input.set_listbox(self._diameter.current_session)

	def _on_click_enter(self):
		"""Process input and update view."""
		labels = self.view.label_range
		if len(labels) == 1:
			self._handle_single_input(labels[0])
		elif len(labels) == 2:
			self._handle_double_input(labels)
		self._update_view()

	def _on_click_delete(self):
		"""Remove the selected items from the measurement session."""
		items = self.view.input.selected_items
		session = self._diameter.current_session
		session = [i for i in session if i not in items]
		del self._diameter.current_session
		self._diameter.current_session = session
		self._update_view()

	def _handle_single_input(self, label):
		"""Add a dimension label to the current measurement session.
		
		Parameters
		----------
		label : str
		
		"""
		text, mod = self._get_valid_input(label)
		if text is not None and mod is None:
			self._diameter.current_session = [text]
		elif text is not None and mod is not None:
			self._diameter.current_session = [text + mod]

	def _handle_double_input(self, labels):
		"""Add a range of dimension labels to the current measurement session.

		Parameters
		----------
		labels : list

		"""
		first, fmod = self._get_valid_input(labels[0])
		sec, smod = self._get_valid_input(labels[1])
		if first is None or sec is None or fmod is not None:
			return

		label_range = self._get_label_range(first, sec)
		if label_range is not None:
			# Update the session with a range of labels
			if smod is None:
				self._diameter.current_session = label_range
			else:
				self._diameter.current_session = [i+smod for i in label_range]
			
	def _get_valid_input(self, label):
		"""Validate the user input.

		Parameters
		----------
		label : str

		Returns
		-------
		str or None, str or None
			A validated label without a modifier followed by the corresponding
			modifier.

		"""
		if len(label) <= 2 and label.isalpha():
			# No modifier
			return label, None

		label_split = label.split('*')
		if len(label_split) == 2:
			# Check for valid modifier
			lb = label_split[0]
			mod = label_split[1]
			if lb.isalpha() and mod.isalpha() and len(lb) <= 2:
				modifier = '*%s' % mod
				if modifier in self.MODIFIERS:
					return lb, modifier

		return None, None

	def _get_label_range(self, first, sec):
		"""Get an alphabetical range of dimension labels.

		Parameters
		----------
		first : str
			An alpha sequence, indexed to set the start of the range.
		sec : str
			An alpha sequence, indexed to set the end of the range.

		Returns
		-------
		list or None
			If not ``None``, a subset of the alphabet.

		"""
		first_index = self._alphabet.index(first)
		sec_index = self._alphabet.index(sec)
		if first_index < sec_index:
			return self._alphabet[first_index : sec_index + 1]
		return None

	def _on_click_start(self):
		"""Initiate a PolyWorks inspection."""
		self._diameter.publish()
		self._diameter.macro_exec(
			self._diameter.MACRO_IN, 
			self._diameter.SCOPE_FILE,
			Path.MACROS
		)
		del self._diameter.current_session
		self._update_view()

	def _on_click_finish(self):
		"""Produce inspection output and close the view window."""
		self._diameter.macro_exec(
			self._diameter.MACRO_OUT,
			self._diameter.OUTPUT_FILE,
			Path.MACROS
		)
		self.view.accept()

	def _on_click_import(self):
		"""Send an existing workscope template to PolyWorks for inspection."""
		if Template.copied(self._definition['Path to Filename'], 'Diameter'):
			self._diameter.macro_exec(
				self._diameter.MACRO_IN,
				self._diameter.SCOPE_FILE,
				Path.MACROS
			)

if __name__ == '__main__':
	# For test
	app = QtGui.QApplication(sys.argv)
	app.setStyle(QtGui.QStyleFactory.create('cleanlooks'))


	# Get test data
	test_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'tests')
	test_file = '123123_Phase1_CentrifugalCompressor.rw'
	data = Data()
	data.open_project(os.path.join(test_dir, test_file))


	# Test DiameterSessionView
	# ------------------------
	# dialog = DiameterSessionView()
	# dialog.exec_()


	# Test DiameterSessionController
	# ------------------------------
	controller = DiameterSessionController(data.definition)
	controller.view.exec_()