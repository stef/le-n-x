  var msgFocus=0, hlFocus=0;
  Array.prototype.contains = function (element) {
    for (var i = 0; i < this.length; i++) {
      if (this[i] == element) { return true; }
    }
    return false; };
  
  function MsgBox(id, idleTime) {
      this.e = $(id);
      this.aborto = new Date();
      this.abortc = new Date();
      this.it = idleTime;
      this.ct = 0; // close timer
      this.show = function(c) { 
          if((new Date())-this.aborto > this.it) {
              if(!$(this.e).is(':visible')) {
                  $(this.e).fadeIn('slow');
                  $('#msgbox_c').html(c);
              } else {
                  $('#msgbox_c').append('<hr />'+c);
              }
          }
      }
      this.timedShow = function(c) {
          var a = this;
          setTimeout( function() { a.show(c); }, this.it);
      }
      this.doHide = function(){  if((new Date())-this.abortc > this.ct) this.e.fadeOut(); }
      this.hide = function(t) {
          this.ct = t;
          var a = this;
          setTimeout(function() { a.doHide(); } , t);
      }
      this.abortClose = function() {
          console.log("abortClose called");
          this.abortc = new Date();
      }
      this.abortOpen = function() {
          console.log("abortOpen called");
          this.aborto = new Date();
      }
  }
  $(document).ready(function() {
     $('#loading').show();
     var msgBox = new MsgBox('#msgbox', 300);
     $('#msgbox').hover(function() { msgBox.abortClose(); }, function() { msgBox.hide(1000); });
     $('.highlight').hover(
         function() {
         $.map($('.'+$(this).attr('class').split(' ')[1]),
             function(e) {
                 $(e).addClass('hovered');
             });
         msgBox.abortClose();
         msgBox.timedShow($(this).html());
         },
         function(){
         $.map($('.'+$(this).attr('class').split(' ')[1]),
             function(e) {
                 $(e).removeClass('hovered');
             });
         msgBox.abortOpen();
         msgBox.hide(2000);
         }
     );
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
