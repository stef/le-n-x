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

# (C) 2009-2010 by Stefan Marsiske, <stefan.marsiske@gmail.com>

from pymongo import Connection
from bson.objectid import ObjectId
from lenx.view.models import Doc, Pippi
import pprint

conn = Connection()
db=conn.pippi
Docs=db.docs
Pippies=db.pippies
MiscDb=db.miscdb

def getRelatedDocs(_id,cutoff=7):
    return [Doc(oid=oid)
            for oid in set([doc['doc']
                            for frag in Pippies.find({'docs.doc' : _id,
                                                      'len' : { '$gte' : int(cutoff) }},
                                                     ['docs.doc'])
                            for doc in frag['docs']
                            if doc['doc'] != _id])]

#for p in Pippi('',oid=pippi['frag']).docs

#doc=Doc(docid='CELEX:32003L0098:EN:HTML')
#pprint.pprint(doc.__dict__)
#print 'asdf'
#pprint.pprint(getRelatedDocs(doc._id))

#p=Pippi('',oid=ObjectId('4bfe948c865c0c49bb0003af'))
#print 'asdf'
#pprint.pprint(p.docs)
#print 'asdf'
#pprint.pprint(p.__dict__)

for d in Docs.find():
    if not 'title' in d:
        doc=Doc(d=d)
        d['title']=doc.title
        Docs.save(d)
