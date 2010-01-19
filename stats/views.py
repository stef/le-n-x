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

from django.http import HttpResponse
from django.template import RequestContext
from django.shortcuts import render_to_response
from django import forms
from brain.stats import SMatchDb

CSSHEADER='<head><link href="http://www.ctrlc.hu/~stef/pippi.css" media="screen" rel="stylesheet" title="" type="text/css"  /></head>'

class StatsForm(forms.Form):
    fn = forms.MultipleChoiceField(required=True)
    fn.choices=[('2',"Frequent Frags"), ('1',"Longest Frags"), ('0',"Overall Statistics")]

def stats(request):
    form = StatsForm(request.GET)
    if form.is_valid():
        fn=form.cleaned_data['fn']
        db=SMatchDb()
        db.load()
        if fn==u'1':
            result='<br />'.join(db.getFreqTokens()).encode('utf8')
        elif fn==u'2':
            result='<br />'.join(db.getFreqFrags()).encode('utf8')
        else:
            result='<br />'.join(db.stats()).encode('utf8')
        return HttpResponse('%s\n%s' % (CSSHEADER,unicode(str(result),'utf8')))
    else:
        return render_to_response('stats.html', { 'form': form, })


