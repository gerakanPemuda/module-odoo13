odoo.define('onpoint_monitoring.logger_dashboard', function (require) {
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
    
    var OnpointLoggerDashboard = Widget.extend(ControlPanelMixin, {
        template: "LoggerDashboardMain",
        events: {
            'click #btn_config': 'act_logger',
            'change #option': 'change_option',
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

            var today = new Date();
            var previous = new Date();
            previous.setDate(today.getDate() - 3);
            var start_date = previous.getDate() + '/' + (previous.getMonth()+1) + "/" + previous.getFullYear();
            var end_date = today.getDate() + '/' + (today.getMonth()+1) + "/" + today.getFullYear();
            var rangeDate = start_date + ' - ' + end_date;
            var option = self.selected_option;
            var period = self.selected_period;

            self.get_logger_data(rangeDate, option, period);
        },
        get_logger_data: function(rangeDate, option, period) {

            var self = this;
            rpc.query({
                model: 'onpoint.logger',
                method: 'get_data',
                args: [self.logger_id, rangeDate, option, period]
            })
            .then(function(result){
                self.logger =  result;

                if(result){
                    $('.o_hr_dashboard').html(QWeb.render('LoggerDashboardContent', {widget: self}));                
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

                    self.preview_logger_chart();
                    self.preview_stats();

                }
                else{
                    $('.o_hr_dashboard').html(QWeb.render('LoggerDashboardWarning', {widget: self}));
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
                
                // annotations: [
                //     {
                //         labelOptions: {
                //             backgroundColor: 'rgba(255,255,255,0.5)',
                //             verticalAlign: 'top',
                //             y: 15
                //         },
                //         labels: [            
                //         {
                //             point: {
                //                 xAxis: 0,
                //                 yAxis: 0,
                //                 x: 1570245317000,
                //                 y: 2.773
                //             },
                //             text: 'Arbois'
                //         }, {
                //             point: {
                //                 xAxis: 0,
                //                 yAxis: 0,
                //                 x: 1570246217000,
                //                 y: 2.861
                //             },
                //             text: 'Montrondxxxx'
                //         }, {
                //             point: {
                //                 xAxis: 0,
                //                 yAxis: 0,
                //                 x: 1570247117000,
                //                 y: 2.845
                //             },
                //             text: 'Montrondyyy'
                //         },
                        
                //         ]
                //     }],   

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
        change_option: function() {
            var self = this;
            if ($("#option").val() == 'all') {
                $('#period').hide();
            }
            else {
                $('#period').show();
            }
        },   
        act_refresh_chart: function() {
            var self = this;
            self.get_logger_data($("#rangeDate").val(), $("#option").val(), $("#period").val());
        },   
        on_reverse_breadcrumb: function() {
            this.update_control_panel({clear: true});
            web_client.do_push_state({action: this.action_id});
        },
    
    });

    core.action_registry.add('onpoint_monitoring.logger_dashboard', OnpointLoggerDashboard);
    return OnpointLoggerDashboard;


});