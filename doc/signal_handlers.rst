Signal handlers
===============


GObject signals
---------------

Signals are very useful object oriented mechanism to react to events and
propagate information between objects. A Class declares signal names and
signatures which can be emitted by its instance. Using `connect` method on an
object one can connect a signal handler to id. A signal handler is a function
or method which is called each time the signal is emitted. Some signals are
emitted automatically by application event, all of them can be emitted by
`emit` method.

Signals in JSON
---------------

ClutterScript allows specifying signal handlers in JSON. To do this use
`signals` key, which value has following form::

    {
        "id": "some_object",
        "type": "SomeType",
        "signals": [
            {
                "name": "signal-name",
                "handler": "handler_name",
                "object": "optional_object_id"
            }
        ]
    }

For each handler there are 3 parameters:

- `name` - signal name as in class declaration
- `handler` - name of the handler,
- `object` - optional object id or dictionary with declaration.

Handler names are dependent on script loader implementation. In Pisak there is
custom handler loader which has its own lookup dictionary. :mod:`pisak.signals`
module has functions to register and resolve handler names. Many useful
handlers are declares in :mod:`pisak.handlers` module.

`object` parameter is optional, not using it is equivalent to setting it to
signal emitter. The downside of connecting signal handlers in JSON is that
there is no local scope for handler to operate in. Then only object available
to the handler is the one specified by `object` key.
