import urllib, logging, simplejson
from pyramid.response import Response
from pyramid.security import NO_PERMISSION_REQUIRED

log = logging.getLogger(__name__)


class JsonAwareRedirect(Exception):
    def __init__(self, location):
        self.location = location

def fwd_raw(request, location):
    raise JsonAwareRedirect(location = location)

def rld_url(request, with_query = True, *args, **kwargs):
    if with_query:
        return request.current_route_url(_query = request.GET, *args, **kwargs)
    else:
        return request.current_route_url(*args, **kwargs)

def rld(request, with_query = True, *args, **kwargs):
    raise JsonAwareRedirect(location = request.rld_url(with_query, *args, **kwargs))
def fwd(request, route_name, *args, **kwargs):
    raise JsonAwareRedirect(location = request.fwd_url(route_name, *args, **kwargs))

def fwd_url(request, route_name, secure = None, *args, **kwargs):
    if secure is None:
        secure = request.scheme == 'https'
    if secure:
        return request.route_url(route_name, _scheme = request.globals.secure_scheme, *args, **kwargs)
    else:
        return request.route_url(route_name, _scheme = "http", *args, **kwargs)

def ajax_url(request, route_name, secure = False, escaped = {}, *args, **kwargs):
    """
        evil hack to generate URLs with potential placeholders for underscore/handlebars templates like {{ TOKEN }}
    """
    tokens = {k:"###{}###".format(k.upper()) for k in escaped}
    params = tokens.copy()
    params.update(kwargs)
    url = request.fwd_url(route_name, secure = secure, *args, **params)
    for key,token in tokens.items():
        url = url.replace(urllib.quote(token), escaped[key])
    return url

def jsonAwareRedirectView(exc, request):
    if request.is_xhr:
        response = Response(simplejson.dumps({'redirect': exc.location}), 200, content_type = 'application/json')
    else:
        response = Response("Resource Found!", 302, headerlist = [('location', exc.location)])
    return response

    

def extend_request(config):
    def furl(request):
        try:
            return request.json_body['furl']
        except ValueError, e:
            return request.params.get("furl") or request.path_qs
    config.add_request_method(furl, 'furl', reify=True)

    def globals(request):
        return request.registry.settings["g"]
    config.add_request_method(globals, 'globals', reify=True)
    def backend(request):
        return request.globals.backend
    config.add_request_method(backend, 'backend', reify=True)

    config.add_request_method(fwd_raw)
    config.add_request_method(rld_url)
    config.add_request_method(rld)
    config.add_request_method(fwd)
    config.add_request_method(fwd_url)
    config.add_request_method(ajax_url)

    config.add_view(jsonAwareRedirectView, context=JsonAwareRedirect, permission = NO_PERMISSION_REQUIRED)
