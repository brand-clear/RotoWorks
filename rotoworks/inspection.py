import re
import sys
import csv
import os.path
import pandas as pd
from PyQt4 import QtGui
from pywinscript.polyworks import Polyworks
from core import Path


class Inspection(object):
	"""
	Inspection base class.

	Class Methods
	-------------
	get_inspection_types

	Class Attributes
	----------------
	PHASES : list
	 
	Attributes
	----------
	SCOPE_FILENAME : str
		The corresponding CSV filename that feeds PolyWorks Inspector.

	OUTPUT_FILENAME : str
		The corresponding CSV filename that feeds AutoCAD.

	LAYOUT_NAME : str
		The corresponding AutoCAD layout name.

	polyworks : Polyworks

	"""
	PHASES = ["Phase 1", "Phase 2", "Final"]

	@classmethod
	def get_inspection_types(cls):
		"""Returns the ``list`` of subclasses.
		
		Notes
		-----
		This method depends on subclass names conforming to CapWords convention 
		(PEP 8).

		"""
		return [Inspection.split_capwords(child.__name__) 
			for child in cls.__subclasses__()]

	@staticmethod
	def split_capwords(value):
		split = re.findall(r'[A-Z](?:[a-z]+|[A-Z]*(?=[A-Z]|$))', value)
		return ' '.join(split)

	def __init__(self):
		self.SCOPE_FILENAME = "%sScope.csv" % self.__class__.__name__
		self.OUTPUT_FILENAME = "%s.csv" % self.__class__.__name__
		self.LAYOUT_NAME = self.__class__.__name__
		self.polyworks = Polyworks()

	def macro_exec(self, *args):
		"""Send a command to PolyWorks Inspector.
		
		Parameters
		----------
		args : tuple
			The first argument must be the path to a PWMACRO file. The following
			arguments are passed to the PWMACRO script.

		"""
		if len(args) == 2:
			self.polyworks.inspector.CommandExecute(
				"""MACRO EXEC ( "%s", "%s" )""" % args
			)
		elif len(args) == 3:
			self.polyworks.inspector.CommandExecute(
				"""MACRO EXEC ( "%s", "%s", "%s" )""" % args
			)		
		
	def export_as_single_column(self, data, filepath):
		"""Save inspection data to a CSV file as a single column.

		Parameters
		----------
		data : list

		filepath : str
			Absolute path to CSV file.
		
		"""
		with open(filepath, "wb") as csvfile:
			writer = csv.writer(csvfile)
			for item in data:
				writer.writerow([item])

	def export_as_multi_column(self, data, filepath):
		"""Save inspection data to a CSV file as a table.

		Parameters
		----------
		data : 2D list

		filepath : str
			Absolute path to CSV file.
		
		"""
		with open(filepath, "wb") as csvfile:
			writer = csv.writer(csvfile)
			writer.writerows(data)


class Diameter(Inspection):
	"""
	Contains paths and functions for Outside Diameter inspections.

	Parameters
	----------
	path : str
		Absolute path to a ROTOWORKS project directory.
	
	Attributes
	----------
	current_session : list

	SCOPE_FILE : str
		Absolute path to CSV file that feeds PolyWorks Inspector.

	OUTPUT_FILE : str
		Absolute path to CSV file that feeds Autodesk AutoCAD.

	MACRO_IN : str
		Absolute path to the PolyWorks macro that drives an inspection.

	MACRO_OUT : str
		Absolute path to the PolyWorks macro that exports inspection 
		documentation.

	See Also
	--------
	Inspection

	"""
	def __init__(self, path):
		super(Diameter, self).__init__()
		self._current_session = []
		self.SCOPE_FILE = os.path.join(path, self.SCOPE_FILENAME)
		self.OUTPUT_FILE = os.path.join(path, self.OUTPUT_FILENAME)
		self.MACRO_IN = os.path.join(Path.MACROS, "diametersIn.pwmacro")
		self.MACRO_OUT = os.path.join(Path.MACROS, "measurementsOut.pwmacro")

	@property
	def current_session(self):
		"""list: Contains the dimensional labels of the active measurement 
		session.
		
		"""
		return self._current_session

	@current_session.setter
	def current_session(self, items):
		"""
		Parameters
		----------
		items : list

		"""
		session_labels = [i.split('*')[0] for i in self._current_session]
		items = [i for i in items if i.split('*')[0] not in session_labels]
		self._current_session.extend(items)

	@current_session.deleter
	def current_session(self):
		"""Reset the active measurement session."""
		self._current_session = []

	def publish(self):
		"""Write the diameter inspection workscope to a CSV file."""
		self.export_as_single_column(self._current_session, self.SCOPE_FILE)


