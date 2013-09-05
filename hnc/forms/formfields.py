from datetime import datetime
from operator import methodcaller, attrgetter
import formencode
from formencode.validators import OneOf
from hnc.forms.validators import TypeAheadValidator, DateValidator
from pyramid.renderers import render
import simplejson
from collections import OrderedDict, namedtuple
from hnc.tools.tools import deep_dict, dict_merge, deep_get


class NullConfigModel(object):
    name = None
    def getKey(self, request):return ''
    def getLabel(self, request):return '---'

GridClasses = namedtuple('GridClasses', ['form_classes', 'control_group_classes', 'label_classes', 'controls_classes', 'input_classes'])
NO_GRID = GridClasses('form-validated', '', '', '', '')
HORIZONTAL_GRID = GridClasses('form-validated form-horizontal', 'row', 'col col-lg-3', 'col col-lg-9', '')

GRID_BS3 = GridClasses('form-validated', 'form-group', 'control-label', 'controls', 'form-control')
HORIZONTAL_GRID_BS3 = GridClasses('form-validated form-horizontal', 'form-group', 'control-label col-lg-3', 'controls col-lg-9', 'form-control')


def normalize_key(k):
    return k.replace("_", "-")

def attrsStringify(attrs, keyMod = None, valMod = None):
    return ' '.join(['{}="{}"'.format(k, v) for k,v in attrs])



class HtmlAttrs(object):
    classes = ''
    def __init__(self, required = False, important = False, placeholder = '', **attrs):
        self.required = required
        self.important = important
        self.attrs = attrs
        if placeholder:
            self.attrs['placeholder'] = placeholder

    def getClasses(self):
        classes = self.classes
        if self.required: classes += ' required'
        if self.important: classes += ' important'
        return classes
    def getInputAttrs(self, request):
        _ = request._
        return attrsStringify([(normalize_key(k), _(v)) for k,v in self.attrs.items()])

    def getGroupAttrs(self): return ''
    getGroupClasses = getClasses

NONE = HtmlAttrs()
REQUIRED = HtmlAttrs(True)
IMPORTANT = HtmlAttrs(False, True)

class Placeholder(HtmlAttrs):
    def __init__(self, placeholder = '', required = False, important = False, **attrs):
        self.placeholder = placeholder
        self.required = required
        self.important = important
        self.attrs = attrs
        self.attrs['placeholder'] = placeholder

class DependentAttrs(HtmlAttrs):
    def __init__(self, placeholder, dependency, dependencyValue, required = False, important = False, **attrs):
        self.required = required
        self.important = important
        self.dependency = dependency
        self.dependencyValue = dependencyValue
        self.attrs = attrs
        self.attrs['placeholder'] = placeholder


    def getGroupClasses(self): return '{} dependent-control'.format(self.getClasses())
    def getGroupAttrs(self):
        return 'data-dependency="{}" data-dependency-value="{}"'.format(self.dependency, self.dependencyValue)

class PictureUploadAttrs(HtmlAttrs):
    def __init__(self, singleFile = True, types="jpg,gif,png", required = False, important = False, **attrs):
        self.singleFile = singleFile
        self.types = types
        self.required = required
        self.important = important
        self.attrs = attrs

    def getClasses(self): return ''
    def getGroupClasses(self): return 'file-upload-control'
    def getGroupAttrs(self):
        return 'data-upload-single="{}" data-file-types="{}"'.format(self.singleFile, self.types)









class BaseSchema(formencode.Schema):
    filter_extra_fields = False
    allow_extra_fields=True



class BaseFormMeta(type):
    def __new__(cls, name, bases, dct):
        if 'fields' in dct:
            dct['fieldMap'] = OrderedDict([(field.name, field) for field in dct['fields']])
        return super(BaseFormMeta, cls).__new__(cls, name, bases, dct)

class BaseForm(object):
    __metaclass__ = BaseFormMeta
    id = 'formdata'
    grid = NO_GRID
    fields = []
    extra_forms = []
    pre_validators = []
    chained_validators = []
    template = 'hnc.forms:templates/baseform.html'

    def __init__(self, **kwargs):
        for k,v in kwargs.items():
            setattr(self,  k, v)
        super(BaseForm, self).__init__()


    def render(self, request):
        return render(self.template, {'form': self}, request)

    @classmethod
    def getSchema(cls, request, values):
        pre_validators = list(cls.pre_validators)
        chained_validators = list(cls.chained_validators)

        validators = {}

        for v in cls.fields:
            if v and v.is_validated:
                val = v.getValidator(request)
                if isinstance(val, formencode.Schema):
                    pre_validators += val.pre_validators
                    chained_validators += val.chained_validators
                    val = val.fields

                validators = dict_merge(validators, val)
        for form in cls.extra_forms:
            validators[form.id] = form.getSchema(request)
        return BaseSchema(chained_validators=chained_validators, pre_validators=pre_validators, **validators)




