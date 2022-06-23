odoo.define('onpoint_monitoring.onpoint_dashboard', function (require) {
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
    

    var OnpointDashboard = Widget.extend(ControlPanelMixin, {
        template: "OnpointDashboardMain",
        events: {
            'click .links': 'act_info',
        },
        init: function(parent, context) {
            this._super(parent, context);
            this.action_id = context.id;
            this.logger = false;
            this._super(parent,context);
        },
        start: function() {
            var self = this;
            for(var i in self.breadcrumbs){
                self.breadcrumbs[i].title = "Dashboard";
            }
            self.update_control_panel({breadcrumbs: self.breadcrumbs}, {clear: true});
            $(".o_control_panel").addClass("o_hidden");

            self.get_data();
        },
        get_data: function() {

            var self = this;
            rpc.query({
                model: 'onpoint.logger',
                method: 'get_map_data',
                args: []
            })
            .then(function(result){
                self.logger =  result;

                if(result){
                    $('.o_hr_dashboard').html(QWeb.render('OnpointDashboardContent', {widget: self}));                
                    self.preview_map();

                }
                else{
                    $('.o_hr_dashboard').html(QWeb.render('OnpointDashboardWarning', {widget: self}));
                    return;
                }
            });

        },
        preview_map: function() {
            var self = this;

            var indonesia = {lat: -0.481531, lng: 117.148743};
            var map_options = {zoom: 9, center: indonesia};
            map = new google.maps.Map(document.getElementById('map'), map_options);


            var markers = self.logger['markers'];

            var positions = [];
            $.each(markers, function(key, data) {

                var contentWindow = "<h4>" + 
                                    data['name']  + 
                                    "</h4><h5>" + 
                                    data['logger_type_name'] + 
                                    "</h5><p>" + 
                                    data['address'] + 
                                    "<br/>" +
                                    "<br/>" +
                                    "<a href='#' class='links' data-id='"+ data["id"] +"'>click here to view</a>" +
                                    "</p>";

                self.add_marker({
                    content: contentWindow,
                    coords: {
                        'lat': parseFloat(data['position'].lat),
                        'lng': parseFloat(data['position'].lng)
                    }
                })


            });

            // var markers = positions.map(function(location, i) {
            //     return new google.maps.Marker({
            //         position: location
            //     });
            // });            


            // Add a marker clusterer to manage the markers.
            // var markerCluster = new MarkerClusterer(map, markers,
            //     {imagePath: 'https://developers.google.com/maps/documentation/javascript/examples/markerclusterer/m'});

        },
        add_marker: function(props) {
            var marker = new google.maps.Marker({
                position: props.coords,
                map: map
            })

            if (props.content) {
                var infoWindow = new google.maps.InfoWindow({
                    content : props.content
                })
            }

            marker.addListener('click', function() {
                infoWindow.open(map, marker);
            })

        },
        act_info: function(e) {
            var self = this;

            var logger_id = $(e.target).data('id');

            e.stopPropagation();
            e.preventDefault();
            var options = {
                on_reverse_breadcrumb: this.on_reverse_breadcrumb,
            };
            self.do_action({
                type: 'ir.actions.client',
                tag: "onpoint_monitoring.logger_dashboard",
                res_id: logger_id,
                context: {'active_id': logger_id, 'logger_id': logger_id},
            }, options);

        },
        act_open_filter: function(e) {

            $('#bottomPanel').slideUp('slow', function() {
                $('#bottomPanel').show();
            });

            // var status = $('#bottomPanel').css('display');
            // if (status == "none") {
            //     $('#bottomPanel').animate({display: 'show'}, 'slow')
            // }
            // else {
            //     // $('#bottomPanel').animate({display: 'hide'}, 'slow')
            // }

        },             
        on_reverse_breadcrumb: function() {
            this.update_control_panel({clear: true});
            web_client.do_push_state({action: this.action_id});
        },
    
    });

    core.action_registry.add('onpoint_monitoring.onpoint_dashboard', OnpointDashboard);
    return OnpointDashboard;


});