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

import document, sys, os
import cache as Cache
CACHE=Cache.Cache('cache');
from fsdb import FilesystemDB
FSDB=FilesystemDB('db')

def getDoc(db,doc):
    if db.docs.has_key(doc): return db.docs[doc]
    db.docs[doc]=document.Doc(doc,storage=FSDB, cache=CACHE)
    return db.docs[doc]

db=document.MatchDb()
for line in sys.stdin:
    (doc1,doc2,matches)=eval(line)
    d1=getDoc(db,doc1)
    d2=getDoc(db,doc2)
    for match in matches:
        db.storeMatch(d1,d2,match)
    db.docs[doc1]=d1
    db.docs[doc2]=d2
db.save(storage=FSDB)
print "\n".join([str((x[0],len(x[1]))) for x in sorted(db.db.items())])
