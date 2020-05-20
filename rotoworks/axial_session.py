#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import sys
from PyQt4 import QtGui, QtCore
from pyqtauto.widgets import DialogButtonBox, Dialog
from machine import Rotor
from core import Path, Image
from data import Data
from inspection import Axial
from view import DuelingListBoxView, InspectionCommandView, InputListView


__author__ = 'Brandon McCleary'


class AxialSessionView(Dialog):
	"""
	Displays the axial inspection window.

	Attributes
	----------
	input : DuelingListBoxView
	cmd : InspectionCommandView

	"""
	def __init__(self):
		super(AxialSessionView, self).__init__('Axial Session')
		self._build_gui()

	def _build_gui(self):
		"""Display widgets."""
		self.setFixedWidth(450)
		self.setMinimumHeight(300)
		self.layout.setSpacing(20)
		self.input = DuelingListBoxView(self.layout, ['Options', 'Session'])
		self.cmd = InspectionCommandView(self.layout)

	@property
	def selected_options(self):
		"""list: Selected items in the 'Options' ``ListBox``."""
		return self.input.source.selected_items

	@property
	def selected_session(self):
		"""list: Selected items in the 'Session' ``ListBox``."""
		return self.input.destination.selected_items


class AxialSessionController(object):
	"""
	Provides a functional GUI for defining an axial workscope, initiating 
	the inspection, and exporting the resulting data.

	Parameters
	----------
	data : Data

	Attributes
	----------
	view : AxialSessionView

	See Also
	--------
	data.Data

	"""
	def __init__(self, data):
		self._definition = data.definition
		self._scope = data.scope
		self._axial = Axial(self._definition['Path to Filename'])
		self._machine = Rotor.get_machine_type_as_object(
			self._definition['Machine Type']
		)

		# self._session_options is the model for self.view.input.source.
		self._session_options = Rotor.stage_names(
			len(self._scope),
			self._definition['Curtis Stage'] == 1
		)
		self._session_options.extend(['Balance Drum', 'Distance', 'Width'])

		# self._session_targets is the model for self.view.input.destination.
		self._session_targets = []

		# self._session_labels contains all unique distance/width labels in the
		# current session (self._session_targets)
		self._session_labels = []

		self.view = AxialSessionView()
		self.view.input.source.set_listbox(self._session_options)
		self.view.input.add_btn.clicked.connect(self._on_click_add)
		self.view.input.subtract_btn.clicked.connect(self._on_click_subtract)
		self.view.cmd.start_btn.clicked.connect(self._on_click_start)
		self.view.cmd.finish_btn.clicked.connect(self._on_click_finish)
	
	def _update_view(self):
		"""Refresh widgets."""
		self.view.input.destination.set_listbox(self._session_targets)

	def _on_click_add(self):
		"""Process a request to add selected options to the session."""
		options = self.view.selected_options
		# Weed out options already in session
		options = [i for i in options if i not in self._session_targets]
		for i in range(len(options)):
			item = options[i]

			if item == 'Distance' or item == 'Width':
				prompt = PromptDimLabels(item, self._session_labels)
				if prompt.exec_():
					for label in prompt.labels:
						self._session_targets.append('%s %s' % (item, label))
						self._session_labels.append(label.split('*')[0])
			else:
				self._session_targets.append(item)

		self._update_view()

	def _on_click_subtract(self):
		"""Process a request to remove selected items from the session."""
		items = self.view.selected_session
		# Extract alpha labels from selected items
		labels = [
			i.split(' ')[-1] for i in items 
			if i.split(' ')[0] == 'Distance' 
			or i.split(' ')[0] == 'Width'
		]
		# Remove selected items from model
		self._session_targets = [
			i for i in self._session_targets if i not in items
		]
		# Remove selected labels from model
		self._session_labels = [
			i for i in self._session_labels if i not in labels
		]
		self._update_view()

	def _on_click_start(self):
		"""Initiate a PolyWorks inspection."""
		self._axial.current_session = [
			self._session_targets, 
			self._machine, 
			self._scope
		]
		self._axial.publish()
		del self._axial.current_session
		self._session_targets = []
		self._session_labels = []
		self._update_view()
		self._axial.macro_exec(
			self._axial.MACRO_IN,
			self._axial.SCOPE_FILE,
			Path.MACROS
		)

	def _on_click_finish(self):
		"""Produce inspection output and close the view window."""
		self._axial.macro_exec(
			self._axial.MACRO_OUT,
			self._axial.OUTPUT_FILE,
			Path.MACROS
		)
		self.view.accept()


class PromptDimLabels(Dialog):
	"""
	A prompt for 'Distance' or 'Width' label inputs.

	Parameters
	----------
	context : str
	unavailable : list

	Attributes
	----------
	label : list
		Accepted dimension labels.

	"""
	def __init__(self, context, unavailable=[]):
		self._context = context
		self._unavailable = unavailable
		self.labels = []
		super(PromptDimLabels, self).__init__('Input needed')
		self._build_gui()

	def _build_gui(self):
		"""Display widgets."""
		self._view = InputListView(
			self.layout, '%s Label:' % self._context, Image.DOWNLOAD
		)
		self._view.input_le.returnPressed.connect(self._add_labels)
		self._view.enter_btn.clicked.connect(self._add_labels)
		self._btns = DialogButtonBox(self.layout, 'okcancel')
		self._btns.accepted.connect(self.accept)
		self._btns.rejected.connect(self.close)
		self._view.connect(
			QtGui.QShortcut(
				QtGui.QKeySequence(QtCore.Qt.Key_Delete), 
				self._view.listbox
			), 
			QtCore.SIGNAL('activated()'), 
			self._on_click_delete
		)

	def _input_is_valid(self, text):
		"""Returns True if text is a valid input.

		Parameters
		----------
		text : str

		"""
		if len(text) == 0 or not text[0].isalpha():
			return

		# Strip whitespace and split by '*'
		text_split = filter(str.strip, text.split('*'))
		label = text_split[0]

		# Evaluate label validity
		if (label not in self._unavailable 
				and label not in self.labels and label.isalpha()):
			try:
				modifier = text_split[1]
			except IndexError:
				return True	
			else:
				if modifier == 'H':
					return True	

	def _add_labels(self):
		"""Update approved label model and view."""
		text = str(self._view.input_le.text()).upper()
		if self._input_is_valid(text):
			self.labels.append(text)
		self._view.set_listbox(self.labels)

	def _on_click_delete(self):
		"""Remove existing labels triggered by DELETE key."""
		items = self._view.selected_items
		for item in items:
			try:
				self.labels.remove(item)
			except ValueError:
				pass
		self._view.set_listbox(self.labels)


if __name__ == '__main__':
	# For test
	app = QtGui.QApplication(sys.argv)
	# app.setWindowIcon(QtGui.QIcon(QtGui.QPixmap(Image.LOGO)))
	app.setStyle(QtGui.QStyleFactory.create('cleanlooks'))


	# Get test data
	test_dir = os.path.join(
		os.path.dirname(os.path.dirname(__file__)), 
		'tests'
	)
	# test_file = '123123_Phase1_CentrifugalCompressor.rw'
	test_file = '123123_Phase1_SteamTurbine.rw'
	data = Data()
	data.open_project(os.path.join(test_dir, test_file))


	# Test AxialSessionView
	# -------------------
	# view = AxialSessionView()
	# view.exec_()


	# Test AxialSessionController
	# -------------------------
	controller = AxialSessionController(data)
	controller.view.exec_()

	



