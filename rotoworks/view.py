#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
from PyQt4 import QtGui, QtCore
from pyqtauto.widgets import ImageButton, Dialog, Spacer, GenericButton, ListBox
from core import Image


__author__ = 'Brandon McCleary'


class InputListView(QtGui.QHBoxLayout):
	"""
	A view with ``QLineEdit``, ``ImageButton``, and ``ListBox`` interaction.

	Parameters
	----------
	parent : QVBoxLayout
	label : str
		QLabel text.
	btn_img : str
		Absolute path to ``ImageButton`` image.

	Attributes
	----------
	input_le : QLineEdit
	enter_btn : ImageButton
	listbox : ListBox

	"""
	def __init__(self, parent, label, btn_img):
		self._parent = parent
		self._label = label
		self._btn_img = btn_img
		super(InputListView, self).__init__()
		self._build_gui()

	def _build_gui(self):
		"""Display widgets."""
		self.addWidget(QtGui.QLabel(self._label))
		self.input_le = QtGui.QLineEdit()
		self.addWidget(self.input_le)
		self.enter_btn = ImageButton(self._btn_img, self)
		self._parent.addLayout(self)
		self.listbox = ListBox()
		self._parent.addWidget(self.listbox)

	def set_listbox(self, items):
		"""Set ListBox items and clear QLineEdit input.

		Parameters
		----------
		items : list

		"""
		self.listbox.set_(items)
		self.input_le.clear()

	@property
	def selected_items(self):
		"""list: Selected ListBox items."""
		return self.listbox.selected_items


class InspectionCommandView(QtGui.QHBoxLayout):
	"""
	A view with start and finish ``GenericButtons`` aligned to the right.

	Parameters
	----------
	parent : QVBoxLayout

	Attributes
	----------
	start_btn : GenericButton
	finish_btn : GenericButton

	"""
	def __init__(self, parent):
		self._parent = parent
		super(InspectionCommandView, self).__init__()
		self._build_gui()

	def _build_gui(self):
		"""Display widgets."""
		self.addStretch(1)
		self.setSpacing(10)
		self.start_btn = GenericButton('Start', self)
		self.finish_btn = GenericButton('Finish', self)
		self._parent.addLayout(self)


class ListBoxHeaderView(QtGui.QVBoxLayout):
	"""
	A view that displays a ``ListBox`` with a header label.

	Parameters
	----------
	parent : QLayout subclass
	header : str

	"""
	def __init__(self, parent, header):
		self._parent = parent
		self._header = header
		super(ListBoxHeaderView, self).__init__()
		self._build_gui()
	
	def _build_gui(self):
		"""Display widgets."""
		self.setSpacing(5)
		self._label = QtGui.QLabel(self._header)
		self._label.setStyleSheet('background: white')
		self._label.setAlignment(QtCore.Qt.AlignCenter)
		self._listbox = ListBox()
		self.addWidget(self._label)
		self.addWidget(self._listbox)
		self._parent.addLayout(self)

	@property
	def selected_items(self):
		return self._listbox.selected_items

	@property
	def items(self):
		return self._listbox.items

	def set_listbox(self, items):
		self._listbox.set_(items)


class DuelingListBoxView(QtGui.QHBoxLayout):
	"""
	A view that displays two ``ListBoxes`` separated by two ``ImageButtons``
	that move data from one ``ListBox`` to another.

	Parameters
	----------
	parent : QLayout subclass
	headers : list

	Attributes
	----------
	source : ListBoxHeaderView
	add_btn : ImageButton
	subtract_btn : ImageButton
	destination : ListBoxHeaderView

	"""
	def __init__(self, parent, headers):
		self._parent = parent
		self._headers = headers
		super(DuelingListBoxView, self).__init__()
		self._build_gui()

	def _build_gui(self):
		"""Display widgets."""
		self.source = ListBoxHeaderView(self, self._headers[0])
		self._btn_layout = QtGui.QVBoxLayout()
		self._btn_layout.addItem(Spacer())
		self.add_btn = ImageButton(Image.FORWARD, self._btn_layout)
		self.subtract_btn = ImageButton(Image.BACK, self._btn_layout)
		self._btn_layout.addItem(Spacer())
		self.addLayout(self._btn_layout)
		self.destination = ListBoxHeaderView(self, self._headers[1])
		self._parent.addLayout(self)


class HomeView(QtGui.QVBoxLayout):
	"""
	The view that is displayed upon application startup.

	Parameters
	----------
	parent : QWidget or subclass

	Attributes
	----------
	new_btn : IconButton
	open_btn : IconButton
	info_btn : IconButton

	"""
	def __init__(self, parent):
		self._parent = parent
		super(HomeView, self).__init__(self._parent)
		self._build_gui()

	def _build_gui(self):
		"""Display widgets."""
		self._logo_layout = QtGui.QHBoxLayout()
		self._logo_layout.setAlignment(QtCore.Qt.AlignCenter)
		self._logo_pm = QtGui.QPixmap(Image.LOGO)
		self._logo_lb = QtGui.QLabel()
		self._logo_lb.setPixmap(self._logo_pm)
		self._logo_layout.addWidget(self._logo_lb)
		self._btn_layout = QtGui.QHBoxLayout()
		self.new_btn = IconButton(
			'New',
			Image.NEW,
			self._btn_layout,
			50, 60
		)
		self.open_btn = IconButton(
			'Open',
			Image.OPEN,
			self._btn_layout,
			50, 60
		)
		self.info_btn = IconButton(
			'Info',
			Image.INFO,
			self._btn_layout,
			50, 60
		)
		self.addLayout(self._logo_layout)
		self.addLayout(self._btn_layout)


class IconButton(QtGui.QToolButton):
	"""
	A ``QToolButton`` with text below the icon.

	Parameters
	----------
	text : str
	icon_path : str
	parent : QLayout subclass
	width : int
	height : int
	
	"""
	def __init__(self, text, icon_path, parent, width, height):
		super(IconButton, self).__init__()
		self.setToolButtonStyle(QtCore.Qt.ToolButtonTextUnderIcon)
		self.setIcon(QtGui.QIcon(QtGui.QPixmap(icon_path)))
		self.setText(text)
		self.setFixedSize(width, height)
		parent.addWidget(self)


if __name__ == '__main__':
	# For test
	app = QtGui.QApplication(sys.argv)
	app.setStyle(QtGui.QStyleFactory.create('cleanlooks'))

	# Test InputListView
	# ------------------
	# dialog = Dialog('test')
	# layout = InputListView(dialog.layout, 'Search:', Image.DOWNLOAD)
	# dialog.exec_()


	# Test InspectionCommandView
	# ------------------
	# dialog = Dialog('test')
	# layout = InspectionCommandView(dialog.layout)
	# dialog.exec_()

	# Test DuelingListView
	# --------------------
	# dialog = Dialog('test')
	# view = DuelingListBoxView(dialog.layout, ['Options', 'Session'])
	# dialog.exec_()

	# Test HomeView
	# -------------
	widget = QtGui.QWidget()
	view = HomeView(widget)
	widget.show()
	app.exec_()