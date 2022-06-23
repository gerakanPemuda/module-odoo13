console.log("CALLLLLLLLLLLLlll")
odoo.define('onpoint_monitor_logger_dashboard', function (require) {
    "use strict";

    console.log("CALL 222222")

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
    var _lt = core._lt;http://localhost:8069/web?debug=assets#
    var map;

    var OnpointLoggerDashboard = Widget.extend(ControlPanelMixin, {
        template: "LoggerDashboardMain",
        events: {},
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
        },
        on_reverse_breadcrumb: function() {
            this.update_control_panel({clear: true});
            web_client.do_push_state({action: this.action_id});
        },

    });

    core.action_registry.add('onpoint_monitor_logger_dashboard', OnpointLoggerDashboard);
    return OnpointLoggerDashboard;

});