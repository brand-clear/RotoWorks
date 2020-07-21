import sys
import logging
import numpy as np
import pandas as pd
from warnings import simplefilter
from comtypes import COMError
from os.path import join as osjoin
from pywinscript.autocad import (AutoCAD, CADOpenError, CADLayerError, 
	CADDocError, CADTable, ACAD)
from inspection import Diameter, Axial, ThermalGap, RotorWeight
from machine import Rotor


# Debugging logger
logger = logging.getLogger('debugger')
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler(stream=sys.stdout)
logger.addHandler(handler)

# Turn of SettingWithCopy warning
pd.set_option('mode.chained_assignment', None)
simplefilter(action='ignore', category=FutureWarning)


class TurboDoc(AutoCAD):
	"""
	AutoCAD documentation base class.

	"""
	def __init__(self):
		self.DOC_TRAIL = '%s.%s' % (self.__class__.__name__, 'txt')
		super(TurboDoc, self).__init__()

	def init_doc(self, layout_name):
		"""Prepare AutoCAD document for automated input.
		
		Parameters
		----------
		layout_name : str

		Raises
		------
		CADOpenError
			If AutoCAD is unavailable (license issue or startup pending).
		CADDocError
			If the active document could not be found.
		AttributeError
			If `layout_name` could not be found.
		
		"""
		try:
			self.set_layout(layout_name)
		except WindowsError:
			raise CADOpenError()
		except COMError:
			raise CADDocError()
		except AttributeError:
			raise

	def load_measurements(self, filepath, float_req=True):
		"""Retrieve measurement session data from a CSV file.

		Parameters
		----------
		filepath : str
			Abolute path to CSV file.
		
		float_req: bool
			If 'Meas' items need to be of type float.

		Returns
		-------
		session : DataFrame

		Raises
		------
		IOError
			If the system cannot find the path specified.

		"""
		try:
			session = pd.read_csv(filepath)
			session.dropna(subset=['Meas'], inplace=True)
			if float_req:
				session = session[session.Name != 'Name']
				session['Meas'] = session['Meas'].astype(np.float64)
		except IndexError:
			raise
		else:
			return session

	def replace_text_with_data(self, data):
		"""Replace placeholder text values with ``DataFrame`` measurements.

		Parameters
		----------
		data : DataFrame
			Placeholder text values are found in the 'Name' column and the 
			corresponding measurements are found in the 'Meas' column.

		Raises
		------
		CADDocError
			If the Document object could not be found.

		"""
		try:
			for txt in self.iter_objects():
				try:
					index = int(data[data['Name'] == txt.TextString].index[0])
					txt.TextString = str(data.get_value(index, 'Meas'))
				except (AttributeError, KeyError, IndexError, ):
					continue
		except COMError:
			raise CADDocError()

	def leave_doc_trail(self, path):
		with open(osjoin(path, self.DOC_TRAIL), 'wb') as f:
			pass


