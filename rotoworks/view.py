import sys
from PyQt4 import QtGui, QtCore
from pyqtauto.widgets import ImageButton, Dialog, Spacer, GenericButton, ListBox
from core import Image


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
		self.addWidget(QtGui.QLabel(self._label))
		self.input_le = QtGui.QLineEdit()
		self.addWidget(self.input_le)
		self.enter_btn = ImageButton(self._btn_img, self, flat=True)
		self.enter_btn.mysquare = 30
		self._parent.addLayout(self)
		self.listbox = ListBox()
		self._parent.addWidget(self.listbox)

	def set_listbox(self, items):
		"""Set ``ListBox`` items and clear ``QLineEdit`` input.

		Parameters
		----------
		items : list

		"""
		self.listbox.items = items
		self.input_le.clear()

	@property
	def selected_items(self):
		"""list: Selected ``ListBox`` items."""
		return self.listbox.selected_items


class InspectionCommandView(QtGui.QHBoxLayout):
	"""
	A view with start and finish ``GenericButton`` objects aligned to the right.

	Parameters
	----------
	parent : QVBoxLayout

	Attributes
	----------
	start_btn : GenericButton
		Clicked to start a process.

	finish_btn : GenericButton
		Clicked to finish a process.

	"""
	def __init__(self, parent):
		self._parent = parent
		super(InspectionCommandView, self).__init__()
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
		"""list: Selected ``ListBox`` items."""
		return self._listbox.selected_items

	@property
	def items(self):
		"""list: Items in ``ListBox``."""
		return self._listbox.items

	def set_listbox(self, items):
		"""
		Parameters
		----------
		items : list

		"""
		self._listbox.items = items


class DuelingListBoxView(QtGui.QHBoxLayout):
	"""
	A view that displays two ``ListBox`` objects separated by two 
	``ImageButton`` objects	that move data from one ``ListBox`` to another.

	Parameters
	----------
	parent : QLayout subclass

	headers : list

	Attributes
	----------
	source : ListBoxHeaderView
		``ListBox`` that is aligned to the left.

	add_btn : ImageButton
		Clicked to send data across ``ListBox`` objects.

	import_btn : ImageButton
		Clicked to import data into a ``ListBox``.

	subtract_btn : ImageButton
		Clicked to send data across ``ListBox`` objects.

	destination : ListBoxHeaderView
		``ListBox`` that is aligned to the right.

	"""
	def __init__(self, parent, headers):
		self._parent = parent
		self._headers = headers
		super(DuelingListBoxView, self).__init__()
		self.source = ListBoxHeaderView(self, self._headers[0])
		self._btn_layout = QtGui.QVBoxLayout()
		self._btn_layout.addItem(Spacer())
		self.add_btn = ImageButton(Image.FORWARD, self._btn_layout)
		self.import_btn = ImageButton(
			Image.IMPORT_RIGHT, self._btn_layout, tooltip='Import'
		)
		self.subtract_btn = ImageButton(Image.BACK, self._btn_layout)
		self.add_btn.mysquare = 30
		self.import_btn.mysquare = 30
		self.subtract_btn.mysquare = 30
		self._btn_layout.addItem(Spacer())
		self.addLayout(self._btn_layout)
		self.destination = ListBoxHeaderView(self, self._headers[1])
		self._parent.addLayout(self)


class HomeView(QtGui.QWidget):
	"""
	Provides GUI for Main Window default.

	"""
	def __init__(self):
		super(HomeView, self).__init__()
		self._layout = QtGui.QVBoxLayout(self)
		self._layout.setAlignment(QtCore.Qt.AlignCenter)
		self._logo_lb = QtGui.QLabel()
		self._logo_lb.setPixmap(QtGui.QPixmap(Image.LOGO))
		self._layout.addWidget(self._logo_lb)


if __name__ == '__main__':
	pass