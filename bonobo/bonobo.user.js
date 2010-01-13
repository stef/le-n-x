// ==UserScript==
// @name               Bonobo
// @description	     provides some updates to the eur-lex database of europan legislation
// @include		http://eur-lex.europa.eu/en/legis/*
// ==/UserScript==

//    This file is part of le-n-x.

//    utterson is free software: you can redistribute it and/or modify
//    it under the terms of the GNU Affero General Public License as published by
//    the Free Software Foundation, either version 3 of the License, or
//    (at your option) any later version.

//    utterson is distributed in the hope that it will be useful,
//    but WITHOUT ANY WARRANTY; without even the implied warranty of
//    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
//    GNU Affero General Public License for more details.

//    You should have received a copy of the GNU Affero General Public License
//    along with utterson.  If not, see <http://www.gnu.org/licenses/>.

// (C) 2009-2010 by Stefan Marsiske, <stefan.marsiske@gmail.com>

var tagserver="http://92.243.28.240:14148/ucloud/?url=";

function addGlobalStyle(css) {
  try {
	 var elmHead, elmStyle;
	 elmHead = document.getElementsByTagName('head')[0];
	 elmStyle = document.createElement('style');
	 elmStyle.type = 'text/css';
	 elmHead.appendChild(elmStyle);
	 elmStyle.innerHTML = css;
	 } catch (e) {
		if (!document.styleSheets.length) {
		  document.createStyleSheet();
		}
		document.styleSheets[0].cssText += css;
	 }
}

var loader = function(item, container) {
  this.item = item;
  this.container = container;
  this.handler = function() {
    GM_xmlhttpRequest({method:'GET', url: tagserver + this.item,
    headers: {
		'User-agent': 'Mozilla/5.0 (compatible) GM Bonobo'
	 },
    onload: function(results) {
      if (results.status != 200) {
	     return;
      }
      //var br = document.createElement('br');
      //br.style.clear="both";
      //container.insertBefore(br,container.firstChild);
      var tagcontainer = document.createElement('div');
      tagcontainer.className="tagcloud";
      tagcontainer.innerHTML=results.responseText;
      container.insertBefore(tagcontainer,container.firstChild);
    }});
  };
};

addGlobalStyle('.size0 { font-size: .4em; }');
addGlobalStyle('.size1 { font-size: .5em }');
addGlobalStyle('.size2 { font-size: .6em }');
addGlobalStyle('.size3 { font-size: .7em }');
addGlobalStyle('.size4 { font-size: .8em }');
addGlobalStyle('.size5 { font-size: .9em }');
addGlobalStyle('.size6 { font-size: 1em }');
addGlobalStyle('.size7 { font-size: 1.1em }');
addGlobalStyle('.size8 { font-size: 1.2em }');
addGlobalStyle('.size9 { font-size: 1.3em }');
addGlobalStyle('.tagcloud { float: right; width: 400px; border: 1px dotted blue; }');


var docs = document.evaluate("//ul[@class='tSearchTable5']/li", document, null,
                             XPathResult.UNORDERED_NODE_SNAPSHOT_TYPE, null);
for (var i = 0; i < docs.snapshotLength; i++) {
  var container=docs.snapshotItem(i);
  var node=document.createElement('li');
  node.innerHTML=container.innerHTML;
  var url = document.evaluate("//a[@class='linkhtml']", node, null,
                             XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue;
  new loader(url, container).handler();
}
