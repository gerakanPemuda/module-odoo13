var app = new Framework7({
  // App root element
  root: '#app',
  // App Name
  name: 'WTCLite',
  // App id
  id: 'id.wtclite.wtccloud',
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
        path: '/index/',
        url: '/wtclite/index',
        options: {
            clearPreviousHistory: true,
            pushState: true
        }
    },
    {
        name: 'logger_form',
        path: '/logger/form',
        url: '/wtclite/logger/form/',
        options: {
            clearPreviousHistory: false,
            pushState: true,
            animate: true,
            transition: 'f7-parallax'
        }
    },
    {
        name: 'logger_detail',
        path: '/logger/detail/:logger_id',
        url: '/wtclite/logger/detail/{{logger_id}}/',
        options: {
            animate: true,
            transition: 'f7-parallax'
        }
    },
    {
        name: 'logger_consumption',
        path: '/logger/consumption/:logger_id/:channel_id',
        url: '/wtclite/logger/consumption/{{logger_id}}/{{channel_id}}/',
        options: {
            animate: true,
            transition: 'f7-parallax'
        }
    },
    {
        name: 'logger_threshold',
        path: '/logger/threshold/:logger_id/:channel_id',
        url: '/wtclite/logger/threshold/{{logger_id}}/{{channel_id}}/',
        options: {
            animate: true,
            transition: 'f7-parallax'
        }
    },
    {
        name: 'logger_channel_form',
        path: '/logger/channel/form/:channel_id',
        url: '/wtclite/logger/channel/form/{{channel_id}}/',
        options: {
            animate: true,
            transition: 'f7-parallax'
        }
    },
  ],
  // ... other parameters
});

var $$ = Dom7;

var mainView = app.views.create('.view-main');

function parseInteger(value) {
    var parsed = parseInt(value);
    // do not accept not numbers or float values
    if (isNaN(parsed) || parsed % 1 || parsed < -2147483648 || parsed > 2147483647) {
        alert('Time is not Valid');
    }
    return parsed;
}

function parseFloatTime(value) {
    var factor = 1;
    if (value[0] === '-') {
        value = value.slice(1);
        factor = -1;
    }
    var float_time_pair = value.split(":");
    if (float_time_pair.length !== 2)
        return factor * parseFloat(value);
    var hours = parseInteger(float_time_pair[0]);
    var minutes = parseInteger(float_time_pair[1]);
    return factor * (hours + (minutes / 60));
}

var $ptrContent = $$('.ptr-content');

$ptrContent.on('ptr:refresh', function(e) {
    mainView.router.refreshPage();

    app.ptr.done();
})

var searchbar = app.searchbar.create({
  el: '.searchbar',
  searchContainer: '.list',
  searchIn: '.card_project',
  on: {
    search(sb, query, previousQuery) {
      console.log(query, previousQuery);
    }
  }
});

var state_battery = '';
var state_battery_value = '';
var state_signal = '';
var state_signal_value = '';
var state_temperature = '';
var state_temperature_value = '';

$$(document).on('page:init', '.page[data-name="index"]', function(e) {
    $$('#icon-add-logger').on('click', function(e) {
        mainView.router.navigate({
                name: 'logger_form'},
                {
                    ignoreCache: true,
                    force: true
                });
    });
});



$$(document).on('page:init', '.page[data-name="logger_info_page"]', function(e) {

});

$$(document).on('page:init', '.page[data-name="logger_form_page"]', function(e) {

    $$('.convert-form-to-data').on('click', function () {
        var form_values = app.form.convertToData('#logger-form');

        app.request.postJSON('./logger/create', form_values, function(data) {
            console.log(data);
            result = data['result'];
            mainView.router.navigate({
                name: 'logger_detail',
                params: { logger_id: result.logger_id}},
                {
                    ignoreCache: true,
                    force: true
                });

        })
    });
});


