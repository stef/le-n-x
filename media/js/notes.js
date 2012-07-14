Notes = ("Notes" in window) ? Notes : {};

Notes.Annotator = function (element) {
  var self = this;
  this.currentUser = null;
  this.options = {
    permissions: { showEditPermissionsCheckbox: false },
    store: {
      prefix: '/annotations',
      loadFromSearch: {
        'limit': 0,
        'all_fields': 1,
        'uri': window.location.href.split('?')[0]
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
         'uri': window.location.href.split('?')[0]
       }
    }
  };

  this.setCurrentUser = function (user) {
    self.annotator.plugins["Permissions"].setUser(user);
  };

  this.annotator = $(element).annotator().data('annotator')
     //.addPlugin('Auth')
     .addPlugin('Unsupported')
     .addPlugin('Filter')
     .addPlugin('Tags')
     .addPlugin('Permissions')
     .addPlugin('Store', self.options.store);

  return this;
};
