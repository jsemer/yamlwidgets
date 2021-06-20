""" Yaml Widgets Module """

import logging
import re

from ruamel.yaml import YAML
from ruamel.yaml.compat import StringIO

from IPython.display import display
import ipywidgets as widgets
from ipywidgets import interactive

module_logger = logging.getLogger('yaml_widgets')

class YamlWidgets():
    """YamlWidgets Class 

    The YamlWidgets class is class used to create a set of control
    widgets in a Jupyter notebook that allows the user to change the
    values of some entries in a YAML document.

    Attributes
    ----------

    The principal attributes of the YamlWidgets class are:

    - `self.yaml`: The YAML document as read in using ruamel.yaml and
      updated with values set by the control widgets

    - `self.controls`: A dictionary with information about the entries
      in the YAML document for which there are control widgets.

    Constructor
    -----------

    The main constructor accepts a document in any form acceptable to
    ruamel.yaml and creates controls for those tags with the special
    form <target-tag>-widget.

    Parameters
    -----------

    doc: string, Path() or class with a .read method, default=None
        A YAML document with special tags to create control widgets

    title: string, default=""
        A title for the controls

    Notes
    -----
      - Use `YamlWidgets.load()` to load a document when doc=None
      - YAML tags of the form <target_tag>-widget are special
      - YAML tags probably should not contain a slash ("/") used by flatten_name

    """

    def __init__(self, doc=None, title=""):
        """ __init__ """
        #
        # Set up logging
        #
        self.logger = logging.getLogger('yaml_widgets')

        #
        # Single level dictionary of widget controls where key is a
        # flattened string of the hierarchical YAML tags
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
    def fromYAMLfile(cls, filename, title=""):
        """ Construct a set of YAML widgets from a string filename 

        See main constructor for more information.

        """

        with open(filename, "r") as f:
            yaml_in = f.read()

        return YamlWidgets(yaml_in, title=title)


    def load(self, doc):
        """ Load a YAML document and create control widgets as specified

        Parameters
        -----------

        doc: string, Path() or class with a .read method
            A YAML document with special tags to create control widgets


        Returns
        -------
        None

        """

        #
        # Convert YAML string into a dictionary and
        # create controls for each tag marked with a widget control
        #
        self.yaml = self.YAML.load(doc)

        self._setupWidgets()


    def display(self):
        """" Display the control widgets

        Parameters
        ----------
        None

        Returns
        -------
        None

        """

        widgets = { tag: value['widget'] for tag, value in self.controls.items()}

        controls = interactive(self._set_params, **widgets)

        display(controls)


    def dump(self, doc=None, strip_controls=True):
        """Dump YAML document based on current state of widgets 

        Parameters
        -----------

        doc: Path() or class with a .write method
            A YAML document to be written with the updated values

        strip_controls: Bool, default-True
            Strip out the tags in the YAML document that specify the
            control widgets


        Notes
        -----

        Once the tags specifying the control widgets are striped they
        are gone forever

        """

        #
        # Optionally strip the control tags
        #
        if strip_controls:
            self._strip_controls()

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

        The dictionary tags in `self.controls` are a flattened name
        comprised of all the hierarchical names in the YAML hierarchy
        and markers for lists.

        """

        if yaml_dict is None:
            yaml_dict = self.yaml


        marker = r'-widget$'

        for tag, value in yaml_dict.items():

            self.logger.debug(f"Processing {tag}")
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
                    new_name = self._flatten_name(name, tag)
                    self._setupWidgets(value, name=new_name)

                if isinstance(value, list) and not isinstance(value, str):
                    for n, list_value in enumerate(value):
                        new_name = self._flatten_name(name, f"{tag}[{n}]")
                        if isinstance(list_value, dict):
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
            # Create a flattened name for this entry
            #
            flattened_name = self._flatten_name(name, target_tag)

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
                    # TBD: Change separator for flattened_name for display...
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


    def _flatten_name(self, name1, name2):
        """ Append a new name to a slash-separated string"""

        if name1 is None:
            return name2
        else:
            return name1 + "/" + name2


    def _set_params(self, **kwargs):
        """ Set values in yaml dictionary based on current values in the widgets """

        for variable, value in kwargs.items():
            control_info = self.controls[variable]

            if 'target_tag' not in control_info:
                continue

            target_dict = control_info['target_dict']
            target_tag = control_info['target_tag']

            if target_dict[target_tag] != value:
                self.logger.debug(f"Setting {variable} to {value}")

            target_dict[target_tag] = value


    def _strip_controls(self, yaml_dict=None):
        """ Strip out widget tags in the YAML dictionary """

        if yaml_dict is None:
            yaml_dict = self.yaml


        marker = r'-widget$'
        del_list = []

        for tag, value in yaml_dict.items():
            if re.search(marker, tag):
                del_list.append(tag)
                continue

            if isinstance(value, dict):
                self._strip_controls(value)
                continue

            if isinstance(value, list) and not isinstance(value, str):
                for list_value in value:
                    if isinstance(list_value, dict):
                        self._strip_controls(list_value)

        for tag in del_list:
            del yaml_dict[tag]
