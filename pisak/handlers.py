"""
ClutterScript signal handler library. See also :module:`pisak.signals`.
"""
from gi.repository import Clutter, Gtk

import pisak
from pisak import signals


@signals.registered_handler("general/run_input_middleware")
def run_input_middleware(source):
    """
    Run the current middleware.

    :param source: signal source.
    """
    pisak.app.window.input_group.run_middleware()


@signals.registered_handler("general/stop_input_middleware")
def stop_input_middleware(source):
    """
    Stop the middleware. Useful if the middleware is planned to be restarted.

    :param source: signal source.
    """
    pisak.app.window.input_group.stop_middleware()


def connect_button(script, button_name, handler, *args):
    """
    Function connecting the given button to a callback using the defalt signal.

    :param script: ClutterScript to get the button from.
    :param button_name: name of the given button.
    :param handler: callable handler.
    :param args: optional arguments to be passed to handler.
    """
    button = script.get_object(button_name)
    if button is not None:
        # the only arguments that will optionally be passed to the handler are
        # 'args', default signal parameter emitted by the button
        #  will be ignored by lambda
        button.connect("clicked",
            lambda source, *args_for_handler: handler(*args_for_handler), *args)


def button_to_view(window, script, button_name, view_to_load=None, data=None):
    """
    Function connecting the given button to a callback loading the given view.

    :param stage: ClutterStage instance being the ancestor of the given button.
    :param script: ClutterScript to get the button from.
    :param button_name: name of the given button.
    :param view_to_load: name of the view to be loaded.
    :param data: optional data.
    """
    button = script.get_object(button_name)
    if button is not None:
        if view_to_load is None:
            if window.type == "gtk":
                button.connect("clicked", lambda *_: Gtk.main_quit())
            else:
                button.connect("clicked", lambda *_: window.stage.destroy())
        else:
            button.connect("clicked", lambda *_: window.load_view(view_to_load,
                                                            data))


@signals.registered_handler("data_source/next_data_set")
def next_data_set(data_source):
    """
    Make the given data source to move to the next data set.

    :param data_source: data source.
    """
    data_source.next_data_set()


@signals.registered_handler("data_source/previous_data_set")
def previous_data_set(data_source):
    """
    Make the given data source to move to the previous data set.

    :param data_source: data source.
    """
    data_source.previous_data_set()


@signals.registered_handler("playlist/next")
def move_next(playlist):
    """
    Move to the next position on the given playlist.

    :param playlist: PisakPlaylist instance.
    """
    playlist.move_next()


@signals.registered_handler("playlist/previous")
def move_previous(playlist):
    """
    Move to the previous position on the given playlist.

    :param playlist: PisakPlaylist instance.
    """
    playlist.move_previous()


@signals.registered_handler("playlist/play")
def play(playlist):
    """
    Start playing the current media item on the given playlist.

    :param playlist: PisakPlaylist instance.
    """
    playlist.move_focus(and_play=True)


@signals.registered_handler("playlist/stop")
def stop(playlist):
    """
    Stop playing of the given playlist.

    :param playlist: PisakPlaylist instance.
    """
    playlist.stop()


@signals.registered_handler("playlist/pause")
def pause(playlist):
    """
    Pause playing the current media item on the given playlist.

    :param playlist: PisakPlaylist instance.
    """
    playlist.pause()
    

@signals.registered_handler("playlist/toggle_looped")
def toggle_looped(playlist):
    """
    Turn on or turn off the looped mode of the given playlist. 

    :param playlist: PisakPlaylist instance.
    """
    playlist.looped = not playlist.looped
    

@signals.registered_handler("playlist/toggle_random_order")
def toggle_random_order(playlist):
    """
    Turn on or turn off the random order of playing the items
    on the given playlist. 

    :param playlist: PisakPlaylist instance.
    """
    playlist.random_order = not playlist.random_order


@signals.registered_handler("playlist/toggle_play")
def toggle_play(playlist):
    """
    Start or pause playing the current media item on the given playlist,
    basing on the current item state.

    :param playlist: PisakPlaylist instance.
    """
    if playlist.is_playing():
        playlist.pause()
    else:
        playlist.move_focus(and_play=True)


@signals.registered_handler("media/toggle_play")
def toggle_play_media(player):
    """
    Start or pause playing the current media stream,
    basing on the current state.

    :param player: PisakMediaPlayback instance.
    """
    if player.is_playing():
        player.pause()
    else:
        player.play()
    

@signals.registered_handler("media/play")
def play_media(player):
    """
    Start playing the media playback.

    :param player: media player instance.
    """
    player.play()


@signals.registered_handler("media/stop")
def stop_media(player):
    """
    Stop playing the media playback.

    :param player: media player instance.
    """
    player.stop()


@signals.registered_handler("media/pause")
def pause_media(player):
    """
    Pause playing the media playback.

    :param player: media player instance.
    """
    player.pause()


