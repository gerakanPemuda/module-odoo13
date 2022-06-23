odoo.define('onpoint_base.copyright_dashboard', function (require) {
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
    
    var OnpointCopyrightDashboard = Widget.extend(ActionMixin, {
        hasControlPanel: true,
        template: "CopyrightDashboardMain",
        init: function(parent, context) {
            this._super(parent, context);
        },
        start: function() {
            var self = this;
            $('.o_dashboard').html(QWeb.render('CopyrightDashboardContent', {widget: self}));
        },
    });

    core.action_registry.add('onpoint_base_copyright_dashboard', OnpointCopyrightDashboard);
    return OnpointCopyrightDashboard;


});