from hnc.forms.formfields import WrapField, NO_GRID, CombinedField


class Sequence(WrapField):
    def __init__(self, *fields):
        self.fields = fields

    def render(self, prefix, request, values, errors, view = None, grid = NO_GRID):
        html = u''.join([field.render(prefix, request, values, errors, view, grid) if field else '' for field in self.fields])
        return html



class BS3_NCOL(WrapField):
    def __init__(self, *fields):
        self.fields = fields

    def render(self, prefix, request, values, errors, view = None, grid = NO_GRID):
        html = u''.join([u'<div class="col-sm-{0}">{1}</div>'.format(
                    12/len(self.fields)
                    , field.render(prefix, request, values, errors, view, grid) if field else ''
                ) for field in self.fields])
        return u'<div class="row">{}</div>'.format(html)



