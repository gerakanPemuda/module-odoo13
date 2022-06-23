//var map;
//function initMap() {
//    map = new google.maps.Map(document.getElementById("map"), {
//        center: { lat: -3.765042, lng: 113.253670 },
//        zoom: 5,
//        disableDefaultUI: true
//    });
//}

odoo.define('onpoint_dashboard.mimic_dashboard', function (require) {
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

    var OnpointDashboardMimic = Widget.extend(ActionMixin, {
        hasControlPanel: true,
        template: "OnpointDashboardMimic",
        events: {
            'click #btn_main': 'act_goto_dashboard_main',
            'click #btn_logger_list': 'act_goto_logger_list',
        },
        init: function(parent, context) {
            this._super(parent, context);
            this.action_manager = parent;

        },
        start: function() {
            var self = this;
            self.viewDashboard();
        },
        viewDashboard: function() {
            var self = this;
            rpc.query({
                model: 'onpoint.logger',
                method: 'get_map_data',
                args: []
            })
            .then(function(result){
                self.logger =  result;

                if(result){
                    $('.o_dashboard').html(QWeb.render('OnpointDashboardMimicContent', {widget: self}));
                }
                else{
                    $('.o_hr_dashboard').html(QWeb.render('OnpointDashboardMimicWarning', {widget: self}));
                    return;
                }
            });
        },
        act_goto_dashboard_main: function(e) {
            var self = this;
            e.stopPropagation();
            e.preventDefault();

            this.do_action({
                name: _t("Maps"),
                type: 'ir.actions.client',
                tag: 'onpoint_dashboard_main_dashboard',
                context: {},
                target: 'fullscreen'
            });
        },
        act_goto_logger_list: function(e) {
            var self = this;
            e.stopPropagation();
            e.preventDefault();

            this.do_action({
                name: _t("Logger"),
                type: 'ir.actions.client',
                tag: 'onpoint_monitor_monitor_dashboard',
                context: {},
                target: 'main'
            });
        },
    });

    core.action_registry.add('onpoint_dashboard_mimic_dashboard', OnpointDashboardMimic);
    return OnpointDashboardMimic;

});