class Axial(Inspection):
	"""
	Contains paths and functions for Axial Measurement inspections.

	Parameters
	----------
	path : str
		Absolute path to a ROTOWORKS project directory.
	
	Attributes
	----------
	SCOPE_FILE : str
		Absolute path to CSV file that feeds PolyWorks Inspector.

	OUTPUT_FILE : str
		Absolute path to CSV file that feeds Autodesk AutoCAD.

	MACRO_IN : str
		Absolute path to the PolyWorks macro that drives an inspection.

	MACRO_OUT : str
		Absolute path to the PolyWorks macro that exports inspection 
		documentation.

	"""
	def __init__(self, path):
		super(Axial, self).__init__()
		self._current_session = None
		self.SCOPE_FILE = os.path.join(path, self.SCOPE_FILENAME)
		self.OUTPUT_FILE = os.path.join(path, self.OUTPUT_FILENAME)
		self.MACRO_IN = os.path.join(Path.MACROS, "axialsIn.pwmacro")
		self.MACRO_OUT = os.path.join(Path.MACROS, "measurementsOut.pwmacro")

	@property
	def current_session(self):
		"""2D list: Contains the dimensional labels of the active measurement 
		session.
		
		Examples
		--------
		>>>	[['Stage 1', 'Eye Face', 'I.C.P.', 'I.B.P.'],
			['Balance Drum],
			['Distance', 'A'],
			['Width', 'B']]

		"""
		return self._current_session

	@current_session.setter
	def current_session(self, session_info):
		"""
		Parameters
		----------
		session_info : list
			[0] session targets
			[1] machine object
			[2] project scope

		"""
		session_targets = session_info[0]
		machine = session_info[1]
		scope = session_info[2]

		# Reformat session_targets and save to targets_adjusted. The new format
		# determines how this data is exported to CSV.
		targets_adjusted = []
		width_row = ['Width']
		distance_row = ['Distance']

		for target in session_targets:
			new_row = []
			if 'Stage' in target:
				stage = target.split(' ')[1]
				new_row.append(target)
				new_row.extend(machine.probe_targets(scope[stage]))
			elif 'Balance Drum' == target:
				new_row.append(target)
			elif 'Distance' in target:
				distance_row.append(target.split(' ')[1])
			elif 'Width' in target:
				width_row.append(target.split(' ')[1])

			# Add new feature row, if used
			if len(new_row) > 0:
				targets_adjusted.append(new_row)
		
		# Add width / distance rows
		for row in (distance_row, width_row):
			if len(row) > 1:
				targets_adjusted.append(row)

		self._current_session = targets_adjusted

	@current_session.deleter
	def current_session(self):
		"""Reset the active measurement session."""
		self._current_session = []

	def publish(self):
		"""Write the axial inspection workscope to a CSV file."""
		self.export_as_multi_column(self._current_session, self.SCOPE_FILE)


class ThermalGap(Inspection):
	
	def __init__(self, path):
		super(ThermalGap, self).__init__()
		self.LAYOUT_NAME = 'Axial'
		self.OUTPUT_FILE = os.path.join(path, self.OUTPUT_FILENAME)


class RotorWeight(Inspection):

	def __init__(self, path):
		super(RotorWeight, self).__init__()
		self.LAYOUT_NAME = 'Axial'
		self.OUTPUT_FILE = os.path.join(path, self.OUTPUT_FILENAME)

if __name__ == '__main__':
	pass
