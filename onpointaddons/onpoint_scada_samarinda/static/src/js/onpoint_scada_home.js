$(document).ready(function() {
    get_data();
});


function get_data() {
    form_values = new Object();
    form_values['timeframe'] = 1;

    $.ajax({
        url: '/home/get_data',
        type: 'post',
        dataType: 'json',
        contentType : 'application/json',
        type : 'POST',
        data: JSON.stringify(form_values),
        }).done(function(results) {
            var data = results['result'];
            var val = data.val;
            $('#info-1').html(val);
        });

}

$(function() {
    setInterval(get_data, 30000);
});
