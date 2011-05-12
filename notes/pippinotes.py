#!/usr/bin/env python2.6
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

# (C) 2011 by Stefan Marsiske, <stefan.marsiske@gmail.com>

from lenx.notes.handlers import Notes
from lxml.etree import tostring
from lxml import etree
from lxml.html.soupparser import parse
from cStringIO import StringIO

def saveNotes(D1,D2,frags,rooturl='http://localhost:8000'):
    pa1=PippiAnnotator(D1)
    pa2=PippiAnnotator(D2)
    for stem, (l, a, b) in frags.items():
        if not(a and b) or l<7: continue
        pa1.pippies2xpaths(D2,sorted(a),l,rooturl)
        pa2.pippies2xpaths(D1,sorted(b),l,rooturl)

class PippiAnnotator:
    def __init__(self,doc):
        self.doc=doc
        self.paths=self._initmap()

    def _initmap(self):
        pos=0
        i=0
        offset=0
        paths={}
        tree = parse(StringIO(self.doc.body))
        textnodes=tree.xpath('//div[@id="TexteOnly"]//text()')
        texts=[unicode(x) for x in textnodes]
        while i<len(texts) and pos<len(self.doc.tokens):
            #print i,len(texts),len(self.doc.tokens),pos, self.doc.tokens[pos]
            offset=texts[i].find(self.doc.tokens[pos],offset)
            if offset==-1:
                i+=1
                offset=0
                continue
            #print (tree.getpath(textnodes[i].getparent()), offset)
            path=tree.getpath(textnodes[i].getparent())[5:]
            paths[pos]=(path, offset)
            pos+=1
        return paths

    def pippies2xpaths(self,d2,pos,l,rooturl):
        for p in pos:
            Notes.save({ 'text' : u'also appearing in <a href="%s">%s</a>' % (rooturl, d2.title.strip().decode('utf8')),
                  'uri' : '%s/doc/%s' % (rooturl, self.doc.docid),
                  'user' : 'Pippi Longstrings',
                  'ranges' : [ { 'start' :self.paths[p][0] ,
                                 'end' : self.paths[p+l][0],
                                 'startOffset' : self.paths[p][1],
                                 'endOffset' : self.paths[p+l][1] + len(self.doc.tokens[p+l])}]})

