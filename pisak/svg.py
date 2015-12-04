"""
Creation and modification of SVG images within PISAK.
"""
import re
import os

import gi

gi.require_version('Rsvg', '2.0')

from gi.repository import Rsvg

from pisak import exceptions, dirs


class PisakSVGError(exceptions.PisakException):
    """
    SVG related exception.
    """
    pass


class PisakSVG:
    """
    SVG file object being PISAK icon.
    """

    def __init__(self, name):
        super().__init__()
        self.path = dirs.get_icon_path(name)
        with open(self.path, 'r') as svg_file:
            self.string = svg_file.read()
        self.css = PisakCSS()
        self._style()

    def _style(self):
        """
        Add style to the svg.
        """
        parts = re.split('(<svg.*?>)', self.string, flags=re.DOTALL)
        self.styled_svg = ''.join([parts[0], parts[1], '\n',
                                   self.css.__str__(), '\n',
                                   parts[2]])

    def get_handle(self):
        """
        Returns Rsvg.Handle of styled svg.
        """
        return Rsvg.Handle.new_from_data(bytes(self.styled_svg,
                                               'utf-8'))

    def get_pixbuf(self):
        """
        Returns pixbuf from Rsvg.Handle of styled svg.
        """
        handle = self.get_handle()
        return handle.get_pixbuf()

    def change_color(self, color):
        """
        Change color of whole SVG.

        :param color: should be string, you can
        define color in hex, rgb(0-255, 0-255, 0-255)
        or word(ie. green, blue).
        """
        self.css.path = {'stroke' : str(color),
                         'fill' : str(color)}
        self.css.g = {'stroke' : str(color),
                      'fill' : str(color)}
        for i in range(1, 6):
            self.css.__setattr__('#L{}'.format(i), {'stroke' : str(color),
                                                    'fill' : str(color)})
        self._style()

    def change_color_selectively(self, color, node_name):
        """
        Change color of one of the nodes of the SVG
        or create such node with set colors.

        :param color: should be string, you can.
        define color in hex, rgb(0-255, 0-255, 0-255)
        or word(ie. green, blue).
        :param node_name: name of the node which color is to be changed.
        """
        self.css.__setattr__(node_name, {'stroke' : str(color),
                                         'fill' : str(color)})

class PisakCSS:
    """
    CSS object to style PisakSVG - icons.
    """

    def __init__(self):
        super().__init__()

    def __str__(self):
        """
        Convert PisakCSS to string.
        """
        braces = ['<style type="text/css">\n<![CDATA[',
                  ']]>\n</style>']
        node_braces = ['{', '}']
        string = ''
        for node_name, props in self.__dict__.items():
            node = '\n'.join(['{}: {};'.format(name, value) for
                              name, value in
                              props.items()])
            string = '{}\n{} {}\n{}\n{}\n'.format(string,
                                                  node_name,
                                                  node_braces[0],
                                                  node,
                                                  node_braces[1])
        string = "{0}\n{1}\n{2}".format(braces[0], string, braces[1])
        return string

    def __setattr__(self, node_name, props):
        """
        Update an existing node of name with props
        or create new node.

        :param node_name: name of the node as string.
        :param props: dic of pairs of property name
        (key of type string) and it's value(value of type string).
        """
        try:
            self.__getattribute__(node_name).update(props)
        except AttributeError:
            super().__setattr__(node_name, props)

    def delete_prop(self, node_name, prop):
        """
        Delete property from node.

        :param node_name: Node name from which to delete the property.
        :param prop: Property name to be deleted.
        """
        msg = '{}({}) does not exist.'
        try:
            del self.__getattribute__(node_name)[prop]
        except AttributeError:
            _LOG.warning(msg.format('Node', node_name))
        except KeyError:
            _LOG.warning(msg.format('Property', prop))
