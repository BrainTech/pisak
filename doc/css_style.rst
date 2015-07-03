CSS style definition
====================

Pisak style
-----------
Due to the very particular requirements of Pisak target users, almost every 
visual aspect of every graphical element should be easily accessed, modified 
and adjusted. For instance, colors be changed to distinct some button with 
important function, font be magnified etc.
In order to achieve this goal, every Pisak widget is highly modifiable and 
especially every widget that is an instance of a MxStylable can have its 
style properties defined in a CSS file.


CSS file
--------
CSS files accepted by Pisak applications should follow starndard CSS syntax.
Objects described in a CSS file can be referenced to by their:

- previously registered GObjects's __gtype__;
- previously declared 'style-class', that is __gtype__ and then 'style-class' 
joined with a single dot. 'style-class' name should unambiguously indicate 
the application that the given object is used by;
- Mx objects hierarchy, with space or '>' sign, needs individual 
case examination.

Each object might have few operating states defined, they are represented by 
'style-pseudo-class', such as highlighted or not.
Object reference name is linked with a particular 'style-pseudo-class'
name with a single colon.

Example of a CSS styling procedure:

- first create some class and declare its GObject type: 
	
	class Foo(object):
	    __gtype_name__ = 'PisakFoo'

- then create two instances of the class in the JSON file and assign different 
'style-class' properties to them:
	
        {
            'id': 'pisak_foo_looks_1',
            'type': 'PisakFoo',
            'style-class': 'Looks1'
        },
        {
            'id': 'pisak_foo_looks_2',
            'type': 'PisakFoo',
            'style-class': 'Looks2'
        }

- define style for these two objects in the CSS file, define also style
for the objects being in a different state ('hover'):
	
	PisakFoo.Looks1 {
	color = white;
	background-color = red;
	font-size = 10pt; }

	PisakFoo.Looks1:hover {
	color = green; }

	PisakFoo.Looks2 {
	color = black;
	background-color = blue;
	font-size = 15pt; }

	PisakFoo.Looks2:hover {
	color = pink;
	font-size = 20pt; }

- now, there is only one type defined but two objects of the same type
 that look completely different.

Frequently used properties:

- 'border-image' - image being a content of a widget, taken from a file 
with a given path, usually in PNG format, specified can be amount of 
an image border that will be pushed close to the widget edges and not evenly
expanded like the rest, middle part of an image;
- 'color' - color of a widget foreground elements, usually it is color 
of a font or/and an icon;
- 'font-size' - size of a font in pixels or in points;
- 'font-family' - name of a font family, must be avalaible in the system;
- 'font-weight' - weight of a font, that is its thickness.


Style related widgets
---------------------

Not every widget used by Pisak applications can be styled through 
a CSS file. Such objects may be styled directly by JSON (:doc:`app_dev_guide`)
or configuration file. Widgets that contribute to the overall style 
impressions and that can not be styled through a CSS file:

:class:`pisak.widgets.BackgroudPattern'

Simple widget used as a background in every Pisak application view. 
Displays one of the avalaible, colorfull patterns.
Adjustable style-related properties are:

- 'pattern' - name of a pattern to be drawn as a widget content, 
for now there are 'fence' and 'gradient' avalaible. 'fence' is a
 dense pattern of thin, slanted lines crossing each other with the
 right angle and 'gradient' is a horizontal, linear gradient from
 a foreground color on both sides to a background color in the middle;
- 'rgba' - color of the foreground pattern parts. 

:class:`pisak.widgets.Aperture`

Semitransparent cover used to highlight other widgets and indicate
 they have the focus.
Style properties:

- 'cover' - specifies how narrow will be a hole left in the middle;
- 'r', 'g', 'b' - specific bands of the cover color.
