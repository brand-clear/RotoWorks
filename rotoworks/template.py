import os.path
import sys
import pandas as pd
from shutil import copy
from PyQt4 import QtGui
from pyqtauto.widgets import ExceptionMessageBox
from data import Data, get_data_source
from history import HistoryController
from core import setup_logger
import logging

setup_logger()


class ComparisonController(object):

	def __init__(self, data, inspection):
		self._data = data
		self._csv = '%s.csv' % inspection.replace(' ', '')
		self._data_csv = os.path.join(self._data.path, self._csv)


	def start(self):
		try:
			# Get measurement DataFrames
			rw_filepath = Template.get_reference_path()
			ref_path = os.path.dirname(rw_filepath)
			ref_job_num = os.path.basename(rw_filepath)[:6]
			ref_data = Template.data_formatted(os.path.join(ref_path, 
				self._csv))
			data = Template.data_formatted(self._data_csv)

			# Get merged comparison DataFrame
			comparison_data = Template.get_comparison(
				self._data.job_num, ref_job_num, data, ref_data
			)

			# Prompt user to save comparison as CSV
			save_path = str(QtGui.QFileDialog.getSaveFileName(caption='Save'))
			if len(os.path.basename(save_path)) != 0:
				comparison_data.to_csv('%s.csv' % save_path, index=False)

		except TypeError as error:
			# object of type 'NoneType' has no len(), user cancellelation
			pass 

		except IOError as error:
			ExceptionMessageBox(error).exec_()


class Template:

	@staticmethod
	def get_reference_path():
		"""Returns the absolute path to the selected file."""
		ref = HistoryController()
		if ref.view.exec_():
			return ref.project

	@staticmethod
	def copied(project_dir, inspection):
		"""Transfer workscope files from a previous job to the current job.
		
		Parameters
		----------
		project_dir : str
		inspection : str
			{'Axial', 'Diameter'}

		Returns
		-------
		True or None

		Raises
		------
		IOError
			If the system cannot find the files specified.

		"""
		ref = Template.get_reference_path()
		if ref is not None:
			data = get_data_source(ref)
			try:
				filename = '%sScope.csv' % inspection
				src = os.path.join(
					data.path, 
					filename
				)
				dst = os.path.join(project_dir, filename)
				copy(src, dst)
			except IOError:
				raise
			else:
				return True

	@staticmethod
	def data_formatted(file_path):
		"""Create and format a ``DataFrame`` from an existing CSV file.

		Parameters
		----------
		file_path : str
			Absolute path to an existing CSV file.

		Returns
		-------
		df : DataFrame

		Raises
		------
		IOError
			If file does not exist.

		"""
		df = pd.read_csv(file_path)
		try:
			df.loc[df['Control'] == 'Custom', 'Control'] = 'Meas'
			df.loc[df['Control'] == '3D Distance', 'Control'] = 'Meas'
			df.loc[df['Control'] == 'Diameter', 'Control'] = 'Meas'
			df = df[df['Control'] == 'Meas']
			df = df[~df['Name'].str.contains('Ref')]
			df.drop(['Control', 'Tol', 'Dev', 'Test', 'Out Tol', 'No. Pts'], 
				axis=1, inplace=True)
		except KeyError:
			# CSV was not a PolyWorks export
			pass
		return df
		

	@staticmethod
	def get_comparison(job_num1, job_num2, job1_df, job2_df):
		"""Build a comparison ``DataFrame`` from two separate jobs.

		Parameters
		----------
		job_num1 : str
		job_num2 : str
		job1_data : DataFrame
		job2_data : DataFrame

		Returns
		-------
		job1_df : DataFrame
			Contains comparison data from `job2_df`.

		"""
		job1_head = '%s Meas' % job_num1
		job2_head = '%s Meas' % job_num2
		job1_df.columns = ['Name', job1_head]
		job1_df[job2_head] = pd.to_numeric(job2_df['Meas'])
		job1_df[job1_head] = pd.to_numeric(job1_df[job1_head])
		job1_df['Deviation'] = abs(job1_df[job1_head] - job1_df[job2_head])
		return job1_df


if __name__ == '__main__':
	pass
