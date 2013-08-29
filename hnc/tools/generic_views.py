from pyramid.httpexceptions import HTTPFound


def logout_func(TOKEN, AnonUserCls):
    def logout(ctxt, req):
        if TOKEN in req.session:
            del req.session[TOKEN]
        ctxt.user = AnonUserCls()
        raise HTTPFound(location = req.resource_url(ctxt))
    return logout
