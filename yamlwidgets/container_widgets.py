""" Container Widgets Module """

import logging

import ipywidgets as widgets

module_logger = logging.getLogger('yaml_widgets')

class ContainerState():
    """Object to hold ContainerWidgets current widget state"""

    def __init__(self, ctype=None, cname=None, widget=None):
        #
        # Information about current container
        #
        self.ctype = ctype
        self.cname = cname
        self.widget = widget

        self.children = []
        self.names = []


    def addWidget(self, widget, name=None):
        """ Add a widget (and optionaly its name) as a child of the current widget """

        self.children.append(widget)

        if name is not None:
            self.names.append(name)


class ContainerWidgets():
    """Container Widgets Class

    """

    def __init__(self):
        """ __init__ """
        #
        # Set up logging
        #
        self.logger = logging.getLogger('yaml_widgets')

        #
        # Current container state
        #
        self.s = ContainerState()

        #
        # Stack of nested container information
        #
        self.stack = []


    def startContainer(self, ctype, name=None):
        """ Start a new nested container """

        # TBD: Fix condition
        if self.s.ctype == "VBox" and ctype == "VBox":
            #
            # Part of a sequence of VBoxes, finish current container
            #
            self.logger.debug("Creating a VBox container in a container - assuming sequential")
            new_child = self.finishContainer()

        #
        # Create the widget and add as a new child of current container
        #
        self.logger.debug(f"Making a {ctype}/{name}")

        if ctype == "VBox":
            widget = widgets.VBox()
        elif ctype == "Tab":
            widget = widgets.Tab()

        self.logger.debug(f"Widget: {widget}")

        self.s.addWidget(widget, name)

        #
        # Save the current container
        #
        self.stack.append(self.s)

        #
        # Initailize new container widget
        #
        self.s = ContainerState(ctype, name, widget)

        return widget


    def addChild(self, child, name=None):
        """ Add a child widget to the current container """

        self.s.addWidget(child, name)


    def finishContainer(self, finish_all=False):
        """ Finish the current container """

        self.logger.debug(f"Finishing {self.s.ctype}/{self.s.cname}")
        self.logger.debug(f"Children of: {self.s.widget} are {self.s.children}")
        self.logger.debug(f"Stack: {self.stack}")

        #
        # Add information in the current container state
        # to the container at the head of the stack.
        #
        self.s.widget.children = self.s.children

        if hasattr(self.s.widget, 'set_title'):
            for n in range(len(self.s.names)):
                self.s.widget.set_title(n, self.s.names[n])

        controls = self.s.widget

        self.s = self.stack.pop()

        if finish_all and len(self.stack) > 0:
            controls = self.finishContainer(True)

        return controls
