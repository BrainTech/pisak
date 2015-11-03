Inputs
======

Specification of devices that can be used to operate PISAK program.

Inputs dictionary:

process - external process needed by a device to work. None or dictionary with keys:
	command - bash command to run the process;
	server - boolean, if there is a need for a web socket server for communication between a process and the main program;
	startup - (optional), function called on process start-up.

middleware - middle layer between an external device and the main program. None or dictionary with keys:
	name - name of the middleware, currently available: "scanning" and "sprite";
	activator - function that triggers the middleware;
	deactivator - function that closes the middleware.
