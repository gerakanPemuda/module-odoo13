// Demo
if (window.parent && window !== window.parent) {
  const html = document.documentElement;
  if (html) {
    html.style.setProperty('--f7-safe-area-top', '44px');
    html.style.setProperty('--f7-safe-area-bottom', '34px');
  }
}

// Dom7
var $$ = Dom7;

// Theme
var theme = 'auto';
if (document.location.search.indexOf('theme=') >= 0) {
  theme = document.location.search.split('theme=')[1].split('&')[0];
}

// Init App
var app = new Framework7({
  id: 'id.onpointlite.wtccloud',
  el: '#app',
  theme,
  // store.js,
  // store: store,
  // routes.js,
  routes: routes,
  navbar: {
    mdCenterTitle: true,
  },

  popup: {
    closeOnEscape: true,
  },
  sheet: {
    closeOnEscape: true,
  },
  popover: {
    closeOnEscape: true,
  },
  actions: {
    closeOnEscape: true,
  },
  vi: {
    placementId: 'pltd4o7ibb9rc653x14',
  },
});

var view = app.views.create('.view-main', {
  on: {
    pageInit: function () {
      console.log('page init')
    },
    
  }
})

var mainView = app.views.create('.view-main');
console.log("masukkk");


$$(document).on('page:init', '.page[data-name="index"]', function(e) {
  console.log("masuk");
  $$('#icon-add-logger').on('click', function(e) {
    console.log("add logger.");
    router.navigate({
      name: 'logger_form'},
      {
        ignoreCache: true,
        force: true
      });
  });
});
