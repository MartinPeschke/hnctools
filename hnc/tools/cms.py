import logging
import polib
from pyramid.path import AssetResolver
from hnc.apiclient.cached import CachedLoader


log = logging.getLogger(__name__)


class StaticContentLoader(object):
    def __init__(self, request, cache, debug):
        self.content = cache.get(request)
        self.debug = debug
        self.cache = cache
        super(StaticContentLoader, self).__init__()

    def refresh(self, request):
        self.cache.refresh(request)

    def __call__(self, key, display_default = True, **kwargs):
        result = self.content.get(key)
        if result is None:
            result = u'###{}###'.format(key) if display_default else  ''
        else:
            result = result.format(kwargs)
        if self.debug:
            result = u'<!-- {} -->{}'.format(key, result)
        return result



def add_content(dictionary_factory, instance_name):
    """
        dictionary_factory: receives request as parameter, returns a dictionary of all static content, the result gets cached, so this is the interface to some persistent storage
    """
    cache = CachedLoader(dictionary_factory, "STATIC_CONTENT:{}".format(instance_name))
    def add_content_impl(event):
        request = event.request
        request._ = StaticContentLoader(request, cache, request.globals.is_debug)
    return add_content_impl


def extend_request_with_content_mgmt(config, potfile_asset_spec, dictionary_factory):
    """
        provide static content backend for hnc projects, text-keys are provided by babel message extractors into the domain.pot file, this is usually located in the root/locale folder

        config: is pyramid configuration instance
        potfile_asset_spec: describing path to potfile message catalog
        render_ctxt_info: is a function with request as sole parameter, when returns truthy value, additional HTML comments are rendered before the output text, normally only admins are interested in this
    """

    def add_renderer_variables(event):
        if event['renderer_name'] != 'json':
            request = event['request']
            event.update({'_' : request._})
        return event

    a = AssetResolver()
    asset_path = a.resolve(potfile_asset_spec)
    if not asset_path.exists():
        raise ValueError("POTFILE does not exist in specified location: {}".format(potfile_asset_spec))
    config.add_subscriber(add_content(dictionary_factory, potfile_asset_spec), 'pyramid.events.ContextFound')
    config.add_subscriber(add_renderer_variables, 'pyramid.events.BeforeRender')


    pofile = polib.pofile(asset_path.abspath())
    def pofile_view(request): return pofile
    config.add_request_method(pofile_view, "_msg_catalog_")