$$(document).on('page:init', '.page[data-name="logger_detail_page"]', function(e) {
    var $ptrContent = $$('.ptr-content-logger');

    $ptrContent.on('ptr:refresh', function(e) {
        app.request.postJSON('/wtclite/logger/refresh', form_values, function(data) {
            mainView.router.refreshPage();
            app.ptr.done();
        });
    })

    form_values = new Object();
    form_values['logger_id'] = $$('#logger_id').val();

    $$('#link-refresh').on('click', function() {
        refresh();
    })

    function refresh() {
        alert('tess');
    }

    // Confirm
    $$('#icon-disable').on('click', function () {
        app.dialog.confirm('Are you sure you want to disable this logger ?', function () {
            app.request.postJSON('./logger/disable', form_values, function(data) {
                mainView.router.navigate({
                    name: 'index'},
                    {
                        ignoreCache: true,
                        force: true
                    });
            })


        });
    });

    $$('.channel-form-link').on('click', function() {
        var channel_id = $$(this).data('id');
        mainView.router.navigate({
                name: 'logger_channel_form',
                params: { channel_id: channel_id}},
                {
                    ignoreCache: true,
                    force: true
                });

    });


    var chart_image_url = false;

    app.request.postJSON('/wtclite/logger/chart', form_values, function(data) {
//        console.log(data);
        data = data['result'];
        var yAxis = data['logger']['yAxis'];
        var series = data['logger']['series'];
        state_battery = data['logger']['state_battery']['src'];
        state_battery_value = data['logger']['state_battery']['last_value'];
        state_signal = data['logger']['state_signal']['src'];
        state_signal_value = data['logger']['state_signal']['last_value'];
        state_temperature = data['logger']['state_temperature']['src'];
        state_temperature_value = data['logger']['state_temperature']['last_value'];

        console.log(series);

        var chart_options = {
            chart: {
                zoomType : 'x'
            },

            title: {
                text: ''
            },

            subtitle: {
                text: ''
            },

            xAxis: {
                type: 'datetime',
                dateTimeLabelFormats: { // don't display the dummy year
                    day: '%Y<br/>%m-%d',
                    month: '%e. %b',
                    year: '%b'
                },
            },

            yAxis: yAxis,

            tooltip: {
                crosshairs : {
                    width : 1,
                    color : '#C0C0C0'
                 },
                shared: true
            },
            legend: {
                enabled: true
            },

            plotOptions: {
                series: {
                    marker: {
                        enabled: false,
                        states: {
                            hover: {
                                enabled: true,
                                radius: 7
                            }
                        }
                    },
                    events: {
                        legendItemClick: function(event) {
                        }
                    }
                }
            },

            series: series,

            responsive: {
                rules: [{
                    condition: {
                        maxWidth: 500
                    },
                    chartOptions: {
                        legend: {
                            layout: 'horizontal',
                            align: 'center',
                            verticalAlign: 'bottom'
                        }
                    }
                }]
            },

            exporting: {
                sourceWidth: 800,
           }
        }

        var data = {
            options: JSON.stringify(chart_options),
            filename: 'test.png',
            type: 'image/png',
            async: true
        };

        var exportUrl = 'https://export.highcharts.com/';
        app.request.post(exportUrl, data, function(data) {
            var imageUrl = exportUrl + data;
            var urlCreator = window.URL || window.webkitURL;
            chart_image_url = imageUrl;
        });


        Highcharts.chart('chart-container', chart_options);


    });

    Highcharts.chart('chart-container', {

        title: {
            text: 'Solar Employment Growth by Sector, 2010-2016'
        },

        subtitle: {
            text: 'Source: thesolarfoundation.com'
        },

        yAxis: {
            title: {
                text: 'Number of Employees'
            }
        },

        xAxis: {
            accessibility: {
                rangeDescription: 'Range: 2010 to 2017'
            }
        },

        legend: {
            layout: 'vertical',
            align: 'right',
            verticalAlign: 'middle'
        },

        plotOptions: {
            series: {
                label: {
                    connectorAllowed: false
                },
                pointStart: 2010
            }
        },

        series: [],

        responsive: {
            rules: [{
                condition: {
                    maxWidth: 500
                },
                chartOptions: {
                    legend: {
                        layout: 'horizontal',
                        align: 'center',
                        verticalAlign: 'bottom'
                    }
                }
            }]
        }

    });

    $$('#icon-download').on('click', function(){

        app.preloader.show();
        form_values = new Object();
        form_values['logger_id'] = $$('#logger_id').val();
        form_values['channel_id'] = false;
        form_values['image_url'] = chart_image_url;
        form_values['state_battery'] = state_battery;
        form_values['state_battery_value'] = state_battery_value;
        form_values['state_signal'] = state_signal;
        form_values['state_signal_value'] = state_signal_value;
        form_values['state_temperature'] = state_temperature;
        form_values['state_temperature_value'] = state_temperature_value;
        form_values['is_flow'] = false;
        form_values['show_data'] = true;
        form_values['interval'] = 'default';

        downloader.init({folder: 'Downloads'});
        app.request.postJSON('./logger/report', form_values, function(data) {
            console.log(data);
            app.preloader.hide();
            var result = data['result'];
//            downloader.get('http://192.168.0.23:8069/web/content/397');
            var url = '/web/content/' + result['report_id'];
//            alert(result['report_id']);
            cordova.InAppBrowser.open(url, '_system', 'location=no');
//            downloader.get(url);

        })

    });

});

