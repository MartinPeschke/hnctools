from collections import OrderedDict
import formencode
from formencode.validators import Invalid
from formencode.variabledecode import variable_decode
from paste.httpexceptions import HTTPNotImplemented
from pyramid.httpexceptions import HTTPFound
from pyramid.renderers import render_to_response

from hnc.forms.messages import GenericErrorMessage, GenericSuccessMessage

import logging
from hnc.tools.request import redirect_response

log = logging.getLogger(__name__)


_ = lambda s:s

class InvalidCSRFToken(Exception):pass





class BaseHandler(object):
    def __init__(self, context, request):
        self.request = request
        self.context = context

    def __call__(self):
        request = self.request
        if request.is_xhr:
            result = getattr(self, 'ajax{}'.format(request.method))(self.context, self.request)
            return render_to_response("json", result, self.request)
        else:
            return getattr(self, request.method)(self.context, self.request)

class ValidatedFormHandlerMetaClass(type):
    def __new__(cls, name, bases, dct):
        if 'schemas' not in dct:
            if 'form' in dct:
                form = dct['form']
                dct['schemas'] = OrderedDict([(form.id, form)])
            elif 'forms' in dct:
                dct['schemas'] = OrderedDict([(form.id, form) for form in dct['forms']])
        return super(ValidatedFormHandlerMetaClass, cls).__new__(cls, name, bases, dct)


class FormHandler(BaseHandler):
    __metaclass__ = ValidatedFormHandlerMetaClass

    def __init__(self, context = None, request = None):
        self.request = request
        self.context = context
        self.result = {'values':{}, 'errors':{}, 'schemas' : self.schemas}
        ### generate groups error/value groups for each schema
        self.result['values'].update([(k,{}) for k in self.schemas.keys()])
        self.result['errors'].update([(k,{}) for k in self.schemas.keys()])

    def pre_fill_values(self, request, result):return result
    def add_globals(self, request, result):return result

    def GET(self, context, request):
        self.request.session.get_csrf_token()
        self.result = self.add_globals(self.request, self.result)
        self.result = self.pre_fill_values(self.request, self.result)
        return self.result

    def POST(self, context, request):
        try:
            return self.validate_form()
        except InvalidCSRFToken:
            self.result = self.add_globals(self.request, self.result)
            return self.result

    def ajaxPOST(self, context, request):
        result = self.validate_json()
        return result

    def validate_form(self):
        values = variable_decode(self.request.params)
        schema_id = values.get('type')
        if not schema_id: raise HTTPNotImplemented()
        try:
            resp = self.validate_values(values)
        except Invalid, error:
            log.error(error.error_dict)
            self.result['values'][schema_id] = error.value or {}
            self.result['errors'][schema_id] = error.error_dict or {}
            self.request.response.status_int = 401
        else:
            ### if validate_values/on_success returns anything else than a redirect, it must be some validation error
            if resp.get('message'):
                if resp.get('success') == True:
                    self.request.session.flash(GenericSuccessMessage(resp.get('message')), 'generic_messages')
                elif resp.get('success') == False:
                        self.request.session.flash(GenericErrorMessage(resp.get('message')), 'generic_messages')
            if resp.get('redirect'):
                # cannot be redirect exception inside an exception view
                return redirect_response(resp.get('redirect'))

            self.result['values'][schema_id] = resp.get('values', values)
            self.result['errors'][schema_id] = resp.get('errors', {})
            self.request.response.status_int = 401
        self.result = self.add_globals(self.request, self.result)
        return self.result

    def validate_json(self, renderTemplates = {}):
        values = self.request.json_body
        schema_id = values['type']

        def wrap_errors(errors):
            map = {}
            map[schema_id] = errors
            return formencode.variabledecode.variable_encode(map)

        try:
            form_result = self.validate_values(values)
        except Invalid, error:
            return {'success': False, 'values':error.value or {}, 'errors':wrap_errors(error.unpack_errors())}
        except HTTPFound, e: # success case
            return {'redirect': e.location}
        except InvalidCSRFToken:
            return {'success':False, 'errorMessage':_("An error occured, please try again.")}
        else:
            form_result.setdefault('success', False)
            form_result['errors'] = wrap_errors(form_result.get('errors', {}))
            return form_result


    def validate_values(self, values, renderTemplates = {}):
        req = self.request
        if values.get('token') != req.session.get_csrf_token():
            raise InvalidCSRFToken()
        try:
            ### determine actual form used in this submission
            schema_id = values['type']
            schema = self.schemas[schema_id]
            form = schema.getSchema(req, values)
        except KeyError, e:
            raise HTTPNotImplemented("Unexpected submission type!")
        else:
            form_result = form.to_python(values.get(schema_id), state=self.request)
            return schema.on_success(self.request, form_result)
