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

import document, sys, cache, os
CACHE=cache.Cache('cache/');
from fsdb import FilesystemDB
FSDB=FilesystemDB('db/')

d=sys.argv[1].strip('\t\n')
db=document.MatchDb()
if not db.load(FSDB,CACHE):
    print "ERR cannot load db"
    sys.exit(1)
if os.path.isfile(d):
   f=open(d,'r')
   for doc in f.readlines():
      db.insert(document.Doc(doc.strip('\t\n')))
else:
   if d in db.docs.keys():
      print "ERR already loaded"
      sys.exit(1)
   db.insert(document.Doc(d))

db.save(storage=FSDB)
print "this code is buggy! it does not respect what's in the db already"
print "diff"
print "rm -rf db ; mkdir -p db/docs; ../brain/pippy.py Canada CARIFORUM; ../brain/addDoc.py asdf | sort >ad"
print "vs"
print "rm -rf db ; mkdir -p db/docs; cat asdf | ../brain/bulkproducer.py 0 1 | tee | ../brain/bulkprocessor.py | ../brain/bulkadd.py | sort >ba"
print "while both print this in the end: "
print "print '\n'.join([str((x[0],len(x[1]))) for x in sorted(db.db.items())])"
