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

from lenx.view.models import Pippi, TfIdf
from lenx.view.eurlex import Eurlex as Doc
from django.core.management import setup_environ
from lenx import settings
from lenx.brain import lcs
setup_environ(settings)
import sys, os, traceback

docs={}
tfidf=TfIdf()
def getDoc(doc):
    if doc in docs: return docs[doc]
    d=Doc(docid=doc)
    if not 'stems' in d.__dict__ or not d.stems:
        # let's calculate and cache the results
        d.title
        d.subject
        tfidf.add_input_document(d.termcnt.keys())
        d.save()
    docs[doc] = d
    return d

def main():
    fails=open('bulkpippy.fails','a')
    for line in sys.stdin:
       (doc1,doc2)=line.strip().split('\t')
       print "[%d] %s, %s" % (os.getpid(),doc1,doc2)
       try:
           d1=getDoc(doc1)
       except:
          print "!!!!PIPPI ERROR: load doc",doc1
          sys.stderr.write("%s\t%s\n" % (doc1,doc2))
          traceback.print_exc(file=sys.stderr)
          fails.write("%s\t%s\n" % (doc1,doc2))
          continue
       if doc2 in d1.pippiDocs:
           print "already done: %s %s" % (doc1,doc2)
           continue
       try:
           d2=getDoc(doc2)
       except:
          print "!!!!PIPPI ERROR: load doc",doc2
          sys.stderr.write("%s\t%s\n" % (doc1,doc2))
          traceback.print_exc(file=sys.stderr)
          fails.write("%s\t%s\n" % (doc1,doc2))
          continue
       try:
          lcs.pippi(d1,d2)
       except:
          print "!!!!PIPPI ERROR: lcs",doc1,doc2
          sys.stderr.write("%s\t%s\n" % (doc1,doc2))
          traceback.print_exc(file=sys.stderr)
          fails.write("%s\t%s\n" % (doc1,doc2))
    tfidf.save()
    fails.close()

if __name__ == "__main__":
    import platform
    if platform.machine() in ['i386', 'i686']:
        import psyco
        psyco.full()
    #import os
    #import cProfile
    #cProfile.run('main()', '/tmp/bp-%d.prof' % (os.getpid()))
    main()
