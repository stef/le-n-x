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
import document, sys, cache
CACHE=cache.Cache('../cache');
from fsdb import FilesystemDB
FSDB=FilesystemDB('../db')

db=document.MatchDb()
d=sys.argv[1].strip('\t\n')

if not db.load(FSDB,CACHE):
    print "ERR cannot load db"
    sys.exit(1)
if d in db.docs.keys():
    print "ERR already loaded"
    sys.exit(1)

newd=document.Doc(d,cache=CACHE,storage=FSDB)
for oldd in db.docs.values():
    db.analyze(newd,oldd)
db.addDoc(newd)
db.save()

print db.docs
