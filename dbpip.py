from view.models import Doc, Frag, Location
from django.core.management import setup_environ
from lenx import settings
from brain import lcs
setup_environ(settings)
import document, sys, os
import cache as Cache
CACHE=Cache.Cache('../cache');

fraglen=len(Frag.objects.all())
doclen=len(Doc.objects.all())
loclen=len(Location.objects.all())

docs={}

def getDoc(doc):
    if docs.has_key(doc): return docs[doc]
    docs[doc], created = Doc.objects.get_or_create(eurlexid=doc)
    if created:
        d.save()
    return docs[doc]

for line in sys.stdin:
    (doc1,doc2)=eval(line)
    d1=getDoc(doc1)
    d2=getDoc(doc2)
    lcs.pippi(d1.stems,d2.stems)

    print 'added frags',len(Frag.objects.all())-fraglen
    print 'added docs',len(Doc.objects.all())-doclen
    print 'added locations', len(Location.objects.all())-loclen
    #print Doc.objects.all()

