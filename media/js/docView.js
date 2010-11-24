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
      this.ids = new Array();
      this.ct = 0; // close timer
      this.show = function(c, id) { 
          if((new Date())-this.aborto > this.it) {
              if(this.ids.length > 0) {
                  for(var i=0; i<this.ids.length; i++) {
                      if(this.ids[i] == id) {
                          return;
                      }
                  }
              }
              this.ids.push(id);
              if(!$(this.e).is(':visible')) {
                  $(this.e).fadeIn('slow');
                  $('#msgbox_c').html(c);
              } else {
                  $('#msgbox_c').append('<hr />'+c);
              }
          }
      }
      this.timedShow = function(c, id) {
          var a = this;
          setTimeout( function() { a.show(c, id); }, this.it);
      }
      this.doHide = function(){  if((new Date())-this.abortc > this.ct) { this.ids = []; this.e.fadeOut(); } }
      this.hide = function(t) {
          this.ct = t;
          var a = this;
          setTimeout(function() { a.doHide(); } , t);
      }
      this.abortClose = function() {
          this.abortc = new Date();
      }
      this.abortOpen = function() {
          this.aborto = new Date();
      }
  }
  $(document).ready(function() {
     $('#loading').show();
     var msgBox = new MsgBox('#msgbox', 300);
     $('#msgbox').hover(function() { msgBox.abortClose(); }, function() { msgBox.hide(1000); });
     $('.msgbox_close').click(function () { msgBox.hide(0); });
     $('.highlight').hover(
         function() {
         var id = $(this).attr('class').split(' ')[1];
         $.map($('.'+id),
             function(e) {
                 $(e).addClass('hovered');
                 c = $('#'+id).html();
                 //console.log(id);
                 msgBox.timedShow(c, id);
             });
         msgBox.abortClose();
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
    $('#loading').hide();
  });
