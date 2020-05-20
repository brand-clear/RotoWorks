#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import json
import collections


__author__ = 'Brandon McCleary'


class Data(object):
    """
    Project data model.

    Attributes
    ----------
    definition : OrderedDict
        A high-level description of the project (machine).
        
    scope : OrderedDict
        Contains information about the stages (disks/impellers) of a machine.
        
    """
    def __init__(self):
        self._definition = None
        self._scope = None

    @property
    def definition(self):
        """OrderedDict or None: The project definition.
        
        Keys : {
            'Job Number', 'Phase', 'Machine Type', 'Curtis Stage', 
            'Stacked', 'Path to Filename', 'Filename', 'Ref Filename'
        }
        
        """
        return self._definition

    @definition.setter
    def definition(self, data):
        """
        Parameters
        ----------
        data : OrderedDict
            Structured as defined by ``DefinitionController``.

        """
        self._definition = data

    @property
    def scope(self):
        """OrderedDict or None: The project inspection scope.

        The keys will represent the machine's stages and the values will 
        represent the features targeted for inspection.

        """
        return self._scope

    @scope.setter
    def scope(self, data):
        """
        Parameters
        ----------
        data : OrderedDict
            Structured as defined by ``ScopeController``.

        """
        self._scope = data

    def open_project(self, filepath):
        """Load project data from file.
        
        Parameters
        ----------
        filepath : str
            Absolute path to the project file.
            
        Raises
        ------
        ValueError
            If no data is found in `filepath`.
        IOError
            If the system cannot find the path specified.

        """
        try:
            with open(filepath, "rb") as project:
                data = json.load(
                    project, 
                    object_pairs_hook=collections.OrderedDict
                )
        except (IOError, ValueError) as error:
            raise error
        else:
            # Set project data
            self.definition = data[0]
            self.scope = data[1]

    def save_project(self):
        """Save project data to file.

        Raises
        ------
        IOError
            If the system cannot find the path specified.

        """
        data = [self.definition, self.scope]
        path = os.path.join(
            self.definition["Path to Filename"], 
            self.definition["Filename"]
        )
        try:
            with open(path, "wb") as project:
                json.dump(data, project)
        except IOError as error:
            raise error

       
if __name__ == '__main__':
    pass

