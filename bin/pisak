#!/usr/bin/env python3

"""
Entry point for the whole PISAK program. Declares descriptor for an application
launched on the PISAK start and, if executed directly, launches the application.
"""
import pisak
from pisak import app_manager, logger


if __name__ == '__main__':
    pisak.init()
    _std_log = logger.get_logger(__name__)
    _event_log = logger.get_event_logger()
    message = "PISAK was launched."
    _std_log.info(message)
    _event_log.info(message)
    _main_app = {
        "app": "main_panel",
        "type": "clutter",
        "views": [("main", None)]  # no preparator needed so far
    }
    app_manager.run(_main_app)
    message = "PISAK was closed."
    _std_log.info(message)
    _event_log.info(message)
