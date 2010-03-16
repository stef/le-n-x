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

from lenx.view.models import Doc, Frag, Location
from django.core.management import setup_environ
from lenx import settings
from lenx.brain import lcs
setup_environ(settings)
import sys, os

docs={}

def getDoc(doc):
    if docs.has_key(doc): return docs[doc]
    docs[doc] = Doc.getDoc(doc)
    return docs[doc]

for line in sys.stdin:
    (doc1,doc2)=eval(line)
    print "[%d] %s, %s" % (os.getpid(),doc1,doc2)
    d1=getDoc(doc1)
    d2=getDoc(doc2)
    lcs.pippi(d1,d2)

