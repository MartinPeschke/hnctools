import logging
from datetime import datetime
from decimal import Decimal
from string import Template
from babel import negotiate_locale, Locale
from babel.numbers import format_currency, format_decimal, get_currency_symbol, get_decimal_symbol, get_group_symbol, parse_number
from babel.dates import format_date, format_datetime, format_time
from pyramid.i18n import get_localizer, TranslationStringFactory


log = logging.getLogger(__name__)



class I18N(object):
    def get_locale(self, request):
        return request._LOCALE_

    def __init__(self, request):
        self.locale = self.get_locale(request)

    def format_int_amount(self, number):
        if number is None:
            return ''
        number = float(number)/100
        if round(number) == number:
            return '%d' % int(number)
        else:
            fnumber = Decimal('%.2f' % number)
            return format_decimal(fnumber, format='#,##0.00', locale=self.locale)

    def get_thous_sep(self):
        return get_group_symbol(locale=self.locale)

    def get_dec_sep(self):
        return get_decimal_symbol(locale=self.locale)

    def display_currency(self, currency):
        return get_currency_symbol(currency, locale=self.locale)

    def format_currency(self, number, currency):
        if round(number) == number:
            return u'€{}'.format(int(number))
        else:
            fnumber = Decimal('%.2f' % number)
            return format_currency(fnumber, currency, locale = self.locale)

    def parse_number(self, strNum):
        return parse_number(strNum, locale=self.locale)

    def format_number(self, number):
        if number is None or number=="": return ""
        fnumber = Decimal('%.2f' % number)
        return format_decimal(fnumber, format='#,##0.##;-#', locale=self.locale)

    def format_date(self, date, with_time = False, format="medium"):
        if not date: return ""
        if with_time:
            return format_datetime(date, format=format, locale=self.locale)
        else:
            return format_date(date, format=format, locale=self.locale)

    def format_time(self, datetime, format="short"):
        if not datetime: return ""
        return format_time(datetime, format=format, locale=self.locale)

    def parse_date_internal(self, date):
        return datetime.strptime(date, "%Y-%m-%d")

    def format_date_internal(self, date):
        if not date: return ""
        return date.strftime('%Y-%m-%d')

    def format_datetime_internal(self, dateTime):
        if not dateTime: return ""
        return dateTime.strftime('%Y-%m-%dT%H:%M:%S')

    def format_short_date(self, date, with_time = False):
        return format_date(date, "d. MMM", locale=self.locale)

    def getFullLocale(self):
        locales = {'en':'en-GB', 'de':'de-DE', 'es':'es-ES'}
        return locales[self.locale]

    def getLangName(self, langCode = None):
        return Locale.parse(self.locale).languages.get(langCode or self.locale)

############################## LOCALE AWARE REQUEST SETUP ##############################



def set_lang(domain, translationFactory):
    def set_lang_impl(request, lang = None):
        if lang:
            request._LOCALE_ = lang
            request.localizer = None
            request.locale_name = None
        localizer = get_localizer(request)

        def auto_translate(string):
            return localizer.translate(translationFactory(string))
        def auto_pluralize(singular, plural, n, mapping = {}):
            mapping.update({'num':n})
            try:
                return localizer.pluralize(singular, plural, n, domain=domain, mapping=mapping)
            except AttributeError, e:
                if n!=1:
                    return Template(plural).substitute(mapping)
                else:
                    return Template(singular).substitute(mapping)
        request.localizer = localizer
        request.ungettext = auto_pluralize
        request._ = auto_translate
    return set_lang_impl


def add_localizer(translationFactory):
    def add_localizer_impl(event):
        request = event.request
        request.set_lang()
        localizer = get_localizer(request)
        def auto_translate(string, mapping = {}):
            return localizer.translate(translationFactory(string, mapping = mapping))
        request.localizer = localizer
        request._ = request.translate = auto_translate
    return add_localizer_impl

class DefaultLocaleNegotiator(object):
    def __init__(self, available_locales, default_locale_name):
        self.available_locales = available_locales
        self.default_locale_name = default_locale_name
        log.info("SETUP LOCALE NEGOTIATION WITH %s (%s)", self.available_locales, self.default_locale_name)

    def negotiate_locale(self, accept_langs):
        def normalize_locale(loc):
            return unicode(loc).replace('-', '_')
        langs = map(normalize_locale, accept_langs)
        return negotiate_locale(langs, self.available_locales, sep="_") or self.default_locale_name

    def __call__(self, request):
        if getattr(request,'_LOCALE_', None):
            locale_name = request._LOCALE_
        elif 'lang' not in request.session or request.session['lang'] not in self.available_locales:
            locale_name = request.session['lang'] = self.negotiate_locale(request.accept_language)
            request._LOCALE_ = locale_name
        else:
            locale_name = request.session['lang']
            request._LOCALE_ = locale_name
        return locale_name


def extend_request(config, domain, available_locales, default_locale_name, tsf = None, i18nImpl = I18N):
    def add_renderer_variables(event):
        if event['renderer_name'] != 'json':
            request = event['request']
            event.update({'_' : request.translate, 'ungettext' : request.ungettext, 'i18n':i18nImpl(request)})
        return event

    translationFactory = tsf or TranslationStringFactory(domain)

    config.set_locale_negotiator(DefaultLocaleNegotiator(available_locales, default_locale_name))
    config.add_translation_dirs('formencode:i18n')
    config.add_translation_dirs('ufostart:locale')

    config.add_request_method(set_lang(domain, translationFactory), "set_lang")
    config.add_request_method(i18nImpl, "i18n", reify = True)

    config.add_subscriber(add_localizer(translationFactory), 'pyramid.events.NewRequest')
    config.add_subscriber(add_renderer_variables, 'pyramid.events.BeforeRender')

