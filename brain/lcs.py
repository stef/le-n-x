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

from lenx.brain import bulksaver, stopwords
from lenx.notes.pippinotes import saveNotes
from lenx import settings

# src: http://chipsndips.livejournal.com/425.html
# kludge: infinity is a very large number
inf = 100000000

StopFrags=stopwords.StopFrags()

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
                elif t in s:
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

def walkACS(i,j,s):
    if not s:
        return [(i,0)]
    return [(end, l+j-i+1) for (m,n,o) in s.values() for (end, l) in walkACS(m,n,o)]

def pippi(D1,D2,saver=bulksaver.Saver()):
    doc1=tuple(D1.stems+('zAq!2WsX',))
    doc2=tuple(D2.stems+('XsW@!qAz',))
    if D2._id in D1.pippiDocs:
        return None
    lcs=LCS(doc1,doc2)

    pips={}
    # filter out sub-pippies, by only retaining the longest ones ending in the same position.
    for end, l in sorted([candidate for i,j,s in lcs.root.values() for candidate in walkACS(i,j,s)]):
        if not end in pips or pips[end]<l:
            pips[end]=l

    frags={}
    ld=len(doc1)
    # calculate stem, and foreach assemble list of pos
    for end, l in pips.items():
        stem=lcs.str[end-l:end]
        if StopFrags.isStopFrag(stem): continue
        if not stem in frags:
            frags[stem]=[l, [],[]]
        # append position to list appointed by sel
        sel=((end-l)/ld)>0
        frags[stem][1+sel].append(end-l-(sel*ld))

    if saver:
        saver.addDocs(D1,D2)
        # also save as annotations
        # TODO only save when saver is set!
        saveNotes(D1,D2,frags,settings.ROOT_URL)
    return [(saver.save(D1,D2,bulksaver.lcsPkt(sorted(a),sorted(b),l,stem,D1,D2))
             if saver
             else (l,stem,sorted(a),sorted(b)))
            for stem, (l, a, b)
            in frags.items()
            if a and b]

if __name__ == "__main__":
    #from lenx.view.eurlex import Doc
    from lenx.view.doc import Doc
    #import pprint
    import sys
    #frag=LCS(doc1,doc2)
    #pprint.pprint(frag.root)

    d1=Doc(docid=sys.argv[1].strip('\t\n'))
    #pprint.pprint(d1.extractMetadata())
    d2=Doc(docid=sys.argv[2].strip('\t\n'))
    #pprint.pprint(d2.extractMetadata())
    pips=pippi(d1,d2,None)
    #pprint.pprint(pips)
