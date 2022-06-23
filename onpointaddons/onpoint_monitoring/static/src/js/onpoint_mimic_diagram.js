odoo.define('onpoint_monitoring.onpoint_mimic_diagram', function (require) {
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
    

    
    var OnpointMimic = Widget.extend(ControlPanelMixin, {
        template: "OnpointMimicMain",
        events: {
        },
        init: function(parent, context) {
            this._super(parent, context);
            this.action_id = context.id;
            this.logger = false;
            this._super(parent,context);

            this.refresh_mimic();

        },
        start: function() {
            var self = this;
            for(var i in self.breadcrumbs){
                self.breadcrumbs[i].title = "Mimic";
            }
            self.update_control_panel({breadcrumbs: self.breadcrumbs}, {clear: true});
            $(".o_control_panel").addClass("o_hidden");

            self.get_data();

        },
        get_data: function() {

            var self = this;
            rpc.query({
                model: 'onpoint.mimic',
                method: 'get_data',
                args: []
            })
            .then(function(result){
                self.logger =  result;

                if(result){
                    $('.o_hr_dashboard').html(QWeb.render('OnpointMimicContent', {widget: self}));                
                }
                else{
                    $('.o_hr_dashboard').html(QWeb.render('OnpointMimicWarning', {widget: self}));
                    return;
                }

                self.refresh_mimic();
            });

        },
        refresh_mimic: function() {

            setInterval(function() {
                var self = this;

                var pressure = (Math.random() * (0.120 - 2.0000) + 2.0000).toFixed(2);
                $('#div_pressure').html(pressure + ' bar');

                var flow = (Math.random() * (0.120 - 5.0000) + 5.0000).toFixed(2);
                $('#div_flow').html(flow + ' l/s');

                var level = (Math.random() * (0.120 - 3.0000) + 3.0000).toFixed(2);
                $('#div_level').html(level + ' m');
                
                var level_percentage = level * 100;
                $('#div_level_percentage').css('height', level_percentage + 'px');
                var background_color = '#33b9ea';
                if (level_percentage < 60)
                {
                    $('#div_level_percentage').css('background-color', 'red');
                }
                else {
                    if (level_percentage < 110 )
                    {
                        $('#div_level_percentage').css('background-color', 'orange');
                    }
                    else {
                        if (level_percentage > 225 )
                        {
                            $('#div_level_percentage').css('background-color', 'red');
                        }
                        else {
                            if (level_percentage > 210 )
                            {
                                $('#div_level_percentage').css('background-color', 'orange');
                            }
                            else {
                                $('#div_level_percentage').css('background-color', '#33b9ea');
                            }
                        }
                    }
                }



                var cp1_pressure = (Math.random() * (0.120 - 2.0000) + 2.0000).toFixed(2);
                $('#div_cp1_pressure').html(cp1_pressure + ' bar');

                var cp2_pressure = (Math.random() * (0.120 - 2.0000) + 2.0000).toFixed(2);
                $('#div_cp2_pressure').html(cp2_pressure + ' bar');

                var cp3_pressure = (Math.random() * (0.120 - 2.0000) + 2.0000).toFixed(2);
                $('#div_cp3_pressure').html(cp3_pressure + ' bar');


            }, 10000);

        },
        on_reverse_breadcrumb: function() {
            this.update_control_panel({clear: true});
            web_client.do_push_state({action: this.action_id});
        },
    
    });

    core.action_registry.add('onpoint_monitoring.onpoint_mimic_diagram', OnpointMimic);
    return OnpointMimic;


});