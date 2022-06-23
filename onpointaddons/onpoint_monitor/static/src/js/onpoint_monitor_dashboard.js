odoo.define('onpoint_monitor.monitor_dashboard', function (require) {
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
    
    var OnpointMonitorDashboard = Widget.extend(ActionMixin, {
        hasControlPanel: true,
        template: "MonitorDashboardMain",
        events: {
            'click .btn_act_view_logger': 'act_view_logger',
            'click .btn_logger': 'act_goto_logger',
        },
        init: function(parent, context) {
            this._super(parent, context);
        },
        start: function() {
            var self = this;
            self.get_logger_data();
            setInterval(function()
            {
                self.get_logger_data();
            }, 900000);

        },
        get_logger_data: function() {
            var self = this;
            rpc.query({
                model: 'onpoint.monitor.dashboard',
                method: 'get_data',
                args: []
            })
            .then(function(result){
                self.company =  result[0].company;
                self.loggers =  result[0].loggers;
                self.activities = result[0].activities;
                self.active_loggers = result[0].active_loggers;
                self.total_loggers = result[0].total_loggers;

                if(result){
                    $('.o_dashboard').html(QWeb.render('MonitorDashboardContent', {widget: self}));
//                    self.preview_logger_chart();
                    $('#badge_active_logger').html(self.active_loggers)
                    $('#badge_total_logger').html(self.total_loggers)
                }
                else{
                    $('.o_dashboard').html(QWeb.render('MonitorDashboardWarning', {widget: self}));
                    return;
                }
            });

        },
        preview_logger_chart: function() {
            var self = this;

            Highcharts.chart('container_logger_chart', {

                chart: {
                    plotBackgroundColor: null,
                    plotBorderWidth: null,
                    plotShadow: false,
                    type: 'pie'
                },
                title: {
                    text: 'Logger Activity'
                },
                tooltip: {
                    pointFormat: '{series.name}: <b>{point.percentage:.1f}%</b>'
                },
                accessibility: {
                    point: {
                        valueSuffix: '%'
                    }
                },
                plotOptions: {
                    pie: {
                        allowPointSelect: true,
                        cursor: 'pointer',
                        dataLabels: {
                            enabled: false
                        },
                        showInLegend: true
                    }
                },
                series: [{
                    name: 'Loggers',
                    colorByPoint: true,
                    data: [{
                        name: 'Active',
                        y: parseInt(self.activities[0].active),
                        sliced: true,
                        selected: true
                    }, {
                        name: 'Inactive',
                        y: parseInt(self.activities[0].inactive),
                    }]
                }]
            });
        },
        act_view_logger: function(e) {
            var self = this;
            e.stopPropagation();
            e.preventDefault();

            var logger_id = parseInt($(e.target).attr('data-logger-id'));

//            this.do_action({
//                name: _t("Logger"),
//                type: 'ir.actions.act_window',
//                res_model: 'onpoint.logger',
//                views: [[false, 'list'], [false, 'form'], [false, 'kanban']],
//                target: 'main'
//            }, {on_reverse_breadcrumb: function(){ return self.reload();}});
//

            this.do_action({
                name: _t("Logger"),
                type: 'ir.actions.client',
                tag: 'onpoint_monitor_logger_chart',
                context: {'logger_id': logger_id },
                target: 'main'
            });
        },
        act_goto_logger: function(e) {
            var self = this;
            e.stopPropagation();
            e.preventDefault();

            this.do_action({
                name: _t("Logger"),
                type: 'ir.actions.act_window',
                res_model: 'onpoint.logger',
                context: {'search_default_filter_enabled_logger' : 1},
                views: [[false, 'list'], [false, 'form'], [false, 'kanban']],
                target: 'main'
            }, {on_reverse_breadcrumb: function(){ return self.reload();}});
        },
        on_reverse_breadcrumb: function() {
            this.updateControlPanel({clear: true});
            web_client.do_push_state({action: this.action_id});
        },
    
    });

    core.action_registry.add('onpoint_monitor_monitor_dashboard', OnpointMonitorDashboard);
    return OnpointMonitorDashboard;


});