import logging
import cssutils

cssutils.log.setLevel(logging.CRITICAL)


class PropsDict(dict):
    '''
    A dictionary with properties.
    Shows properties if no record inside.
    '''
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._properties = {}

    def __setitem__(self, key, value):
        super().__setitem__(key, value)

    def __repr__(self):
        if self == {}:
            return 'properties - {}'.format(repr(self._properties))
        else:
            return super().__repr__()
        
    @property
    def properties(self):
        '''
        Properties of the record stored within the dict.
        '''
        return self._properties

    @properties.setter
    def properties(self, value):
        self._properties = value
                

class CssDict(dict):
    '''
    A nested dict of PropsDict's that are css classes, theirs style
    and pseudo classes.

    :param path: path to the css file that is to be converted to dict
    '''
    def __init__(self, path):
        super().__init__()
        self.css_path = path
        self.raw_css = None
        self._parse_css()

    @staticmethod
    def resolve_class_name(name):
        '''
        Helper function to decompose the css class name
        into class name, style, and pseudo-style.

        :param name: css descriptor of class (e.g. MxLabel.PisakLabel:hover)

        :returns: class name, style-class name, pseudo-style-class name
        '''
        dec_name = name.replace(' ', '')
        pseudo_style_class = None
        style_class = None
        if ':' in dec_name:
            dec_name = dec_name.split(':')
            pseudo_style_class = dec_name[-1]
            dec_name = dec_name[0]
        if '.' in dec_name:
            dec_name = dec_name.split('.')
            style_class = dec_name[-1]
            object_name = dec_name[0]
        else:
            object_name = dec_name
        return object_name, style_class, pseudo_style_class

    def _parse_css(self):
        self.raw_css = cssutils.parseFile(self.css_path)
        rule_gen = (rule for rule in self.raw_css.cssRules
                    if hasattr(rule, "selectorList"))
        for rule in rule_gen:
            class_names = rule.selectorText.replace(' ', '').split(',')
            for class_name in class_names:
                object_name, style_class, pseudo_style_class = self.resolve_class_name(
                    class_name)
                if object_name not in self:
                    self[object_name] = PropsDict()
                if pseudo_style_class:
                    pseudo_dict = PropsDict()
                    pseudo_dict.properties = dict(rule.style)
                    if style_class:
                        if style_class not in self[object_name]:
                            self[object_name][style_class] = PropsDict()
                        self[object_name][style_class][pseudo_style_class] = \
                            pseudo_dict
                            
                elif style_class:
                    style_dict = PropsDict()
                    style_dict.properties = dict(rule.style)
                    self[object_name][style_class] = style_dict
                else:
                    self[object_name].properties = dict(rule.style)

    def get_properties(self, full_name):
        '''
        Getter of properties for a css descriptor.
        Merges properties of the class, style-class and pseudo-style-class.

        :param full_name: A css descriptor (e.g. MxLabel.PisakLabel:hover)

        :returns: dict with properties for given css descriptor
        '''
        name, style_class, pseudo_style_class = self.resolve_class_name(full_name)
        props = self[name].properties.copy()
        if style_class:
            props.update(self[name][style_class].properties)
            if pseudo_style_class:
                props.update(
                    self[name][style_class][pseudo_style_class].properties)
        elif pseudo_style_class:
            props.update(self[name][pseudo_style_class].properties)
        return props
