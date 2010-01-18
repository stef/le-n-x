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
CACHE=cache.Cache('../cache');
from fsdb import FilesystemDB
FSDB=FilesystemDB('../db')

def printLongFrags(self):
    frags=self.longestFrags()
    res=[]
    for (k,docs) in frags:
        for d in docs:
            res.append(u'%s: %s\n' % (d,self.docs[d[0]].getFrag(d[1],d[2])))
        res.append(u'-----\n')
    return '\n'.join(res).encode('utf8')

db=document.MatchDb()
d1=document.Doc(sys.argv[1].strip('\t\n'),cache=CACHE,storage=FSDB)
d2=document.Doc(sys.argv[2].strip('\t\n'),cache=CACHE,storage=FSDB)
db.analyze(d1,d2)
db.addDoc(d1)
db.addDoc(d2)
print printLongFrags(db)
