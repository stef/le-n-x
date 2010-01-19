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

# (C) 2009-2010 by Stefan Marsiske, <stefan.marsiske@gmail.com>

import os, cPickle

class FilesystemDB():
    def __init__(self,base):
        self.__dict__['base']=base+'/'

    def __getattr__(self, name):
        if name in self.__dict__.keys():
            return self.__dict__[name]
        else:  raise AttributeError, name

    def __setattr__(self, name, value):
        if name in self.__dict__.keys():
            self.__dict__[name]=value
        else:  raise AttributeError, name

    def getDict(self,dir,create=True):
        if not os.path.exists(self.base+dir):
            if not create: return None
            os.mkdir(self.base+dir)
        return dir

    def getKeys(self,key):
        return os.listdir(self.base+"/"+key)

    def storeVal(self,key,value):
        file=open(self.base+key,'w')
        file.write(cPickle.dumps(value))
        file.close()

    def loadVal(self,key):
        file=open(self.base+key,'r')
        res=cPickle.loads(file.read())
        file.close()
        return res

