""" Yaml Widgets Modules """

import logging
import re

from ruamel.yaml import YAML
from ruamel.yaml.compat import StringIO

from IPython.display import display
import ipywidgets as widgets
from ipywidgets import interactive

module_logger = logging.getLogger('yaml_widgets')

class YamlWidgets():
    """ YamlWidgets Class 

    Notes:
        - YAML tags of the form <name>-widget are special
        - YAML tags cannot contain a dot (.)

    """

    def __init__(self, doc=None, title=""):
        """ __init__ """
        #
        # Set up logging
        #
        self.logger = logging.getLogger('yaml_widgets')

        #
        # Single level dictionary of widget controls
        # where key is a flattened (dot-separated) string
        # of the hierarchical YAML tags
        #
        self.controls = {}
        self.controls['Title'] = widgets.Label(value=title)

        #
        # Set up ruamel YAML
        #
        self.YAML = YAML()

        #
        # Dictionary corresponding to final YAML values
        #
        self.yaml = None

        if doc is not None:
            self.load(doc)


    @classmethod
    def fromYAMLfile(cls, filename):
        """ Construct a set of YAML widgets from a string filename """

        with open(filename, "r") as f:
            yaml_in = f.read()

        return YamlWidgets(yaml_in)


    def load(self, doc):
        """ Setup Widgets for yaml """

        #
        # Convert YAML string into a dictionary and
        # create controls for each tag marked with a widget control
        #
        self.yaml = self.YAML.load(doc)

        self._setupWidgets(self.yaml)


    def display(self):
        """" Display the widgets """

        controls = interactive(self._set_params,**self.controls)

        display(controls)


    def dump(self, doc=None):
        """ Dump YAML document based on current state of widgets """

        #
        # When doc is None, return a string dump of the YAML
        #
        if doc is None:
            return self.dump2string()

        return self.YAML.dump(self.yaml, doc)


    def dump2string(self):
        """ Dump YAML document to a string """

        stream = StringIO()
        self.YAML.dump(self.yaml, stream)
        return stream.getvalue()

#
# Internal utility functions
#
    def _setupWidgets(self, yaml_dict, name=None):
        """ Internal setup widgets """

        #
        # Take in YAML dictionary and create requested widget controls
        # and create a new YAML dictionary with only data values (i.e.,
        # without widget-related directives
        #

        marker = r'-widget$'
        control_tags = []

        for tag, value in yaml_dict.items():

            #
            # Check if this is just a normal yaml entry
            #
            if not re.search(marker, tag):
                #
                # Only need to do something if we need to recurse
                #
                if isinstance(value, dict):
                    self._setupWidgets(value,
                                       name=self._dotted_name(name, tag))

                continue

            #
            # Process a yaml entry that describes a widget
            # First, find actual tag that widget is setting
            #
            target_tag = re.sub(marker, '', tag)

            widget_info = value
            widget_type = widget_info['type']
            widget_args = widget_info['args']

            if widget_type == "IntSlider":
                flattened_name = self._dotted_name(name, target_tag)

                if 'description' not in widget_args:
                    widget_args['description'] = f'{flattened_name}'

                if 'value' not in widget_args:
                    widget_args['value'] = yaml_dict[target_tag]

                new_control = widgets.IntSlider(**widget_args)

                self.controls[flattened_name] = new_control

            control_tags.append(tag)

        #
        # Remove all controls from the original yaml dictionary
        #
        for control_tag in control_tags:
            del yaml_dict[control_tag]


    def _dotted_name(self, name1, name2):
        """ Append a new name to a dot-separated string"""

        if name1 is None:
            return name2
        else:
            return name1 + "." + name2


    def _set_params(self, **kwargs):
        """ Set values in yaml dictionary based on current values in the widgets """

        for variable, value in kwargs.items():
            if variable in ['Title']:
                continue

            self.logger.debug(f"Setting {variable} to {value}")

            self._set_variable(self.yaml, variable, value)


    def _set_variable(self, yaml_dict, variable, value):
        """ Set value in hierarchical dictionary based on dotted variable name """

        if '.' not in variable:
            yaml_dict[variable] = value
            return

        name = re.sub(r"\..*", "", variable)
        rest = re.sub(r"^[^.]*\.", "", variable)

        if name not in yaml_dict:
            print(f"Did not find {name} in {yaml_dict}")
            return

        self._set_variable(yaml_dict[name], rest, value)
