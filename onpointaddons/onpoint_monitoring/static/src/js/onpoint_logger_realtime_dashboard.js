odoo.define('onpoint_monitoring.logger_realtime_dashboard', function (require) {
    "use strict";
    
    var ControlPanelMixin = require('web.ControlPanelMixin');
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
    
    var OnpointLoggerRealtimeDashboard = Widget.extend(ControlPanelMixin, {
        template: "LoggerRealtimeDashboardMain",
        events: {
            'click #btn_config': 'act_logger',
            'click #btn_refresh': 'act_refresh_chart'
        },
        init: function(parent, context) {
            this._super(parent, context);
            this.action_id = context.id;
            this.logger_id = context.context['logger_id'];
            this.logger = false;
            this.selected_option = 'all';
            this.selected_period = 'hour';
            this.map;
            this._super(parent,context);

        },
        start: function() {
            var self = this;
            for(var i in self.breadcrumbs){
                self.breadcrumbs[i].title = "Dashboard";
            }
            self.update_control_panel({breadcrumbs: self.breadcrumbs}, {clear: true});
            // $(".o_control_panel").html("Tesss");
            $(".o_control_panel").removeClass("o_hidden");

            self.get_logger_realtime_data();            
            
            setInterval(function() {
                $('#btn_refresh').click();
            }, 36000000);
        

        },
        get_logger_realtime_data: function() {

            var self = this;
            rpc.query({
                model: 'onpoint.logger',
                method: 'get_realtime_data',
                args: [self.logger_id]
            })
            .then(function(result){
                self.logger =  result;

                if(result){
                    $('.o_hr_dashboard').html(QWeb.render('LoggerRealtimeDashboardContent', {widget: self}));                

                    self.preview_logger_chart();
                    // self.preview_stats();

					var today = new Date();
					var currentHours = ("0" + today.getHours()).slice(-2);
					var currentMinutes = ("0" + today.getMinutes()).slice(-2);
					var currentSeconds = ("0" + today.getSeconds()).slice(-2);

					var time = "Last refresh : " + today.getDate() + "-" + (today.getMonth()+1) + "-" + today.getFullYear() + " " +  currentHours + ":" + currentMinutes + ":" + currentSeconds;
					$('#last_update').html(time);					
                }
                else{
                    $('.o_hr_dashboard').html(QWeb.render('LoggerRealtimeDashboardWarning', {widget: self}));
                    return;
                }
            });

        },
        preview_logger_chart: function() {
            var self = this

            Highcharts.chart('container_logger_chart', {

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
                }
            });
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
        act_refresh_chart: function() {
            var self = this;
            self.get_logger_realtime_data();

        },   
        on_reverse_breadcrumb: function() {
            this.update_control_panel({clear: true});
            web_client.do_push_state({action: this.action_id});
        },
    
    });



    
    core.action_registry.add('onpoint_monitoring.logger_realtime_dashboard', OnpointLoggerRealtimeDashboard);
    return OnpointLoggerRealtimeDashboard;


});