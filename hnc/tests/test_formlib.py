from datetime import datetime
from random import sample
import unittest
from BeautifulSoup import BeautifulSoup
from pyramid import testing
from hnc.forms.formfields import ChoiceField, MultipleFormField, StringField, DateField, Field, REQUIRED, HtmlAttrs


class DummyNamedModel(object):
    def __init__(self, key, val):
        self.key = key
        self.val = val
    def getKey(self, request): return self.key
    def getLabel(self, request): return self.val

def DUMMY_OPTIONS(n): return [DummyNamedModel(i, i) for i in range(n)]


class DummyRequest(object):
    def _(self, key): return key



class TestSimpleTemplatesFunctions(unittest.TestCase):
    def _callFUT(self, info):
        from pyramid.mako_templating import renderer_factory
        return renderer_factory(info)

    def _getLookup(self, name='mako.'):
        from pyramid.mako_templating import IMakoLookup
        return self.config.registry.getUtility(IMakoLookup, name=name)

    def setUp(self):
        import pyramid.mako_templating
        self.config = testing.setUp()
        self.config.add_settings({})
        self.config.add_renderer('.html', pyramid.mako_templating.renderer_factory)


    #Base Field Classes

    def test_field_all_classes(self):
        output = BeautifulSoup(Field('name', 'label', input_classes="INPUT_CLASS", control_classes="CONTROLS_CLASS", group_classes="GROUP_CLASS").render("FORM", DummyRequest(), {}, {}))
        self.assertTrue('GROUP_CLASS' in output.div['class'])
        self.assertTrue('CONTROLS_CLASS' in output.div.div['class'])
        self.assertTrue('INPUT_CLASS' in output.div.div.input['class'])

    def test_field_attrs_required(self):
        output = BeautifulSoup(Field('name', 'label', attrs = REQUIRED).render("FORM", DummyRequest(), {}, {}))
        self.assertEqual(output.find('input', 'required')['name'], "FORM.name")
        self.assertTrue("required" in output.find('div', 'control-group')['class'])

    def test_field_attrs_placeholder(self):
        output = BeautifulSoup(Field('name', 'label', attrs = HtmlAttrs(placeholder="REAL_PLACEHOLDER"), input_classes="SUPER_CLASS").render("FORM", DummyRequest(), {}, {}))
        self.assertEqual(output.find('input', 'SUPER_CLASS')['placeholder'], "REAL_PLACEHOLDER")

    def test_field_attrs_data(self):
        output = BeautifulSoup(Field('name', 'label', attrs = HtmlAttrs(placeholder="REAL_PLACEHOLDER", data_target_plan="TARGET_PLAN"), input_classes="SUPER_CLASS").render("FORM", DummyRequest(), {}, {}))
        self.assertEqual(output.find('input', 'SUPER_CLASS')['placeholder'], "REAL_PLACEHOLDER")
        self.assertEqual(output.find('input', 'SUPER_CLASS')['data-target-plan'], "TARGET_PLAN")


    #Choice Fields

    def test_zero_choices_field(self):
        output = BeautifulSoup(ChoiceField('name', 'label', lambda x: []).render("FORM", DummyRequest(), {}, {}))
        self.assertEqual(len(output.div.div.find("select").findAll("option")), 0)

    def test_many_choices_field(self):
        output = BeautifulSoup(ChoiceField('name', 'label', lambda x: DUMMY_OPTIONS(220)).render("FORM", DummyRequest(), {}, {}))
        self.assertEqual(len(output.div.div.find("select").findAll("option")), 220)

    def test_choice_name_field(self):
        prefix = ''.join(sample("abcdefgehijkkllmnoprstuvw", 10))
        output = BeautifulSoup(ChoiceField('name', 'label', lambda x: []).render(prefix, DummyRequest(), {}, {}))
        self.assertEqual(output.div.div.find("select")['name'], "{}.name".format(prefix))


    # Multi Form

    def _get_multi_form(self, values = {}, errors = {}):
        class Field(MultipleFormField):
            fields = [ StringField("enrolled", "Enrolled"), StringField("graduated", "Graduated") ]
        return BeautifulSoup(Field('VALUE', None).render("FORM", DummyRequest(), values, errors))

    def test_multi_form(self):
        form = self._get_multi_form()
        self.assertEqual(len(form.div.findAll("div", 'control-group')), 2)
        self.assertEqual(len(form.div.findAll("label")), 2)

    def test_multi_form_with_one_value(self):
        form = self._get_multi_form({"VALUE":[{'enrolled':2}]})
        self.assertEqual(len(form.div.findAll("div", 'control-group')), 2)

    def test_multi_form_with_many_values(self):
        form = self._get_multi_form({"VALUE":[{'enrolled':2}]*8})
        self.assertEqual(len(form.div.findAll("div", 'control-group')), 16)


    # DateFields

    def getDateField(self, format = "%Y-%m-%d", values= {}, errors= {}):
        return BeautifulSoup(DateField('VALUE', format=format).render("FORM", DummyRequest(), values, errors))

    def test_simple_date_validation(self):
        field = self.getDateField(format = "%Y-%m-%d", values = {'VALUE': datetime(2010, 12, 31)})
        self.assertEqual(field.find("input")['value'], "2010-12-31")

    def test_simple_date_validation(self):
        field = self.getDateField(format = "%d.%m.%Y", values = {'VALUE': datetime(2010, 12, 31)})
        self.assertEqual(field.find("input")['value'], "31.12.2010")





class DummyLookup(object):
    def __init__(self, exc=None):
        self.exc = exc

    def get_template(self, path):
        self.path = path
        return self

    def get_def(self, path):
        self.deffed = path
        return self

    def render_unicode(self, **values):
        if self.exc:
            raise self.exc
        self.values = values

class DummyRendererInfo(object):
    def __init__(self, kw):
        self.__dict__.update(kw)


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestSimpleTemplatesFunctions))
    return suite


