odoo.define('onpoint_analytic.night_flow', function (require) {
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
    
    var OnpointNightFlow = Widget.extend(ActionMixin, {
        hasControlPanel: true,
        template: "NightFlowMain",
        events: {
            'click #btn_refresh_before_chart': 'act_refresh_before_chart',
            'click #btn_refresh_after_chart': 'act_refresh_after_chart',
            'click #btn_new': 'act_new'
        },
        init: function(parent, context) {
            this._super(parent, context);
            this.action_id = context.id;
            this.night_flow_id = context.context['night_flow_id'];
            this.title = 'Title';
            this.sub_title = 'Sub Title';
            this.name = context.context['name'];
            this.source_selection = context.context['source_selection'];
            this.logger_id = context.context['logger_id'];
            this.logger_compare_id = context.context['logger_compare_id'];
            this.channel_id = context.context['channel_id'];
            this.logger = false;
            this.first_period;
            this.second_period;
            this.chart;
            this.chart_options;
            this.chart_image_url;
            this._super(parent,context);
        },
        start: function() {
            var self = this;
            for(var i in self.breadcrumbs){
                self.breadcrumbs[i].title = "Chart";
            }
            self.updateControlPanel({breadcrumbs: self.breadcrumbs}, {clear: true});

            $(".o_control_panel").removeClass("o_hidden");

            var today = new Date();
            var previous = new Date();

            if (self.night_flow_id === undefined) {
            }
            else {
                self.get_night_flow_data();
            }
        },
        act_new: function(e) {
            var self = this;

            this.do_action({
                name: 'New',
                type: 'ir.actions.act_window',
                res_model: 'onpoint.night.flow',
                view_mode: 'form',
                view_type: 'form',
                views: [[false, 'form']],
                context: {},
                target: 'new'
            });
        },
        get_night_flow_data: function() {
            var self = this;

            var args = {
                'night_flow_id': 1,
                'name': 'Coba Name'
            }

            rpc.query({
                model: 'onpoint.night.flow',
                method: 'get_data',
                args: [args]
            })
            .then(function(result){

                if(result){
                    $('.o_hr_chart').html(QWeb.render('NightFlowContent', {widget: self}));
                    $('#night_flow_id').val(self.night_flow_id);
                    $('#name').html(self.name);
                    $('#source_selection').val(self.source_selection);
                    $('#logger_id').val(self.logger_id);
                    $('#logger_compare_id').val(self.logger_compare_id);
                    $('#channel_id').val(self.channel_id);

                    var first_picker = new Lightpick({
                        field: document.getElementById('first_period'),
                        singleDate: false
                    });
                    first_picker.setDateRange(moment().add(-7, 'day'), new Date());

                    var second_picker = new Lightpick({
                        field: document.getElementById('second_period'),
                        singleDate: false
                    });
                    second_picker.setDateRange(moment().add(-7, 'day'), new Date());

                    self.act_refresh_before_chart();
                    self.act_refresh_after_chart();

                }
                else{
                    $('.o_hr_chart').html(QWeb.render('NightFlowWarning', {widget: self}));
                    return;
                }
            });

        },
        act_refresh_before_chart: function(e) {
            var self = this;
            var args = [$('#night_flow_id').val(),
                        $("#first_period").val(),
                        $("#input_start_hour").val(),
                        $("#input_start_minute").val(),
                        $("#input_end_hour").val(),
                        $("#input_end_minute").val()]
            self.get_chart_data('container_before', args);
        },
        act_refresh_after_chart: function(e) {
            var self = this;
            var args = [$('#night_flow_id').val(),
                        $("#second_period").val(),
                        $("#input_start_hour").val(),
                        $("#input_start_minute").val(),
                        $("#input_end_hour").val(),
                        $("#input_end_minute").val()]
            self.get_chart_data('container_after', args);
        },
        get_chart_data: function(target, args) {
            var self = this;

            rpc.query({
                model: 'onpoint.night.flow',
                method: 'get_chart_data',
                args: args
            })
            .then(function(result){

                if(result){
                    self.logger = result;
                    self.preview_chart(target + '_chart', result);
                    $('#' + target + '_stats').html(QWeb.render('NightFlowStats', {widget: self}));
                }
                else{
                    $('.o_hr_chart').html(QWeb.render('NightFlowWarning', {widget: self}));
                    return;
                }
            });
        },
        preview_chart: function(target, result) {

            self.logger = result;

            self.chart_options = {
                chart: {
                    zoomType : 'x',
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
                    plotLines: self.logger['plot_lines']
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


            self.chart = Highcharts.chart(target, self.chart_options);
        },
        on_reverse_breadcrumb: function() {
            this.updateControlPanel({clear: true});
            web_client.do_push_state({action: this.action_id});
        },
    
    });

    core.action_registry.add('onpoint_analytic_night_flow', OnpointNightFlow);
    return OnpointNightFlow;


});