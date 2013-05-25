import base64
import decimal
from urlparse import urlunparse, urlparse
import zlib
import itertools
import datetime
import simplejson


def remove_chars(refstr, chars):
    return ''.join([ c for c in refstr if c not in chars])


def zigzag(map, pred, mod):
    t1,t2 = itertools.tee(map.iteritems())
    even = itertools.imap(mod, itertools.ifilter(pred, t1))
    odd = itertools.ifilterfalse(pred, t2)
    return even,odd
def split_list(list, pred):
    t1,t2 = itertools.tee(list)
    return itertools.ifilter(pred, t1), itertools.ifilterfalse(pred, t2)

class DateAwareJSONEncoder(simplejson.JSONEncoder):
    """
    JSONEncoder subclass that knows how to encode date/time and decimal types.
    """
    DATE_FORMAT = "%Y-%m-%d"
    TIME_FORMAT = "%H:%M:%S"
    def default(self, o):
        if isinstance(o, datetime.datetime):
            return o.strftime("%s %s" % (self.DATE_FORMAT, self.TIME_FORMAT))
        elif isinstance(o, datetime.date):
            return o.strftime(self.DATE_FORMAT)
        elif isinstance(o, datetime.time):
            return o.strftime(self.TIME_FORMAT)
        elif isinstance(o, decimal.Decimal):
            return str(o)
        else:
            return super(DateAwareJSONEncoder, self).default(o)

def dict_contains(d, keys):
    if not d or not keys:
        return False
    return len(keys) == len(filter(lambda x: bool(x), [d.get(k, None) for k in keys]))

def encode_minimal_repr(map):
    return base64.urlsafe_b64encode(zlib.compress(simplejson.dumps(map, cls=DateAwareJSONEncoder)))
def decode_minimal_repr(value):
    if not value: return None
    return simplejson.loads(zlib.decompress(base64.urlsafe_b64decode(str(value))))

def contains_one(arr, map):
    for k in arr:
        if k in map:
            return True
    return False
def contains_one_ne(map, arr):
    for k in arr:
        if map.get(k):
            return True
    return False
def contains_all_ne(map, arr):
    for k in arr:
        if not map.get(k):
            return False
    return True
def has_ne_prop(c, key):
    return bool(hasattr(c, key) and getattr(c, key))



def add_url_param(url, name, value):
    scheme, netloc, path, params, query, fragment = urlparse(url)
    if query:
        query = '{}&{}={}'.format(query, name, value)
    else:
        query = '{}={}'.format(name, value)
    return urlunparse((scheme, netloc, path, params, query, fragment))


def word_truncate_by_letters(s, length):
    if not s: return ''
    if s and len(s) > length:
        s = s[:length].rsplit(None,1)[0] + '...'
    return s
