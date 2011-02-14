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

# (C) 2009-2011 by Stefan Marsiske, <stefan.marsiske@gmail.com>

from lxml import etree
from lxml.html.soupparser import parse
from lxml.etree import tostring
from cStringIO import StringIO
from urlparse import urljoin
from multiprocessing import Pool
import urllib2, urllib, cookielib, tidy, datetime, sys, json, pymongo

def dumpAsJSON(data):
    print json.dumps(data,default=dateJSONhandler)

def dumpToMongo(data):
    #Docs.ensure_index([('docid', pymongo.ASCENDING)])
    print >> sys.stderr, '>', data.get('Identification procedure',data.get('Identification document'))['Title']
    docs.save(data)

def fetch(url):
    # url to etree
    f=urllib2.urlopen(url)
    raw=f.read()
    f.close()
    raw=tidy.parseString(raw,
            **{'output_xhtml' : 1,
               'output-encoding': 'utf8',
               'add_xml_decl' : 1,
               'indent' : 0,
               'tidy_mark' : 0,
               'doctype' : "strict",
               'wrap' : 0})
    return parse(StringIO(str(raw)))

def toDate(node):
    text=tostring(node,method="text",encoding='utf8').replace('\xc2\xa0','').strip()
    if text is None or not len(text): return
    lines=text.split('\n')
    if len(lines)>1:
        result=[]
        for text in lines:
            value=[int(x) for x in text.strip().split('/')]
            result.append(datetime.date(value[2], value[1], value[0]).toordinal())
        return result
    else:
        value=[int(x) for x in text.strip().split('/')]
        return datetime.date(value[2], value[1], value[0]).toordinal()

def toText(node):
    if node is None: return ''
    text=tostring(node,method="text",encoding='utf8').replace('\xc2\xa0','').strip()

    links=node.xpath('a')
    if not links: return text
    return (text, urljoin(base,links[0].get('href')))

def toLines(node):
    text=toText(node).split('\n')
    if len(text)==1:
        return text[0]
    else: return text

def urlFromJS(node):
    a=node.xpath('a')
    if(a and
       (a[0].get('href').startswith('javascript:OpenNewPopupWnd(') or
        a[0].get('href').startswith('javascript:ficheUniquePopUp('))):
        return urljoin(base,(a[0].get('href').split("'",2)[1]))
    return ''

def convertRow(cells,fields):
    res={}
    if not len(cells)==len(fields): return None
    for i,cell in enumerate(cells):
        tmp=fields[i][1](cell)
        if tmp: res[fields[i][0]]=tmp
    return res

def toObj(table,fields):
    res=[]
    for row in table.xpath('tr')[2:]:
        items=row.xpath('td')
        value=convertRow(items,fields)
        if value:
            res.append(value)
        else:
            print >>sys.stderr, '[*] unparsed row:', tostring(row)
    return res

def dateJSONhandler(obj):
    if hasattr(obj, 'isoformat'):
        return obj.isoformat()
    else:
        raise TypeError, 'Object of type %s with value of %s is not JSON serializable' % (type(Obj), repr(Obj))

def identification(table):
    res={}
    for row in table.xpath('tr'):
        items=row.xpath('td')
        key=tostring(items[0],method="text",encoding='utf8').strip()
        if key=='Subject(s)':
            value=[x.strip() for x in items[1].xpath('text()')]
        else:
            value=tostring(items[1],method="text",encoding='utf8').strip()
        if key and value:
            res[key]=value
    return res

def forecasts(table):
    res={}
    for row in table.xpath('tr'):
        items=row.xpath('td')
        key=tostring(items[2],method="text",encoding='utf8').strip()
        date=toDate(items[0])
        if key and date:
            res[key]=date
    return res

def links(table):
    res={}
    for row in table.xpath('tr'):
        items=row.xpath('td')
        key=tostring(items[0],method="text",encoding='utf8').strip()
        value=tostring(items[1],method="text",encoding='utf8').strip()
        url=items[1].xpath('a')[0].get('href')
        if key and value:
            res[key]=(value, url)
        else:
            print >>sys.stderr, 'bad link', tostring(items), key, value, url
    return res

def OtherAgents(table,res):
    table=table.xpath('following-sibling::*')
    if not len(table): return
    table=table[0]
    if(not toText(table)=='European Commission and Council of the Union'): return
    table=table.xpath('following-sibling::*')[0]
    for row in table.xpath('tr'):
        fields=row.xpath('td')
        if(len(fields)==3 and toText(fields[0]).startswith('European Commission DG')):
            item={'Agent': toText(fields[0]),
                  'Department': toText(fields[1])}
            tmp=toText(fields[2]).split(' ')
            if len(tmp)==3:
                value=[int(x) for x in tmp[2].strip().split('/')]
                item['Date']=datetime.date(value[2], value[1], value[0]).toordinal()
            res.append(item)
        elif(len(fields)==5 and toText(fields[0]).startswith('Council of the Union')):
            item={'Agent': 'Council of the Union',
                  'Summary URL': urlFromJS(fields[1]),
                  'Department': toText(fields[2]),
                  }
            tmp=toText(fields[3]).split(' ')
            if len(tmp)==2:
                item['Meeting number']=tmp[1]
            tmp=toText(fields[4]).split(' ')
            if len(tmp)==2:
                value=[int(x) for x in tmp[1].strip().split('/')]
                item['Meeting Date']=datetime.date(value[2], value[1], value[0]).toordinal()
            res.append(item)
        else:
            raise ValueError
            print >> sys.stderr, 'unparsed row:', len(fields), toText(row)

