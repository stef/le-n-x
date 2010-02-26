from lenx.view.models import Doc, Frag, Location
from django.core.management import setup_environ
from lenx import settings
from lenx.brain import lcs
setup_environ(settings)
import sys, os

docs={}

def getDoc(doc):
    if docs.has_key(doc): return docs[doc]
    docs[doc], created = Doc.objects.get_or_create(eurlexid=doc)
    if created:
        docs[doc].save()
    return docs[doc]

fraglen=len(Frag.objects.all())
doclen=len(Doc.objects.all())
loclen=len(Location.objects.all())
for line in sys.stdin:
    print line
    (doc1,doc2)=eval(line)
    d1=getDoc(doc1)
    d2=getDoc(doc2)
    lcs.pippi(d1,d2)

print 'added frags',len(Frag.objects.all())-fraglen
print 'added docs',len(Doc.objects.all())-doclen
print 'added locations', len(Location.objects.all())-loclen
#print Doc.objects.all()

