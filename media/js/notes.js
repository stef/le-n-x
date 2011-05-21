Notes = ("Notes" in window) ? Notes : {};

Notes.Annotator = function (element) {
  var $ = jQuery, self = this;

  this.annotator = $(element).annotator().data('annotator');
  this.currentUser = null;

  this.options = {
    user: { },
    tags: { },

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
         // TODO decouple from hostname! also in notes/pippinotes.py
         'uri': window.location.href
       }
    }
  }

  // Init
  ;(function () {
     self.annotator.addPlugin("User", self.options.user);
     self.annotator.addPlugin("Store", self.options.store);
     self.annotator.addPlugin("Tags", self.options.tags);
  })();

  this.setCurrentUser = function (user) {
    self.annotator.plugins["User"].setUser(user);
  };

  return this;
};
