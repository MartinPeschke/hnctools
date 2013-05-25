"""
Message container for Twitter Bootstrap alert messages, to be put into request.session.flash and read out into a template.
"""

class GenericMessage(object):
  types = ['success', 'info', 'block', 'error', 'danger'] 
  def __init__(self, body, heading= None):
    self.heading = heading
    self.body= body
class GenericSuccessMessage(GenericMessage):
  type = 'success'
class GenericInfoMessage(GenericMessage):
  type = 'info'
class GenericBlockMessage(GenericMessage):
  type = 'block'
class GenericErrorMessage(GenericMessage):
  type = 'error'
class GenericDangerMessage(GenericMessage):
  type = 'danger'