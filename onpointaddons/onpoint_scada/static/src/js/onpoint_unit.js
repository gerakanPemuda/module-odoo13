window.location.href = '/web#action=' + $('#unit_action_id').val() + '&active_id=' + $('#unit_id').val() + '&cids=1&menu_id=140';

//var picker = new Lightpick({
//    field: document.getElementById('rangeDate'),
//    singleDate: false
//});
//set_range();
//$('#rangeDate').hide();
//
//$('#select_period').on('change', function() {
//    if ($("#select_period").val() == 'custom') {
//        $('#rangeDate').show();
//    }
//    else {
//        set_range();
//        $('#rangeDate').hide();
//    }
//})
//
//get_data();
//
//$('#btn_refresh').on('click', function() {
//    get_data();
//});
//
//$('.btn-unit').on('click', function() {
//    window.location.href = '/unit/' + $(this).data('unit-id');
//})
//
//$('#auto_refresh').on('click', function() {
//    $.post('/unit/toggle_auto_refresh',
//        {
//            'unit_id': $('#unit_id').val(),
//        }).done(function(results) {
//
//        })
//})
//
//refresh_interval = setInterval(function() {auto_refresh();}, 300000);
//
//function auto_refresh() {
//    var auto_refresh_enabled = $('#auto_refresh').is(':checked');
//    if (auto_refresh_enabled == true)
//    {
//        $('#btn_refresh').click();
//    }
//}
//
//
//function set_range() {
//
//    var today = new Date();
//    var previous = new Date();
//    var interval_days = 1;
//
//    var selected_period_val = $("#select_period").val();
//    switch(selected_period_val) {
//        case '1d':
//            interval_days = 1;
//            break;
//        case '3d':
//            interval_days = 3;
//            break;
//        case '1w':
//            interval_days = 7;
//            break;
//        case '2w':
//            interval_days = 14;
//            break;
//        case '1m':
//            interval_days = 30;
//            break;
//        case '2m':
//            interval_days = 60;
//            break;
//    }
//    previous.setDate(today.getDate() - interval_days);
//    var start_date = previous.getDate() + '/' + (previous.getMonth()+1) + "/" + previous.getFullYear();
//    var end_date = today.getDate() + '/' + (today.getMonth()+1) + "/" + today.getFullYear();
//    var rangeDate = start_date + ' - ' + end_date;
//    var option = self.selected_option;
//    var period = self.selected_period;
//
//    if (rangeDate == "") {
//        picker.setDateRange(moment().add(-7, 'day'), new Date());
//    }
//    else {
//        $("#rangeDate").val(rangeDate);
//    }
//
//}
//
//const blob2base64 = (blob) => new Promise((resolve, reject) => {
//    const reader = new FileReader();
//    reader.onerror = reject;
//    reader.onload = () => resolve(reader.result);
//    reader.readAsDataURL(blob);
//});
//
//var chart_options = '';
//
//document.getElementById('btn_generate_image').addEventListener('click', async () => {
//
//    // Prepare POST data
//    const body = new FormData();
//    body.append('infile', document.getElementById('infile').value);
//    body.append('width', 400);
//
//    // Post it to the export server
//    const blob = await fetch('https://export.highcharts.com/', {
//        body,
//        method: 'post'
//    }).then(result => result.blob());
//
//    // Create the image
//    const img = new Image();
//    img.src = await blob2base64(blob);
//    document.getElementById('img_chart').setAttribute('src', img.src);
//    $('#img_chart_text').text(img.src);
//});
//
//function get_data() {
//
//    $.post('/unit/get_data_detail',
//        {
//            'unit_id': $('#unit_id').val(),
//            'select_hour': $('#select_hour').val(),
//            'rangeDate': $('#rangeDate').val(),
//            'interval': $('#select_interval').val()
//        }).done(function(results) {
//        var y_axis = results['results'].y_axis;
//        var series = results['results'].series;
//        var stats = results['results'].stats;
//
//        chart_options = {
//            chart: {
//                zoomType: 'x'
//            },
//            title: {
//                text: ''
//            },
//            subtitle: {
//                text: ''
//            },
//            xAxis: {
//                type: 'datetime',
//                dateTimeLabelFormats: { // don't display the dummy year
//                    day: '%Y<br/>%m-%d',
//                    month: '%e. %b',
//                    year: '%b'
//                },
//            },
//            yAxis: y_axis,
//            tooltip: {
//                crosshairs : {
//                    width : 1,
//                    color : '#C0C0C0'
//                 },
//                shared: true
//            },
//            legend: {
//                enabled: true
//            },
//
//            plotOptions: {
//                series: {
//                    marker: {
//                        enabled: false,
//                        states: {
//                            hover: {
//                                enabled: true,
//                                radius: 7
//                            }
//                        }
//                    },
//                    events: {
//                        legendItemClick: function(event) {
//                        }
//                    },
//                    responsive: {
//                        rules: [{
//                            condition: {
//                                maxWidth: 500
//                            },
//                            chartOptions: {
//                                legend: {
//                                    layout: 'horizontal',
//                                    align: 'center',
//                                    verticalAlign: 'bottom'
//                                }
//                            }
//                        }]
//                    },
//
//                    exporting: {
//                        sourceWidth: 800,
//                   }
//
//                }
//            },
//            series: series
//        };
//
//        Highcharts.chart('container_unit_chart', chart_options);
//
//        var data = {
//            options: JSON.stringify(chart_options),
//            filename: 'test.png',
//            type: 'image/png',
//            async: true
//        };
//
//        $('#infile').text(JSON.stringify(chart_options));
//        $('#btn_generate_image').click();
//
////        var chart_image_url = '';
////        var exportUrl = 'https://export.highcharts.com/';
////        $.post(exportUrl, data, function(data) {
////            var imageUrl = exportUrl + data;
////            var urlCreator = window.URL || window.webkitURL;
////            chart_image_url = imageUrl;
////            alert(chart_image_url);
////        });
//
//
//        var idx = 0;
//        for (idx = 0; idx < stats.length; idx++) {
//            $('#last_value_' + stats[idx].unit_line_id).html(stats[idx].last_value);
//            $('#last_date_' + stats[idx].unit_line_id).html(stats[idx].last_date);
//            $('#min_value_' + stats[idx].unit_line_id).html(stats[idx].min_value);
//            $('#min_date_' + stats[idx].unit_line_id).html(stats[idx].min_date);
//            $('#max_value_' + stats[idx].unit_line_id).html(stats[idx].max_value);
//            $('#max_date_' + stats[idx].unit_line_id).html(stats[idx].max_date);
//            $('#avg_value_' + stats[idx].unit_line_id).html(stats[idx].avg_value);
//        }
//
//    });
//
//}
//
//$('#btn_print').on('click', function() {
//
//    $.post('/unit/print',
//        {
//            'unit_id': $('#unit_id').val(),
//            'img_chart': $('#img_chart_text').text(),
//        }).done(function(results) {
//            x = 1;
//        });
//
//})
