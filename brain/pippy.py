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

# (C) 2010 by Stefan Marsiske, <stefan.marsiske@gmail.com>

import document, sys, cache
from operator import itemgetter
CACHE=cache.Cache('cache');
from fsdb import FilesystemDB
FSDB=FilesystemDB('db')

def printLongFrags(self):
    frags=self.longestFrags()
    res=[]
    for (k,docs) in frags:
        for d in docs:
            res.append(u'%s: %s' % (d,self.docs[d[0]].getFrag(d[1],d[2]).decode("utf8")))
        res.append(u'-----\n')
    return '\n'.join(res).encode('utf8')

db=document.MatchDb()
d1=document.Doc(sys.argv[1].strip('\t\n'),cache=CACHE,storage=FSDB)
d2=document.Doc(sys.argv[2].strip('\t\n'),cache=CACHE,storage=FSDB)
#db.analyze(d1,d2)
#db.docs[d1.id]=d1
#db.docs[d2.id]=d2
#db.save(storage=FSDB)
#print printLongFrags(db)
print "\n".join(map(lambda x: str(x)+"\n"+" ".join(d1.tokens[x[0]:x[0]+x[2]])+"\n"+" ".join(d2.tokens[x[1]:x[1]+x[2]]), sorted(db.getMatches(d1,d2), reverse=True, key=itemgetter(2)))).encode('utf8')
