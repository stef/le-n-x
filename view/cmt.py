#!/usr/bin/env python
#    This file is part of le(n)x.

#    le(n)x is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.

#    le(n)x is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.

#    You should have received a copy of the GNU Affero General Public License
#    along with le(n)x.  If not, see <http://www.gnu.org/licenses/>.

# (C) 2009-2010 by Stefan Marsiske, <stefan.marsiske@gmail.com>

import re, urllib2, htmlentitydefs

CMTRE = re.compile('^\W*(https?:\/\/)(.+\.co-ment.com)\/text(\/[a-zA-Z0-9]+\/).+\/?\W*$', re.I | re.U)
from lenx.view.doc import DOC, Doc
from lenx.view.models import tfidf

def unescape(text):
    def fixup(m):
        text = m.group(0)
        if text[:2] == "&#":
            # character reference
            try:
                if text[:3] == "&#x":
                    return unichr(int(text[3:-1], 16))
                else:
                    return unichr(int(text[2:-1]))
            except ValueError:
                pass
        else:
            # named entity
            try:
                text = unichr(htmlentitydefs.name2codepoint[text[1:-1]])
            except KeyError:
                pass
        return text # leave as is
    return re.sub("&#?\w+;", fixup, text)

class Coment(DOC):
    def __init__(self, url,*args,**kwargs):
        self.__dict__['type'] = 'co-ment'
        hostValidator = CMTRE.search(url)
        if hostValidator and hostValidator.group(0) == url:
            context = urllib2.urlopen(url).read()
            soup = BeautifulSoup(context)
            title=''.join(soup.title.findAll(text=True)).strip().encode('utf8')
            docid=kwargs.get('docid',"%s%s" % (hostValidator.group(2), hostValidator.group(3))).encode('utf8')

            dataurl = "%s%s/text%s%s" % (hostValidator.group(1), hostValidator.group(2), hostValidator.group(3), 'comments/')
            data = urllib2.urlopen(dataurl).read()
            soup = BeautifulSoup(data)

            raw = '<html><head><title>%s</title><meta http-equiv="content-type" content="text/html; charset=utf-8" /></head><body>%s</body></html>' % (title, unescape(unicode(soup.find(attrs={'id' : 'textcontainer'}))).encode('utf8'))
            d=Doc(raw=raw,docid=docid)
            if not 'stems' in d.__dict__ or not d.stems:
                # let's calculate and cache the results
                tfidf.add_input_document(d.termcnt.keys())
                d.save()
        super(Coment,self).__init__(raw=raw, *args, **kwargs)

    def __unicode__(self):
        return unicode(self.title)

from django.core.management import setup_environ
from lenx import settings
setup_environ(settings)
from lenx.brain import cache as Cache
CACHE=Cache.Cache(settings.CACHE_PATH)
from BeautifulSoup import BeautifulSoup
from datetime import date
import urllib2

if __name__ == "__main__":
    url='https://actamotion.co-ment.com/text/LbtpIg2HWfs/view/'
    Coment(url)
