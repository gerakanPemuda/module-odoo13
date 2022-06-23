var app = new Framework7({
  // App root element
  root: '#app',
  // App Name
  name: 'Onpoint - Work Order',
  // App id
  id: 'com.mobile.onpoint',
  // Enable swipe panel
  panel: {
    swipe: 'left',
  },
  view: {
    stackPages: false,
    pushState: true
  },
  // Add default routes
  routes: [
    {
        name: 'index',
        path: '/wo/index/',
        url: '/mobile/wo/index',
    },
    {
        name: 'wo_detail',
        path: '/wo/detail/:wo_id',
        url: '/mobile/wo/detail/{{wo_id}}',
    },
    {
        name: 'wo_picture',
        path: '/wo/picture/:wo_id/:state_to',
        url: '/mobile/wo/picture/{{wo_id}}/{{state_to}}',
    }
  ],
  // ... other parameters
});

var $$ = Dom7;

var mainView = app.views.create('.view-main');


var openGoogleMaps = function(latitude, longitude) {
    window.location.href = 'https://www.google.com/maps/dir/?api=1&destination=' + latitude + ',' + longitude;
};


$$(document).on('page:init', '.page[data-name="index"]', function(e) {

    var $ptrContent = $$('.ptr-content');

    $ptrContent.on('ptr:refresh', function(e) {
        mainView.router.refreshPage();
        app.ptr.done();
    })


    $$('.card').on('click', function() {
        mainView.router.navigate({
                name: 'wo_detail',
                params: { wo_id: $$(this).data('wo_id')}},
                {
                    ignoreCache: true,
                    force: true
                });

    });

});

$$(document).on('page:init', '.page[data-name="wo_detail_page"]', function(e) {

    $$('.fab_response').on('click', function() {

        form_values = new Object();
        form_values['wo_id'] = $$(this).data('wo_id');
        form_values['response'] = $$(this).data('response');

        app.dialog.confirm('Are you sure, you want to ACCEPT this Work Order  ?',
                           function() {
                                app.request.postJSON('/mobile/wo/response', form_values, function(data) {
                                    mainView.router.refreshPage();
                           })
        })
    });

    $$('.fab_add_picture').on('click', function() {

        mainView.router.navigate({
                name: 'wo_picture',
                params: {
                            wo_id: $$(this).data('wo_id'),
                            state_to: $$(this).data('state_to')
                        }
                },
                {
                    ignoreCache: true,
                    force: true
                });
    });
});

$$(document).on('page:init', '.page[data-name="wo_picture_page"]', function(e) {

    $$('#btn_camera').on('click', function(e) {
        e.preventDefault();

        if (!navigator.camera) {
            alert('Camera not supported');
            return;
        }

        var options = {
            quality: 70,
            destinationType: Camera.DestinationType.DATA_URL,
            sourceType: Camera.PictureSourceType.CAMERA,
            mediaType: Camera.MediaType.PICTURE,
            encodingType: Camera.EncodingType.JPEG,
            cameraDirection: Camera.Direction.BACK,
            targetWidth: 800,
        }
        //    alert("tesss");
        navigator.camera.getPicture(function(imageURI) {
            var image = document.getElementById('photo');
            var textPicture = document.getElementById('textPicture');
            image.src = "data:image/jpeg;base64," + imageURI;
            textPicture.value = imageURI;
        }, function(message) {
            alert('failed : ' + message);
        }, options);



    })
    $$('#btn_camera').click();

    $$('#btn_submit_report').on('click', function(e) {
        e.preventDefault();

        app.dialog.confirm('Are you sure to submit this Report ?',
                           function() {

                                form_values = new Object();
                                form_values['wo_id'] = $$('#wo_id').val();
                                form_values['state_to'] = $$('#state_to').val();
                                form_values['image'] = $$('#textPicture').val();
                                form_values['remark'] = $$('#txt_remark').val();

                                app.request.postJSON('/mobile/wo/picture/submit', form_values, function(data) {
                                    mainView.router.navigate({
                                            name: 'wo_detail',
                                            params: { wo_id: $$('#wo_id').val()}},
                                            {
                                                ignoreCache: true,
                                                force: true
                                            });
                           })
        })
    })

});

