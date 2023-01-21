YAML Widgets
============

Install
=======

To install an editable copy in your home directory run the following
in the root directory of a clone of this repository:

```console
python3 -m pip install --user -e .
```
To install from the remote git repository, run the following:

```console
python3 -m pip install git+https://github.com/jsemer/yamlwidgets
```


Usage
=======

Define a input

```
yaml_in = """
#
# Unmodifiable entry
#
a: 2
#
# Modifiable entry with default description and value
#
b: 3
b-widget:
    type: IntSlider
    args: {min: 1, max: 20, step: 1}
#
# Modifiable entry with explictly set initial value
#
c: 3
c-widget:
    type: IntSlider
    args: {min: 1, max: 10, step: 1, value: 4}
#
# Modifiable entry with explictly set description
#
d: 20
d-widget:
    type: IntSlider
    args: {description: "The real D", min: 0, max: 40, step: 5}
"""
```

In a Jupyter cell create the controls

```
yaml_widgets = YamlWidgets()

yaml_widgets.load(yaml_in)
yaml_widgets.display()

```

In a Jupyter cell get the updated yaml string

```
yaml_out = yaml_widgets.dump()

```
