"""
Module with various Pisak utility functions.
"""
import os
import functools
import time
from datetime import datetime

import json
from lxml import etree

from gi.repository import Clutter
import pydenticon

from pisak import logger


_LOG = logger.get_logger(__name__)


def json_to_xml(json_path):
    """
    Convert file containing UI definition in the JSON format to the one in
    the XML format.

    :param json_path: path to a json file.

    :return: path to a xml file or None if conversion failed.
    """
    def register_json_objects(json_obj):
        if isinstance(json_obj, list):
            for obj in json_obj:
                register_json_objects(obj)
        elif isinstance(json_obj, dict):
            keys = json_obj.keys()
            if "id" in keys:
                obj_id = json_obj["id"]
                if obj_id == "main":
                    obj_id = "interface"
                json_objects[obj_id] = json_obj
            if "children" in keys:
                for child in json_obj["children"]:
                    register_json_objects(child)
        else:
            msg = "Accepted are single JSON object being a dictionary" \
                        "or list containing many JSON objects."
            _LOG.warning(msg)

    def create_xml_tree(parent, child, top_level=False):
        if isinstance(child, str):
            child = json_objects[child]
        if top_level:
            child_el = parent
        else:
            child_el = etree.SubElement(parent, "child")
        child_attrib = child_el.attrib
        obj_el = etree.SubElement(child_el, "object")
        obj_attrib = obj_el.attrib
        for param, value in child.items():
            if param == "type":
                obj_attrib["class"] = value
            elif param == "class":
                obj_attrib[param] = value
            elif param == "id":
                obj_attrib[param] = value
            elif param == "signals":
                for signal in value:
                    add_xml_signal(obj_el, signal)
            elif param == "children":
                for child in value:
                    create_xml_tree(obj_el, child)
            elif param == "internal-child" and not top_level:
                child_attrib[param] = value
            else:
                add_xml_property(obj_el, param, value)

    def add_xml_property(element, name, value):
        prop_el = etree.SubElement(element, "property", name=name)
        prop_el.text = str(value)

    def add_xml_signal(element, signal):
        name = signal["name"]
        handler = signal["handler"]
        sig_el = etree.SubElement(element, "signal", name=name,
                              handler=handler)
        object_id = signal.get("object")
        if object_id:
            sig_el.attrib["object"] = object_id

    json_objects = {}
    json_list = None
    xml_file = None
    with open(json_path, 'r') as json_file:
        json_list = json.load(json_file)
    if not json_list:
        _LOG.warning("Failed to open json file: {}".format(json_path))
        return
    register_json_objects(json_list)
    main_xml_el = etree.Element("interface")
    create_xml_tree(main_xml_el, json_objects["interface"], True)
    xml_string = etree.tostring(main_xml_el, pretty_print=True,
                                xml_declaration=True, encoding='utf-8')
    xml_path = os.path.splitext(json_path)[0] + ".xml"
    with open(xml_path, 'wb') as xml_file:
        xml_file.write(xml_string)
    if xml_file:
        return xml_path
    else:
        _LOG.warning("Failed to generate xml file from the json file: {}".format(
                json_path))


def _local_tz_datetime_offset():
    """
    Offset of the local time zone time relative to the UTC.

    :return: datetime delta object with the offset.
    """
    now = time.time()
    return datetime.fromtimestamp(now) - datetime.utcfromtimestamp(now)


def utc_datetime_to_local_str(utc_dt, format):
    """
    Convert UTC datetime to the local time zone datetime
    and format it as a string.

    :param utc_dt: UTC datetime.

    :return: string with the local time zone datetime.
    """
    return (utc_dt + _local_tz_datetime_offset()).strftime(format)


