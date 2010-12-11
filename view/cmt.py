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

import re

CELEXRE=re.compile(r'CELEX:[0-9A-Z:()]*:HTML')
from lenx.view.doc import DOC

class Coment(DOC):
    def __init__(self, url,*args,**kwargs):
        self.__dict__['type'] = 'co-ment'
        raw=CACHE.fetchUrl(url)
        if not 'docid' in kwargs:
            kwargs['docid']=self.celexid
        super(Eurlex,self).__init__(raw=raw, *args, **kwargs)

    def _getbody(self):
        return unicode(str(BeautifulSoup(self.raw).find(id='TexteOnly')), 'utf8')

    def _gettext(self):
        res=self._getExtField('text')
        if res: return res
        soup = BeautifulSoup(self.raw)
        # TexteOnly is the id used on eur-lex pages containing docs
        res = [unicode(x) for x in soup.find(id='TexteOnly').findAll(text=True)]
        self._setExtField('text',res) # cache data
        return res

    def __getattr__(self, name):
        if name in self.__dict__:
            return self.__dict__[name]
        if name == 'title':
            self.__dict__['title']=self._gettitle()
        if name == 'subject':
            self.__dict__['subject']=self._getsubj()
        return super(Eurlex,self).__getattr__(name)

    def __unicode__(self):
        return unicode(self.title)

    def __repr__(self):
        return self.__unicode__()

    def _getHTMLMetaData(self, attr):
        soup = BeautifulSoup(self.raw)
        res=map(lambda x: (x and x.has_key('content') and x['content']) or "", soup.findAll('meta',attrs={'name':attr}))
        return '|'.join(res).encode('utf-8')

    def _gettitle(self):
        return self._getHTMLMetaData('DC.description') or self.celexid

    def _getsubj(self):
        return self._getHTMLMetaData('DC.subject')

    def extractMetadata(self):
        raw = urllib2.urlopen("%s%s%s" % (EURLEXURL, self.celexid, ':NOT')).read()
        soup = BeautifulSoup(raw.decode('utf8'))
        result={}
        print soup
        eurovocs=soup.find('strong', text="EUROVOC descriptor:")
        if eurovocs:
            result['eurovocs']=fltr([''.join(x.findAll(text=True)).strip() for x in eurovocs.parent.parent.findAll('a')])
        dates=soup.find('h2',text="Dates")
        if dates:
            result['dates']={}
            for (k,v) in [y.split(": ") for y in fltr([x.strip() for x in dates.parent.findNextSibling('ul').findAll(text=True) if x.strip()])]:
                note=''
                dte=None
                try:
                    (dte, note) = v.split("; ")
                except:
                    dte=v
                if not dte == '99/99/9999':
                    (d,m,y)=[int(e) for e in dte.split('/')]
                    dte=date(y,m,d)
                result['dates'][k]={'date': dte, 'note': note}
        return result
        #cls=soup.h2(text="Classifications")
        #print cls
        #if cls:
        #    print 'class', fltr(cls.ul.findAll(text=True)),
        #misc=soup.h2(text="Miscellaneous information")
        #print misc
        #if misc:
        #    print 'misc', fltr(misc.ul.findAll(text=True)),
        #proc=soup.h2(text="Procedure")
        #print proc
        #if proc:
        #    print 'proc', fltr(proc.ul.findAll(text=True)),
        #rels=soup.h2(text="Relationship between documents")
        #print rels
        #if rels:
        #    print 'rels', fltr(rels.ul.findAll(text=True)),

def fltr(lst):
    return [x for x in lst if not re.search(r"\s*\\n',\s*'\s*",x)]

if __name__ == "__main__":
    print Eurlex("CELEX:31994D0006:EN:HTML")
    print Eurlex("CELEX:31994L0006:EN:HTML")
    print Eurlex("CELEX:51994XP006:EN:HTML")

    # test metadata extraction
    #EURLEXURL="http://eur-lex.europa.eu/LexUriServ/LexUriServ.do?uri="
    #text = urllib2.urlopen(url).read()
    import pprint
    tcom=Eurlex("CELEX:32009L0140:EN:HTML")
    f=open("../arch/CELEX:32009L0140:EN:NOT.html",'U')
    html=f.readlines()
    f.close()
    pprint.pprint(tcom.extractMetadata(html))

    ecom=Eurlex("CELEX:32004L0048:EN:HTML")
    f=open("../arch/CELEX:32004L0048:EN:NOT.html",'U')
    html=f.readlines()
    f.close()
    pprint.pprint(ecom.extractMetadata(html))

from django.core.management import setup_environ
from lenx import settings
setup_environ(settings)
from lenx.brain import cache as Cache
CACHE=Cache.Cache(settings.CACHE_PATH)
from BeautifulSoup import BeautifulSoup
from datetime import date
import urllib2

def importDoc(request):
    if request.method == 'POST':
        form = ImportForm(request.POST)
        if form.is_valid():
            url=form.cleaned_data['url']
            docid=form.cleaned_data['docid']
            hostValidator = re.compile('^\W*https?:\/\/(.+\.co-ment.com)(\/text\/[a-zA-Z0-9]+\/).+\/?\W*$', re.I | re.U).search(url)
            if not hostValidator or hostValidator.group(0) != url:
                return render_to_response('error.html', {'error': 'Wrong co-ment URL: %s!' % (url)})
            HOSTNAME = hostValidator.group(1)
            # /text/JplAuXN9be2/comments
            try:
                conn = httplib.HTTPSConnection(HOSTNAME)
                conn.putrequest('GET', hostValidator.group(2)+'comments/')
                conn.endheaders()
                response = conn.getresponse()
                html = response.read()
                soup = BeautifulSoup(html)
            except:
                return render_to_response('error.html', {'error': 'Cannot download URL, please try again!'})
            #print unicode(unescape(''.join(soup.find(attrs={'id' : 'textcontainer'}))))
            # TODO DC.subject parse
            raw = u'<html><head><title>%s</title><meta name="DC.subject" content="%s" /> <meta http-equiv="content-type" content="text/html; charset=utf-8" /> </head><body>%s</body></html>' % (docid, url, unescape(unicode(soup.find(attrs={'id' : 'textcontainer'}))))
            d=Doc(raw=raw.encode('utf8'),docid=docid.encode('utf8'))
            if not 'stems' in d.__dict__ or not d.stems:
                # let's calculate and cache the results
                tfidf.add_input_document(d.termcnt.keys())
                d.save()
            return HttpResponseRedirect('/doc/%s' % (d.title))
    else:
        form = ImportForm()
    return render_to_response('import.html', { 'form': form, })
