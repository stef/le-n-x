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

# src: http://chipsndips.livejournal.com/425.html
import sys
from view.models import Doc, Frag, Location

# kludge: infinity is a very large number
inf = 100000000

# Define a class for a node in the suffix tree
class SuffixNode(dict):
    def __init__(self):
        self.suffixLink = None # Suffix link as defined by Ukkonen

    def Print(self,str,ws=""):
        for t in self:
            k,p,s = self[t]
            if p == inf:
                print "%s%s" % (ws, str[k:])
            else:
                print "%s%s" % (ws, str[k:p+1])
                s.Print(str,ws+"|"*(p-k+1))

class LCS:
    def __init__(self,str1,str2):
        str = str1 + str2
        inf = len(str)
        self.str = str   #Keep a reference to str to ensure the string is not garbage collected
        self.seed = SuffixNode() #Seed is a dummy node. Suffix link of root points to seed. For any char,there is a link from seed to root
        self.root = SuffixNode() # Root of the suffix tree
        self.root.suffixLink = self.seed
        self.root.depth = 0
        self.deepest = 0,0

        # For each character of str[i], create suffixtree for str[0:i]
        s = self.root; k=0
        for i in range(len(str)):
            self.seed[str[i]] = -2,-2,self.root
            oldr = self.seed
            t = str[i]
            #Traverse the boundary path of the suffix tree for str[0:i-1]
            while True:
               # Decend the suffixtree until state s has a transition for the stringstr[k:i-1]
                while i>k:
                   kk,pp,ss = s[str[k]]
                   if pp-kk < i-k:
                       k = k + pp-kk+1
                       s = ss
                   else:
                       break
               # Exit this loop if s has a transition for the string str[k:i] (itmeans str[k:i] is repeated);
               # Otherwise, split the state if necessary
                if i>k:
                   tk = str[k]
                   kp,pp,sp = s[tk]
                   if t == str[kp+i-k]:
                       break
                   else: # Split the node
                       r = SuffixNode()
                       j = kp+i-k
                       tj = str[j]
                       r[tj] = j, pp, sp
                       s[str[kp]] = kp,j-1, r
                       r.depth = s.depth + (i-k)
                       sp.depth = r.depth + pp - j + 1
                       if j<len(str1)<i and r.depth>self.deepest[0]:
                           self.deepest = r.depth,j-1
                elif s.has_key(t):
                    break
                else:
                    r = s
               # Add a transition from r that starts with the letter str[i]
                tmp = SuffixNode()
                r[t] = i,inf,tmp
                # Prepare for next iteration
                oldr.suffixLink = r
                oldr = r
                s = s.suffixLink
            # Last remaining endcase
            oldr.suffixLink = s

    def LongestCommonSubstring(self):
        return self.str[self.deepest[1]-self.deepest[0]+1:self.deepest[1]+1]

    def Print(self):
        self.root.Print(self.str)

def findlist(sub,target):
    c=0
    t=target
    while t:
        try:
            i=t.index(sub[0])
        except:
            return None
        c=c+i
        if t[i:i+len(sub)]==sub:
            return c
        t=t[i+1:]
    return None

def find(sub,target):
    res=[]
    c=0
    t=target
    m=findlist(sub,t)
    while m:
        res.append(m+c)
        del t[m:m+len(sub)]
        m=findlist(sub,t)
        c=c+len(sub)
    return res


def getACS(str,st,d):
    for n in st:
        i,j,s = st[n]
        if(j<inf) and s:
            d=getACS(str,s,d)
            l=j+1-i
            if not d.has_key(j) or l>d[j]['l']:
                d[j]={
                    'l':l,
                    'pos':[x[0]-l for x in s.values()],
                    'frag':str[i:j+1],
                    }
    return d

def getDoc(doc):
    d, created = Doc.objects.get_or_create(eurlexid=doc)
    if created:
        #print d
        d.save()
    return d

def getLoc(d,pos,l):
    txt=unicode(d.gettokens()[0][pos:pos+l])
    loc, created = Location.objects.get_or_create(doc=d,idx=pos,txt=txt)
    if created:
        #print loc
        loc.save()
    return loc

def getFrag(stem):
    frag, created = Frag.objects.get_or_create(frag=unicode(stem),l=len(stem))
    if created:
        #print frag
        frag.save()
    return frag

def pippi(d1,d2,store=True):
    doc1=[x or ('!1@3#@@%4%$#^7*(',) for x in d1]+['zAq!2WsX']
    doc2=[x or ('!1@3#@@%4%$#^7*(',) for x in d2]+['XsW@!qAz']
    D1=getDoc(sys.argv[1])
    D2=getDoc(sys.argv[2])

    frag=LCS(doc1,doc2)
    res={}
    for m in getACS(frag.str,frag.root,{}).values():
        a=[]
        b=[]
        for p in m['pos']:
            if p<len(doc1):
                a.append(p)
            else:
                b.append(p-len(doc1))
        if a and b:
            stem=tuple([() if x==('!1@3#@@%4%$#^7*(',) else x for x in m['frag']])
            res[stem]=(a,b)
            l=len(stem)
            if store and l>1:
                frag=getFrag(stem)
                for p in a:
                    loc=getLoc(D1,p,l)
                    frag.docs.add(loc)
                for p in b:
                    loc=getLoc(D2,p,l)
                    frag.docs.add(loc)
                frag.save()
    return res

if __name__ == "__main__":
    import document, cache
    import pprint

    CACHE=cache.Cache('../cache');
    d1=document.Doc(sys.argv[1].strip('\t\n'),cache=CACHE)
    d2=document.Doc(sys.argv[2].strip('\t\n'),cache=CACHE)
    #CACHE=cache.Cache('../tmp');
    #d1=document.Doc('test1.html'.strip('\t\n'),cache=CACHE)
    #d2=document.Doc('test2.html'.strip('\t\n'),cache=CACHE)

    from operator import itemgetter
    topfrags=[ x for x in sorted( pippi(d1.stems,d2.stems,store=False).items(),
                                 reverse=True,
                                 cmp=lambda x,y: cmp(len(x[0]),len(y[0])))
                if len(x[0])>0 ]
    print pprint.pprint(topfrags)

    #print pprint.pprint(frag.root)+"\n"+frag.LongestCommonSubstring()
    #print getfrags(d1.tokens,d2.tokens)
