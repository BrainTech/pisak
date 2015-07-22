JSON structure
--------------

What can be seen on a computer's screen at one moment when an application
is running, is referenced here as the 'view'. Every view of each Pisak
application is described by a single so-called JSON view. That is,
simply a script that can be loaded by ClutterScript instance and is
in the JavaScript ObjectNotation format and therefore obeys its syntax rules.
Such a script defines the graphical layout, the structure
and mutual relations of all the elements that may or may not be visible
on the screen. All that makes up to what is seen as an application view.
Features of JSON file accepted by ClutterScript:

- object definition is enclosed in a curly bracket;
- values are in a format of ``'key: value'``;
- each object has to be of some ``'type'``;
- each ``'type'`` must be a previously registered GObject's ``__gtype__``;
- accepted data types are: number, string, boolean, array, object;
- objects can be referenced to by their ``'id'`` value or can be declared in place.

Important characteristics of Pisak JSON script:

- each contains object with id ``'main'`` that is the most top widget
  and that is later placed on an application Stage by the Launcher;
- each object definiton consists of ``'type'``, optionally ``'id'``
  and declarations of properties;
- each property must be previously registered GObject's ``__gproperty__``;
- relations between objects that are ``ClutterActor`` instances are
  defined by a 'children' property, that is an ordered list of all
  objects that the given object is a parent to;
- objects can be infinitely nested through a 'children' property,
  it is then allowed to create invisible, backbone-like widgets
  just to achieve some specific layout effect;
- contains declaration of at least one ``ScanningGroup`` that
  in turn contains elements that the scanning proccess will be conducted at;
- each signal connected to an object must be a previously registered
  GObject's ``__gsignal__``;
- to achieve custom appearance of some general widget it is highly recommended,
  if possible, to assign ``'style-class'`` property to an object, instead of
  subclassing it;
- what is recommended is a flat structure of the script, what means that one should
  reference to the objects with their ``'id'`` values instead of declaring them in place.

Examples of JSON's objects
--------------------------

Here's the example of the JSON's object. It's the row of menu buttons which can be seen
in every PISAK's speller under the writing board.::

    {
        "id": "keyboard_menu_box",
        "type": "PisakBoxLayout",
        "ratio_spacing": 0.0128,
        "children": [
                        "keyboard_menu_button_10", "keyboard_menu_button_9",
                        "keyboard_menu_button_8", "keyboard_menu_button_7",
                        "keyboard_menu_button_6", "keyboard_menu_button_5",
                        "keyboard_menu_button_4", "keyboard_menu_button_3",
                        "keyboard_menu_button_2", "keyboard_menu_button_1"
                    ]
    },

It consists of ``"id"``, ``"type"`` previously defined as a GObject's ``"__gtype__"``,
``"ratio_spacing"`` that sets specified spaces between subobjects (the number is from
range 0 - 1 and describes the proportion of pixels to the size of the whole screen)
and ``"children"`` property - the array of subobjects. One of them is below::

    {
        "id": "keyboard_menu_button_2",
        "type": "PisakButton",
        "style-class": "PisakSpellerButton",
        "text": " ",
        "ratio-width": 0.048,
        "ratio-height": 0.085,
        "icon-size": 30,
        "icon-name": "spacja",
        "spacing": 0,
        "signals": [
                       {
                           "name": "clicked",
                           "handler": "speller/space",
                           "object": "text_box"
                       }
                   ]
     },

This object has the additional properties:

- ``"style-class"`` - defines that the object is the type of a general widget,
- ``"text"`` - text displayed on the screen (in this case there is just an icon on the button),
  and, in some cases, rewritten to the text board,
- ``"ratio-width"`` and ``"ratio-height"`` - sizes of the object, being set in the same way as
  ``"ratio-spacing"``,
- ``"icon-size"`` - size of displayed image, in pixels,
- ``"icon-name"`` - name of the graphic file, without an extension if file is in the specified
  folder ``pisak/res/icons``,
- ``"signals"`` - an array of properties describing reacting to a certain signals:

  - ``"name"`` - the name of the performed action,
  - ``"handler"`` - the handler that includes instructions being applied when the action occurs,
  - ``"object"`` - target object of the action.

  In this certain case, the button, when chosen by the user, writes a single space on the text board.