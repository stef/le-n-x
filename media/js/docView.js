  Array.prototype.contains = function (element) {
    for (var i = 0; i < this.length; i++) {
      if (this[i] == element) { return true; }
    }
    return false; };

  $(document).ready(function() {
    $('#loading').show();

     $('.highlight').hover(
         function() {
         $.map($('.'+$(this).attr('class').split(' ')[1]), 
             function(e) { 
                 $(e).addClass('hovered'); 
             });
         }, 
         function(){
         $.map($('.'+$(this).attr('class').split(' ')[1]), 
             function(e) { 
                 $(e).removeClass('hovered');
             });
         });
	 $(".highlight").each(function(){
	 	var el = $(this);

      tipId=el.attr("class").split(" ")[1];
      parents=el.parents(".highlight");
      // if we have hilited parents, then we merge the 'alsoin' tooltip contents
      if(parents.length>0) {
        var moreDocs=[];
        tip=$('#'+tipId);
        newpid=[tip.attr('id')];

        // we collect the list items and the pippiOid for every parent hilite
        parents.each(function() {
          pid=$(this).attr('class').split(" ")[1];
          newpid.push(pid);
          moreDocs=moreDocs.concat($("#"+pid).find('li'));
        });

        newTipId=newpid.join('-');
        // if no composite tooltip exists yet for this nested pippi, create one
        if($("#"+newTipId).length==0) {
          newTip=$("<span>").addClass('pippiNote').attr('id',newTipId);
          newTip.append(tip.children().clone());
          ul=newTip.find("ul");
          links=ul.find("a").attr('href');
          if(typeof(links) == 'string') links=Array(links);

          // add each unique parent doc to the composite tooltip
          moreDocs.forEach(function(elem) {
            curl=$(elem).find("a").attr('href');
            if(! links.contains(curl)) {
              ul.append($(elem).clone());
              links.push(curl);
            }
          });
          $('#tooltips').append(newTip);
        }
        tipId=newTipId;
      }

		el.tooltip({
        effect: 'fade',
        delay: 150,
        predelay: 400,
		  tip : '#'+tipId,
        onBeforeShow: function(e,pos) {
          e.stopPropagation();
        },
               });
	 });

    $('#loading').hide();
  });
