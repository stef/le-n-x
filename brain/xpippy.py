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

import document, sys
from fsdb import FilesystemDB
FSDB=FilesystemDB('../db')
import cache as Cache
CACHE=Cache.Cache('../cache');

def dumpRefs(this,docs):
    refs=sorted(this.refs.items(),reverse=True,cmp=lambda x,y: cmp(len(x[0]), len(y[0])))
    for (stem,ref) in refs:
        if len(stem) < 5: return
        print u"----- new frag -----\n>>",u"from",this.id+u":",ref['matches']
        print this.getFrag(ref['matches'][0][0],ref['matches'][0][1])
        for doc in ref['refs']:
            d=docs[doc]
            m=d.refs[stem]['matches']
            for f in m:
                print u"\noccurs also in",doc,m,u"\n",d.getFrag(f[0],f[1])
        print

db=document.MatchDb()
d=sys.argv[1].strip('\t\n')

if not db.load(FSDB,CACHE):
    print "ERR cannot load db"
    sys.exit(1)

dumpRefs(db.docs[d],db.docs)
