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

# (C) 2010 by Stefan Marsiske, <stefan.marsiske@gmail.com>

from tempfile import mkstemp
import msgpack, os, itertools, re
from datetime import datetime
from lenx.view.models import Doc, Pippi, Pippies, PippiFrag

resultDir='/tmp/pippibulksaver'

def lcsPkt(p1,p2,l,stem,d1,d2):
    if l>1:
        return {'pippi' : stem,
                'l'     : l,
                'd1ps'  : [{'pos' : p, 'txt' : d1.tokens[p:p+l]} for p in p1],
                'd2ps'  : [{'pos' : p, 'txt' : d2.tokens[p:p+l]} for p in p2],
                }

class Saver():
    queue=[]

    def write(self,pkt):
        if pkt:
            self.queue.append(pkt)

    def flush(self,d1,d2):
        (fd,fname)=mkstemp(dir=resultDir)
        fd=os.fdopen(fd, "w+b")
        fd.write(msgpack.packb({'d1': d1.eurlexid,
                      'd2': d2.eurlexid,
                      'pippies': self.queue}))
        fd.close()
        os.rename(fname,fname+'.batch')
        self.queue=[]

class DocPool():
    docs={}
    size=2
    def get(self,d):
        if(not d in self.docs):
            self.docs[d]={'doc': Doc(d), 'last': datetime.now()}
            if len(self.docs)>self.size:
                old=reduce(lambda x,y: x[1]['last']<y[1]['last'] and x or y, self.docs.items())
                old[1]['doc'].save()
                del self.docs[old[0]]
        else:
            self.docs[d]['last']=datetime.now()
        return self.docs[d]['doc']

    def flush(self):
        for doc in self.docs.values():
            doc['doc'].save()

class FragPool():
    frags={}
    dirtyQ=[]
    fragsBucket=64

    def get(self,f):
        if len(self.dirtyQ)>self.fragsBucket:
            self.flush()
        if(not f in self.frags):
            self.frags[f]=Pippi(f)
        return self.frags[f]

    def add(self,f):
        self.frags[f.pippi]=f
        #print f.docs
        if not f.pippi in self.dirtyQ:
            self.dirtyQ.append(f.pippi)

    def flush(self):
        for frag in self.dirtyQ:
            self.frags[frag].save()
        del self.dirtyQ[:]

DOCS=DocPool()
FRAGS=FragPool()

def read(fname):
    fd=open(fname,'r+b')
    pkt=msgpack.unpackb(fd.read())
    fd.close()
    d1=DOCS.get(pkt['d1'])
    d2=DOCS.get(pkt['d2'])
    for pippi in pkt['pippies']:
        storePippi(pippi,d1,d2)
    d1.addDoc(d2)
    d2.addDoc(d1)
    os.rename(fname,fname+'.stored')

def storePippi(pkt,d1,d2):
    frag=FRAGS.get(pkt['pippi'])

    d1.pippies.extend([{'pos':p['pos'],'txt':tuple(p['txt']),'l':pkt['l'],'frag':frag._id}
                for p in pkt['d1ps']])
    d2.pippies.extend([{'pos':p['pos'],'txt':tuple(p['txt']),'l':pkt['l'],'frag':frag._id}
                for p in pkt['d2ps']])
    frag.docs=frag.docs.union([PippiFrag(p['pos'],p['txt'],pkt['l'],d) for (d,p) in
                               [(d1._id, p) for p in pkt['d1ps']]+[(d2._id, p) for p in pkt['d2ps']]])
    FRAGS.add(frag)

def mainloop():
    # flush out what's in the resultDir
    while True:
        batches=[fn for fn in os.listdir(resultDir) if fn[-6:]=='.batch']
        if not batches: break
        for (i,batch) in itertools.izip(itertools.count(1),batches):
            print (float(i)/len(batches))*100,"%"
            read(resultDir+'/'+batch)

    DOCS.flush()
    FRAGS.flush()

if __name__ == "__main__":
    import platform
    if platform.machine() in ['i386', 'i686']:
        import psyco
        psyco.full()
    import cProfile
    cProfile.run('mainloop()', '/tmp/bs.prof')
    #mainloop()
