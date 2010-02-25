from brain.fsdb import FilesystemDB
from view.models import Doc, Frag, Location
from django.core.management import setup_environ
from lenx import settings
setup_environ(settings)

def storeMatch(doc,stem,pos,l):
    d, created = Doc.objects.get_or_create(eurlexid=doc)
    if created:
        print d
        d.save()
    txt=unicode(d.gettokens()[0][pos:pos+l])
    l, created = Location.objects.get_or_create(doc=d,idx=pos,txt=txt)
    if created:
        print l
        l.save()
    frag, created = Frag.objects.get_or_create(frag=str(stem),l=len(stem))
    if created:
        print frag
    frag.docs.add(l)
    frag.save()

fsdb=FilesystemDB('db')
pippies={}
pippies=fsdb.loadVal("matches") or {}
for stem,frags in pippies.items():
    for doc,pos,l in frags:
        assert l == len(stem)
        storeMatch(doc,stem,pos,l)

print 'total frags',len(Frag.objects.all())
print 'total docs',len(Doc.objects.all())
print 'total locations', len(Location.objects.all())
print Doc.objects.all()
