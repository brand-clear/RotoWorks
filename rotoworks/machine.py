#!/usr/bin/env python
# -*- coding: utf-8 -*-
from os.path import join as osjoin
import re
from collections import OrderedDict
from core import Path


__author__ = 'Brandon McCleary'


class Rotor(object):
	"""
	Rotor base class.

	Attributes
	----------
	FEATURES : list

	"""

	@classmethod
	def get_machine_types(cls):
		"""Returns the ``list`` of ``Rotor`` subclasses (machine types).

		Notes
		-----
		This method depends on ``Rotor`` subclass names conforming to CapWords 
		convention (PEP 8).

		"""
		children = []
		for item in [re.sub("([a-z])([A-Z])", r"\1 \2", child.__name__).split() 
			for child in cls.__subclasses__()]:
			children.append(" ".join(item))
		return children

	@classmethod
	def get_machine_sub_types(cls):
		"""Returns the ``list`` of machine sub-types.

		Machine sub-types are found in the SUB_TYPES constant of each ``Rotor`` 
		subclass.

		"""
		sub_list = [" "]
		for sub in cls.__subclasses__():
			try:
				sub_list.extend(sub.SUB_TYPES)
			except AttributeError:
				# No sub-types found.
				continue
		return sub_list

	@classmethod
	def get_machine_type_as_object(cls, machine_type):
		"""Returns an instance of a ``Rotor`` subclass.
		
		Parameters
		----------
		machine_type : str
			The name of a ``Rotor`` subclass with a space in between each 
			capitalized word (Ex. 'Steam Turbine', not 'SteamTurbine').
		
		"""
		return next(child() for child in cls.__subclasses__() 
		if machine_type.replace(" ","") == child.__name__)

	@classmethod
	def stage_names(cls, stage_count, is_curtis):
		"""Returns a ``list`` of stage labels.

		Parameters
		----------
		stage_count : int
		is_curtis : bool

		"""
		if is_curtis:
			return [
				'Stage %s' % cls._curtis_label(i) 
				for i in range(1, stage_count + 1)
			]
		else:
			return ['Stage %s' % i for i in range(1, stage_count + 1)]

	@classmethod
	def _curtis_label(cls, stage):
		"""Convert a standard stage number into curtis stage format.

		Parameters
		----------
		stage : int

		Returns
		-------
		str

		Examples
		--------
		>>> _get_curtis_label(1)
		'C1'
		>>> _get_curtis_label(4)
		'R2'

		"""
		letter = ('C' if stage <= 2 else 'R')
		return (letter + str(stage) if letter == 'C' else letter + str(stage - 2))   

	def __init__(self):
		self.FEATURES = ["Stage"]


class CentrifugalCompressor(Rotor):
	"""
	Contains all data specific to Centrifugal Compressors.
	
	Both PolyWorks and AutoCAD will use this object to extract relevant	machine 
	information during measurement and documentation sessions.
	
	Attributes:
		FEATURES : list

	"""
	_CLOSE_FACE_FEATURES = [
		'Eye Face', 
		'I.C.P.', 
		'I.B.P.'
	]
	_OPEN_FACE_FEATURES = [
		'Leading Edge', 
		'Trailing Edge', 
		'I.B.P.', 
		'O.B.P.'
	]
	_CLOSE_FACE_ROWS = [
		'Eye Face', 
		'I.B.P.', 
		'G.P. Width'
	]
	_OPEN_FACE_ROWS = [
		'Leading Edge', 
		'I.B.P.', 
		'G.P. Width', 
		'B.P. Width'
	]
	_COMBO_FACE_ROWS = [
		'Leading Edge', 
		'Eye Face', 
		'I.B.P.', 
		'G.P. Width', 
		'B.P. Width'
	]

	def __init__(self):
		Rotor.__init__(self)
		self.FEATURES.append("Open Face")

	def probe_targets(self, stage_scope):
		"""Returns a ``list`` of axial inspection target areas.

		Parameters
		----------
		stage_scope : list
			Axial inspection work scope of a particular stage.

		"""
		if stage_scope[0] == 1:
			return self._OPEN_FACE_FEATURES
		else:
			return self._CLOSE_FACE_FEATURES

	def feature_rows(self, scope):
		"""Returns a ``list`` of ``DocTable`` row names.
		
		Parameters
		----------
		scope : OrderedDict
			The project scope that defines the axial measurement features.

		See Also
		--------
		data.Data.scope

		"""
		rows = ["Feature"]
		stage_count = len(scope)
		open_face_count = sum([scope[item][0] for item in scope.keys()])
		if open_face_count == 0:
			# All stages are close-faced
			rows.extend(self._CLOSE_FACE_ROWS)
			return rows
		elif open_face_count == stage_count:
			# All stages are open-faced
			rows.extend(self._OPEN_FACE_ROWS)
			return rows
		else:
			# Stages are both open and close-faced
			rows.extend(self._COMBO_FACE_ROWS)
			return rows


class ScrewCompressor(Rotor):
	
	SUB_TYPES = ["Male", "Female"]
	
	def __init__(self):
		Rotor.__init__(self)
		

class AxialFlowCompressor(Rotor):
	
	def __init__(self):
		Rotor.__init__(self)
		self.FEATURES.extend([
			"Disk Face", 
			"Shroud Band", 
			"Blade Root", 
			"Blade Edge"
		])


class SteamTurbine(Rotor):
	"""
	Contains all data specific to Steam Turbines.

	Both PolyWorks and AutoCAD will use this object to extract relevant machine
	information during measurement and documentation sessions.

	"""
	def __init__(self):
		Rotor.__init__(self)
		self.OPTIONS = ["Disk Face", "Shroud Band", "Blade Root", "Blade Edge"]
		self.FEATURES.extend(self.OPTIONS) 

	def probe_targets(self, stage_scope):
		"""Returns a ``list`` of axial inspection target areas.

		Parameters
		----------
		stage_scope : list
			Axial inspection work scope of a particular stage.

		"""
		return [
			self.OPTIONS[i] for i in range(len(stage_scope)) 
			if stage_scope[i] == 1
		]

	def feature_rows(self, scope):
		"""Returns a ``list`` of ``DocTable`` row names.
		
		Parameters
		----------
		scope : OrderedDict
			The project scope that defines the axial measurement features.

		See Also
		--------
		data.Data.scope

		"""
		rows = ["Feature"]

		# Get the sum of scope values for each index in a single list.
		sums = [0] * len(self.OPTIONS)
		for item in scope.values():
			for i in range(len(item)):
				sums[i] = sums[i] + item[i]

		# A positive value at an index indicates a scoped feature.
		additions = [self.OPTIONS[i] for i in range(len(sums)) if sums[i] > 0]
		rows.extend(additions)
		return rows


class Expander(Rotor):
	
	def __init__(self):
		Rotor.__init__(self)
		self.FEATURES.extend([
			"Disk Face", 
			"Seal Eye Face", 
			"Shroud Band", 
			"Blade Root", 
			"Blade Edge"
		])


class Gear(Rotor):
	
	SUB_TYPES = ["Bull", "Pinion"]
	
	def __init__(self):
		Rotor.__init__(self)
		


if __name__ == '__main__':
	pass