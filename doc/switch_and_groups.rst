Switch and groups
=================

Switch interface
----------------

Switch interface is designed to operate computer with only one button. User is presented a screen with buttons and other activatable widgets. Widgets are then highlighted sequentially (scanned). Pressing a switch button causes currently highlighted widget to be activated (for example highlighted button will be clicked). Layout can define groups of widgets that are highlighted together. Selecting a group enters it: scanning will be performed inside that group.

Defining groups
---------------

To define a scanning group use pisak.scanning.Group widget. This widgets automatically detects selectable widgets and subgroups among its descendants. Actors which are not selectable are "transparent" and can be freely used inside group to adjust layout. The scanning can be started with start_cycle method. To start scanning automatically used "BLABLA_TODO" handler.

Scanning features
-----------------

One of the key features of the scanning cycle is its ability to "go to sleep". When the scanning elapses a previously defined number of max cycles and its group is not related to any other with the "unwind_to" property, it turns into a standby mode. That is, it turns off a highlight on all elements of its group and starts waiting for being restarted by a user's action.