class DocTable(CADTable):
	"""A custom AutoCAD table for axial inspection documentation packages.

	Parameters
	----------
	cad : AutoCAD
	row_headers : list
	col_headers : list
	bal_drum : int

	"""
	_ROW_OFFSET = 1
	_COL_OFFSET = 1
	_DEFAULT_TABLE_POS = .061
	_TITLE_ROW_HEIGHT = .2533
	_DATA_ROW_HEIGHT = .2133
	_DATA_TEXT_HEIGHT = .07
	_TABLE_WIDTH = 10.375

	def __init__(self, cad, row_headers, col_headers, bal_drum):
		self._row_headers = row_headers
		self._col_headers = col_headers

		# Adjust headers if balance drum was measured
		if bal_drum:
			self._row_headers.append('B.D. Face')
			self._col_headers.append('B.D.')

		# Create table
		super(DocTable, self).__init__(
			cad, self._DEFAULT_TABLE_POS, self._calc_table_y(), 
			len(self._row_headers) + self._ROW_OFFSET,
			len(self._col_headers) + self._COL_OFFSET,
			self._DATA_ROW_HEIGHT,
			self._TABLE_WIDTH
		)
		self.set_title_row(
			'Axial Measurements From Active Face', 
			.1, self._TITLE_ROW_HEIGHT
		)
		self._set_column_headers()
		self._setup_feature_cells()
		self.add_contrast()

	def _calc_table_y(self):
		"""Return the Y coordinate ``float`` that positions the ``DocTable``.

		The ``DocTable`` origin is the top-left corner. The overall height is
		calculated, adjusted for margin, then returned.
		
		"""
		data_row_height = len(self._row_headers) * self._DATA_ROW_HEIGHT
		table_height = data_row_height + self._TITLE_ROW_HEIGHT
		return table_height + self._DEFAULT_TABLE_POS

	def _setup_feature_cells(self):
		"""Format rows and set header texts."""
		self.table.SetAlignment(ACAD.acDataRow, ACAD.acMiddleCenter)
		target_row = self._ROW_OFFSET
		for header in self._row_headers:
			self.table.SetText(target_row, 0, header)
			for col in range(self.table.columns):
				self.table.SetCellTextHeight(
					target_row, col, 
					self._DATA_TEXT_HEIGHT
				)
			self.table.SetRowHeight(target_row, self._DATA_ROW_HEIGHT)
			target_row += 1

	def _set_column_headers(self):
		"""Format column header cells and set header texts."""
		for col in range(self.table.columns):
			self.table.SetCellTextHeight(1, col, self._DATA_ROW_HEIGHT)
			try:
				self.table.SetText(
					1, col + self._COL_OFFSET, self._col_headers[col]
				)
			except IndexError:
				pass

	def _table_pos(self, meas_item):
		"""Get the row and column index for a ``DocTable`` data item.

		Parameters
		----------
		meas_item : str
			Stage and feature names separated by "-", as found in the axial 
			inspection output file (Axials.csv). `meas_item` should be validated
			prior to calling this function.
		
		Returns
		-------
		row, col : int, int
			The row and column index of the `meas_item`.

		Raises
		------
		ValueError
			If `meas_item` splits are not found in the "col_headers".
		IndexError
			If `meas_item` does not contain "-".

		"""
		item_split = meas_item.split('-')
		try:
			stage = item_split[0]
			col = self._col_headers.index(stage) + self._COL_OFFSET
			feature = item_split[1]
			row = self._row_headers.index(feature) + self._ROW_OFFSET
		except ValueError:
			raise 
		except IndexError:
			raise
		else:
			return row, col

	def populate_table(self, data):
		"""Add axial measurement data to the ``DocTable``.

		Parameters
		----------
		data : DataFrame
			Contains axial measurement data.
			
			The ['Name'] column should contain labels in "Stage-Feature" format.
				Ex.) str: Stage 1-Eye Face

			The ['Meas'] column should contain the corresponding measurements.
				Ex.) float: 12.6255

		"""
		for index, row in data.iterrows():
			try:
				_row, _col = self._table_pos(row['Name'])
			except (ValueError, IndexError) as error:
				logger.debug(error)
			else:
				self.table.SetText(_row, _col, row['Meas'])


class AxialDoc(TurboDoc):
	"""
	Provides methods which support AutoCAD automation for Axial inspection 
	documentation packages.

	Parameters
	----------
	data : Data

	"""
	def __init__(self, data):
		self._data = data
		self._scope = data.scope.data
		self._axials = Axial(self._data.path)
		try:
			self._row_headers = self._data.machine_obj.feature_rows(self._scope)
		except:
			self._row_headers = None
		else:
			self._col_headers = Rotor.stage_names(
				len(self._scope), 
				self._data.is_curtis == 1
			)
		super(AxialDoc, self).__init__()

	def start(self):
		"""Initiate Axial inspection documentation.

		Raises
		------
		CADOpenError
			If AutoCAD is unavailable (license issue or startup pending).
		CADDocError
			If the AutoCAD document could not be found.
		CADLayerError
			If the AutoCAD document layer is locked.
		AttributeError
			If the AutoCAD layout could not be found.
		IOError
			If the system cannot find the path specified.

		"""
		self.init_doc(self._axials.LAYOUT_NAME)
		data = self.load_measurements(self._axials.OUTPUT_FILE)
		table_data, text_data = self._table_text_split(data)
		if self._row_headers is not None:
			self._table = DocTable(
				self, 
				self._row_headers, 
				self._col_headers,
				self._has_bal_drum(table_data)
			)
			self._table.populate_table(table_data)
		self.replace_text_with_data(text_data)
		self.regen()
		self.leave_doc_trail(self._data.path)

	def _has_bal_drum(self, data):
		"""Verify the existence of a balance drum measurement.

		Returns
		-------
		int
			1 if this session contains a balance drum measurement, else 0.

		"""
		try:
			data[data['Name'] == 'B.D.-B.D. Face'].index[0]
		except IndexError:
			return 0
		else:
			return 1

	def _table_text_split(self, data):
		"""Split a DataFrame into two subsets.

		The first subset is used to populate a ``DocTable`` and the	second is 
		used to replace AutoCAD text objects with measurement data.

		Parameters
		----------
		data : DataFrame
			As retrieved from an axial measurement session CSV file.

		Returns
		-------
		table_data, text_data : DataFrame, DataFrame

		Notes
		-----
		This method raises SettingWithCopyWarning, which, in this context, can 
		be safely ignored.

		See Also
		--------
		TurboDoc.replace_text_with_data

		"""
		logger.debug(data)
		data = data[
			(data['Control'] == '3D Distance') &
			(~data['Name'].str.contains('Ref'))
		]
		table_data = data[
			(~data['Name'].str.contains('To Distance')) & 
			# Here is a very subtle distinction between a generic 'Width' and 
			# the 'G.P. Width'. This should weed out the generic widths and
			# ignore the gas path data.
			(~data['Name'].str.contains('Width '))
		]
		logger.debug(table_data)
		text_data = data[~data['Name'].str.contains('-')]
		text_data['Name'] = text_data['Name'].apply(lambda x: x.split(' ')[-1])
		logger.debug(text_data)
		return table_data, text_data


