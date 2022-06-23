// Get the modal
var modal = document.getElementById("myModal");

// Get the button that opens the modal
var btn = document.getElementById("myBtn");

// Get the <span> element that closes the modal
var span = document.getElementsByClassName("close")[0];

// When the user clicks on the button, open the modal
$('.mimic-tag').click(function() {
    modal.style.display = "block";
    var logger_id = $(this).data('logger_id');
    var channel_id = $(this).data('channel_id');
    $('#container-chart').hide();
    $.get('/mimic/chart/' + logger_id + '/' + channel_id, function(results) {
        var result = JSON.parse(results);
        var logger_url = '/web#action=' + result.action_id +'&active_id=' + result.logger.id + '&cids=1&menu_id=' + result.menu_id;

        Highcharts.chart('container-chart', {
            chart: {
                zoomType : 'x'
            },
            title: {
                text: result.channel.name
            },
            yAxis: {
                title: {
                    text: result.channel.value_unit
                }
            },
            xAxis: {
                type: 'datetime',
                dateTimeLabelFormats: { // don't display the dummy year
                    day: '%Y<br/>%m-%d',
                    month: '%e. %b',
                    year: '%b'
                },
            },
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
            series: [{
                name: result.series_data.name,
                type: 'spline',
                data: result.series_data.data
            }],
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
        });
        $('.title').html(result.logger.name);
        $('.logger-link').attr('href', logger_url);

    }).done(function() {
        $('#container-chart').show();
    });

});

$('.close').click(function() {
  modal.style.display = "none";
})

btn.onclick = function() {
    modal.style.display = "block";

}

// When the user clicks on <span> (x), close the modal
span.onclick = function() {
  modal.style.display = "none";
}

// When the user clicks anywhere outside of the modal, close it
window.onclick = function(event) {
  if (event.target == modal) {
    modal.style.display = "none";
  }
}

setTimeout(function() {
    location.reload();

}, 300000);



