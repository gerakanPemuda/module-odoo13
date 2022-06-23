//$('.onpoint_monitor').on('click', function() {
//    location.href = '/dashboard/goto_monitor'
//})
//

odoo.define('onpoint_dashboard.main_dashboard', function (require) {
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
    var infoWindows = [];

    var OnpointDashboardMain = Widget.extend(ActionMixin, {
        hasControlPanel: true,
        template: "OnpointDashboardMain",
        events: {
            'click #icon_filter_logger_type': 'act_slide_logger_type',
            'click #icon_filter_logger': 'act_slide_logger_keyword',
            'click .icon-logger-type': 'act_view_logger_type',
            'click #icon_search': 'act_search',
            'keypress #logger_keyword': 'act_search_submit',
            'click #btn_mimic': 'act_goto_dashboard_mimic',
            'click #btn_logger_list': 'act_goto_logger_list',
            'click #btn_monitor': 'act_goto_monitor',
            'click #btn_analytic': 'act_goto_analytic',
            'click #btn_work_order': 'act_goto_work_order',
            'click .logger_links': 'act_view_logger',
            'click #icon_filter_brand_type': 'act_change_marker_type'
        },
        init: function(parent, context) {
            this._super(parent, context);
            this.action_manager = parent;
            this.logger = false;
            this.logger_type = false;
            this.markers = [];
        },
        start: function() {
            var self = this;
            self.viewDashboard(0);
        },
        viewDashboard: function(logger_type_id) {
            var self = this;
            rpc.query({
                model: 'onpoint.dashboard.main',
                method: 'get_data',
                args: [logger_type_id]
            })
            .then(function(result){
                self.logger =  result['loggers'];
                self.logger_type =  result['logger_types'];
//                alert(self.logger['company_logo']);

                if(result){
                    $('.o_dashboard').html(QWeb.render('OnpointDashboardMainContent', {widget: self}));

                    var indonesia = {lat: -0.510370, lng: 117.172094};
                    var map_options = { zoom: 10,
                                        zoomControl: false,
                                        fullscreenControl: false,
                                        mapTypeControl: false,
                                        scaleControl: false,
                                        streetViewControl: false,
                                        rotateControl: false,
                                        mapTypeId: 'satellite'};
                    map = new google.maps.Map(document.getElementById('map'), map_options);
                    map.setZoom(map.getZoom());

                    self.preview_map();
                    $( ".container-logger-type" ).hide();
                    $( ".container-logger-search" ).hide();
                }
                else{
                    $('.o_hr_dashboard').html(QWeb.render('OnpointDashboardMainWarning', {widget: self}));
                    return;
                }
            });
        },
        preview_map: function() {
            var self = this;

            var loggerMarkers = self.logger['markers'];

            var positions = [];
            // Loop through markers and set map to null for each
            for (var i=0; i < this.markers.length; i++) {

                this.markers[i].setMap(null);
            }

            // Reset the markers array
            this.markers = [];

            $.each(loggerMarkers, function(key, data) {

                var contentWindow = "<b>" +
                                    data['name']  +
                                    "</b>" +
                                    "<br/>" +
                                    data["channel_info"] +
                                    "<br/>" +
                                    "<a href='#' class='logger_links' data-id='"+ data["id"] +"'>click here to view</a>" +
                                    "</p>";

                self.add_marker({
                    content: contentWindow,
                    brand_owner: data['brand_owner'],
                    coords: {
                        'lat': parseFloat(data['position'].lat),
                        'lng': parseFloat(data['position'].lng)
                    },
                    logger_type_id: data['logger_type_id'],
                    icon: data['icon']
                })
            });

            google.maps.event.trigger(map, "resize");

        },
        add_marker: function(props) {
            var iconBase = '/onpoint_dashboard/static/src/img/markers/'

//            icon = {
//                size: new google.maps.Size(220,220),
//                scaledSize: new google.maps.Size(32,32),
//                origin: new google.maps.Point(0,0),
//                url: props.icon,
//                anchor: new google.maps.Point(16,16
//            }
//
            var icons = {
                      pointorange: {
                        icon: iconBase + 'marker_pointorange.png'
                      },
                      seba: {
                        icon: iconBase + 'marker_seba.png'
                      },
                    };

            var marker = new google.maps.Marker({
                map: map,
                position: props.coords,
                icon: {
                    scaledSize: new google.maps.Size(48,48),
                    url: "data:image/png;base64, " + props.icon,
                    },
                descrip: props.content
            })

            this.markers.push(marker);

            map.setZoom(12);
            map.panTo(marker.position);

            if (props.content) {
                var infoWindow = new google.maps.InfoWindow({
                    content : props.content
                })
                infoWindows.push(infoWindow);
            }

            marker.addListener('click', function() {
                //close all
                for (var i = 0; i < infoWindows.length; i++) {
                    infoWindows[i].close();
                }
                infoWindow.open(map, marker);
            })

            map.addListener('click', function() {
                //close all
                for (var i = 0; i < infoWindows.length; i++) {
                    infoWindows[i].close();
                }
                $( ".container-logger-search" ).hide();
                $( ".container-logger-type" ).hide();
            })

        },
        act_slide_logger_type: function() {
            $( ".container-logger-search" ).hide();
            $( ".container-logger-type" ).toggle( "slide" );
        },
        act_slide_logger_keyword: function() {
            $( ".container-logger-type" ).hide();
            $( ".container-logger-search" ).toggle( "slide" );
        },
        act_view_logger_type: function(e) {
            var self = this;
            var logger_type_id = parseInt($(e.target).attr('data-logger_type_id'));
            $("#logger_type_id").val(logger_type_id);
            $('#logger_keyword').val('');

            self.view_logger_type();

            $('#icon_filter_logger_type').attr('src', $(e.target).attr('src'));
        },
        view_logger_type: function() {
            var self = this;
            var logger_type_id = $("#logger_type_id").val();
            var marker_type = $('#marker_type').val();
            var keyword = $('#logger_keyword').val();

            rpc.query({
                model: 'onpoint.dashboard.main',
                method: 'get_data',
                args: [logger_type_id, marker_type, keyword]
            })
            .then(function(result){
                self.logger =  result['loggers'];
                self.logger_type =  result['logger_types'];

                if(result){
                    $( ".container-logger-type" ).hide();
                    self.preview_map();
                }
            });

        },
        act_change_marker_type: function(e) {
            var self = this;
            var marker_type = $('#marker_type').val();
            if (marker_type == 'logger_type') {
                marker_type = 'logger_brand';
            }
            else {
                marker_type = 'logger_type';
            }
            $('#marker_type').val(marker_type);
            self.view_logger_type();

        },
        act_search: function(elem) {
            elem = elem || document.documentElement;
              if (!document.fullscreenElement && !document.mozFullScreenElement &&
                !document.webkitFullscreenElement && !document.msFullscreenElement) {
                if (elem.requestFullscreen) {
                  elem.requestFullscreen();
                } else if (elem.msRequestFullscreen) {
                  elem.msRequestFullscreen();
                } else if (elem.mozRequestFullScreen) {
                  elem.mozRequestFullScreen();
                } else if (elem.webkitRequestFullscreen) {
                  elem.webkitRequestFullscreen(Element.ALLOW_KEYBOARD_INPUT);
                }
              } else {
                if (document.exitFullscreen) {
                  document.exitFullscreen();
                } else if (document.msExitFullscreen) {
                  document.msExitFullscreen();
                } else if (document.mozCancelFullScreen) {
                  document.mozCancelFullScreen();
                } else if (document.webkitExitFullscreen) {
                  document.webkitExitFullscreen();
                }
              }
        },
        act_search_submit: function(e) {
            var self = this;
            if (e.which == 13) {
                self.view_logger_type();
            }
        },
        act_goto_dashboard_mimic: function(e) {
            var self = this;
            e.stopPropagation();
            e.preventDefault();

            location.href = '/dashboard/goto_mimic';

//            this.do_action({
//                name: _t("Mimic Diagram"),
//                type: 'ir.actions.client',
//                tag: 'onpoint_dashboard_mimic_dashboard',
//                context: {},
//                target: 'fullscreen'
//            });
        },
        act_view_logger: function(e) {
            var self = this;
            e.stopPropagation();
            e.preventDefault();

            var logger_id = parseInt($(e.target).attr('data-id'));

            this.do_action({
                name: _t("Logger"),
                type: 'ir.actions.client',
                tag: 'onpoint_monitor_logger_chart',
                context: {'logger_id': logger_id },
                target: 'main'
            });
        },
        act_goto_monitor: function(e) {
            var self = this;
            e.stopPropagation();
            e.preventDefault();
            var options = {
                on_reverse_breadcrumb: self.on_reverse_breadcrumb,
            };

            location.href = '/dashboard/goto_monitor';

//            this.do_action({
//                name: _t("Logger"),
//                type: 'ir.actions.act_window',
//                res_model: 'onpoint.logger',
//                views: [[false, 'list'], [false, 'form'], [false, 'kanban']],
//                target: 'main'
//            }, {on_reverse_breadcrumb: function(){ return self.reload();}});
        },
        act_goto_analytic: function(e) {
            var self = this;
            e.stopPropagation();
            e.preventDefault();
            var options = {
                on_reverse_breadcrumb: self.on_reverse_breadcrumb,
            };
            this.do_action({
                name: _t("CP Recap"),
                type: 'ir.actions.act_window',
                res_model: 'onpoint.cp.recap',
                views: [[false, 'list'], [false, 'form']],
                target: 'main'
            }, {on_reverse_breadcrumb: function(){ return self.reload();}});
        },
        act_goto_work_order: function(e) {
            var self = this;
            e.stopPropagation();
            e.preventDefault();
            var options = {
                on_reverse_breadcrumb: self.on_reverse_breadcrumb,
            };
            this.do_action({
                name: _t("Work Order"),
                type: 'ir.actions.act_window',
                res_model: 'onpoint.work.order',
                views: [[false, 'kanban'], [false, 'form'], [false, 'list']],
                target: 'main'
            }, {on_reverse_breadcrumb: function(){ return self.reload();}});
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

    core.action_registry.add('onpoint_dashboard_main_dashboard', OnpointDashboardMain);
    return OnpointDashboardMain;

});
