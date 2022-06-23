// Demo
if (window.parent && window !== window.parent) {
  const html = document.documentElement;
  if (html) {
    html.style.setProperty('--f7-safe-area-top', '44px');
    html.style.setProperty('--f7-safe-area-bottom', '34px');
  }
}

// Dom7
var $ = Dom7;

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
  // routes: routes,
  routes: [
    // {
    //   path: '/',
    //   // componentUrl: '/onpointlite_base/static/src/pages/home.html',
    // //   componentUrl: '/mobile/index',
    //   url: '/mobile/index',
    //   name: 'index',
    //   master(f7) {
    //     return f7.theme === 'aurora';
    //   },
    // },
    {
      path: '/index/',
      // componentUrl: '/mobile/index',
      url: '/mobile/index',
      name: 'index',
      options: {
          clearPreviousHistory: true,
          pushState: true
      }
      // master(f7) {
      //     return f7.theme === 'aurora';
      // },
    },
  ],
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

// var $$ = Dom7;

// var mainView = app.views.create('.view-main');