class DiameterDoc(TurboDoc):
	"""
	Provides methods which support AutoCAD automation for Diameter inspection 
	documentation packages.

	Parameters
	----------
	data : Data
		Active data model.

	"""
	def __init__(self, data):
		self._path = data.path
		self._diameters = Diameter(self._path)
		super(DiameterDoc, self).__init__()

	def start(self):
		"""Initiate Diameter inspection documentation.

		Raises
		------
		CADOpenError
			If AutoCAD is unavailable (license issue or startup pending).
		CADDocError
			If the AutoCAD document could not be found.
		CADLayerError
			If the AutoCAD document layer is locked.
		AttributeError
			If the AutoCAD layout could not be found.
		IOError
			If the system cannot find the path specified.

		"""
		self.init_doc(self._diameters.LAYOUT_NAME)
		data = self.load_measurements(self._diameters.OUTPUT_FILE)
		self.replace_text_with_data(data)
		self.regen()
		self.leave_doc_trail(self._path)


class ThermalGapDoc(TurboDoc):
	"""
	Provides methods which support AutoCAD automation for Thermal Gap inspection
	documentation packages.

	Parameters
	----------
	data : Data
		Active data model.

	"""
	def __init__(self, data):
		self._path = data.path
		self._tg = ThermalGap(self._path)
		super(ThermalGapDoc, self).__init__()

	def start(self):
		"""Initiate Thermal Gap inspection documentation.

		Raises
		------
		CADOpenError
			If AutoCAD is unavailable (license issue or startup pending).
		CADDocError
			If the AutoCAD document could not be found.
		CADLayerError
			If the AutoCAD document layer is locked.
		AttributeError
			If the AutoCAD layout could not be found.
		IOError
			If the system cannot find the path specified.

		"""
		self.init_doc(self._tg.LAYOUT_NAME)
		data = self.load_measurements(self._tg.OUTPUT_FILE)
		self.replace_text_with_data(data)
		self.regen()
		self.leave_doc_trail(self._path)


class RotorWeightDoc(TurboDoc):
	"""
	Provides methods which support AutoCAD automation for Rotor Weight 
	inspection documentation packages.

	Parameters
	----------
	data : Data
		Active data model.

	"""
	def __init__(self, data):
		self._path = data.path
		self._weights = RotorWeight(self._path)
		super(RotorWeightDoc, self).__init__()

	def start(self):
		"""Initiate Rotor Weight inspection documentation.

		Raises
		------
		CADOpenError
			If AutoCAD is unavailable (license issue or startup pending).
		CADDocError
			If the AutoCAD document could not be found.
		CADLayerError
			If the AutoCAD document layer is locked.
		AttributeError
			If the AutoCAD layout could not be found.
		IOError
			If the system cannot find the path specified.

		"""
		self.init_doc(self._weights.LAYOUT_NAME)
		data = self.load_measurements(self._weights.OUTPUT_FILE, False)
		self.replace_text_with_data(data)
		self.regen()
		self.leave_doc_trail(self._path)


if __name__ == '__main__':
	pass