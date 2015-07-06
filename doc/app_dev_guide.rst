App developer guide
===================

Most basic Pisak applications consist of:

- one or more JSON files
- python module with app descriptor.

JSON files contain declarative description of application views. Python module
uses launcher module to set up view transitions and acts as app's executable.
This guide will show how to create a simple Pisak application.

App descriptor
--------------

App descriptor is simply a container of paths to JSON files, callbacks and
other data needed to launch an application. Below you can find a description 
of necessary entries and their keys:

views
    Dictionary of all views available in an application.
    
    For each "view"" there should be an entry where "view" name is the key and
    "value" is a pair of a path to JSON file and a callback function. Callback
    functions are used to prepare the view after loading it and they are 
    described below.
    
initial-view
    Name of the "view" shown when the application starts.
    
initial-data
    Value passed to callback when preparing the "view".


Callback functions are called each time the "view" is loaded. Their purpose is
to connect the standalone "view" with the rest of the application. Each such
function should have a folowing signature::

    def prepare_view_1(stage, script, data):

Where stage is a reference to the default stage, script is ClutterScript
object with loaded JSON file and data is an arbitraty value passed from view
loader.

Here is an example of app descriptor::

    EXAMPLE_APP = {
        "views": {
            "view_1": ("view_1.json", prepare_view_1),
            "view_2": ("view_2.json", prepare_view_2))
        },
        "initial-view": "view_1",
        "initial-data": None
    }
    
It declares 2 "views": `view_1` and `view_2`, the "view" named `view_1` is the
initial one and it is prepared by sending `None` value to `prepare_view_1` 
function. After loading the `view_2` it will be prepared by calling 
`prepare_view_2` function. 


JSON views
----------

What can be seen on a computer's screen at one moment when an application is running, is referenced here as the 'view'.
Every view of each Pisak application is described by a single
so-called JSON view. That is, simply a script that can be loaded by 
ClutterScript instance and is in the JavaScript ObjectNotation format
and therefore obeys its syntax rules.
Such a script defines the graphical layout, the structure
and mutual relations of all the elements that may or may not be visible
on the screen. All that makes up to what is seen as an application view. 
Features of JSON file accepted by ClutterScript:

- object definition is enclosed in a curly bracket;
- values are in a format of 'key: value';
- each object has to be of some 'type';
- each 'type' must be a previously registered GObject's __gtype__;
- accepted data types are: number, string, boolean, array, object;
- objects can be referenced to by their 'id' value or can be declared in place.

Important characteristics of Pisak JSON script:

- each contains object with id 'main' that is the most top widget and that is later placed on an application Stage by the Launcher;
- each object definiton consists of 'type', optionally 'id' and declarations of properties;
- each property must be previously registered GObject's __gproperty__;
- relations between objects that are ClutterActor instances are defined by a 'children' property, that is an ordered list of all objects that the given object is a parent to;
- objects can be infinitely nested through a 'children' property, it is then allowed to create invisible, backbone-like widgets just to achieve some specific layout effect;
- contains declaration of at least one ScanningGroup that in turn contains elements that the scanning proccess will be conducted at;
- each signal connected to an object must be a previously registered GObject's __gsignal__;
- to achieve custom appearance of some general widget it is highly recommended, if possible, to assign 'style-class' property to an object, instead of subclassing it;
- recommended is a flat structure of the script, that is, one should reference to the objects with their 'id' values instead of declaring them in place.


What next?
----------
- :doc:`useful_widgets`
- :doc:`switch_and_groups`
- :doc:`signal_handlers`
- :doc:`css_style`
