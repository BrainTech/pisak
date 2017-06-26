Making simple press button
==========================

Idea
----
This tutorial is intended to allow the creation of a simple switch button
which can be used as one of the possible PISAK's inputs. The main advantage of
the switch is that it is highly customizable. It can fit different mechanical
solutions such as buttons or pneumatic mechanisms, so it is possible to
adjust the method of input individually to the patient's needs.

Hardware
--------
First, the following pieces of hardware will be needed:
 - PC with Ubuntu and PISAK software,
 - USB - microUSB connecting cable,
 - Wattuino Nanite 85 (https://github.com/watterott/wattuino),
 - proper micro switch,
 - mechanical system, for example 3D-printed button.

Firmware
--------
There are a few things to do to prepare the PC to cope with the Nanite 85.
Following Watterott, Nanite 85 is provided with Micronucleus, a tiny bootloader.
In order to be able to upload the firmware straight to Nanite flash memory, you need
to copy the micronucleus git repository to your PC. It can be done by using
the following command::

    $git clone https://github.com/micronucleus/micronucleus

You'll need libusb library (http://www.libusb.org/). If you don't have it, type::

    $sudo apt-get install libusb-dev

Micronucleus requires avr-gcc and avr-libc in order to be compiled::

    $sudo apt-get install avr-libc gcc-avr

Next, go to the /micronucleus/commandline and install micronucleus::

    $make
    $sudo make install

Now, you are able to upload the .hex files to the Nanite.

Pisak-switch
------------
Visit https://github.com/BrainTech/pisak-switch to find a project with ready to use firmware.
If you want to write your own firmware, check at least configuration in
``usbdrv/usbconfig.h``, without it the communication between the PC and the Nanite is impossible.
