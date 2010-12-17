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

EURLEXURL="http://eur-lex.europa.eu/LexUriServ/LexUriServ.do?uri="

SHORTCUTRE=r'([Dd]irective|[Rr]egulation|[Dd]ecision)/([0-9]{4})/([0-9]{,4})/EC'
CELEXRE=re.compile(r'(?:CELEX:[0-9A-Z:()]*(:HTML)?)|(?:'+SHORTCUTRE+r')')
SHORTCUTMAP={'Directive': 'L', 'directive': 'L',
             'Regulation': 'R', 'regulation': 'R',
             'decision': 'D', 'Decision': 'D'}

from lenx.view.doc import DOC
from lenx.view.db import Docs

CELEXCODES={
    "1": { "Sector": "Treaties",
           "Document Types" : { "D": "Treaty of Amsterdam 1997",
                                "M": "Treaty on the European Union, Maastricht 1992 - EU Treaty - consolidated version 1997",
                                "E": "EEC Treaty 1957 - EEC Treaty - consolidated version 1992 - EEC Treaty - consolidated version 1997",
                                "K": "ECSC Treaty 1951",
                                "A": "EURATOM Treaty 1957",
                                "U": "Single European Act 1986",
                                "G": "Groenland Treaty 1985",
                                "R": "Treaty amending certain financial provisions 1975",
                                "F": "Treaty amending certain budgetary provisions 1970",
                                "F": "Merger Treaty 1965",
                                "B": "Accession Treaty 1972 (United Kingdom, Denmark, Ireland, Norway)",
                                "H": "Accession Treaty 1979 (Greece)",
                                "I": "Accession Treaty 1985 (Spain, Portugal)",
                                "N": "Accession Treaty 1994 (Austria, Sweden, Finland, Norway)",
                                }},
    "2": { "Sector": "External Agreements",
           "Document Types" : { "A":"Agreements with non-member States or international organisations",
                                "D":"Acts of bodies created by international agreements",
                                "P":"Acts of parliamentary bodies created by international agreements",
                                "X":"Other Acts ",},},
    "3": { "Sector": "Legislation",
           "Document Types" : { "E":"Common Foreign and Security Policy (CFSP) - common positions / joint actions / common strategies",
                                "F":"Justice and Home Affairs (JHA) - common positions / framework decisions",
                                "R":"Regulations",
                                "L":"Directives",
                                "D":"Decisions sui generis",
                                "S":"ECSC Decisions of general interest",
                                "M":"Non-opposition to a notified concentration",
                                "J":"Non-opposition to a notified joint venture",
                                "B":"Budget",
                                "K":"Recommendations ECSC",
                                "O":"Guidelines ECB",
                                "H":"Recommendations",
                                "A":"Avis",
                                "G":"Resolutions",
                                "C":"Declarations",
                                "Q":"Institutional arrangements, Rules of Procedure, Internal agreements",
                                "X":"Other documents",},},
    "4": { "Sector": "Internal Agreements",
           "Document Types" : { "D":"Decisions of the representatives of the governments of the Member States",
                                "X":"Other acts",},},
    "5": { "Sector": "Proposals + preparatory documents",
           "Document Types" : { "AG":"Council - common positions",
                                "KG":"Council - assent ECSC",
                                "IG":"Member States - Initiatives",
                                "XG":"Council - other acts",
                                "PC":"COM Documents - proposals for legislation",
                                "DC":"COM Documents - other documents",
                                "SC":"SEC Documents",
                                "XC":"Commission - other acts",
                                "AP":"EP - legislative resolution",
                                "BP":"EP - budget",
                                "IP":"EP - other resolutions",
                                "XP":"EP - other acts",
                                "AA":"Court of Auditors - opinions",
                                "TA":"Court of Auditors - reports",
                                "SA":"Court of Auditors - special reports",
                                "XA":"Court of Auditors - other acts",
                                "AB":"ECB - opinions",
                                "HB":"ECB - recommendations",
                                "XB":"ECB - other acts",
                                "AE":"ESC - opinions on consultation",
                                "IE":"ESC - other opinions",
                                "XE":"ESC - other acts",
                                "AR":"CR - opinions on consultation",
                                "IR":"CR - other opinions",
                                "XR":"CR - other acts",
                                "AK":"ECSC Com. - opinions",
                                "XK":"ECSC Com. - other acts",
                                "XX":"Other acts ", }, },
    "6": { "Sector": "Case Law",
           "Document Types" : { "A":"Court of First Instance Judgments",
                                "B":"Court of First Instance - Orders",
                                "D":"Court of First Instance - Third Party Proceedings",
                                "F":"Court of First Instance - Opinions",
                                "H":"Court of First Instance - Case report",
                                "C":"Court of Justice - Conclusions of the Avocate-General",
                                "J":"Court of Justice - Judgments",
                                "O":"Court of Justice - Orders",
                                "P":"Court of Justice - Case report",
                                "S":"Court of Justice - Seizure",
                                "T":"Court of Justice - Third Party Proceedings",
                                "V":"Court of Justice - Opinions",
                                "X":"Court of Justice - Rulings",},},
    "7": { "Sector": "National Implementation",
           "Document Types" : {"L":"National Implementation Measures - implementation of directives",},},
    "9": { "Sector": "European Parliamentary Questions",
           "Document Types" : { "E":"European European Parliament - Written Questions",
                                "H":"European European Parliament - Questions at Questiontime",
                                "O":"European European Parliament - Oral questions",},},
    "C": { "Sector": "OJC Documents", "Document Types" : {},},
    "E": { "Sector": "EFTA Documents",
           "Document Types" : { "A":"International Agreements",
                                "C":"Acts of the EFTA Surveillance Authority",
                                "G":"Acts of the EFTA Standing Committee",
                                "J":"Decisions, Orders, Consultative opinions of the EFTA Court",
                                "P":"Pending cases of the EFTA Court",
                                "X":"EFTA - Other Acts",},},
    }

