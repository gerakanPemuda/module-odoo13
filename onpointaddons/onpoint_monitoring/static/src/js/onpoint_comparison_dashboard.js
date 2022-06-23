odoo.define('onpoint_monitoring.comparison_dashboard', function (require) {
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
    

    var OnpointComparisonDashboard = Widget.extend(ControlPanelMixin, {
        template: "ComparisonDashboardMain",
        events: {
            'change #option_comparison': 'change_option',
            'click #btn_refresh': 'act_refresh_chart'
        },
        init: function(parent, context) {
            this._super(parent, context);
            this.action_id = context.id;
            this.comparison_id = context.context['comparison_id'];
            this.comparison = false;
            this.selected_option = 'all';
            this.selected_period = 'hour';
            this._super(parent,context);
    
        },
        start: function() {
            var self = this;
            for(var i in self.breadcrumbs){
                self.breadcrumbs[i].title = "Dashboard";
            }
            self.update_control_panel({breadcrumbs: self.breadcrumbs}, {clear: true});
            
            var today = new Date();
            var previous = new Date();
            previous.setDate(today.getDate() - 3);
            var start_date = previous.getDate() + '/' + (previous.getMonth()+1) + "/" + previous.getFullYear();
            var end_date = today.getDate() + '/' + (today.getMonth()+1) + "/" + today.getFullYear();
            var rangeDate = start_date + ' - ' + end_date;
            var option = self.selected_option;
            var period = self.selected_period;

            self.get_comparison_data(rangeDate, option, period);

        },   
        get_comparison_data: function(rangeDate, option, period) {

            var self = this;
            rpc.query({
                model: 'onpoint.comparison',
                method: 'get_data',
                args: [self.comparison_id, rangeDate, option, period]
            })
            .then(function(result){
                self.comparison =  result[0];

                if(result){
                    $('.o_hr_dashboard').html(QWeb.render('ComparisonDashboardContent', {widget: self}));                

                    var picker = new Lightpick({ 
                        field: document.getElementById('rangeDate'),
                        singleDate: false
                    })

                    if (rangeDate == "") {
                        picker.setDateRange(moment().add(-7, 'day'), new Date());
                    }
                    else {
                        $("#rangeDate").val(rangeDate);
                    }


                    $('div.div_option select').val(self.comparison.selected_option);
                    $('div.div_period select').val(self.comparison.selected_period);

                    self.change_option();

                    self.preview_comparison_chart();

                }
                else{
                    $('.o_hr_dashboard').html(QWeb.render('ComparisonDashboardWarning', {widget: self}));
                    return;
                }
            });

        },
        preview_comparison_chart: function() {
            var self = this

            Highcharts.chart('container_comparison_chart', {

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
                    type: 'datetime'
                },
            
                yAxis: self.comparison['yAxis'],
                
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

                series: self.comparison['series'],
            
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
        change_option: function() {
            var self = this;
            if ($("#option_comparison").val() == 'all') {
                $('#period_comparison').hide();
            }
            else {
                $('#period_comparison').show();
            }
        },   
        act_refresh_chart: function() {
            var self = this;
            self.get_comparison_data($("#rangeDate").val(), $("#option_comparison").val(), $("#period_comparison").val());
        },
        on_reverse_breadcrumb: function() {
            this.update_control_panel({clear: true});
            web_client.do_push_state({action: this.action_id});
        },
    
    });

    core.action_registry.add('onpoint_monitoring.comparison_dashboard', OnpointComparisonDashboard);
    return OnpointComparisonDashboard;


});