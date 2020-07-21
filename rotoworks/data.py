import os.path
import cPickle as pickle
from collections import OrderedDict
from abc import ABCMeta, abstractmethod
from pyqtauto.widgets import TableCheckBox
from core import Path, setup_logger
from machine import Rotor
import logging


setup_logger()


class Data(object):
	"""
	Project data source.

	Attributes
	----------
	job_num : str
	phase : str
	machine_type : str
	is_curtis : bool
	path : str
	filename : str
	machine_obj : Rotor subclass
	features : list
	scope : ScopeModel
	
	"""
	def __init__(self, job_num, phase, machine_type, is_curtis, filepath):
		self.job_num = job_num
		self.phase = phase
		self.machine_type = machine_type
		self.machine_obj = Rotor.get_machine_type_as_object(self.machine_type)
		self.features = self.machine_obj.FEATURES
		self.is_curtis = is_curtis
		self.path, self.filename = os.path.split(filepath)
		self.filepath = filepath
		self.scope = ScopeModel(is_curtis, len(self.features))

	def save(self):
		"""Save this instance to file.

		Raises
		------
		IOError
			If the system cannot find the path specified.

		"""
		try:
			with open(self.filepath, "wb") as project:
				pickle.dump(self, project)
		except IOError as error:
			logging.warning(error)
			raise error


class DataModel(object):
	"""
	Data model base class.

	The structure of this model is provided by an ``OrderedDict``, where the 
	keys are integer strings and the values are lists whose data is provided by
	the subclass. The keys correspond to stage numbers and the values correspond
	to yes or no.

	Parameters
	----------
	is_curtis : bool
		An assertion that a machine contains a curtis stage.
	feature_count : int
		The number of possible measurement features in an axial inspection.

	Attributes
	----------
	data : OrderedDict
	is_curtis : bool
	feature_count : int

	Methods
	-------
	clear
	init

	Notes
	-----
	update() must be implemented by the subclass.
	
	"""

	__metaclass__ = ABCMeta

	def __init__(self, is_curtis, feature_count):
		self.data = OrderedDict()
		self.is_curtis = is_curtis
		self.feature_count = feature_count
		super(DataModel, self).__init__()

	def clear(self):
		"""Empty ``DataModel``."""
		for key in self.data.keys():
			del self.data[key]

	def init(self, stage_count, value):
		"""Initializes model with default values.
		
		Parameters
		----------
		stage_count : int
		value : int or TableCheckBox

		"""
		self.clear()
		stage_labels = Rotor.stage_names(stage_count, self.is_curtis)
		stage_labels = [i.replace('Stage ', '') for i in stage_labels]
		for label in stage_labels:
			try:
				self.data[label] = [value()] * self.feature_count
			except TypeError:
				self.data[label] = [value] * self.feature_count

	@abstractmethod
	def update(self):
		"""To be implemented by subclass."""
		pass


class ScopeModel(DataModel):
	"""
	A ``DataModel`` whose list values are binary integers.

	This subclass is to contain responses to yes or no questions (as indicated 
	by binary integers) and may be serialized.

	Parameters
	----------
	is_curtis : bool
		An assertion that a machine contains a curtis stage.
	feature_count : int
		The number of possible measurement features in an axial inspection.

	Attributes
	----------
	data : OrderedDict
		Underlying data source

	"""
	def __init__(self, is_curtis, feature_count):
		super(ScopeModel, self).__init__(is_curtis, feature_count)

	def init(self, stage_count):
		"""Initialize with zeros (unselected options).
		
		Parameters
		----------
		stage_count : int

		"""
		super(ScopeModel, self).init(stage_count, 0)

	def update(self, table_map):
		"""Map object content from a ``TableMap`` instance.

		Parameters
		----------
		table_map : TableMap

		"""
		for key in table_map.data:
			self.data[key] = []
			for i in range(len(table_map.data.keys()[0])):
				if table_map.data[key][i].isChecked():
					self.data[key].append(1)
				else:
					self.data[key].append(0)


class TableMap(DataModel):
	"""
	A ``DataModel`` whose list values are ``TableCheckBox`` objects.

	This subclass is to contain responses to yes or no questions (as indicated 
	by the ``TableCheckBox`` checked states) and cannot be serialized; it exists 
	only to hold temporary graphical state. 
	
	Parameters
	----------
	is_curtis : bool
		An assertion that a machine contains a curtis stage.
	feature_count : int
		The number of possible measurement features in an axial inspection.

	Attributes
	----------
	data : OrderedDict
		Underlying data source

	Notes
	-----
	To save the state of a ``TableMap`` object, map the instance to a 
	``ScopeModel`` instace.

	"""
	def __init__(self, is_curtis, feature_count):
		super(TableMap, self).__init__(is_curtis, feature_count)
		
	def init(self, stage_count):
		"""Initialize with unchecked ``TableCheckBox`` objects.
				
		Parameters
		----------
		stage_count : int
		
		"""
		super(TableMap, self).init(stage_count, TableCheckBox)

	def update(self, scope_model):
		"""Map object content from a ``ScopeModel`` instance.

		Parameters
		----------
		scope_model : ScopeModel

		"""
		self.clear()
		for stage in scope_model.data:
			self.data[stage] = []
			for item in scope_model.data[stage]:
				self.data[stage].append(TableCheckBox(checked=(item == 1)))


def get_data_source(path):
	"""Retrieve data source object from file.

	Parameters
	----------
	path : str
		Absolute path to data file.

	Returns
	-------
	data : Data

	"""
	try:
		with open(path, 'rb') as project:
			data = pickle.load(project)
	except IOError:
		raise
	else:
		return data


if __name__ == '__main__':
	pass