$$(document).on('page:init', '.page[data-name="logger_channel_form_page"]', function(e) {

    $$('.submit-channel-data').on('click', function () {
        var form_values = app.form.convertToData('#logger-channel-form');

        app.request.postJSON('./logger/channel/update', form_values, function(data) {
            console.log(data);
            result = data['result'];
            mainView.router.back();
            var notificationFull = app.notification.create({
                    title: 'WTCLite',
                    titleRightText: 'now',
                    subtitle: 'Channel Update',
                    text: 'Data has been updated',
                    closeTimeout: 3000,
                  });
            notificationFull.open();
        })
    });


//    var form_values = new Object();
//    form_values['channel_id'] = $$('#channel_id').val();
//
//    app.request.postJSON('./logger/channel/form/get_data', form_values, function(data) {
//        console.log(data);
//        var formData = data['result']['channel'];
//        app.form.fillFromData('#logger-channel-form', formData);
//    })


});


function get_consumption_chart(interval) {
    form_values = new Object();
    form_values['logger_id'] = $$('#logger_id').val();
    form_values['channel_id'] = $$('#channel_id').val();
    form_values['interval'] = interval;

    app.preloader.show();
    $$('#act-download').hide();
    $$('#interval').val(interval);

    app.request.postJSON('/wtclite/logger/consumption/chart', form_values, function(data) {
        data = data['result'];
        var title = '';
        var yAxis = data['logger']['yAxis'];
        var series = data['logger']['series'];
        $$('#report_period').val(data['logger']['report_period']);

        console.log(series);

        var consumption_chart_options = {
            chart: {
                zoomType : 'x'
            },
            title: {
                text: title
            },
            xAxis: {
                type: 'datetime',
                dateTimeLabelFormats: { // don't display the dummy year
                    day: '%Y<br/>%m-%d',
                    month: '%e. %b',
                    year: '%b'
                },
            },
            yAxis: yAxis,
            tooltip: {
                crosshairs : {
                    width : 1,
                    color : '#C0C0C0'
                 },
                shared: true
            },
            plotOptions: {
                column: {
                    pointPadding: 0.2,
                    borderWidth: 0
                }
            },
            series: series
        }

        var data = {
            options: JSON.stringify(consumption_chart_options),
            filename: 'test.png',
            type: 'image/png',
            async: true
        };

        var exportUrl = 'https://export.highcharts.com/';
        app.request.post(exportUrl, data, function(data) {
            var imageUrl = exportUrl + data;
            var urlCreator = window.URL || window.webkitURL;
            chart_image_url = imageUrl;
            $$('#chart_image_url').val(chart_image_url);
            $$('#act-download').show();
        })

        var consumption_chart = Highcharts.chart('consumption-chart-container', consumption_chart_options);
        app.preloader.hide();
//        $$('#act-download').show();
    });

}