class Eurlex(DOC):
    def __init__(self, docid=None, *args,**kwargs):
        if docid:
            alias=re.match(SHORTCUTRE,docid)
            if alias:
                self.__dict__['sector'] = '3'
                self.__dict__['year'] = alias.group(2)
                self.__dict__['doctype'] = SHORTCUTMAP[alias.group(1)]
                self.__dict__['refno'] = "%04d" % int(alias.group(3))
                self.__dict__['lang'] = 'EN' # assuming default
            else:
                (code,lang)=docid.split(":")[1:3]
                st=7 if code[6].isalpha() else 6
                self.__dict__['sector'] = code[0]
                self.__dict__['year'] = code[1:5]
                self.__dict__['doctype'] = code[5:st]
                self.__dict__['refno'] = code[st:]
                self.__dict__['lang'] = lang
            self.__dict__['type'] = 'eurlex'
            kwargs['docid']=self.docid
            if not Docs.find_one({"docid": self.docid}):
                retries=4
                while True:
                    raw=CACHE.fetchUrl(EURLEXURL+self.docid+":HTML")
                    soup=BeautifulSoup(raw)
                    # TODO handle empty or invalid celex ids - also handle other languages besides english!!!
                    # <TITLE>Request Error</TITLE>
                    # <h1>The parameters of the link are incorrect.</h1>
                    if soup.title and soup.title.string == "Request Error":
                        if retries>0:
                            retries=retries-1
                            continue
                        else:
                            raise ValueError, "Request Error"
                    if soup.h1 and soup.h1.string == 'The parameters of the link are incorrect.':
                        if retries>0:
                            retries=retries-1
                            continue
                        else:
                            raise ValueError, "Parameter Error"
                    # no errors found, continue, nothing to see here
                    break
                # > /* There is no English version of this document available since it was not included in the English Special Edition.
                content=soup.find(id='TexteOnly')
                if (content and
                    content.findAll('p') and
                    len(content.findAll('p'))>1 and
                    'string' in dir(content.findAll('p')[1]) and
                    content.findAll('p')[1].string.strip().startswith('/* There is no English version of this document available since it was not included in the English Special Edition.')):
                    raise ValueError, "Language Error"
                kwargs['raw']=raw
                self.__dict__['metadata'] = self.extractMetadata()
        super(Eurlex,self).__init__(*args, **kwargs)

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
        if name == 'typeDesc':
            return CELEXCODES[self.sector]['Document Types'][self.doctype] if self.doctype != 'C' else CELEXCODES[self.sector]['Sector']
        if name == 'docid':
            self.__dict__['docid']="CELEX:%s%s%s%s:%s" % (self.sector, self.year,self.doctype,self.refno,self.lang)
        if name == 'title':
            self.__dict__['title']=self._gettitle()
        if name == 'subject':
            self.__dict__['subject']=self._getsubj()
        if name == 'metadata':
            self.__dict__['metadata']=self.extractMetadata()
        return super(Eurlex,self).__getattr__(name)

    def __unicode__(self):
        if self.sector=='3' and self.doctype=='L':
            return "%s/%s/EEC" % (self.year, self.refno)
        return "%s %s/%s" % (self.typeDesc,
                             self.year,
                             self.refno)

    def __repr__(self):
        return self.__unicode__()

    def _getHTMLMetaData(self, attr):
        soup = BeautifulSoup(self.raw)
        res=map(lambda x: (x and x.has_key('content') and x['content']) or "", soup.findAll('meta',attrs={'name':attr}))
        return '|'.join(res).encode('utf-8')

    def _gettitle(self):
        return self._getHTMLMetaData('DC.description') or self.docid

    def _getsubj(self):
        return self._getHTMLMetaData('DC.subject')

    def fetchMeta(self,soup,name,result):
        key=soup.find('strong', text=name)
        if key:
            res=[[]]
            for line in key.findParent('li').contents:
                if line and str(line).strip() and not line == key.parent:
                    if not 'name' in dir(line):
                        res[-1].append(str(line).strip())
                    elif not line.name=='br':
                        res[-1].append(' '.join(line.findAll(text=True)).strip())
                    elif res[-1]:
                        res[-1]=' '.join(res[-1])
                        res.append([])
            if isinstance(res[-1],list):
                res[-1]=' '.join(res[-1])
            if res[0]:
                result[name.strip(':')] = res

    def extractMetadata(self):
        raw=CACHE.fetchUrl(EURLEXURL+self.docid+":NOT")
        soup = BeautifulSoup(raw.decode('utf8'))
        result={}
        # dates
        dates=soup.find('h2',text="Dates")
        if dates:
            result['dates']={}
            for (k,v) in [y.split(": ") for y in fltr([x.strip() for x in dates.parent.findNextSibling('ul').findAll(text=True) if x.strip()])]:
                result['dates'][k]=[v]
        for t,l in [("Classifications",
                     ["Subject matter:","Directory code:"]),
                    ("Miscellaneous information",
                     ["Author:","Form:","Addressee:","Additional information:"]),
                    ("Procedure",
                     ["Procedure number:","Legislative history:"]),
                    ("Relationship between documents",
                     ["Treaty:",
                      "Legal basis:",
                      "Amendment to:",
                      "Amended by:",
                      "Consolidated versions:",
                      "Subsequent related instruments:",
                      "Affected by case:",
                      "Instruments cited:"])]:
            s=soup.find('h2',text=t)
            if not s: continue
            s=s.findNext('ul')
            if not s: continue
            result[t]={}
            for k in l:
                self.fetchMeta(s,k,result[t])

        # classification
        eurovocs=soup.find('strong', text="EUROVOC descriptor:")
        if eurovocs:
            result.get('Classifications',{})["EUROVOC descriptor:"]=[str(x.string).strip() for x in eurovocs.findParent('li').findAll('a')]
        dc=result.get('Classifications',{}).get('Directory code',[])
        if dc:
            result['Classifications']['Directory code']=[dircode.split(' ',1)[0] for dircode in dc if dircode]
            result['Classifications']['Directories']=[dircode.split(' ',1)[1].split(' / ') for dircode in dc if dircode]
        return result

def fltr(lst):
    return [x for x in lst if not re.search(r"\s*\\n',\s*'\s*",x)]

from django.core.management import setup_environ
from lenx import settings
setup_environ(settings)
from lenx.brain import cache as Cache
CACHE=Cache.Cache(settings.CACHE_PATH)
from BeautifulSoup import BeautifulSoup
from datetime import date
import urllib2

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
