// ==UserScript==
// @name               Bonobo
// @description	     provides some updates to the eur-lex database of europan legislation
// @include		http://eur-lex.europa.eu/en/legis/*
// ==/UserScript==

var tagserver="http://www.ctrlc.hu:14148/ucloud/?url=";

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
addGlobalStyle('.tagcloud { float: right; width: 400px; height: 80px; border: 1px dotted blue; }');


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
