""" Yaml Widgets Modules """

import logging
import re
import yaml

from IPython.display import display
import ipywidgets as widgets
from ipywidgets import interactive

module_logger = logging.getLogger('yaml_widgets')

class YamlWidgets():
    """ YamlWidgets Class """

    def __init__(self, yaml_in=None):
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
        self.controls['Title'] = widgets.Label(value=f"Tensor")

        #
        # Dictionary corresponding to final YAML values
        #
        self.yaml = {}

        if yaml_in is not None:
            self.setupWidgets(yaml_in)


    @classmethod
    def fromYAMLfile(cls, yaml_file):
        """ Construct a set of YAML widgets from a file """

        with open(yaml_file, "r") as f:
            yaml_in = f.read()

        return YamlWidgets(yaml_in)


    def setupWidgets(self, yaml_text):
        """ Setup Widgets for yaml """

        #
        # Convert YAML string into a dictionary and
        # create controls for each tag marked with a widget control
        #
        yaml_dict = yaml.load(yaml_text, Loader=yaml.SafeLoader)

        self._setupWidgets(yaml_dict, self.yaml)


    def _setupWidgets(self, dict_in, dict_out, name=None):
        """ Internal setup widgets """

        #
        # Take in YAML dictionary and create requested widget controls
        # and create a new YAML dictionary with only data values (i.e.,
        # without widget-related directives
        #

        marker = r'-widget$'

        for tag, value in dict_in.items():

            #
            # Check if this is just a normal yaml entry
            #
            if not re.search(marker, tag):
                #
                # Check if we need to recurse
                #
                if isinstance(value, dict):
                    dict_out[tag] = {}
                    self._setupWidgets(value, dict_out[tag], name=self._dotted_name(name, tag))
                else:
                    dict_out[tag] = value

                continue

            #
            # Process a yaml entry that describes a widget
            #

            #
            # Find name of entry that widget is setting
            #
            vname = re.sub(marker, '', tag)

            widget_type = value['type']
            widget_args = value['args']

            if widget_type == "IntSlider":
                name_string = self._dotted_name(name, vname)

                if 'description' not in widget_args:
                    widget_args['description'] = f'{name_string}'

                if 'value' not in widget_args:
                    widget_args['value'] = dict_in[vname]

                new_control = widgets.IntSlider(**widget_args)

                self.controls[name_string] = new_control


    def _dotted_name(self, name1, name2):
        """ Append a new name to a dot-separated string"""

        if name1 is None:
            return name2
        else:
            return name1 + "." + name2


    def displayWidgets(self):
        """" Display the widgets """

        controls = interactive(self._set_params,**self.controls)

        display(controls)


    def dumpYAMLfile(self, yaml_file):
        """ Dump YAML file based on current state of widgets """

        with open(yaml_file, "w") as f:
            f.write(self.dumpWidgets())


    def dumpWidgets(self):
        """ Create yaml string based on the current values from the widgets """

        yaml_text = yaml.dump(self.yaml, Dumper=yaml.SafeDumper)

        return yaml_text


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
