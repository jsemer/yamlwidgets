import ipywidgets as widgets


class WidgetInfo():
    """ Information about each widget type """

    def __init__(self, widget, standard, container):
        """ Initailize a widget type """

        self.widget = widget
        self.standard = standard
        self.container = container