stageFields=( ('stage', toText),
              ('stage document',urlFromJS),
              ('source institution',toText),
              ('source reference',toText),
              ('Equivalent references', toText),
              ('Vote references', toText),
              ('Amendment references', urlFromJS),
              ('Joint Resolution', toText),
              ('Date of document', toDate),
              ('Date of publication in Official Journal', urlFromJS)
            )
agentFields=( ('Commitee', toText),
              ('Rapporteur', toLines),
              ('Political Group',toLines),
              ('Appointed',toDate),
            )
summaryFields=( ('URL', urlFromJS),
                ('Date', toDate),
                ('Title',toText),
              )

def scrape(url):
    try:
        _scrape(url)
    except:
        print >>sys.stderr, url
        raise

def _scrape(url):
    tree=fetch(url)
    sections=tree.xpath('//h2')
    res={'source': url}
    for section in sections:
        table=section.xpath('../../../following-sibling::*')[0]
        if section.text in ['Identification procedure',
                            'Identification resolution',
                            'Identification document']:
            res[section.text]=identification(table)
        elif section.text in ['Stages procedure',
                              'Stages resolution']:
            res[section.text]=toObj(table,stageFields)
        elif section.text == 'Forecasts procedure':
            res['Forecasts procedure']=forecasts(table)
        elif section.text in ['Agents procedure',
                              'Agents document',
                              'Agents resolution']:
            tmp=toObj(table,agentFields)
            for row in tmp:
                commitee=row['Commitee']
                if commitee:
                    tmp1=commitee.split(' ')
                    row['Commitee']=' '.join(tmp1[:-1])
                    row['Commitee role']=tmp1[-1][1:-1]
            res[section.text]=tmp
            OtherAgents(table, res[section.text])
        elif section.text == 'Links to other sources procedure':
            res['Links to other sources procedure']=links(table)
        elif section.text == 'List of summaries':
            res['List of summaries']=toObj(table,summaryFields)
        else:
            print >> sys.stderr, '[*] unparsed:', section.text
    if not cb:
        return res
    else:
        cb(res)

def getStages():
    tree=fetch('http://www.europarl.europa.eu/oeil/search_procstage_stage.jsp')
    select=tree.xpath('//select[@name="stageId"]')[0]
    return [(opt.get('value'), toText(opt))
            for opt
            in select.xpath('option')
            if opt.get('value')]

def nextPage(req):
    result=[]
    response = opener.open(req)
    raw=tidy.parseString(response.read(),
                         **{'output_xhtml' : 1,
                            'output-encoding': 'utf8',
                            'add_xml_decl' : 1,
                            'indent' : 0,
                            'tidy_mark' : 0,
                            'doctype' : "strict",
                            'wrap' : 0})
    tree=parse(StringIO(str(raw)))
    result.extend([pool.apply_async(scrape, [item])
                   for item
                   in ['http://www.europarl.europa.eu/oeil/'+x.get('href')
                       for x
                       in tree.xpath('//a[@class="com_acronym"]')]])

    img=tree.xpath('//a/img[@src="img/cont/activities/navigation/navi_next_activities.gif"]')
    if len(img):
        next='http://www.europarl.europa.eu/'+img[0].xpath('..')[0].get('href')
        print >>sys.stderr, '.'
        result.extend(nextPage(next))
    return result

def crawl():
    result=[]
    for (stageid, stage) in getStages(): # TODO remove this test limititation!
        print >>sys.stderr, 'crawling:', stage
        data={'xpath': '/oeil/search/procstage/stage',
              'scope': 'stage',
              'searchCriteria': stage,
              'countEStat': True,
              'startIndex': 1,
              'stageId': stageid,
              'pageSize': 50}
        req = urllib2.Request('http://www.europarl.europa.eu/oeil/FindByStage.do',
                              urllib.urlencode(data))
        result.extend(nextPage(req))
    return result

# some config thingies hidden at the end of the file :)
pool = Pool(8)   # reduce if less aggressive
cb = dumpToMongo # dumpAsJSON

# and some global objects
base = 'http://www.europarl.europa.eu/oeil/file.jsp'
opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cookielib.CookieJar()))

# connect to  mongo
conn = pymongo.Connection()
db=conn.oeil
docs=db.docs

if __name__ == "__main__":
    crawl()
    pool.close()
    pool.join()

    # some tests
    #import pprint
    #scrape("http://www.europarl.europa.eu/oeil/file.jsp?id=5872922")
    #pprint.pprint(scrape("http://www.europarl.europa.eu/oeil/file.jsp?id=5872922"))
    #print 'x'*80
    #scrape("http://www.europarl.europa.eu/oeil/FindByProcnum.do?lang=en&procnum=RSP/2011/2510")
    #pprint.pprint(scrape("http://www.europarl.europa.eu/oeil/FindByProcnum.do?lang=en&procnum=RSP/2011/2510"))
    #print 'x'*80
    #scrape("http://www.europarl.europa.eu/oeil/file.jsp?id=5831162")
    #pprint.pprint(scrape("http://www.europarl.europa.eu/oeil/file.jsp?id=5831162"))
    #print 'x'*80
    #scrape("http://www.europarl.europa.eu/oeil/file.jsp?id=5632032")
    #pprint.pprint(scrape("http://www.europarl.europa.eu/oeil/file.jsp?id=5632032"))
    #print 'x'*80
    #scrape("http://www.europarl.europa.eu/oeil/file.jsp?id=5699432")
    #pprint.pprint(scrape("http://www.europarl.europa.eu/oeil/file.jsp?id=5699432"))
