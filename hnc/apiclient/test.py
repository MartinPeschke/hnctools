# -*- coding: utf-8 -*-
import simplejson
from itertools import izip_longest
from . import Mapping, TextField, BaseUnitField, IntegerField, PictureField, DictField, DateTimeField, TypedField


class Merchant(Mapping):
  id = IntegerField()
  name = TextField()

class Product(Mapping):
  id = IntegerField()
  name = TextField()
  description = TextField()
  price = BaseUnitField()
  picture = PictureField()

class Venue(Mapping):
  id = IntegerField()
  name = TextField()
  description = TextField()
  line1 = TextField()
  line2 = TextField()
  post_code = TextField()
  city = TextField()
  area = TextField()
  picture = PictureField()
  merchant = DictField(Merchant, "Merchant")

class User(Mapping):
  id = IntegerField()
  name = TextField()
  picture = PictureField()
  facebook_id = TextField()
  email = TextField()
    
class Gift(Mapping):
  id = IntegerField()
  token = TextField()
  message = TextField()
  thankyou = TextField()
  status = TextField()
  created = DateTimeField()
  issued = DateTimeField()
  redeemed = DateTimeField()
  expiry = IntegerField()
  sender = DictField(User, "Sender")
  recipient = DictField(User, "Recipient")
  venue = DictField(Venue, "Venue")
  product = DictField(Product, "Product")

  def isOpen(self):
      return self.status == 'OPEN'
  def isIssued(self):
      return self.status == 'ISSUED'
  def isRedeemed(self):
      return self.status == 'REDEEMED'
  def isExpired(self):
    return self.expiry < 0

  def expiresIn(self):
    expiry = self.expiry
    if expiry:
      if expiry == 1:
        return '1 day'
      if expiry < 7:
        return '{} days'.format(expiry)
      if expiry < 31:
        return "{} weeks".format(expiry/7)
      if expiry < 365:
        return "{} months".format(expiry/30)
      return "{} years".format(expiry/365)

  def getProductRepr(self):
    return self.product.name
  def getPrettyPrice(self):
      return "&pound; {}".format(self.product.price)
  def isForMe(self, u_id):
    return self.recipient.id == u_id 
    
g = Gift.wrap({"id":"813","token":"0AF685DF-9505-4EC5-A411-7BFAB3105C7E","Recipient":{"id":"254","name":"Mapa Technorac","facebook_id":"100000924808399","picture":"http://graph.facebook.com/100000924808399/picture"},"Sender":{"id":"539","name":"Grant Hutchinson","facebook_id":"100001848870955","email":"test77@friendfund.com","picture":"http://graph.facebook.com/100001848870955/picture"},"Product":{"name":"Chablis","price":"330","description":"A relaxing Glass of Wine","id":"2","picture":"/pics/products/pint_.png"},"Venue":{"id":"5","name":"The Jolly Butchers","line1":"5 the street","line2":"a street","post_code":"l1","city":"London","area":"Notting Hill","picture":"/pics/venues/temp.jpg","description":"the best venue in town","Merchant":{"id":"3","name":"Bass"}},"message":"Hello Mate, this is awesome and works nice! Well done! Get thepint on me! You've earned it!","status":"REDEEMED","issued":"2012-02-21T08:49:42.050","redeemed":"2012-02-21T08:50:08.287","created":"2012-02-17T19:12:37.107","expiry":"-5"})

from decimal import Decimal

assert g.product.price == Decimal("3.30")
assert g.isExpired() == True
assert g.sender.name == "Grant Hutchinson"
assert g.recipient.name == "Mapa Technorac"
assert g.thankyou == None
assert str(g.created) == '2012-02-17 19:12:37'
assert g.created.year == 2012




def grouper(n, iterable, fillvalue=None):
    "grouper(3, 'ABCDEFG', 'x') --> ABC DEF Gxx"
    args = [iter(iterable)] * n
    return izip_longest(*args, fillvalue=fillvalue)

class CardDetails(Mapping):
  type = TextField()
  number = TextField(name='card_number')
  def getSavedGroupedDetails(self, no):
    self._cc_groupings = list(map("".join, grouper(4, self.number, " ")))
    return self._cc_groupings[no]

class AmexCardDetails(CardDetails):
  cvc_length = 4
  cvc_max = 9999
  cvc_hint = "4 digit code on the front of your credit card"

class CreditCardDetails(CardDetails):
  cvc_length = 3
  cvc_max = 999
  cvc_hint = "3 digit code on the back of your credit card"

class User(Mapping):
  id = IntegerField()
  name = TextField()
  picture = PictureField()
  access_token = TextField()
  user_token = TextField()
  facebook_id = TextField()
  email = TextField()
  saved_card_details = TypedField({'AMEX': AmexCardDetails, 'VISA': CreditCardDetails, 'MC': CreditCardDetails}, type_key='type', name="SavedDetails")

  def isAnon(self):
    return self.id is None

  def isMe(self, user_map):
    return (not self.isAnon()) and (self.facebook_id == user_map.get('facebook_id') or self.email == user_map.get('email'))

  def isAnonJSON(self):
      return simplejson.dumps(self.isAnon())
  def toJSON(self):
    return simplejson.dumps(self.unwrap())
  def hasSavedDetails(self):
    return self.saved_card_details is not None

assert User().isAnon() == True
u = User.wrap({"id":"254","access_token":"AAADipxqvveoBAAfcvgGqVshOj03XcarNAijDZCqz45KZCHNL7MKK5nw41n4luNQjNneTtmqkBGUVOFSRaM1ht6RZCV0LjSDkTpaD9VlFgZDZD","user_token":"B6FBC0F1-04E5-40A4-AE1D-4D4B40369BAB","name":"Mapa Technorac","facebook_id":"100000924808399","email":"martin.peschke@gmx.net","picture":"http://graph.facebook.com/100000924808399/picture","SavedDetails":{"card_number":"xxxxxxxxxxxx002","type":"AMEX"}})
assert u.saved_card_details.getSavedGroupedDetails(0) == 'xxxx'
assert u.saved_card_details.getSavedGroupedDetails(1) == 'xxxx'
assert u.saved_card_details.getSavedGroupedDetails(2) == 'xxxx'
assert u.saved_card_details.getSavedGroupedDetails(3) == '002 '


from backend import RemoteProc
def backend(root_key, url, method, data):
  return {"id":"254","access_token":"AAADipxqvveoBAAfcvgGqVshOj03XcarNAijDZCqz45KZCHNL7MKK5nw41n4luNQjNneTtmqkBGUVOFSRaM1ht6RZCV0LjSDkTpaD9VlFgZDZD","user_token":"B6FBC0F1-04E5-40A4-AE1D-4D4B40369BAB","name":"Mapa Technorac","facebook_id":"100000924808399","email":"martin.peschke@gmx.net","picture":"http://graph.facebook.com/100000924808399/picture","SavedDetails":{"card_number":"xxxxxxxxxxxx002","type":"AMEX"}}


rp = RemoteProc("/api/product/catalog", "POST", 'User', User)
user = rp(backend, {"id":"1"})
assert isinstance(user, User)
assert user.saved_card_details.type == 'AMEX'




