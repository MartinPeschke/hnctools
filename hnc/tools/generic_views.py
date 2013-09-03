from pyramid.decorator import reify
from pyramid.httpexceptions import HTTPFound


def logout_func(TOKEN, AnonUserCls):
    def logout(ctxt, req):
        if TOKEN in req.session:
            del req.session[TOKEN]
        ctxt.user = AnonUserCls()
        raise HTTPFound(location = req.resource_url(ctxt))
    return logout


class BaseContext(object):
    children = {}
    workflow = None

    def __init__(self, parent, name):
        self.__name__ = name
        self.__parent__ = parent

    def __getitem__(self, item):
        return self.children[item](self, item)
    @reify
    def settings(self):
        return self.__parent__.settings
    @reify
    def request(self):
        return self.__parent__.request

    #=================================================== Hierarchy Helpers =============================================



    @reify
    def __hierarchy__(self):
        result = []
        p = self
        while p:
            result.append(p)
            p = p.__parent__
        return result[::-1]


    def get_main_area(self):
        return self.__hierarchy__[1] if len(self.__hierarchy__)>1 else None
    main_area = reify(get_main_area)

    def get_area_url(self, *args, **kwargs):
        return self.request.resource_url(self.main_area, *args, **kwargs)

    def get_sub_area(self):
        return self.__hierarchy__[2] if len(self.__hierarchy__)>2 else None
    sub_area = reify(get_sub_area)


