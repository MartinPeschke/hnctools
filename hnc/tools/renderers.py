from cStringIO import StringIO
import csv

class CSVRenderer(object):
    def __init__(self, info):
        pass

    def __call__(self, value, system):
        fout = StringIO()
        writer = csv.writer(fout, delimiter=value.get('delimiter', ';'), quoting=csv.QUOTE_ALL)

        writer.writerow(value['header'])
        writer.writerows(value['rows'])

        resp = system['request'].response
        resp.content_type = 'text/csv'
        resp.content_disposition = 'attachment;filename="{}"'.format(value['filename'])
        return fout.getvalue()