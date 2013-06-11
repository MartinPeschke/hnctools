STANDARD_VIEW_ATTRS = [{'attr' :"GET", 'request_method' : "GET"}]
STANDARD_FORM_ATTRS = [{'attr' :"GET", 'request_method' : "GET"}, {'attr' :"POST", 'request_method' : "POST"}]
JSON_HANDLER_ATTRS = [{'attr' :"ajax", 'request_method' : "POST", 'xhr' : True, 'renderer':'json'}]
JSON_FORM_ATTRS = [{'attr' :"GET", 'request_method' : "GET"}, {'attr' :"POST", 'request_method' : "POST", 'xhr' : False}, {'attr' :"ajax", 'request_method' : "POST", 'xhr' : True, 'renderer':'json'}]
JSON_LINK_ATTRS = [{'attr' :"GET", 'request_method' : "GET"}, {'attr' :"ajax", 'request_method' : "POST", 'xhr' : True, 'renderer':"json"}]

FULL_JSON_ATTRS = [{'attr' :"GET", 'request_method' : "GET", 'xhr' : False}, {'attr' :"POST", 'request_method' : "POST", 'xhr' : False}, {'attr' :"ajax", 'request_method' : "POST", 'xhr' : True, 'renderer':'json'}, {'attr' :"ajaxGET", 'request_method' : "GET", 'xhr' : True, 'renderer':'json'}]


class App(object):
    def __init__(self, name):
        self.name = name


class BaseRoute(object):
    def getRouteName(self, app_name, route_name = None):
        return route_name if route_name is not None else self.name

    def setup(self, apps, config):
        raise NotImplementedError()



def redirectView(toRoute, *args, **kwargs):
    def redirect(request):
        request.fwd(toRoute, *args, **kwargs)
    return redirect

class RedirectRoute(BaseRoute):
    renderer = None
    def __init__(self, name, path_exp, to_route, *args, **kwargs):
        self.name = name
        self.path_exp = path_exp
        self.to_route = to_route
        self.route_args = args
        self.route_kwargs = kwargs

    def setup(self, app, config):
        route_name =self.getRouteName(app.name)
        config.add_route(route_name, self.path_exp)
        view = redirectView(self.getRouteName(app.name, self.to_route), *self.route_args, **self.route_kwargs)
        config.add_view(view, route_name = route_name)



class FunctionRoute(BaseRoute):
    def __init__(self, name, path_exp, factory, view, renderer, route_attrs = {}):
        self.name = name
        self.path_exp = path_exp
        self.factory = factory
        self.view = view
        self.renderer = renderer
        self.route_attrs = route_attrs

    def setup(self, app, config):
        route_name =self.getRouteName(app.name)
        config.add_route(route_name, self.path_exp, factory = self.factory, **self.route_attrs)
        self.addView(config, route_name)

    def addView(self, config, route_name):
        if(self.view):config.add_view(self.view, route_name = route_name, renderer = self.renderer)

    def adjust_renderers(self, path):
        if self.renderer:
            if self.renderer.endswith(".html"):
                self.renderer = "{}{}".format(path, self.renderer)
            elif self.renderer.endswith(".xml"):
                self.renderer = "{}{}".format(path, self.renderer)


class OAuthLoginRoute(FunctionRoute):
    def __init__(self, name, path_exp, factory, view, renderer, route_attrs={}):
        super(OAuthLoginRoute, self).__init__(name, path_exp, factory, view, renderer, route_attrs)

    def setup(self, app, config):
        route_name =self.getRouteName(app.name)
        config.add_route(route_name, self.path_exp, factory = self.factory, **self.route_attrs)
        config.add_route('{}_login'.format(route_name), '{}/*traverse'.format(self.path_exp), factory = self.factory, use_global_views = True)
        self.addView(config, route_name)

    def addView(self, config, route_name):
        config.add_view(self.view, route_name = route_name, renderer = self.renderer)



class ClassRoute(FunctionRoute):
    def __init__(self, name, path_exp, factory, view, renderer = None, view_attrs = []):
        self.view_attrs = view_attrs
        super(ClassRoute, self).__init__(name, path_exp, factory, view, renderer)
    def addView(self, config, route_name):
        for attrs in self.view_attrs:
            attrs = attrs.copy()
            renderer = attrs.pop("renderer", self.renderer)
            config.add_view(view = self.view, route_name = route_name, renderer = renderer, **attrs)

class OAuthClassRoute(ClassRoute):
    def setup(self, app, config):
        route_name =self.getRouteName(app.name)
        config.add_route(route_name, self.path_exp, factory = self.factory, **self.route_attrs)
        config.add_route('{}_login'.format(route_name), '{}/*traverse'.format(self.path_exp), factory = self.factory, use_global_views = True)
        self.addView(config, route_name)


def route_factory(projectlabel, route_list, app, config, template_path_prefix):
    for route in route_list:
        route.adjust_renderers("{}:{}/templates/".format(projectlabel, template_path_prefix))
        route.setup(app, config)