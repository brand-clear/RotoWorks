import os.path
from pywinscript.win import create_folder
from sulzer.extract import Extract, ProjectsFolderRootError
from core import Path
from data import Data


class Project(object):
	
	@staticmethod
	def folder(job_num, phase, subtype, nickname):
		"""Get the absolute path to a ROTOWORKS project folder.

		Parameters
		----------
		job_num : str
		phase : str
		subtype : str
		nickname: str
		
		Returns
		-------
		rw_project_folder : str

		Raises
		------
		ProjectsFolderRoot
			If the PROJECTS FOLDER root cannot be found. This path is used to 
			help determine the ROTOWORKS path.
		WindowsError
			If a ROTOWORKS folder could not be created due to a missing link.

		"""
		# Search for the PROJECTS FOLDER root
		try:
			pfolder_root = Extract.projects_folder_root(job_num)
		except ProjectsFolderRootError as error:
			msg = 'Make sure this job has a valid PROJECTS FOLDER and try again'
			error.message = "%s\n%s." % (error.message, msg)
			logging.warning(error)
			raise

		# Create the ROTOWORKS project folder
		try:
			rw_job_root = create_folder(
				os.path.join(Path.JOBS, os.path.basename(pfolder_root))
			)
			rw_job_folder = create_folder(os.path.join(rw_job_root, job_num))
			rw_project_folder = create_folder(
				os.path.join(rw_job_folder, phase)
			)
			if len(subtype) > 1:
				# An empty string of len(1) is used as a placeholder
				rw_project_folder = create_folder(
					os.path.join(rw_project_folder, subtype)
				)
			if len(nickname) > 0:
				rw_project_folder = create_folder(
					os.path.join(rw_project_folder, nickname)
				)
		except WindowsError as error:
			logging.warning(error)
			raise 

		return rw_project_folder

	@staticmethod
	def filename(job_num, phase, machine, subtype, nickname):
		"""Get the filename that will store a ROTOWORKS project.

		Parameters
		----------
		job_num : str
		phase : str
		machine : str
		subtype : str
		nickname : str

		Returns
		-------
		filename : str

		"""
		filename = '%s_%s_%s_%s_%s.rw' % (
			job_num,
			phase,
			machine,
			subtype,
			nickname
		)
		# Strip whitespace and duplicate underscores
		filename = filename.replace(' ', '')
		filename = filename.replace('__', '_')
		filename = filename.replace('_.', '.')
		return filename

	@staticmethod
	def filepath(job_num, phase, machine, subtype, nickname):
		"""Get the filename that will store a ROTOWORKS project.

		Parameters
		----------
		job_num : str
		phase : str
		machine : str
		subtype : str
		nickname : str

		Returns
		-------
		str
			Absolute path to project file
		
		Raises
		------
		ProjectsFolderRoot
			If the PROJECTS FOLDER root cannot be found. This path is used to 
			help determine the ROTOWORKS path.
		WindowsError
			If a ROTOWORKS folder could not be created due to a missing link.

		"""
		# Get project folder
		try:
			folder = Project.folder(job_num, phase, subtype, nickname)
		except (ProjectsFolderRootError, WindowsError) as error:
			raise error

		# Get project filename
		filename = Project.filename(
			job_num, phase, machine, subtype, nickname
		)
		return os.path.join(folder, filename)

	@staticmethod
	def init_data(job_num, phase, machine_type, is_curtis, filepath):
		"""Get the ``Data`` object pertaining to the current project.

		Parameters
		----------
		job_num : str
		phase : str
		machine_type : str
		is_curtis : bool
		filepath : str

		Returns
		-------
		data : Data

		Raises
		------
		IOError
			If an error occured while saving the project.

		"""
		data = Data(job_num, phase, machine_type, is_curtis, filepath)
		try:
			data.save()
		except IOError as error:
			raise error
		else:
			return data


if __name__ == '__main__':
	pass