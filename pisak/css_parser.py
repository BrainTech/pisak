from collections import UserDict
import logging
import cssutils

cssutils.log.setLevel(logging.CRITICAL)

def resolve_name(name):
    dec_name = name.replace(' ', '')
    pseudo_style_class = None
    style_class = None
    object_name = None
    if ':' in dec_name:
        dec_name = dec_name.split(':')
        assert len(dec_name) == 2, ("It is assumed that an object has one"
                                    " pseudo-style-class defined")
        pseudo_style_class = dec_name[1]
        dec_name = dec_name[0]
    if '.' in dec_name:
        dec_name = dec_name.split('.')
        assert len(dec_name) == 2, ("It is assumed that an object has one"
                                    " style-class defined")
        style_class = dec_name[1]
        object_name = dec_name[0]
    else:
        object_name = dec_name
    return object_name, style_class, pseudo_style_class


class PropsDict(UserDict):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._properties = {}
        self._children = []

    def __setitem__(self, key, value):
        super().__setitem__(key, value)
        self._children.append(key)

    def __repr__(self):
        if self == {}:
            return 'properties - {}'.format(repr(self._properties))
        else:
            return super().__repr__()
        
    @property
    def properties(self):
        return self._properties

    @properties.setter
    def properties(self, value):
        self._properties = value

    @property
    def children(self):
        return self._children
                

class CssToDict(UserDict):
    def __init__(self, path):
        super().__init__()
        self.css_path = path
        self.raw_css = None
        self._parse_css()

    def _parse_css(self):
        self.raw_css = cssutils.parseFile(self.css_path)
        rule_gen = (rule for rule in self.raw_css.cssRules
                    if hasattr(rule, "selectorList"))
        for rule in rule_gen:
            class_names = rule.selectorText.replace(' ', '').split(',')
            for class_name in class_names:
                object_name, style_class, pseudo_style_class = resolve_name(
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
                elif object_name:
                    self[object_name].properties = dict(rule.style)
                else:
                    raise Warning("Func {} returned only Nones".format(
                        resolve_name))


    def get_properties(self, full_name):
        name, style_class, pseudo_style_class = resolve_name(full_name)
        props = self[name].properties.copy()
        if style_class:
            props.update(self[name][style_class].properties)
            if pseudo_style_class:
                props.update(
                    self[name][style_class][pseudo_style_class].properties)
        elif pseudo_style_class:
            props.update(self[name][pseudo_style_classes].properties)
        return props
