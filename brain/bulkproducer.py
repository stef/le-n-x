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

import sys
from itertools import izip, count

try:
    from itertools import combinations
except ImportError:
    def combinations(iterable, r):
        # combinations('ABCD', 2) --> AB AC AD BC BD CD
        # combinations(range(4), 3) --> 012 013 023 123
        pool = tuple(iterable)
        n = len(pool)
        if r > n:
            return
        indices = range(r)
        yield tuple(pool[i] for i in indices)
        while True:
            for i in reversed(range(r)):
                if indices[i] != i + n - r:
                    break
            else:
                return
            indices[i] += 1
            for j in range(i+1, r):
                indices[j] = indices[j-1] + 1
            yield tuple(pool[i] for i in indices)

alldocs=[x.strip('\t\n') for x in sys.stdin]
#l=len(alldocs)*(len(alldocs)-1)/2
#allops=[(x,y) for x,i in zip(alldocs,xrange(l)) for y in alldocs[i+1:]]

idx=int(sys.argv[1])
clusters=int(sys.argv[2])

counter=count(0)
combis=combinations(alldocs,2)
try:
    job=combis.next()
    while job:
        if (counter.next() % clusters)==idx: print job
        job=combis.next()
except StopIteration:
    pass