$$(document).on('page:init', '.page[data-name="logger_consumption_page"]', function(e) {
    get_consumption_chart('default');
    var chart_image_url = '';

    $$('.btn_consumption_intervals').on('click', function(e) {
        var interval = $$(e.target).data("interval");

        $$('.btn_consumption_intervals').removeClass('color-green');
        $$('#button-consumption-' + interval).addClass('color-green');
        chart_image_url = get_consumption_chart(interval);
    });
    $$('#act-download').on('click', function(e) {
        app.preloader.show();
        form_values = new Object();
        form_values['report_period'] = $$('#report_period').val();
        form_values['logger_id'] = $$('#logger_id').val();
        form_values['channel_id'] = $$('#channel_id').val();
        form_values['image_url'] = $$('#chart_image_url').val();
        form_values['state_battery'] = state_battery;
        form_values['state_battery_value'] = state_battery_value;
        form_values['state_signal'] = state_signal;
        form_values['state_signal_value'] = state_signal_value;
        form_values['state_temperature'] = state_temperature;
        form_values['state_temperature_value'] = state_temperature_value;
        form_values['is_flow'] = true;
        form_values['show_data'] = true;
        form_values['interval'] = $$('#interval').val();

        app.request.postJSON('./logger/report', form_values, function(data) {
            console.log(data);
            app.preloader.hide();
            var result = data['result'];
//            downloader.get('http://192.168.0.23:8069/web/content/397');
            var url = '/web/content/' + result['report_id'];
//            alert(result['report_id']);
            cordova.InAppBrowser.open(url, '_system', 'location=no');
//            downloader.get(url);

        })

    });

});

$$(document).on('page:init', '.page[data-name="logger_threshold_page"]', function(e) {

    $$('#btn-submit-threshold').on('click', function(e) {
        form_values = new Object();
        var overrange_enabled = false;
        if ($$('#overrange_enabled').is(':checked')) {
            overrange_enabled = true;
        }
        var hi_hi_enabled = false;
        if ($$('#hi_hi_enabled').is(':checked')) {
            hi_hi_enabled = true;
        }
        var hi_enabled = false;
        if ($$('#hi_enabled').is(':checked')) {
            hi_enabled = true;
        }
        var lo_enabled = false;
        if ($$('#lo_enabled').is(':checked')) {
            lo_enabled = true;
        }
        var lo_lo_enabled = false;
        if ($$('#lo_lo_enabled').is(':checked')) {
            lo_lo_enabled = true;
        }
        var underrange_enabled = false;
        if ($$('#underrange_enabled').is(':checked')) {
            underrange_enabled = true;
        }
        
        form_values['logger_channel_id'] = $$('#logger_channel_id').val();
        form_values['overrange_enabled'] = overrange_enabled;
        form_values['overrange_threshold'] = $$('#overrange_threshold').val();
        form_values['hi_hi_enabled'] = hi_hi_enabled;
        form_values['hi_hi_threshold'] = $$('#hi_hi_threshold').val();
        form_values['hi_enabled'] = hi_enabled;
        form_values['hi_threshold'] = $$('#hi_threshold').val();
        form_values['lo_enabled'] = lo_enabled;
        form_values['lo_threshold'] = $$('#lo_threshold').val();
        form_values['lo_lo_enabled'] = lo_lo_enabled;
        form_values['lo_lo_threshold'] = $$('#lo_lo_threshold').val();
        form_values['underrange_enabled'] = underrange_enabled;
        form_values['underrange_threshold'] = $$('#underrange_threshold').val();

        // Create toast
        if (!toastCenter) {
        var toastCenter = app.toast.create({
          text: 'Threshold Setup Successful',
          closeTimeout: 2000,
        });
        }

        app.request.postJSON('./logger/threshold/update', form_values, function(data) {
            console.log(data);
            toastCenter.open();
//            mainView.router.navigate({
//                        url: '/mobile/journal/hourly/list/' + journal_id + '/tab-unit-report/'
//                    },
//                    {
//                        ignoreCache: true,
//                        force: true,
//                        reloadCurrent: true,
//                    });
        })


    });

});

$$(document).on('click', '.link-logout', function() {

    data = {}
    app.request.getJSON('./logout', data, function(data) {
        console.log(data);
        window.location.href = "/wtclite/index";
    })

})

