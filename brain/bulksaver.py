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

from lenx.view.models import Pippi, Frag,
from lenx.view.db import Pippies, Frags, Docs
from lenx.view.doc import Doc

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
        pippi=Pippi(pkt['pippi'])
        Docs.update({'_id': d1._id},
                    { '$addToSet' : { 'pippies' : pippi._id } })
        Docs.update({'_id': d2._id},
                    { '$addToSet' : { 'pippies' : pippi._id } })
        Pippies.update({'_id' : pippi._id},
                       {'$addToSet': { 'docs' : { '$each' : [d for d in [d1._id, d2._id]]}},
                        '$inc' : { 'docslen' : 2 }})
        [Frags.save({'pos': p['pos'], 'txt': p['txt'], 'l': pkt['l'], 'doc': d, 'pippi': pippi._id})
                    for (d,p) in
                    [(d1._id, p) for p in pkt['d1ps']]+[(d2._id, p) for p in pkt['d2ps']]]
        return pkt

    def addDocs(self,d1,d2):
        Docs.update({"_id" : d1._id},
                    { '$push' : { 'pippiDocs' : d2._id },
                      '$inc' : { 'pippiDocsLen' : 1 }})
        Docs.update({"_id" : d2._id},
                    { '$push' : { 'pippiDocs' : d1._id },
                      '$inc' : { 'pippiDocsLen' : 1 }})