class BaseField(object):
    is_validated = False
    html_help = None
    validator_args = {}
    classes = ''
    input_classes = ''
    group_classes = ''
    label_classes = ''
    input_classes = ''
    control_classes = ''
    attrs = NONE
    name = None


class HeadingField(BaseField):
    tag = 'legend'
    template = 'hnc.forms:templates/heading.html'
    def __init__(self, format_string, classes = ''):
        self.format_string = format_string
        self.classes = classes
    def getHeading(self, request, view):
        return unicode(self.format_string).format(request = request, view = view)
    def render(self, prefix, request, values, errors, view = None, grid = NO_GRID):
        return render(self.template, {'widget': self, 'view':view, 'grid': grid}, request)
    def getClasses(self):
        return self.classes
    renderControl = render

class PlainHeadingField(BaseField):
    def __init__(self, label, tag = 'h4', classes = ''):
        self.label = label
        self.tag = tag
        self.classes = classes
    def render(self, prefix, request, values, errors, view = None, grid = NO_GRID):
        return '<{0.tag} class="{0.classes}">{1}</{0.tag}>'.format(self, request._(self.label))
    renderControl = render


class Field(BaseField):
    template = 'hnc.forms:templates/basefield.html'
    is_validated = True
    if_empty = ''
    default = ''
    min = None
    max = None
    type = 'text'



    def __init__(self, name, label = None, attrs = NONE, **kwargs):
        self.name = name
        self.label = label
        self.attrs = attrs
        for k,v in kwargs.items():
            setattr(self, k, v)

    def getInputAttrs(self, request):
        attrs = self.attrs.getInputAttrs(request)
        if self.min:
            attrs += ' minlength="{}"'.format(self.min)
        if self.max:
            attrs += ' maxlength="{}"'.format(self.max)
        return attrs

    def getValidatorArgs(self):
        params = self.validator_args.copy()
        if self.validator_args: params.update(self.validator_args)

        params['required'] = self.attrs.required
        params['not_empty'] = self.attrs.required
        if self.min:
            params['min'] =self.min
        if self.max:
            params['max'] =self.max
        if not self.attrs.required:
            params.setdefault('if_missing', None)
        return params
    def getValidator(self, request):
        return deep_dict(self.name, self._validator(**self.getValidatorArgs()))

    def valueToForm(self, value): return '' if value is None else value

    def hasLabel(self):
        return bool(self.label)
    def getLabel(self, request):
        return request._(self.label)
    def getName(self, prefix):
        return '{}.{}'.format(prefix, self.name)
    def getClasses(self):
        return  '{} {}'.format(self.input_classes, self.attrs.getClasses())

    def getValues(self, name, request, values, errors, view):
        return {'value': deep_get(values, name, self.default), 'error':deep_get(errors, name, self.if_empty)}

    def render(self, prefix, request, values, errors, view = None, grid = NO_GRID):
        if isinstance(errors, formencode.Invalid):
            errors = errors.error_dict
        params = self.getValues(self.name, request, values, errors, view)
        params.update({'widget': self, 'prefix':prefix, 'view': view, 'grid': grid})
        return render(self.template, params, request)
    def renderControl(self, prefix, request, values, errors, view = None, grid = NO_GRID):
        if isinstance(errors, formencode.Invalid):
            errors = errors.error_dict
        params = self.getValues(self.name, request, values, errors, view)
        params.update({'widget': self, 'prefix':prefix, 'view': view, 'grid':grid})

        t = self.template.replace(".html", '#controls.html')
        return render(t, params, request)


class WrapField(BaseField):
    is_validated = True
    def __init__(self, tag = 'div', classes = '', *fields):
        self.tag = tag
        self.classes = classes
        self.fields = fields

    def render(self, prefix, request, values, errors, view = None, grid = NO_GRID):
        return '<{0.tag} class="{0.classes}">{1}</{0.tag}>'.format(self, ''.join([methodcaller("render", prefix, request, values, errors, view, grid), self.fields]))

    def getValidator(self, request):
        validators = {}
        for v in self.fields:
            if v and v.is_validated:
                validators = dict_merge(validators, v.getValidator(request))
        return validators



