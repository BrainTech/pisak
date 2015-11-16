import cssutils

def _name_resolver(self, name):
        dec_name = name.replace(' ', '')
        pseudo_style_class = None
        style_class = None
        object_name = None
        if dec_name.contains(':'):
            dec_name = dec_name.split(':')
            pseudo_style_class = dec_name.pop()
            dec_name = dec_name[0]
        if dec_name.contains('.'):
            dec_name = dec_name.split(':')
            style_class = dec_name.pop()
            object_name = dec_name[0]
        else:
            object_name = dec_name
        return object_name, style_class, pseudo_style_class

class DictCss(dict):
    def __init__(self, path):
        self.css_path = path
        self.raw_css = None
        self._parse_css()

    def _parse_css(self):
        self.raw_css = cssutils.parseFile(self.css_path)
        for rule in self.raw_css.cssRules:
            if hasattr(rule, "selectorList"):
                object_name, style_class, pseudo_style_class = _name_resolver(
                rule.selectorText)
                if pseudo_style_class:
                    self[object_name].add_pseudo_style_class(
                        pseudo_style_class, {k : rule.style[k] in k for
                                             rule.style.keys()})
                elif style_class

# zrobic zagniezdzone obiekty sensowniej
                
class CssObject(object):
    def __init(self, name, props=None):
        self.name = name
        if props:
            assert isinstance(props, dict), "Properties must be a dict!"
            self.properties = props
        else:
            self.properties = {}
        self.style_classes = {}
        self.pseudo_style_classes = {}

    def add_style_class(self, name, props):
        assert isinstance(props, dict), "Properties must be a dict!"
        self.style_classes[name] = props

    def add_pseudo_style_class(self, name, props):
        assert isinstance(props, dict), "Properties must be a dict!"
        self.style_classes[name] = props

    def get_properties(self, full_name):
        name, style_class, pseudo_style_class = _name_resolver(full_name)
        assert name == self.name, "Wrong name!"
        props = self.properties.copy()
        if style_class:
            props.update(self.style_classes[style_class])
            if pseudo_style_class:
                props.update(
                    self.style_classes[style_class][pseudo_style_class])
        elif pseudo_style_class:
            props.update(self.pseudo_style_classes[pseudo_style_class])
        return props
