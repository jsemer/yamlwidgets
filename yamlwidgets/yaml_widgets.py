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
        self.controls['Title'] = {'widget': widgets.Label(value=title)}

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

        self._setupWidgets()


    def display(self):
        """" Display the widgets """

        widgets = { tag: value['widget'] for tag, value in self.controls.items()}

        controls = interactive(self._set_params, **widgets)

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
    def _setupWidgets(self, yaml_dict=None, name=None):
        """Internal function to set up control widgets

        This method recursively processes a YAML dictionary,
        starting at `self.yaml`, and creates a record in
        `self.controls` with the information on the target tags to be
        controlled and creates the control widgets themselves for YAML
        tags that will have controls. Those tags are identified by
        special tags that look like '<target_tag>-widget', which have
        specifications of the widget to be created. Note: those
        special tags are stripped from the output YAML.

        The dictionary tags in `self.controls` are a dot-separated
        name comprised of all the hierarchical names in the YAML
        hierarchy and markers for lists.

        """

        if yaml_dict is None:
            yaml_dict = self.yaml


        marker = r'-widget$'
        control_tags = []

        for tag, value in yaml_dict.items():

            #
            # Check if this is just a normal yaml entry, i.e., an
            # entry that does not have the marker for a control widget
            # '<target_tag>-widget'
            #
            if not re.search(marker, tag):
                #
                # Only need to do something if we need to recurse for
                # a subtree in the YAML or for a YAML list
                #
                if isinstance(value, dict):
                    new_name = self._dotted_name(name, tag)
                    self._setupWidgets(value, name=new_name)

                if isinstance(value, list):
                    for n, list_value in enumerate(value):
                        new_name = self._dotted_name(name, f"{tag}[{n}]")
                        self._setupWidgets(list_value, name=new_name)

                continue

            #
            # Fall through to here to process a YAML tag entry for a
            # control widget.
            #
            # For each such tag, we will create an entry in
            # `self.controls` that contains the target_{dict,tag} to
            # be updated and the associated control widget.
            #
            target_tag = re.sub(marker, '', tag)

            #
            # Create a flattened dot-separated name for this entry
            #
            flattened_name = self._dotted_name(name, target_tag)

            #
            # Memoize the target_{dict,tag} for this control
            #
            control_info = {}
            control_info['target_dict'] = yaml_dict
            control_info['target_tag'] = target_tag

            #
            # Parse the information about the control widget
            #
            widget_info = value
            widget_type = widget_info['type']
            widget_args = widget_info['args']

            #
            # Create widget for this target_{dict,tag}
            #
            standard_widgets = ["IntSlider",
                                "FloatLogSlider" ]

            if widget_type in standard_widgets:

                if 'description' not in widget_args:
                    widget_args['description'] = f'{flattened_name}'

                if 'value' not in widget_args:
                    widget_args['value'] = yaml_dict[target_tag]

            if widget_type == "IntSlider":
                new_control = widgets.IntSlider(**widget_args)
                control_info['widget'] = new_control

            if widget_type == "FloatLogSlider":
                new_control = widgets.FloatLogSlider(**widget_args)
                control_info['widget'] = new_control

            self.controls[flattened_name] = control_info
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
            control_info = self.controls[variable]

            if 'target_tag' not in control_info:
                continue

            self.logger.debug(f"Setting {variable} to {value}")

            target_dict = control_info['target_dict']
            target_tag = control_info['target_tag']

            target_dict[target_tag] = value

