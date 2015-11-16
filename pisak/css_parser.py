from collections import UserDict
import cssutils


def name_resolver(name):
    dec_name = name.replace(' ', '')
    pseudo_style_class = None
    style_class = None
    object_name = None
    if ':' in dec_name:
        dec_name = dec_name.split(':')
        pseudo_style_class = dec_name.pop()
        dec_name = dec_name[0]
    if '.' in dec_name:
        dec_name = dec_name.split('.')
        style_class = dec_name.pop()
        object_name = dec_name[0]
    else:
        object_name = dec_name
    return object_name, style_class, pseudo_style_class


class StyleDict(UserDict):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._properties = {}
        self._child_styles = []

    def __setitem__(self, key, value):
        super().__setitem__(key, value)
        self._child_styles.append(key)

    def __repr__(self):
        if not self:
            return 'properties - {}'.format(self.properties.__repr__())
        else:
            return '{}'.format(super().__repr__())
        
    @property
    def properties(self):
        return self._properties

    @properties.setter
    def properties(self, value):
        self._properties = value

    @property
    def child_styles(self):
        return self._child_styles
                

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
                object_name, style_class, pseudo_style_class = name_resolver(
                class_name)
                if object_name not in self.keys():
                    self[object_name] = StyleDict()
                if pseudo_style_class:
                    pseudo_dict = StyleDict()
                    pseudo_dict.properties = {k: rule.style[k] for k in
                                              rule.style.keys()}
                    if style_class:
                        if style_class not in self[object_name].keys():
                            self[object_name][style_class] = StyleDict()
                        self[object_name][style_class][pseudo_style_class] =\
                        pseudo_dict
                            
                elif style_class:
                    style_dict = StyleDict()
                    style_dict.properties = {k: rule.style[k] for k in
                                             rule.style.keys()}
                    self[object_name][style_class] = style_dict
                elif object_name:
                    self[object_name].properties = {k: rule.style[k] for k in
                                                    rule.style.keys()}
                else:
                    raise Warning("Func {} returned only None".format(
                        name_resolver))


    def get_properties(self, full_name):
        name, style_class, pseudo_style_class = name_resolver(full_name)
        props = self[name].properties.copy()
        if style_class:
            props.update(self[name][style_class].properties)
            if pseudo_style_class:
                props.update(
                    self[name][style_class][pseudo_style_class].properties)
        elif pseudo_style_class:
            props.update(self[name][pseudo_style_classes].properties)
        return props
