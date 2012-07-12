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

# (C) 2009-2010 by Stefan Marsiske, <stefan.marsiske@gmail.com>

import pymongo
import gridfs

conn = pymongo.Connection()
db=conn.pippi
DocStore=conn.DocStore
fs = gridfs.GridFS(DocStore)
Docs=db.docs
Docs.ensure_index([('docid', pymongo.ASCENDING)])
Docs.ensure_index([('title', pymongo.ASCENDING)])
Docs.ensure_index([('pippiDocsLen', pymongo.DESCENDING)])

DocTexts=db.DocTexts
DocStems=db.DocStems
DocStems.ensure_index([('value', pymongo.ASCENDING)])
DocTokens=db.DocTokens

Pippies=db.pippies
Pippies.ensure_index([('pippi', pymongo.ASCENDING)])
Pippies.ensure_index([('relevance', pymongo.ASCENDING)])

Frags=db.frags
Frags.ensure_index([('pippi', pymongo.ASCENDING),
                    ('doc', pymongo.ASCENDING),
                    ('pos', pymongo.ASCENDING)], unique=True)
Frags.ensure_index([('l', pymongo.DESCENDING)])

MiscDb=db.miscdb