class MultipleFormField(Field):
    __metaclass__ = BaseFormMeta
    template = 'hnc.forms:templates/repeatableform.html'
    fields = []
    add_more_link_label = '+'
    positioned_label = ''
    prepend = False
    appendTarget = "embedded-form-fields"
    classes = 'form-embedded-wrapper'


    def getClasses(self):
        return self.classes

    def getValidator(self, request):
        validators = {}
        pre_validators = []
        chained_validators = []
        for v in self.fields:
            if v and v.is_validated:
                val = v.getValidator(request)
                if isinstance(val, formencode.Schema):
                    pre_validators += val.pre_validators
                    chained_validators += val.chained_validators
                    val = val.fields

                validators = dict_merge(validators, val)
        return {self.name : formencode.ForEach(BaseSchema(pre_validators=pre_validators, chained_validators=chained_validators, **validators), not_empty = self.attrs.required, convert_to_list = True, if_empty = None)}

    def render(self, prefix, request, values, errors, view = None, grid = NO_GRID):
        name = self.name
        return render(self.template, {'widget': self, 'prefix':"{}.{}".format(prefix, self.name), 'value': values.get(name, ''), 'error':errors.get(name, ''), 'view':view, 'grid': grid}, request)

    def getPositionedLabel(self, request, position):
        return '{} <span class="numbering">{}</span>'.format(request._(self.positioned_label), position)


class SubForm(Field):
    __metaclass__ = BaseFormMeta
    template = 'hnc.forms:templates/subform.html'
    fields = []
    if_empty = {}

    def getValidator(self, request):
        validators = {}
        for v in self.fields:
            if v and v.is_validated:
                validators = dict_merge(validators, v.getValidator(request))
        return {self.name : BaseSchema(**validators)}


class StaticHiddenField(Field):
    _validator = formencode.validators.String
    def __init__(self, name, value):
        self.name = name
        self.value = value
    def render(self, prefix, request, values, errors, view = None, grid = NO_GRID):
        return '<input type="hidden" name="{}" value="{}"/>'.format(self.getName(prefix), self.value)

class HiddenField(Field):
    _validator = formencode.validators.String
    def render(self, prefix, request, values, errors, view = None, grid = NO_GRID):
        return '<input type="hidden" name="{}" value="{}"/>'.format(self.getName(prefix), values.get(self.name, ''))

    def __init__(self, name):
        self.name = name


class StringField(Field):
    _validator = formencode.validators.String


class TextareaField(Field):
    template = 'hnc.forms:templates/textarea.html'
    _validator = formencode.validators.String

class IntField(Field):
    input_classes = 'digits'
    _validator = formencode.validators.Int
    maxlength = 6
    def getInputAttrs(self, request):
        attrs = self.attrs.getInputAttrs(request)
        if self.min:
            attrs += ' min="{}"'.format(self.min)
        if self.max:
            attrs += ' max="{}"'.format(self.max)
        if self.maxlength:
            attrs += ' maxlength="{}"'.format(self.maxlength)
        return attrs

class DecimalField(Field):
    input_classes = 'number'
    _validator = formencode.validators.Number


class URLField(Field):
    input_classes = 'input-xxlarge'
    _validator = formencode.validators.String

class EmailField(StringField):
    input_classes = ' email'
    type = 'email'
    validator_args = {'resolve_domain': True}
    _validator = formencode.validators.Email
class PasswordField(StringField):
    input_classes = ''
    type = 'password'
    validator_args = {'min': 6}
    _validator = formencode.validators.String

class CheckboxField(Field):
    template = 'hnc.forms:templates/checkbox.html'
    input_classes = 'checkbox'
    value = 'true'
    validator_args = {'if_missing': False}
    _validator = formencode.validators.StringBool

    def getValidator(self, request):
        return super(CheckboxField, self).getValidator(request)


class CheckboxPostField(CheckboxField):
    template = 'hnc.forms:templates/checkbox_post.html'
    input_classes = ''


class RadioBoolField(CheckboxField):
    template = 'hnc.forms:templates/radiobool.html'
    input_classes = 'radio'


class DateField(StringField):
    input_classes = 'date-field'
    format = "%Y-%m-%d"

    def valueToForm(self, value):
        if not value: return ''
        elif isinstance(value, basestring): return datetime.strptime(value, "%Y-%m-%dT%H:%M:%S").strftime(self.format)
        else: return value.strftime(self.format)

    def getValidator(self, request):
        return deep_dict(self.name, DateValidator(format = self.format, not_empty = self.attrs.required))



