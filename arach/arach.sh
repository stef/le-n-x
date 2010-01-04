#!/bin/ksh
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

root=http://eur-lex.europa.eu/en/legis/20091201
traverse $root/index.htm ./

function traverse {
    response=`mktemp -t arach.sh.XXXXXX`
    trap "rm $response* 2>/dev/null" 0
    curl --retry 4 -sq "$1" >$response
    # handle downloading of referenced docs
    grep -o 'LexUriServ[.]do[?]uri=[0-9A-Z:]*:NOT">.*</a>' <$response | scrape "$2"
    # traverse sub chapters
    grep -o '<a href="chap[0-9]*.htm">.*</a>' <$response |
        while read chapter; do
            file=$(echo "$chapter" | cut -d'"' -f2)
            chn=${file##chap}; chn=${chn%%.htm}
            title=$(echo "$chapter" | cut -d' ' -f3- | sed 's/<\/a>//')
            [[ -n "$title" ]] && {
                mkdir -p "$2$chn $title"
                print "traverse $root/$file $2$chn $title/"
                traverse $root/$file "$2$chn $title/"
            }
        done
}

function scrape {
    regex='uri=.*:HTML" class="linkhtml">html<\/a>'
    while read doc; do
        url=${doc##*=}; url=${url%%\">*}
        title=${doc%%<*}; title=${title##*>}
        destdir="$1$title"
        echo -n "$title"
        mkdir -p "$destdir"
        curl --retry 4 -sq "http://eur-lex.europa.eu/LexUriServ/LexUriServ.do?uri=$url" >"$destdir/index"
        grep -o "$regex" <"$destdir/index" |
            while read langdoc; do
                url=${langdoc##*uri=}; url=${url%%\"*}
                lang=${url%%:HTML}; lang=${lang##*:}
                echo -n " $lang"
                curl --retry 4 -qs "http://eur-lex.europa.eu/LexUriServ/LexUriServ.do?uri=$url" >"$destdir/$lang";
            done
        echo
    done
}
