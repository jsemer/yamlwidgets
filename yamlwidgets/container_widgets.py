""" Container Widgets Module """

import logging

import ipywidgets as widgets

module_logger = logging.getLogger('yaml_widgets')


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
        # Stack of nested container information
        #
        self.stack = []

        #
        # Information about current container
        #
        self.ctype = None
        self.cname = None

        self.children = []
        self.names = []

        self.widget = None


    def startContainer(self, ctype, name=None):
        """ Start a new nested container """

        # TBD: Fix condition
        if self.ctype == "VBox" and ctype == "VBox":
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

        self.children.append(widget)
        if name is not None:
            self.names.append(name)

        #
        # Save the current container
        #
        self.stack.append((self.ctype,
                           self.cname,
                           self.widget,
                           self.children,
                           self.names))

        #
        # Initailize new container widget
        #
        self.ctype = ctype
        self.cname = name
        self.widget = widget
        
        self.children = []
        self.names = []


        return widget


    def addChild(self, child, name=None):
        """ Add a child widget to the current container """

        self.children.append(child)

        if name is not None:
            self.names.append(name)


    def finishContainer(self, finish_all=False):
        """ Finish the current container """

        self.logger.debug(f"Finishing {self.ctype}/{self.cname}")
        self.logger.debug(f"Children of: {self.widget} are {self.children}")
        self.logger.debug(f"Stack: {self.stack}")

        if self.ctype == "VBox":
            self.widget.children = self.children
        elif self.ctype == "Tab":
            self.widget.children = self.children

            for n in range(len(self.names)):
                self.widget.set_title(n, self.names[n])

        controls = self.widget

        (self.ctype,
         self.cname,
         self.widget,
         self.children,
         self.names) = self.stack.pop()

      
        if finish_all and len(self.stack) > 0:
            controls = self.finishContainer(True)

        return controls