class ChoiceField(Field):
    template = 'hnc.forms:templates/dropdown.html'
    def __init__(self, name, label, optionGetter, attrs = NONE, **kwargs):
        self.optionGetter = optionGetter
        super(ChoiceField, self).__init__( name, label, attrs, **kwargs)

    def getValidator(self, request):
        return deep_dict(self.name, OneOf(map(methodcaller('getKey', request), self.optionGetter(request)), hideList = True))
    def getOptions(self, request):
        return self.optionGetter(request)
    def isSelected(self, option, value, request):
        return option.getKey(request) == value

class RadioChoice(ChoiceField):
    template = 'hnc.forms:templates/radioselect.html'
    input_classes = 'radio inline'

def configattr(name, default_none):
    def f(request):
        values = getattr(request.root.config, name)
        if default_none:
            values = [NullConfigModel()] + list(values)
        return values
    return f

class ConfigChoiceField(ChoiceField):
    def __init__(self, name, label, configAttr, default_none = False, attrs = NONE, **kwargs):
        optionGetter = configattr(configAttr, default_none)
        super(ConfigChoiceField, self).__init__(name, label, optionGetter, attrs, **kwargs)



class TypeAheadField(StringField):
    template = 'hnc.forms:templates/typeahead.html'
    if_empty = ''
    classes = 'typeahead'
    js_module = "libs/typeahead"
    def __init__(self, name, label, api_url, api_result, dependency = None, attrs = NONE, **kwargs):
        self.dependency = dependency
        self.api_result = api_result
        self.api_type = None
        self.api_url = api_url
        super(TypeAheadField, self).__init__(name, label, attrs, **kwargs)

class ConfigTypeAheadField(StringField):
    template = 'hnc.forms:templates/typeahead_config.html'
    if_empty = ''
    classes = 'configtypeahead'
    def __init__(self, name, label, configAttr, attrs = NONE, **kwargs):
        super(ConfigTypeAheadField, self).__init__(name, label, attrs, **kwargs)
        self.configAttr = configAttr



class TagSearchField(StringField):
    template = 'hnc.forms:templates/tagsearch.html'
    tag_class = "label label-info spaced text-small"
    tag_container_class = "current-tags"
    api_type = None
    classes = 'tagsearch'
    query_extra={}
    api_allow_new = True
    attrs = NONE
    group_classes = ''
    label_classes = ''
    input_classes = ''

    def __init__(self, name, label, api_url, api_result, **kwargs):
        super(TagSearchField, self).__init__(name, label, **kwargs)
        self.api_result = api_result
        self.api_allow_new = kwargs.get('api_allow_new', 'false')
        self.api_url = api_url
        if kwargs.get('query_extra'): self.query_extra = simplejson.dumps(kwargs.get('query_extra')).replace('"', '&quot;')
        else: self.query_extra = None

    def getValidator(self, request):
        return deep_dict(self.name, formencode.ForEach(name = formencode.validators.String(required=True)))

    def getValueData(self, name, request, value):
        return simplejson.dumps(value) if value else 'null'
    def getQueryExtra(self):
        if self.query_extra:
            return 'data-query-extra="{}"'.format(self.query_extra)
        else:
            return ''


class TokenTypeAheadField(StringField):
    template = 'hnc.forms:templates/typeahead_token.html'
    classes = 'typeahead'
    js_module = "libs/typeahead"
    def __init__(self, name, label, api_url, api_result, dependency = None, attrs = NONE, **kwargs):

        super(TokenTypeAheadField, self).__init__(name, label, attrs, **kwargs)
        self.dependency = dependency
        self.api_result = api_result
        self.api_url = api_url

    def getValidator(self, request):
        return deep_dict(self.name, TypeAheadValidator(self.attrs))

    def getValues(self, name, request, values, errors, view):
        return {'value': deep_get(values, name, {}), 'error':deep_get(errors, name, {})}







# =========================== COMPOUNDS

def MultiConfigChoiceField(name, label, configKey, *args, **kwargs):
    class cls(MultipleFormField):
        fields = [
            ConfigChoiceField(name, label, configKey)
        ]
    return cls(*args, **kwargs)





class CombinedField(StringField):
    template = 'hnc.forms:templates/combined.html'
    def __init__(self, fields, label, *args, **kwargs):
        super(StringField, self).__init__(None, label, *args, **kwargs)
        self.fields = fields
    def getValidator(self, request):
        validator = {}
        for w in self.fields:
            if w.name:
                dict_merge(validator, w.getValidator(request))
        return validator
    def getValues(self, name, request, values, errors, view):
        # this probably breaks on dotted notation
        return {'value': values, 'error':{f.name: errors.get(f.name) for f in self.fields if errors.get(f.name)}}