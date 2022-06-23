odoo.define('onpoint_monitor.logger_chart', function (require) {
    "use strict";
    
    var ActionMixin = require('web.ActionMixin');
    var core = require('web.core');
    var session = require('web.session');
    var ajax = require('web.ajax');
    var rpc = require('web.rpc');
    var ActionManager = require('web.ActionManager');
    var view_registry = require('web.view_registry');
    var web_client = require('web.web_client');
    var Widget = require('web.Widget');
    
    var QWeb = core.qweb;
    
    var _t = core._t;
    var _lt = core._lt;
    var map;
    var refresh_interval = null;
    
    var OnpointLoggerChart = Widget.extend(ActionMixin, {
        hasControlPanel: true,
        template: "LoggerChartMain",
        events: {
            'click #btn_config': 'act_logger',
            'click #btn_report': 'act_view_logger_value',
            'change #select_period': 'change_period',
            'click #btn_refresh': 'act_refresh_chart',
            'click #btn_act_view_data_channels': 'act_view_data_channels',
            'click #card_power': 'act_view_power',
            'click #card_signal': 'act_view_signal',
            'click #card_temperature': 'act_view_temperature',
            'click .div_flow_channel': 'act_view_consumption',
            'click .btn_consumption_intervals': 'act_view_consumption',
            'click #back_to_logger': 'act_view_logger_chart',
            'click #btn_print': 'act_print',
            'click #auto_refresh': 'act_toggle_auto_refresh'
        },
        init: function(parent, context) {
            this._super(parent, context);
            this.action_id = context.id;
            this.logger_id = context.context['logger_id'];
            this.logger = false;
            this.flow_channels = false;
            this.selected_option = '1d';
            this.selected_hour = '00';
            this.selected_period = 'hour';
            this.rangeDate;
            this.map;
            this.chart;
            this.chart_options;
            this.chart_image_url;
            this.power_chart;
            this.power_chart_options;
            this.is_flow = false;
            this.channel_id = 0;
            this.consumption_chart;
            this.consumption_chart_options;
            this.auto_refresh = false;
            this._super(parent,context);
    
        },
        start: function() {
            var self = this;
            for(var i in self.breadcrumbs){
                self.breadcrumbs[i].title = "Chart";
            }
            self.updateControlPanel({breadcrumbs: self.breadcrumbs}, {clear: true});
            // $(".o_control_panel").html("Tesss");
            $(".o_control_panel").removeClass("o_hidden");

            self.selected_option = $('#select_period').val();
            if (typeof $('#select_hour').val() !== 'undefined') {
                self.selected_hour = $('#select_hour').val();
            }
            else {
                self.selected_hour = '00';
            }
            var today = new Date();
            var previous = new Date();
            previous.setDate(today.getDate() - 3);
            var start_date = previous.getDate() + '/' + (previous.getMonth()+1) + "/" + previous.getFullYear();
            var end_date = today.getDate() + '/' + (today.getMonth()+1) + "/" + today.getFullYear();
            var rangeDate = start_date + ' - ' + end_date;
            var option = self.selected_option;
            var option_hour = self.selected_hour;
            var period = self.selected_period;

            self.get_logger_data(rangeDate, option, period, option_hour);
            refresh_interval = setInterval(function() {self.act_auto_refresh_chart();}, 300000);
        },
        get_logger_data: function(rangeDate, option, period, option_hour) {

            var self = this;

            rpc.query({
                model: 'onpoint.logger',
                method: 'get_data',
                args: [self.logger_id, rangeDate, option, period, option_hour]
            })
            .then(function(result){
                self.logger =  result;

                if(result){
                    $('.o_hr_chart').html(QWeb.render('LoggerChartContent', {widget: self}));

                    var picker = new Lightpick({
                        field: document.getElementById('rangeDate'),
                        singleDate: false
                    });
//                    if (rangeDate == "") {
//                        picker.setDateRange(moment().add(-7, 'day'), new Date());
//                    }
//                    else {
                    $("#rangeDate").val(rangeDate);
//                    }

                    $('#auto_refresh').prop('checked', self.logger.auto_refresh);

                    $('#select_period').val(self.logger.option);
                    $('#select_hour').val(self.logger.option_hour);
                    $('div.div_option select').val(self.logger.selected_option);
                    $('div.div_period select').val(self.logger.selected_period);

                    self.change_period();

                    self.preview_logger_chart();
                    self.preview_stats();

					var today = new Date();
					var currentDate = ("0" + today.getDate()).slice(-2);
					var currentMonth = ("0" + (today.getMonth()+1)).slice(-2);
					var currentYear = today.getFullYear();
					var currentHours = ("0" + today.getHours()).slice(-2);
					var currentMinutes = ("0" + today.getMinutes()).slice(-2);
					var currentSeconds = ("0" + today.getSeconds()).slice(-2);

					var time = currentDate + "/" + currentMonth + "/" + currentYear + " " +  currentHours + ":" + currentMinutes + ":" + currentSeconds;
					$('#last_update').html(time);
                    $('#div_consumption').hide();
                    self.get_flow_channels();
                }
                else{
                    $('.o_hr_chart').html(QWeb.render('LoggerChartWarning', {widget: self}));
                    return;
                }
            });

        },
        get_flow_channels: function() {
            var self = this;

            rpc.query({
                model: 'onpoint.logger',
                method: 'get_flow_channels',
                args: [self.logger_id]
            })
            .then(function(result){
                self.flow_channels =  result;

                if(result){
                    if(self.flow_channels != "") {
                        $('#label-consumption').show();
                    }
                    else {
                        $('#label-consumption').hide();
                    }
                    $('#div_flow_channels').html(QWeb.render('LoggerFlowChannels', {widget: self}));
                }
            });
        },
        preview_logger_chart: function() {
            var self = this

            self.chart_options = {
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

                yAxis: self.logger['yAxis'],

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


                series: self.logger['series'],

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
                options: JSON.stringify(self.chart_options),
                filename: 'test.png',
                type: 'image/png',
                async: true
            };

            $('#infile').text(JSON.stringify(self.chart_options));

            self.async_chart();
//            var exportUrl = 'https://export.highcharts.com/';
//            $.post(exportUrl, data, function(data) {
//                var imageUrl = exportUrl + data;
//                var urlCreator = window.URL || window.webkitURL;
//                self.chart_image_url = imageUrl;
//            });


            self.chart = Highcharts.chart('container_logger_chart', self.chart_options);
        },
        async_chart: async function() {
            const blob2base64 = (blob) => new Promise((resolve, reject) => {
                const reader = new FileReader();
                reader.onerror = reject;
                reader.onload = () => resolve(reader.result);
                reader.readAsDataURL(blob);
            });

            // Prepare POST data
            const body = new FormData();
            body.append('infile', $('#infile').val());
            body.append('width', 800);

            // Post it to the export server
            const blob = await fetch('https://export.highcharts.com/', {
                body,
                method: 'post'
            }).then(result => result.blob());

            // Create the image
            const img = new Image();
            img.src = await blob2base64(blob);
            $('#img_chart_text').text(img.src);
//            document.getElementById('img_chart').setAttribute('src', img.src);
//            $('#img_chart_text').text(img.src);

        },
        preview_stats: function() {
            var self = this

        },
        act_logger: function(e) {
            var self = this;
            e.stopPropagation();
            e.preventDefault();
            var options = {
                on_reverse_breadcrumb: this.on_reverse_breadcrumb,
            };
            this.do_action({
                name: _t("Logger"),
                type: 'ir.actions.act_window',
                res_model: 'onpoint.logger',
                view_mode: 'form',
                view_type: 'form',
                views: [[false, 'form']],
                context: {},
                res_id: this.logger_id,
                target: 'main'
            }, options);
   
        },  
        change_period: function() {
            var self = this;
            var today = new Date();
            var previous = new Date();
            var interval_days = 1;

            if ($("#select_period").val() == 'custom') {
                $('#rangeDate').show();
            }
            else {
                var selected_period_val = $("#select_period").val();
                switch(selected_period_val) {
                    case '1d':
                        interval_days = 1;
                        break;
                    case '3d':
                        interval_days = 3;
                        break;
                    case '1w':
                        interval_days = 7;
                        break;
                    case '2w':
                        interval_days = 14;
                        break;
                    case '1m':
                        interval_days = 30;
                        break;
                    case '2m':
                        interval_days = 60;
                        break;
                }
                previous.setDate(today.getDate() - interval_days);
                var start_date = previous.getDate() + '/' + (previous.getMonth()+1) + "/" + previous.getFullYear();
                var end_date = today.getDate() + '/' + (today.getMonth()+1) + "/" + today.getFullYear();
                var rangeDate = start_date + ' - ' + end_date;
                var option = self.selected_option;
                var period = self.selected_period;

                var picker = new Lightpick({
                    field: document.getElementById('rangeDate'),
                    singleDate: false
                });
                if (rangeDate == "") {
                    picker.setDateRange(moment().add(-7, 'day'), new Date());
                }
                else {
                    $("#rangeDate").val(rangeDate);
                }
                $('#rangeDate').hide();
            }
        },   
        act_refresh_chart: function() {
            var self = this;
            self.get_logger_data($("#rangeDate").val(), $("#select_period").val(), $("#period").val(), $('#select_hour').val());
        },
        act_view_logger_value: function(e) {
            var self = this;
            e.stopPropagation();
            e.preventDefault();
            var options = {
                on_reverse_breadcrumb: this.on_reverse_breadcrumb,
            };

//            this.do_action({
//                name: _t("Logger"),
//                type: 'ir.actions.act_window',
//                res_model: 'onpoint.logger.value',
//                views: [[false, 'list']],
//                context: {},
//                domain: [['channel_id', 'in', channel_ids],
//                         ['dates', '>=', self.logger['period_start']],
//                         ['dates', '<=', self.logger['period_end']],
//                         ['value_type', '=', 'trending']],
//                target: 'main'
//            });

            this.do_action({
                name: _t("Logger"),
                type: 'ir.actions.act_window',
                res_model: 'onpoint.logger.value',
                view_mode: 'form',
                view_type: 'form',
                views: [[false, 'list']],
                context: {
                    'group_by': 'channel_id'
                },
                domain: [['logger_id', '=', self.logger_id],
                         ['dates', '>=', self.logger['period_start']],
                         ['dates', '<=', self.logger['period_end']]],
                target: 'main'
            }, options);

        },
        act_view_data_channels: function(e) {
            var self = this;
            e.stopPropagation();
            e.preventDefault();
            var options = {
                on_reverse_breadcrumb: this.on_reverse_breadcrumb,
            };

            var idx = 0;
            var channel_ids = [];
            for(idx = 0; idx < self.logger['events'].length; idx++) {
                channel_ids.push(self.logger['events'][idx].channel_id);
            }

            this.do_action({
                name: _t("Logger"),
                type: 'ir.actions.act_window',
                res_model: 'onpoint.logger.value',
                views: [[false, 'list']],
                context: {},
                domain: [['channel_id', 'in', channel_ids],
                         ['dates', '>=', self.logger['period_start']],
                         ['dates', '<=', self.logger['period_end']],
                         ['value_type', '=', 'trending']],
                target: 'main'
            });


        },
        act_logger_value_report: function(e) {
            var self = this;
            e.stopPropagation();
            e.preventDefault();
            var options = {
                on_reverse_breadcrumb: this.on_reverse_breadcrumb,
            };

            this.do_action({
                name: _t("Logger"),
                type: 'ir.actions.act_window',
                res_model: 'onpoint.logger.value.report',
                view_mode: 'form',
                view_type: 'form',
                views: [[false, 'form']],
                context: {
                    default_logger_id: this.logger_id,
                },
                target: 'main'
            }, options);
        },
        act_view_logger_chart: function(e) {
            e.stopPropagation();
            e.preventDefault();

            var self = this;
            self.is_flow = false;
            self.channel_id = false;

            self.act_refresh_chart();

            $('#back_to_logger').hide();
            $('#div_consumption').hide();
            $('#div_alarm').hide();
            $('#div_logger').show();

        },
        act_view_power: function(e) {
            var self = this;

            rpc.query({
                model: 'onpoint.logger',
                method: 'get_data_alarm',
                args: [self.logger_id, $("#rangeDate").val(), 'power', $("#select_hour").val()]
            })
            .then(function(result) {
                $('#div_alarm').show();
                $('#back_to_logger').show();
                $('#div_logger').hide();
                $('#div_consumption').hide();
                self.preview_alarm_chart(result);
            })
        },
        act_view_signal: function(e) {
            var self = this;

            rpc.query({
                model: 'onpoint.logger',
                method: 'get_data_alarm',
                args: [self.logger_id, $("#rangeDate").val(), 'signal', $("#select_hour").val()]
            })
            .then(function(result) {
                $('#div_alarm').show();
                $('#back_to_logger').show();
                $('#div_logger').hide();
                self.preview_alarm_chart(result);
            })
        },
        act_view_temperature: function(e) {
            var self = this;

            rpc.query({
                model: 'onpoint.logger',
                method: 'get_data_alarm',
                args: [self.logger_id, $("#rangeDate").val(), 'temperature', $("#select_hour").val()]
            })
            .then(function(result) {
                $('#div_alarm').show();
                $('#back_to_logger').show();
                $('#div_logger').hide();
                self.preview_alarm_chart(result);
            })
        },
        preview_alarm_chart: function(result) {
            var self = this
            $('#back_to_logger').show();

            self.power_chart_options = {
                chart: {
                    zoomType : 'x'
                },
                title: {
                    text: result['title']
                },
                xAxis: {
                    type: 'datetime',
                    dateTimeLabelFormats: { // don't display the dummy year
                        day: '%Y<br/>%m-%d',
                        month: '%e. %b',
                        year: '%b'
                    },
                },
                yAxis: {
                    title: {
                        text: result['title_axis']
                    }
                },
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
                series: result['series']
            }


            self.power_chart = Highcharts.chart('container_power_chart', self.power_chart_options);

        },
        act_view_consumption: function(e) {
            e.preventDefault();
            var self = this;

            var channel_id = $(e.target).data("channel-id");
            var interval = $(e.target).data("interval");
            $('.btn_consumption_intervals').removeClass('btn-success').addClass('btn-primary');
            $('#button-consumption-' + interval).removeClass('btn-primary').addClass('btn-success');

            rpc.query({
                model: 'onpoint.logger',
                method: 'get_data_consumption',
                args: [
                        self.logger_id,
                        channel_id,
                        $("#rangeDate").val(),
                        $("#select_hour").val(),
                        interval
                      ]
            })
            .then(function(result) {
                $('.btn_consumption_intervals').data('channel-id', channel_id);
                $('#div_consumption').show();
                $('#back_to_logger').show();
                $('#div_logger').hide();
                $('#div_alarm').hide();
                $('#interval').val(interval);
                $('#consumption_last_value').html(result['last_value']);
                $('#consumption_last_date').html(result['last_date']);
                $('#consumption_min_value').html(result['min_value']);
                $('#consumption_min_date').html(result['min_date']);
                $('#consumption_max_value').html(result['max_value']);
                $('#consumption_max_date').html(result['max_date']);
                $('#consumption_last_totalizer').html(result['last_totalizer']);
                self.is_flow = true;
                self.channel_id = channel_id;
                self.preview_consumption_chart(result);
            })
        },
        preview_consumption_chart: function(result) {
            var self = this
            $('#back_to_logger').show();

            self.consumption_chart_options = {
                chart: {
                    zoomType : 'x'
                },
                title: {
                    text: result['title']
                },
                xAxis: {
                    type: 'datetime',
                    dateTimeLabelFormats: { // don't display the dummy year
                        day: '%Y<br/>%m-%d',
                        month: '%e. %b',
                        year: '%b'
                    },
                },
                yAxis: result['yAxis'],
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
                series: result['series']
            }

            var data = {
                options: JSON.stringify(self.consumption_chart_options),
                filename: 'test.png',
                type: 'image/png',
                async: true
            };

            $('#infile').text(JSON.stringify(self.consumption_chart_options));

            self.async_chart();

//            var exportUrl = 'https://export.highcharts.com/';
//            $.post(exportUrl, data, function(data) {
//                var imageUrl = exportUrl + data;
//                var urlCreator = window.URL || window.webkitURL;
//                self.chart_image_url = imageUrl;
//            });

            self.consumption_chart = Highcharts.chart('container_consumption_chart', self.consumption_chart_options);


        },
        act_print: function(e) {
            var self = this;

            this.do_action({
                name: 'Print Result',
                type: 'ir.actions.act_window',
                res_model: 'onpoint.logger.report',
                view_mode: 'form',
                view_type: 'form',
                views: [[false, 'form']],
                context: {
                    default_logger_id: this.logger_id,
                    default_report_period: $("#rangeDate").val(),
                    default_start_date: self.logger['period_start'],
                    default_end_date: self.logger['period_end'],
                    default_option_hour: $("#select_hour").val(),
                    default_image_url: self.chart_image_url,
                    default_image_base64: $('#img_chart_text').text(),
                    default_power_image: self.logger.state_battery.src,
                    default_power_value: self.logger.state_battery.last_value,
                    default_signal_image: self.logger.state_signal.src,
                    default_signal_value: self.logger.state_signal.last_value,
                    default_temperature_image: self.logger.state_temperature.src,
                    default_temperature_value: self.logger.state_temperature.last_value,
                    default_is_flow: self.is_flow,
                    default_channel_id: self.channel_id,
                    default_interval: $("#interval").val()
                },
                target: 'new'
            });
        },
        act_toggle_auto_refresh: function(e) {
            var self = this;
            e.stopPropagation();
            e.preventDefault();

            rpc.query({
                model: 'onpoint.logger',
                method: 'act_toggle_auto_refresh',
                args: [self.logger_id]
            })
            .then(function(result) {
                self.auto_refresh = result;
                $('#auto_refresh').prop('checked', self.auto_refresh);
            })
        },
        act_auto_refresh_chart: function() {
            var self = this;
            var auto_refresh_enabled = $('#auto_refresh').is(':checked');
            if (auto_refresh_enabled == true) {
                self.get_logger_data($("#rangeDate").val(), $("#select_period").val(), $("#period").val(), $('#select_hour').val());
            }
        },
        on_reverse_breadcrumb: function() {
            this.updateControlPanel({clear: true});
            web_client.do_push_state({action: this.action_id});
        },
    
    });

    core.action_registry.add('onpoint_monitor_logger_chart', OnpointLoggerChart);
    return OnpointLoggerChart;


});