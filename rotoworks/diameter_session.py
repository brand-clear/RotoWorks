import os
import sys
import string
import itertools
from PyQt4 import QtGui, QtCore
from pyqtauto.widgets import Dialog, ImageButton
from view import InputListView, InspectionCommandView
from inspection import Diameter
from template import Template
from core import Image, Path
from machine import Rotor
from data import Data


class DiameterSessionView(Dialog):
	"""
	Displays the diameter inspection window.

	Attributes
	----------
	label_range : list

	"""
	def __init__(self, return_callback, import_callback, start_callback, 
			finish_callback, delete_callback):
		self._return_callback = return_callback
		self._import_callback = import_callback
		self._start_callback = start_callback
		self._finish_callback = finish_callback
		self._delete_callback = delete_callback
		super(DiameterSessionView, self).__init__('Diameter Session')
		self._build_gui()

	def _build_gui(self):
		"""Display widgets."""
		self._input = InputListView(self.layout, 'Dimension:', Image.IMPORT_LEFT)
		self._input.input_le.setValidator(
			QtGui.QRegExpValidator(QtCore.QRegExp("[a-z-A-Z-*]+"), self)
		)
		self._input.input_le.setMaxLength(7)
		self._input.enter_btn.setAutoDefault(False)
		self._input.enter_btn.setToolTip('Import')
		self._cmd = InspectionCommandView(self.layout)
		self._input.input_le.returnPressed.connect(self._return_callback)
		self._input.enter_btn.clicked.connect(self._import_callback)
		self._cmd.start_btn.clicked.connect(self._start_callback)
		self._cmd.finish_btn.clicked.connect(self._finish_callback)
		self.connect(
			QtGui.QShortcut(
				QtGui.QKeySequence(QtCore.Qt.Key_Delete), 
				self._input.listbox
			), 
			QtCore.SIGNAL('activated()'), 
			self._delete_callback
		)

	@property
	def label_range(self):
		"""list: QLineEdit input texts in all caps."""
		text = str(self._input.input_le.text()).upper()
		return filter(str.strip, text.split('-'))

	@property
	def selected_items(self):
		"""list: Selected ``QListWidget`` items."""
		return self._input.selected_items

	def update_labels(self, labels):
		"""Refresh ``QListWidget`` items.

		Parameters
		----------
		labels : list

		"""
		self._input.set_listbox(labels)


class DiameterSessionController(object):
	"""
	Provides a functional GUI for defining a diametrical workscope, initiating 
	the inspection, and exporting the resulting data.

	Parameters
	----------
	data : Data

	Attributes
	----------
	MODIFIERS : list
	view : DiameterSessionView

	"""
	# *H is a signal for hand measurements
	# *P is a signal for constraining planes
	MODIFIERS = ['*H', '*P']

	def __init__(self, data):
		self._data = data
		self._diameter = Diameter(self._data.path)
		self._diameter.polyworks.connect_to_inspector()
		self._alphabet = list(string.ascii_uppercase)
		self._alphabet.extend(
			[i+b for i in self._alphabet for b in self._alphabet]
		)
		self.view = DiameterSessionView(
			self._on_click_enter,
			self._on_click_import,
			self._on_click_start,
			self._on_click_finish,
			self._on_click_delete
		)

	def _update_view(self):
		"""Refresh widgets."""
		self.view.update_labels(self._diameter.current_session)

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
		items = self.view.selected_items
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
		if Template.copied(self._data.path, 'Diameter'):
			self._diameter.macro_exec(
				self._diameter.MACRO_IN,
				self._diameter.SCOPE_FILE,
				Path.MACROS
			)

if __name__ == '__main__':
	pass