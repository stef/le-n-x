#!/usr/bin/env python
#    This file is part of le-n-x.

#    utterson is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.

#    utterson is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.

#    You should have received a copy of the GNU Affero General Public License
#    along with utterson.  If not, see <http://www.gnu.org/licenses/>.

# (C) 2009-2010 by Stefan Marsiske, <stefan.marsiske@gmail.com>

import re
import urllib2

filterre=re.compile("http://eur-lex\.europa\.eu/LexUriServ/LexUriServ\.do\?uri=(.*)")

class Cache:
    def __init__(self,dir):
        self.__dict__={}
        self.__dict__['basedir'] = dir

    def __getattr__(self, name):
        if name in self.__dict__.keys():
            return self.__dict__[name]
        else:  raise AttributeError, name

    def __setattr__(self, name, value):
        if name in self.__dict__.keys():
            self.__dict__[name]=value
        else:  raise AttributeError, name


    """ returns the contents of an url either from the cache or the web """
    def fetchUrl(self,url):
        filter=re.match(filterre,url)
        if(not filter): return
        id=filter.group(1)
        try:
            f = open(self.basedir+'/'+id, 'r')
        except IOError:
            text = urllib2.urlopen(url).read()
            # write out cached object
            f = open(self.basedir+'/'+id, 'w')
            f.write(text)
            f.close()
        else:
            text = f.read()
        f.close()
        return text
