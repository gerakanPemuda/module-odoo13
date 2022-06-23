var woView = app.views.create('.view-wo', {
   routesAdd: [
    {
        name: 'wo_index',
        path: '/wo/index/',
        url: '/mobile/wo/index'
    },
   ]
});

$$(document).on('page:init', '.page[data-name="index"]', function(e) {

    $$('#menu_wo').on('click', function() {

        woView.router.navigate({
                name: 'wo_index'
                },
                {
                    ignoreCache: true,
                    force: true
                });
    })

});
