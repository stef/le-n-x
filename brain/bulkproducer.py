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

alldocs=[x.strip('\t\n') for x in sys.stdin]
l=len(alldocs)*(len(alldocs)-1)/2
allops=[(x,y) for x,i in zip(alldocs,xrange(l)) for y in alldocs[i+1:]]

idx=int(sys.argv[1])
clusters=int(sys.argv[2])

start=idx*l/clusters
end=start+l/clusters
print "\n".join([str(x) for x in allops][start:end])
