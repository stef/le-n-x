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

# (C) 2010 by Stefan Marsiske, <stefan.marsiske@gmail.com>

from lenx.view.models import Doc, Pippi, Pippies, Docs

def lcsPkt(p1,p2,l,stem,d1,d2):
    if l>1:
        return {'pippi' : stem,
                'l'     : l,
                'd1ps'  : [{'pos' : p, 'txt' : d1.tokens[p:p+l]} for p in p1],
                'd2ps'  : [{'pos' : p, 'txt' : d2.tokens[p:p+l]} for p in p2],
                }

class Saver():
    def save(self,d1,d2,pkt):
        # todo new code to directly addtoset mongo-style
        if not pkt: return
        frag=Pippi(pkt['pippi'])
        Pippies.update({'_id' : frag._id},
                       {'$addToSet': { 'docs' : { '$each' :
                            [{'pos': p['pos'], 'txt': p['txt'], 'l': pkt['l'], 'doc': d}
                             for (d,p) in
                             [(d1._id, p) for p in pkt['d1ps']]+[(d2._id, p) for p in pkt['d2ps']]] } } })
        Docs.update({"_id" : d1._id},
                    { '$addToSet' : { 'pippies' : { '$each' :
                          [{'pos' : p['pos'], 'txt' : tuple(p['txt']), 'l' : pkt['l'], 'frag' : frag._id}
                           for p in pkt['d1ps']] } } })
        Docs.update({"_id" : d2._id},
                    { '$addToSet' : { 'pippies' : { '$each' :
                          [{'pos' : p['pos'], 'txt' : tuple(p['txt']), 'l' : pkt['l'], 'frag' : frag._id}
                           for p in pkt['d2ps']] } } })

    def addDocs(self,d1,d2):
        Docs.update({"_id" : d1._id},
                    { '$push' : { 'pippiDocs' : d2._id },
                      '$inc' : { 'pippiDocsLen' : 1 }})
        Docs.update({"_id" : d2._id},
                    { '$push' : { 'pippiDocs' : d1._id },
                      '$inc' : { 'pippiDocsLen' : 1 }})
