odoo.define('onpoint_scada.unit_chart', function (require) {
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
    var refresh_interval = null;
    
    var OnpointScadaUnitChart = Widget.extend(ActionMixin, {
        hasControlPanel: true,
        template: "UnitChartMain",
        events: {
            'change #select_period': 'change_period',
            'click .btn_unit': 'act_goto_unit',
            'click #btn_loggers': 'act_goto_loggers',
            'click #btn_refresh': 'act_refresh_chart',
            'click #btn_print': 'act_print',
        },
        init: function(parent, context) {
            this._super(parent, context);
            this.action_id = context.id;
            this.unit_id = context.context['unit_id'];
            this.unit = false;
            this.selected_period = '1d';
            this.selected_hour = '00';
            this.selected_interval = '900';
            this.rangeDate;
            this.chart;
            this.chart_options;
            this._super(parent,context);
    
        },
        start: function() {
            var self = this;
            for(var i in self.breadcrumbs){
                self.breadcrumbs[i].title = "Chart";
            }
            self.updateControlPanel({breadcrumbs: self.breadcrumbs}, {clear: true});
            // $(".o_control_panel").html("Tesss");
            $(".o_control_panel").removeClass("o_hidden");

            if (typeof $('#select_hour').val() !== 'undefined') {
                self.selected_period = $('#select_period').val();
                self.rangeDate = $("#rangeDate").val();
                self.selected_hour = $('#select_hour').val();
                self.selected_interval = $('#select_interval').val();
            }
            else {
                var today = new Date();
                var previous = new Date();
                previous.setDate(today.getDate() - 3);
                var start_date = previous.getDate() + '/' + (previous.getMonth()+1) + "/" + previous.getFullYear();
                var end_date = today.getDate() + '/' + (today.getMonth()+1) + "/" + today.getFullYear();
                self.rangeDate = start_date + ' - ' + end_date;
                self.selected_hour = '00';
                self.selected_interval = '900';
            }
            self.get_unit_data(self.rangeDate, self.selected_period, self.selected_hour, self.selected_interval);
//            refresh_interval = setInterval(function() {self.act_auto_refresh_chart();}, 300000);
        },
        set_range: function() {

            var today = new Date();
            var previous = new Date();
            var interval_days = 1;

            var selected_period_val = $("#select_period").val();
            switch(selected_period_val) {
                case '1d':
                    interval_days = 1;
                    break;
                case '3d':
                    interval_days = 3;
                    break;
                case '1w':
                    interval_days = 7;
                    break;
                case '2w':
                    interval_days = 14;
                    break;
                case '1m':
                    interval_days = 30;
                    break;
                case '2m':
                    interval_days = 60;
                    break;
            }
            previous.setDate(today.getDate() - interval_days);
            var start_date = previous.getDate() + '/' + (previous.getMonth()+1) + "/" + previous.getFullYear();
            var end_date = today.getDate() + '/' + (today.getMonth()+1) + "/" + today.getFullYear();
            var rangeDate = start_date + ' - ' + end_date;

            if (rangeDate == "") {
                picker.setDateRange(moment().add(-7, 'day'), new Date());
            }
            else {
                $("#rangeDate").val(rangeDate);
            }
            if (selected_period_val == 'custom') {
                $("#rangeDate").show();
            }
            else {
                $("#rangeDate").hide();
            }
        },
        change_period: function() {
            var self = this;
            self.set_range();
        },
        get_unit_data: function(rangeDate, period, option_hour, interval) {
            var self = this;

            rpc.query({
                model: 'onpoint.scada.unit',
                method: 'get_unit_data',
                args: [self.unit_id, rangeDate, period, option_hour, interval]
            })
            .then(function(result){
                self.unit =  result;

                if(result){
                    $('.o_hr_chart').html(QWeb.render('UnitChartContent', {widget: self}));
                    self.preview_logger_chart();
                    var picker = new Lightpick({
                        field: document.getElementById('rangeDate'),
                        singleDate: false
                    });
                    self.set_range();
                    $('#select_period').val(self.unit.period);
                    $('#select_hour').val(self.unit.option_hour);
                    $('#select_interval').val(self.unit.interval);
                    self.change_period();
                }
                else{
                    $('.o_hr_chart').html(QWeb.render('UnitChartWarning', {widget: self}));
                    return;
                }
            });
        },
        preview_logger_chart: function() {
            var self = this
            $('#print_loading').show();
            $('#btn_print').hide();

            self.chart_options = {
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

                yAxis: self.unit['yAxis'],

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
                            legendItemClick: function(event) {
                            }
                        }
                    }
                },


                series: self.unit['series'],
                stats: self.unit['stats'],

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

            $('#infile').text(JSON.stringify(self.chart_options));

            self.async_chart();
            self.chart = Highcharts.chart('container_unit_chart', self.chart_options);

            var stats = self.unit['stats'];

        },
        async_chart: async function() {
            const blob2base64 = (blob) => new Promise((resolve, reject) => {
                const reader = new FileReader();
                reader.onerror = reject;
                reader.onload = () => resolve(reader.result);
                reader.readAsDataURL(blob);
            });

            // Prepare POST data
            const body = new FormData();
            body.append('infile', $('#infile').val());
            body.append('width', 800);

            // Post it to the export server
            const blob = await fetch('https://export.highcharts.com/', {
                body,
                method: 'post'
            }).then(result => result.blob());

            // Create the image
            const img = new Image();
            img.src = await blob2base64(blob);
            $('#image_base64_text').text(img.src);
            $('#print_loading').hide();
            $('#btn_print').show();

//            document.getElementById('img_chart').setAttribute('src', img.src);
//            $('#img_chart_text').text(img.src);

        },
        act_refresh_chart: function() {
            var self = this;
            self.get_unit_data($("#rangeDate").val(), $('#select_period').val(), $('#select_hour').val(), $('#select_interval').val());
        },
        act_goto_unit: function(e) {
            var self = this;
            e.stopPropagation();
            e.preventDefault();
            var options = {
                on_reverse_breadcrumb: this.on_reverse_breadcrumb,
            };
            var goto_unit_id = parseInt($(e.target).attr('data-unit-id'));
            this.do_action({
                name: _t("Unit"),
                type: 'ir.actions.client',
                tag: 'onpoint_scada_unit_chart',
                context: {'unit_id': goto_unit_id },
                target: 'main'
            });
        },
        act_goto_loggers: function(e) {
            var self = this;
            e.stopPropagation();
            e.preventDefault();
            var options = {
                on_reverse_breadcrumb: this.on_reverse_breadcrumb,
            };
            this.do_action({
                name: _t("Unit"),
                type: 'ir.actions.client',
                tag: 'onpoint_monitor_monitor_dashboard',
                context: {},
                target: 'main'
            });
        },
        act_print: function(e) {
            var self = this;

            this.do_action({
                name: 'Print Result',
                type: 'ir.actions.act_window',
                res_model: 'onpoint.scada.unit.report',
                view_mode: 'form',
                view_type: 'form',
                views: [[false, 'form']],
                context: {
                    default_unit_id: this.unit_id,
                    default_report_period: $("#rangeDate").val(),
                    default_highchart_options: $("#infile").text(),
                    default_image_base: $('#image_base64_text').text(),
                },
                target: 'new'
            });
        },

        on_reverse_breadcrumb: function() {
            this.updateControlPanel({clear: true});
            web_client.do_push_state({action: this.action_id});
        },
    
    });

    core.action_registry.add('onpoint_scada_unit_chart', OnpointScadaUnitChart);
    return OnpointScadaUnitChart;


});