def date_to_when(date):
    """
    Convert numerical date and time from the past to more human friendly time
    description, relative to the current time.

    :param date: datetime.

    :return: string with time description.
    """
    def compare_unit(unit, unit_name_base):
        last_digit = int(str(int(unit))[-1])
        if 22 <= unit and 2 <= last_digit < 5:
            unit_name = unit_name_base + "y"
        elif 22 <= unit and (5 <= last_digit or last_digit <= 1):
            unit_name = unit_name_base
        elif 5 <= unit < 22:
            unit_name = unit_name_base
        elif 2 <= unit < 5:
            unit_name = unit_name_base + "y"
        elif unit == 1:
            unit_name = unit_name_base + "ę"
        return str(int(unit)) + " " + unit_name + " " + ago

    if not isinstance(date, datetime):
        msg = "Date must be an instance of the datetime.datetime from the" \
             "python standard library."
        _LOG.warning(msg)
        raise TypeError(msg)
    ago = "temu"
    date += _local_tz_datetime_offset()  # add offset of the local time rel to the UTC
    delta = datetime.today() - date
    seconds = delta.seconds if delta.seconds >= 0 else 0
    minutes = seconds // 60 if seconds >= 0 else 0
    hours = minutes // 60
    days = delta.days
    years = delta.days // 365
    months = delta.days // 30
    if 2 <= years:
        when = str(date)
    elif years == 1:
        when = "rok " + ago
    elif years < 1 <= months :
        if 5 <= months:
            month = "miesięcy"
        elif 2 <= months < 5:
            month = "miesiące"
        elif months == 1:
            month = "miesiąc"
        when = str(int(months)) + " " + month + " " + ago
    elif months == 0 and 1 <= days:
        if 1 < days:
            when = str(int(days)) + " dni " + ago
        elif days == 1:
            when = "wczoraj"
    elif days == 0 and 1 <= hours:
        when = compare_unit(hours, "godzin")
    elif hours == 0 and 1 <= minutes:
        when = compare_unit(minutes, "minut")
    elif minutes == 0 and 1 <= seconds:
         when = compare_unit(seconds, "sekund")
    elif seconds == 0:
        when = "teraz"
    return when


def find_folder_image(dir_files, folder_name, folder_path, image_extensions):
    """
    Find image representing the given folder.

    :param dir_files: list of files in the given folder among
    whom the search will be conducted.
    :param folder_name: name of the given folder.
    :param folder_path: full path of the folder.
    :param image_extensions: possible extensions of the potential image file.

    :return: path to a file or None if nothing found.
    """
    for file in dir_files:
        file_name, ext = os.path.splitext(file.lower())
        if ext in image_extensions and (
                "cov" in file_name or "fold" in file_name or
                file_name in folder_name):
            return os.path.join(folder_path, file)


def produce_identicon(string, bins_count=(10, 10), size=(600, 600),
                      save_path=None, image_format="png",
                      background="rgb(230, 230, 230)", foreground=None):
    """
    Generate identicon picture from hashtag corresponding to the given string.

    :param string: string to be transformed into identicon.
    :param bins_count: tuple with numbers of bins in one row and one column.
    :param size: tuple with width and height of the resulting picture in px.
    :param save_path: path that the resulting picture will be located at,
    if None the resulting picture will not be saved on disc.
    :param foreground: colors to be used as the foregrounds.
    :param background: colors to be used as the backgrounds.
    :param image_format: format of the output image file.

    :return: freshly generated identicon, as bytes buffer.
    """
    if not foreground:
        foreground = ["rgb(45,79,255)", "rgb(254,180,44)",
                      "rgb(226,121,234)", "rgb(30,179,253)",
                      "rgb(232,77,65)", "rgb(49,203,115)",
                      "rgb(141,69,170)"]
    try:
        gen = pydenticon.Generator(bins_count[0], bins_count[1],
                               foreground=foreground, background=background)
    except ValueError:
        gen = pydenticon.Generator(4, 4,
                               foreground=foreground, background=background)
    identicon = gen.generate(string, size[0], size[1],
                             output_format=image_format)
    if save_path:
        with open(save_path, "wb") as file:
            file.write(identicon)
    return identicon


def convert_color(color):
    """
    Return tuple with color bands normalized int values converted from
    the given color.

    :param color: instance of ClutterColor or string color description
    in one of the formats accepted by ClutterColor.

    :return: 4-element tuple.
    """
    if isinstance(color, Clutter.Color):
        clutter_color = color
    else:
        clutter_color = Clutter.Color.new(0, 0, 0, 255)
        clutter_color.from_string(color)
    return hex_to_rgba(clutter_color.to_string())


def hex_to_rgba(value):
    """
    Convert given color description in a hexadecimal format
    to normalized int values for separate color bands.

    :param value: color desc in hexadecimal format as returned by ClutterColor
    to_string method, that is: #rrggbbaa.

    :return: 4-element tuple.
    """
    rgba = ()
    for idx in range(1, 9, 2):
        rgba += (int(value[idx:idx+2], 16)/255.,)
    return rgba
