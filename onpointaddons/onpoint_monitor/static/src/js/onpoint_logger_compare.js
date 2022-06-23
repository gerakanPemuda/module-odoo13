odoo.define('onpoint_monitor.logger_compare', function (require) {
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
    
    var OnpointLoggerCompare = Widget.extend(ActionMixin, {
        hasControlPanel: true,
        template: "LoggerCompareMain",
        events: {
            'click #btn_config': 'act_logger_compare',
            'change #option': 'change_option',
            'click #btn_refresh': 'act_refresh_compare',
            'click #btn_act_view_data_channels': 'act_view_data_channels',
            'click #btn_print': 'act_print',
        },
        init: function(parent, context) {
            this._super(parent, context);
            this.action_id = context.id;
            this.logger_compare_id = context.context['compare_id'];
            this.logger = false;
            this.selected_option = 'all';
            this.selected_period = 'hour';
            this.chart;
            this.chart_options;
            this.chart_image_url;
            this.map;
            this._super(parent,context);
    
        },
        start: function() {
            var self = this;
            for(var i in self.breadcrumbs){
                self.breadcrumbs[i].title = "Compare";
            }
            self.updateControlPanel({breadcrumbs: self.breadcrumbs}, {clear: true});
            $(".o_control_panel").removeClass("o_hidden");

            var today = new Date();
            var previous = new Date();
            previous.setDate(today.getDate() - 3);
            var start_date = previous.getDate() + '/' + (previous.getMonth()+1) + "/" + previous.getFullYear();
            var end_date = today.getDate() + '/' + (today.getMonth()+1) + "/" + today.getFullYear();
            var rangeDate = start_date + ' - ' + end_date;
            var option = self.selected_option;
            var period = self.selected_period;

            self.get_logger_data(rangeDate, option, period);

//            setInterval(function() {
//                $('#btn_refresh').click();
//            }, 18000000);
        },
        get_logger_data: function(rangeDate, option, period) {
            var self = this;
            rpc.query({
                model: 'onpoint.logger.compare',
                method: 'get_data',
                args: [self.logger_compare_id, rangeDate]
            })
            .then(function(result){
                self.logger =  result;

                if(result){
                    $('.o_hr_chart').html(QWeb.render('LoggerCompareContent', {widget: self}));
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

                    $('div.div_option select').val(self.logger.selected_option);
                    $('div.div_period select').val(self.logger.selected_period);

                    // self.change_option();

                    self.preview_logger_compare();
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
                }
                else{
                    $('.o_hr_chart').html(QWeb.render('LoggerCompareWarning', {widget: self}));
                    return;
                }
            });

        },
        preview_logger_compare: function() {
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

            var exportUrl = 'https://export.highcharts.com/';
            $.post(exportUrl, data, function(data) {
                var imageUrl = exportUrl + data;
                var urlCreator = window.URL || window.webkitURL;
                self.chart_image_url = imageUrl;
            });

            self.chart = Highcharts.chart('container_logger_compare', self.chart_options);
        },
        preview_stats: function() {
            var self = this

        },
        act_logger_compare: function(e) {
            var self = this;
            e.stopPropagation();
            e.preventDefault();
            var options = {
                on_reverse_breadcrumb: this.on_reverse_breadcrumb,
            };
            this.do_action({
                name: _t("Logger"),
                type: 'ir.actions.act_window',
                res_model: 'onpoint.logger.compare',
                view_mode: 'form',
                view_type: 'form',
                views: [[false, 'form']],
                context: {},
                res_id: this.logger_compare_id,
                target: 'main'
            }, options);
   
        },  
        change_option: function() {
            var self = this;
            if ($("#option").val() == 'all') {
                $('#period').hide();
            }
            else {
                $('#period').show();
            }
        },   
        act_refresh_compare: function() {
            var self = this;
            self.get_logger_data($("#rangeDate").val(), $("#option").val(), $("#period").val());
        },
        act_print: function(e) {
            var self = this;

            this.do_action({
                name: 'Print Result',
                type: 'ir.actions.act_window',
                res_model: 'onpoint.logger.compare.report',
                view_mode: 'form',
                view_type: 'form',
                views: [[false, 'form']],
                context: {
                    default_logger_compare_id: this.logger_compare_id,
                    default_report_period: $("#rangeDate").val(),
                    default_start_date: self.logger['period_start'],
                    default_end_date: self.logger['period_end'],
                    default_image_url: self.chart_image_url,
                },
                target: 'new'
            });
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
        on_reverse_breadcrumb: function() {
            this.updateControlPanel({clear: true});
            web_client.do_push_state({action: this.action_id});
        },
    
    });

    core.action_registry.add('onpoint_monitor_logger_compare', OnpointLoggerCompare);
    return OnpointLoggerCompare;


});