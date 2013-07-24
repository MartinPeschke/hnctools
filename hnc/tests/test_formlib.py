from random import sample
import unittest
from bs4 import BeautifulSoup
from pyramid import testing
from hnc.forms.formfields import ChoiceField

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

    def test_zero_choices_field(self):
        output = BeautifulSoup(ChoiceField('name', 'label', lambda x: []).render("FORM", DummyRequest(), {}, {}))
        self.assertEqual(len(output.div.div.find("select").find_all("option")), 0)

    def test_many_choices_field(self):
        output = BeautifulSoup(ChoiceField('name', 'label', lambda x: DUMMY_OPTIONS(220)).render("FORM", DummyRequest(), {}, {}))
        self.assertEqual(len(output.div.div.find("select").find_all("option")), 220)

    def test_choice_name_field(self):
        prefix = ''.join(sample("abcdefgehijkkllmnoprstuvw", 10))
        output = BeautifulSoup(ChoiceField('name', 'label', lambda x: []).render(prefix, DummyRequest(), {}, {}))
        self.assertEqual(output.div.div.find("select")['name'], "{}.name".format(prefix))







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


