""" Yaml Widgets Module """

import logging
import re

from ruamel.yaml import YAML
from ruamel.yaml.compat import StringIO

from IPython.display import display
import ipywidgets as widgets
from ipywidgets import interactive

from .container_widgets import ContainerWidgets
from .widget_info import WidgetInfo

module_logger = logging.getLogger('yaml_widgets')
debug1 = logging.DEBUG+1
debug2 = logging.DEBUG+2


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

    - `self.controls`: A dictionary with information about the ALL the
      entries in the YAML document for which there are control
      widgets.


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

    def __init__(self, doc=None, title="Title"):
        """ __init__ """
        #
        # Set up logging
        #
        self.logger = logging.getLogger('yaml_widgets')

        #
        # Define information about the different kinds of widgets
        #
        self.widgetinfo = self._defineWidgetInfo()

        #
        # Single level dictionary of ALL widget controls where key is
        # a flattened string of the hierarchical YAML tags
        #
        self.controls = {}

        #
        # Create container management object and start outer container
        #
        self.containers = ContainerWidgets(self.widgetinfo)
        self.containers.startContainer("VBox", name="ROOT", nested=True)

        #
        # Set up a top level widget
        #
        widget_info = {'type': "Label", 'args': {'value': title}}
        self._createWidget(widget_info, "Title")

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

    def _defineWidgetInfo(self):

        wi = {}

        #
        # Ordinary controls
        #
        wi['Label'] = WidgetInfo(widgets.Label, True, False)
        wi['Text'] = WidgetInfo(widgets.Text, True, False)

        wi['IntSlider'] = WidgetInfo(widgets.IntSlider, True, False)
        wi['BoundedIntText'] = WidgetInfo(widgets.BoundedIntText, True, False)
        wi['IntText'] = WidgetInfo(widgets.IntText, True, False)

        wi['FloatLogSlider'] = WidgetInfo(widgets.FloatLogSlider, True, False)
        wi['BoundedFloatText'] = WidgetInfo(widgets.BoundedFloatText, True, False)
        wi['FloatText'] = WidgetInfo(widgets.FloatText, True, False)

        wi['Checkbox'] = WidgetInfo(widgets.Checkbox, True, False)

        wi['Dropdown'] = WidgetInfo(widgets.Dropdown, True, False)
        wi['RadioButtons'] = WidgetInfo(widgets.RadioButtons, True, False)
        wi['SelectMultiple'] = WidgetInfo(widgets.SelectMultiple, True, False)

        #
        # Container controls
        #
        wi['Accordion'] = WidgetInfo(widgets.Accordion, False, True)
        wi['Tab'] = WidgetInfo(widgets.Tab, False, True)
        wi['VBox'] = WidgetInfo(widgets.VBox, False, True)

        #
        # Special controls
        #
        wi['Close'] = WidgetInfo(None, False, False)

        return wi


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

        controls = self.containers.finishContainer(finish_all=True)
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
        controlled. And it also creates the control widgets themselves for YAML
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
                    #
                    # Recurse to next level for simple subtrees
                    #
                    new_name = self._flatten_name(name, tag)
                    self._setupWidgets(value, name=new_name)

                if isinstance(value, list) and not isinstance(value, str):
                    #
                    # Recurse to next level for each entry in a list that is a subtree
                    #
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
            # Create the widget and control structures
            #
            if not isinstance(value, list):
                #
                # Handle a single widget directive
                #
                self._createWidget(value, flattened_name, yaml_dict, target_tag)
            else:
                #
                # Handle a list of widget directives
                #
                for n, v in enumerate(value):
                    if n == 0:
                        self._createWidget(v, flattened_name, yaml_dict, target_tag)
                    else:
                        self._createWidget(v, f"{flattened_name}-{n}", yaml_dict, target_tag)


    def _createWidget(self,
                      widget_info,
                      flattened_name,
                      yaml_dict=None,
                      target_tag="dummy"):
        """Internal function actually create the control widgets

        """
        #
        # Sanity check the wiget_info
        #
        if 'type' not in widget_info:
            self.logger.error("Widget must have a type key: %s",flattened_name)
            return

        #
        # Memoize the target_{dict,tag} for this control
        #
        control_info = {}
        control_info['target_dict'] = yaml_dict
        control_info['target_tag'] = target_tag

        #
        # Make sure there is some value in the target_dict
        #
        if yaml_dict is not None:
            if target_tag not in yaml_dict:
                self.logger.error("Target tag not in yaml: %s", target_tag)
                return
        else:
            yaml_dict = {}
            yaml_dict[target_tag] = None

        #
        # Parse the information about the control widget
        #
        widget_type = widget_info['type']
        if widget_type not in self.widgetinfo:
            self.logger.error("Unknown widget type: %s", widget_type)
            return

        widget_args = {}
        if 'args' in widget_info:
            widget_args = widget_info['args']

        #
        # Handle close widget
        #
        if widget_type == 'Close':
            self.logger.debug("Closing widget")
            self.containers.finishContainer()
            return

        #
        # Extract the chanacteristics of the widget
        #
        widget_constructor = self.widgetinfo[widget_type].widget
        widget_standard = self.widgetinfo[widget_type].standard
        widget_container = self.widgetinfo[widget_type].container

        #
        # Create widget for this target_{dict,tag}
        #
        if widget_standard or widget_container:

            if 'description' not in widget_args:
                # TBD: Change separator for flattened_name for display...
                widget_args['description'] = f'{flattened_name}'

            if 'value' not in widget_args:
                widget_args['value'] = yaml_dict[target_tag]

        #
        # Handle container widgets (e.g, "VBox", "Tab" etc")
        #
        if widget_container:
            self.logger.debug(f"Starting {widget_type}: {yaml_dict[target_tag]}")
            widget_name = widget_args['value']
            widget_nested = 'nested' in widget_info and widget_info['nested']

            new_control = self.containers.startContainer(widget_type,
                                                         name=widget_name,
                                                         nested=widget_nested)

            control_info['widget'] = new_control

            self.controls[flattened_name] = control_info

        #
        # Handle normal widgets
        #
        if not widget_container:
            self.logger.debug(f"{widget_constructor} - {widget_args}")
            new_control = widget_constructor(**widget_args)
            new_control.observe(self._set_params)

            control_info['widget'] = new_control

            self.controls[flattened_name] = control_info
            self.containers.addChild(control_info['widget'])


    def _flatten_name(self, name1, name2):
        """ Append a new name to a slash-separated string"""

        if name1 is None:
            return name2
        else:
            return name1 + "/" + name2


    def _set_params(self, change):
        """ Set values in yaml dictionary based on current values in the widgets """

        widget = change.owner
        value = widget.value

        #
        # Scan all the widgets
        #
        # TBD: Just go directly to correct widget
        #
        for variable, control_info in self.controls.items():
            #
            # Check if this the the widget that was updated
            #
            if control_info['widget'] != widget:
                continue

            #
            # Get target information (which is known to exist!)
            #
            target_dict = control_info['target_dict']
            target_tag = control_info['target_tag']

            #
            # Check if value needs to be updated
            #
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
