import re
from formencode.validators import Invalid
from BeautifulSoup import BeautifulSoup
import formencode
from datetime import datetime
from babel.numbers import parse_decimal, format_decimal, NumberFormatError
from operator import methodcaller

import logging
log = logging.getLogger(__name__)

_ = lambda s: s


class Choice(object):
    def __init__(self, key, label, **kwargs):
        self.label = label
        self.key = key
        for k,v in kwargs.items():
            setattr(self, k, v)

    def getKey(self, state = None):
        return self.key or ''
    def getValue(self, state = None):
        return self.label
    getLabel = getValue




class SanitizedHTMLString(formencode.validators.String):
  messages = {"invalid_format":'There was some error in your HTML!'}
  valid_tags = ['a','strong', 'em', 'p', 'ul', 'ol', 'li', 'br', 'b', 'i', 'u', 's', 'strike', 'font', 'pre', 'blockquote', 'div', 'span', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6']
  valid_attrs = ['size', 'color', 'face', 'title', 'align', "style"]

  def linkAttrs(self, attrs):
    return [('href', attrs.get('href')), ('target', '_blank')]

  def sanitize_html(self, html):
      soup = BeautifulSoup(html)
      for tag in soup.findAll(True):
          if tag.name.lower() not in self.valid_tags:
              tag.extract()
          elif tag.name.lower() != "a":
              tag.attrs = [attr for attr in tag.attrs if attr[0].lower() in self.valid_attrs]
          else:
              attrs = dict(tag.attrs)
              tag.attrs = self.linkAttrs(attrs)
      val = soup.renderContents()
      return val.decode("utf-8")
  def _to_python(self, value, state):
    value = super(SanitizedHTMLString, self)._to_python(value, state)
    try:
      return self.sanitize_html(value)
    except Exception, e:
      log.error("HTML_SANITIZING_ERROR %s", value)
      raise formencode.Invalid(self.message("invalid_format", state, value = value), value, state)


class OneOfChoice(formencode.validators.OneOf):
    custom_attribute = 'custom'
    tabindex=5
    def keyToPython(self, value, state = None):
        return value
    
    def getKeys(self, state):
        return map(methodcaller("getKey", state), self.getItems(state))
    def getValues(self, state):
        return map(methodcaller("getValue", state), self.getItems(state))
    def getItems(self, state):
      return self.choices
    
    def _to_python(self, value, state):
        val = self.keyToPython(value, state)
        self.list = self.getKeys(state)
        if not val in self.list:
            if self.hideList:
                raise Invalid(self.message('invalid', state), val, state)
            else:
                try:
                    items = '; '.join(map(str, self.list))
                except UnicodeError:
                    items = '; '.join(map(unicode, self.list))
                raise Invalid(
                    self.message('notIn', state,
                        items=items, val=val), val, state)
        return val
    validate_python = formencode.FancyValidator._validate_noop
    
class OneOfChoiceInt(OneOfChoice):
    def keyToPython(self, value, state):
        if value is None: return None
        try:
            return int(value)
        except:
            raise Invalid(self.message('invalid', state), value, state)

class OneOfStateChoice(OneOfChoice):
    def getItems(self, request):
      obj = request
      for key in self.stateKey.split("."): obj = getattr(obj, key)
      return obj

class ManyOfStateChoice(OneOfChoice):
    def getItems(self, request):
        obj = request
        for key in self.stateKey.split("."): obj = getattr(obj, key)
        return obj
    def _to_python(self, value, state):
        if not isinstance(value, list): value = [value]
        values = [self.keyToPython(v, state) for v in value]
        self.list = self.getKeys(state)
        if len(set(values).difference(self.list)):
            if self.hideList:
                raise Invalid(self.message('invalid', state), values, state)
            else:
                try:
                    items = '; '.join(map(str, self.list))
                except UnicodeError:
                    items = '; '.join(map(unicode, self.list))
                raise Invalid(
                    self.message('notIn', state,
                        items=items, val=values), val, state)
        return values
    
class OneOfState(formencode.validators.OneOf):
    isChoice = True
    list = None
    stateKey = None
    testValueList = False
    hideList = False
    getValue = None
    getKey = None
    custom_attribute = 'custom'
    __unpackargs__ = ('list',)

    def getValues(self, request):
      obj = request
      for key in self.stateKey.split("."): obj = getattr(obj, key)
      return map(self.getValue, obj)
    def getKeys(self, request):
      obj = request
      for key in self.stateKey.split("."): obj = getattr(obj, key)
      return map(self.getKey, obj)
    def getItems(self, request):
      obj = request
      for key in self.stateKey.split("."): obj = getattr(obj, key)
      return obj
    def hasCustom(self, request):
      return len(filter(None, map(lambda item: getattr(item, self.custom_attribute, False),self.getItems(request)))) > 0

    def keyToPython(self, value, state = None):
        return value

    def customValueToPython(self, value, state = None):
        return value

    def _to_python(self, value, state):
        if isinstance(value, dict):
          custom = self.customValueToPython(value.get("custom", None), state)
          val = self.keyToPython(value.get("value", None), state)
          items = {self.getKey(s):getattr(s, self.custom_attribute, False) for s in self.getItems(state)}
          is_custom = items.get(val, False)
        else:
          is_custom = False
          val = self.keyToPython(value, state)
        self.list = self.getKeys(state)
        if not val in self.list:
            if self.hideList:
                raise Invalid(self.message('invalid', state), val, state)
            else:
                try:
                    items = '; '.join(map(str, self.list))
                except UnicodeError:
                    items = '; '.join(map(unicode, self.list))
                raise Invalid(
                    self.message('notIn', state,
                        items=items, val=val), val, state)
        else:
            # breaking change: this was
            # return custom if is_custom and custom else val

          return custom if is_custom else val

    validate_python = formencode.FancyValidator._validate_noop

class OneOfStateNoCustom(OneOfState):
    def hasCustom(self, req):
        return False

class OneOfStateInt(OneOfState):
    def keyToPython(self, value, state):
        if value is None: return None
        try:
            return int(value)
        except:
            raise Invalid(self.message('invalid', state), value, state)



class DateValidator(formencode.FancyValidator):
  messages = dict(
        badFormat=_('Please enter the date in the form %(format)s'),
        monthRange=_('Please enter a month from 1 to 12'),
        invalidDay=_('Please enter a valid day'),
        dayRange=_('That month only has %(days)i days'),
        invalidDate=_('That is not a valid day (%(exception)s)'),
        unknownMonthName=_('Unknown month name: %(month)s'),
        invalidYear=_('Please enter a number for the year'),
        fourDigitYear=_('Please enter a four-digit year after 1899'),
        wrongFormat=_('Please enter the date in the form %(format)s')
    )
  def _to_python(self, value, state):
    try:
      value = datetime.strptime(value, self.format)
      if value.year < 1900:
        raise formencode.Invalid(self.message('fourDigitYear', state), value, state)
    except ValueError, e:
      raise formencode.Invalid(self.message("badFormat", state, format = self.format.replace('%d', 'dd').replace('%m', 'mm').replace('%Y', 'yyyy')), value, state)
    else: return value








class DecimalValidator(formencode.FancyValidator):
  is_number_validator = True
  step = 0.01
  messages = {"invalid_amount":_(u'Bitte eine Zahl eingeben'),
        "amount_too_high":_(u"Bitte eine Zahl %(max_amount)s oder kleiner eingeben"),
        "amount_too_low":_(u"Bitte eine Zahl %(min_amount)s oder größer eingeben")
      }
  max = None
  min = None
  def _to_python(self, value, state):
    if not getattr(self, 'required', False) and not value:
        return getattr(self, 'if_missing', None)
    try:
      value = parse_decimal(value, locale = state._LOCALE_)
      if self.max and value > self.max:
        raise formencode.Invalid(self.message("amount_too_high", state, max_amount = format_decimal(self.max, locale=state._LOCALE_)), value, state)
      if self.min and value < self.min:
        raise formencode.Invalid(self.message("amount_too_low", state, min_amount = format_decimal(self.min, locale=state._LOCALE_)), value, state)
    except NumberFormatError, e:
      raise formencode.Invalid(self.message("invalid_amount", state, value = value), value, state)
    except ValueError, e:
      raise formencode.Invalid(self.message("amount_too_high", state, max_amount = format_decimal(self.max, locale=state._LOCALE_)), value, state)
    else: return value



def TypeAheadValidator(attrs):
    if attrs.required:
        validator = formencode.validators.String(required = True)
    else:
        validator = formencode.validators.String(required = False, not_empty = False, if_missing= '')
    return formencode.Schema(name = validator, token = validator, filter_extra_fields = True, required = False, if_missing= dict({'name':'', 'token':''}))



# Compound Form Validators

class LessThanEach(formencode.validators.FormValidator):
    field_names = None
    validate_partial_form = True
    format_ref = lambda s:s
    __unpackargs__ = ('*', 'field_names')

    messages = dict(
        notLess=_('Field should be greater than %(ref)s'),
        notDict=_('Fields should be a dictionary')
        )

    def __init__(self, *args, **kw):
        super(LessThanEach, self).__init__(*args, **kw)
        if len(self.field_names) < 2:
            raise TypeError('FieldsMatch() requires at least two field names')

    def _to_python(self, field_dict, state):
        try:
            errors = {}
            for i in xrange(1, len(self.field_names)):

                name = self.field_names[i]
                val = field_dict[name]
                lastVal = field_dict[self.field_names[i-1]]

                if lastVal >= val:
                    errors[name] = self.message('notLess', state, ref=self.format_ref(lastVal))

        except TypeError:
            # Generally because field_dict isn't a dict
            raise formencode.Invalid(self.message('notDict', state), field_dict, state)
        if errors:
            error_list = errors.items()
            error_list.sort()
            error_message = '<br>\n'.join(
                ['%s: %s' % (name, value) for name, value in error_list])
            raise formencode.Invalid(error_message, field_dict, state, error_dict=errors)

class SettlementValidator(formencode.validators.FormValidator):
    settlementOption = 'settlementOption'
    __unpackargs__ = ('settlementOption',)
    messages = {
        'MissingAField': _("SETTLEMENT_PAYPAL_EMAIL_MISSIN_Please enter a valid value"),
        'InvalidOption': _("SETTLEMENT_Invalid Settlement Option")
        }

    def validate_python(self, field_dict, state):
        errors = self._validateReturn(field_dict, state)
        if errors:
            error_list = errors.items()
            error_list.sort()
            raise formencode.Invalid(
                '<br>\n'.join(["%s: %s" % (name, value)
                               for name, value in error_list]),
                field_dict, state, error_dict=errors)

    def _validateReturn(self, field_dict, state):
        settlementOption = field_dict[self.settlementOption]
        values = field_dict.get(settlementOption)
        errors = {}
        try:
            so = state.merchant.map[settlementOption]
        except KeyError, e:
            errors["settlementOption"] = self.message('InvalidOption', state)
        else:
            for field in so.required_fields:
                try:
                    field.validator.to_python(values[field.name])
                except KeyError, e:
                    errors["settlementOption"] = self.message('MissingAField', state)
                except formencode.Invalid, e:
                    errors[settlementOption] = errors.get(settlementOption, {})
                    errors[settlementOption][field.name] = e
        return errors



# from bitbucket repo, patched for unicode support (not available in 1.2.6)
class URL(formencode.FancyValidator):
    """
    Validate a URL, either http://... or https://.  If check_exists
    is true, then we'll actually make a request for the page.

    If add_http is true, then if no scheme is present we'll add
    http://

    ::

        >>> u = URL(add_http=True)
        >>> u.to_python('foo.com')
        'http://foo.com'
        >>> u.to_python('http://hahaha.ha/bar.html')
        'http://hahaha.ha/bar.html'
        >>> u.to_python('http://xn--m7r7ml7t24h.com')
        'http://xn--m7r7ml7t24h.com'
        >>> u.to_python('http://xn--c1aay4a.xn--p1ai')
        'http://xn--c1aay4a.xn--p1ai'
        >>> u.to_python('http://foo.com/test?bar=baz&fleem=morx')
        'http://foo.com/test?bar=baz&fleem=morx'
        >>> u.to_python('http://foo.com/login?came_from=http%3A%2F%2Ffoo.com%2Ftest')
        'http://foo.com/login?came_from=http%3A%2F%2Ffoo.com%2Ftest'
        >>> u.to_python('http://foo.com:8000/test.html')
        'http://foo.com:8000/test.html'
        >>> u.to_python('http://foo.com/something\\nelse')
        Traceback (most recent call last):
            ...
        Invalid: That is not a valid URL
        >>> u.to_python('https://test.com')
        'https://test.com'
        >>> u.to_python('http://test')
        Traceback (most recent call last):
            ...
        Invalid: You must provide a full domain name (like test.com)
        >>> u.to_python('http://test..com')
        Traceback (most recent call last):
            ...
        Invalid: That is not a valid URL
        >>> u = URL(add_http=False, check_exists=True)
        >>> u.to_python('http://google.com')
        'http://google.com'
        >>> u.to_python('google.com')
        Traceback (most recent call last):
            ...
        Invalid: You must start your URL with http://, https://, etc
        >>> u.to_python('http://formencode.org/doesnotexist.html')
        Traceback (most recent call last):
            ...
        Invalid: The server responded that the page could not be found
        >>> u.to_python('http://this.domain.does.not.exist.example.org/test.html')
        ... # doctest: +ELLIPSIS
        Traceback (most recent call last):
            ...
        Invalid: An error occured when trying to connect to the server: ...

    If you want to allow addresses without a TLD (e.g., ``localhost``) you can do::

        >>> URL(require_tld=False).to_python('http://localhost')
        'http://localhost'

    By default, internationalized domain names (IDNA) in Unicode will be
    accepted and encoded to ASCII using Punycode (as described in RFC 3490).
    You may set allow_idna to False to change this behavior::

        >>> URL(allow_idna=True).to_python(u'http://\u0433\u0443\u0433\u043b.\u0440\u0444')
        'http://xn--c1aay4a.xn--p1ai'
        >>> URL(allow_idna=True, add_http=True).to_python(u'\u0433\u0443\u0433\u043b.\u0440\u0444')
        'http://xn--c1aay4a.xn--p1ai'
        >>> URL(allow_idna=False).to_python(u'http://\u0433\u0443\u0433\u043b.\u0440\u0444')
        Traceback (most recent call last):
            ...
        Invalid: That is not a valid URL
    """

    check_exists = False
    add_http = True
    require_tld = True
    allow_idna = True

    url_re = re.compile(r'''
        ^(http|https)://
        (?:[%:\w]*@)?                           # authenticator
        (?P<domain>[a-z0-9][a-z0-9\-]{,62}\.)*  # (sub)domain - alpha followed by 62max chars (63 total)
        (?P<tld>[a-z]{2,}|xn--[a-z0-9\-]{2,})   # TLD
        (?::[0-9]+)?                            # port

        # files/delims/etc
        (?P<path>/.*)?
        $
    ''', re.I | re.VERBOSE)

    scheme_re = re.compile(r'^[a-zA-Z]+:')

    messages = dict(
        noScheme=_('You must start your URL with http://, https://, etc'),
        badURL=_('That is not a valid URL'),
        httpError=_('An error occurred when trying to access the URL:'
                    ' %(error)s'),
        socketError=_('An error occured when trying to connect to the server:'
                      ' %(error)s'),
        notFound=_('The server responded that the page could not be found'),
        status=_('The server responded with a bad status code (%(status)s)'),
        noTLD=_('You must provide a full domain name (like %(domain)s.com)'))

    def _to_python(self, value, state):
        value = value.strip()
        if self.add_http:
            if not self.scheme_re.search(value):
                value = 'http://' + value
        # MP: commented because we really want the unicode, damn it
        # if self.allow_idna:
        #    value = self._encode_idna(value)
        if self.allow_idna:
           value = unicode(value)

        match = self.scheme_re.search(value)
        if not match:
            raise Invalid(self.message('noScheme', state), value, state)
        value = match.group(0).lower() + value[len(match.group(0)):]
        match = self.url_re.search(value)
        if not match:
            raise Invalid(self.message('badURL', state), value, state)
        if self.require_tld and not match.group('domain'):
            raise Invalid(
                self.message('noTLD', state, domain=match.group('tld')),
                value, state)
        if self.check_exists and (
                value.startswith('http://') or value.startswith('https://')):
            self._check_url_exists(value, state)
        return value

    def _encode_idna(self, url):
        global urlparse
        if urlparse is None:
            import urlparse
        scheme, netloc, path, params, query, fragment = urlparse.urlparse(url)
        try:
            return str(urlparse.urlunparse((
                scheme, netloc.encode('idna'), path, params, query, fragment)))
        except UnicodeError:
            return url

    def _check_url_exists(self, url, state):
        global httplib, urlparse, socket
        if httplib is None:
            import httplib
        if urlparse is None:
            import urlparse
        if socket is None:
            import socket
        scheme, netloc, path, params, query, fragment = urlparse.urlparse(
            url, 'http')
        if scheme == 'http':
            ConnClass = httplib.HTTPConnection
        else:
            ConnClass = httplib.HTTPSConnection
        try:
            conn = ConnClass(netloc)
            if params:
                path += ';' + params
            if query:
                path += '?' + query
            conn.request('HEAD', path)
            res = conn.getresponse()
        except httplib.HTTPException, e:
            raise Invalid(
                self.message('httpError', state, error=e), state, url)
        except socket.error, e:
            raise Invalid(
                self.message('socketError', state, error=e), state, url)
        else:
            if res.status == 404:
                raise Invalid(
                    self.message('notFound', state), state, url)
            if not 200 <= res.status < 500:
                raise Invalid(
                    self.message('status', state, status=res.status),
                    state, url)