@signals.registered_handler("media/increase_volume")
def increase_volume(player):
    """
    Increase volume of the media playback.

    :param player: media player instance.
    """
    player.increase_volume()


@signals.registered_handler("media/decrease_volume")
def decrease_volume(player):
    """
    Decrease volume of the media playback.

    :param player: media player instance.
    """
    player.decrease_volume()


@signals.registered_handler("media/skip_forward")
def skip_forward(player):
    """
    Skip the media playback forward.

    :param player: media player instance.
    """
    player.skip_forward()


@signals.registered_handler("media/skip_backward")
def skip_backward(player):
    """
    Skip the media playback backward.
    
    :param player: media player instance.
    """
    player.skip_backward()


@signals.registered_handler("media/toggle_rewind_forward")
def toggle_rewind_forward(player):
    """
    Start or stop rewinding of the media playback forward.

    :param player: media player instance.
    """
    player.toggle_rewind_forward()


@signals.registered_handler("media/toggle_rewind_backward")
def toggle_rewind_backward(player):
    """
    Start or stop rewinding of the media playback backward.
    
    :param player: media player instance.
    """
    player.toggle_rewind_backward()


@signals.registered_handler("general/exit")
def exit_app(source):
    """
    Destroy stage of the given element.

    :param source: element whose stage should be destroyed.
    """
    source.get_stage().destroy()


@signals.registered_handler("general/start_group")
def start_group(source):
    """
    Start scanning group.

    :param source: signal source.
    """
    if source.get_property("mapped"):
        source.start_cycle()


@signals.registered_handler("general/kill_group")
def kill_group(source):
    """
    Stop scanning group, fatally.

    :param source: signal source.
    """
    source.killed = True


@signals.registered_handler("scanning/toggle_pause_group")
def toggle_pause_group(source):
    """
    Pause or restart to scan group.

    :param source: signal source.
    """
    source.paused = not source.paused


@signals.registered_handler("scanning/unpause_group")
def unpause_group(source):
    """
    Unpause the scanning of a group.

    :param source: signal source.
    """
    source.paused = False


@signals.registered_handler("pager/scan_page")
def scan_page(pager):
    """
    Start scanning the current page of the given pager.

    :param pager: pisak pager instance.
    """
    pager.scan_page()


@signals.registered_handler("pager/next_page")
def next_page(pager):
    """
    Move to the next page of the given pager.

    :param pager: pisak pager instance.
    """
    pager.next_page()


@signals.registered_handler("pager/previous_page")
def previous_page(pager):
    """
    Move to the previous page of the given pager.

    :param pager: pisak pager instance.
    """
    pager.previous_page()


@signals.registered_handler("pager/toggle_automatic")
def toggle_automatic(pager):
    """
    Turn on or turn off the automatic mode of pages flipping.

    :param pager: pisak pager instance.
    """
    if not pager.is_running:
        pager.run_automatic()
    else:
        pager.stop_automatic()


@signals.registered_handler("scanning/set_pending_group")
def set_pending_group(group):
    """
    Set the given group strategy's unwind to as the group's parent group.
    Set the given group as a pending group of its window.

    :param group: pisak scanning group instance.
    """
    group.parent_group = group.strategy.unwind_to
    pisak.app.window.pending_group = group


@signals.registered_handler("general/switch_label")
def switch_label(button):
    """
    Switch label on the given button.

    :param button: pisak button instance.
    """
    button.switch_label()


@signals.registered_handler("general/switch_icon")
def switch_icon(button):
    """
    Switch icon on the given button.

    :param button: pisak button instance.
    """
    button.switch_icon()


@signals.registered_handler("general/toggle_toggle")
def toggle_toggle(button):
    """
    Turn on or off the toggled state of the given button.

    :param button: pisak button instance.
    """
    if button.is_toggled():
        button.untoggle()
    else:
        button.toggle()


@signals.registered_handler("general/untoggle")
def untoggle(button):
    """
    Turn off the toggled state of the given button.

    :param button: pisak button instance.
    """
    button.untoggle()


@signals.registered_handler("general/toggle")
def toggle(button):
    """
    Turn on the toggled state of the given button.

    :param button: pisak button instance.
    """
    button.toggle()


@signals.registered_handler("general/set_working")
def set_working(button):
    """
    Turn on the working state of the given button.

    :param button: pisak button instance.
    """
    button.set_working()


@signals.registered_handler("general/set_unworking")
def set_unworking(button):
    """
    Turn off the working state of the given button.

    :param button: pisak button instance.
    """
    button.set_unworking()


@signals.registered_handler("general/toggle_working")
def toggle_working(button):
    """
    Turn on or turn off the working state of the given button.

    :param button: pisak button instance.
    """
    if button.is_working():
        button.set_unworking()
    else:
        button.set_working()
