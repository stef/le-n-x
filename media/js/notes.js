Notes = ("Notes" in window) ? Notes : {};

Notes.Annotator = function (element) {
  var $ = jQuery, self = this;

  this.annotator = $(element).annotator().data('annotator');
  this.currentUser = null;

  this.options = {
    user: { },

    store: {
      prefix: '/annotations',
      loadFromSearch: {
         'limit': 0,
         'uri': window.location.href
       },
       urls: {
         create:  '/',
         update:  '/:id',
         destroy: '/:id',
         read:    '/:id',
         search:  '/search'
       },
       annotationData: {
         'uri': window.location.href
       }
    }
  }

  // Init
  ;(function () {
     self.annotator.addPlugin("User", self.options.user);
     self.annotator.addPlugin("Store", self.options.store);
  })();

  this.setCurrentUser = function (user) {
    self.annotator.plugins["User"].setUser(user);
  };

  return this;
};
