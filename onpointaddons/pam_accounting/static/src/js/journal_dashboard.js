odoo.define('pam_accounting.journal_dashboard', function (require) {
    "use strict";
    
//    var ControlPanelMixin = require('web.ControlPanelMixin');
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
    

    var JournalDashboard = Widget.extend(ActionMixin, {
        hasControlPanel: true,
        template: "JournalDashboardMain",
        events: {
            'click #link-ju': 'act_ju',
            'click #link-ap': 'act_ap',
            'click #link-co': 'act_co',
            'click #link-ci': 'act_ci',
            'click #link-bl': 'act_bl',
            'click #link-in': 'act_in',
            'click #link-aj': 'act_aj',
        },
        init: function(parent, context) {
            this._super(parent, context);
            this.action_id = context.id;
            this.journal = false;
            this._super(parent,context);
        },
        start: function() {
            var self = this;
            for(var i in self.breadcrumbs){
                self.breadcrumbs[i].title = "Dashboard";
            }
            self.updateControlPanel({breadcrumbs: self.breadcrumbs}, {clear: true});
            $(".o_control_panel").addClass("o_hidden");

            self.get_data();
        },
        get_data: function() {

            var self = this;
            // $('.o_hr_dashboard').html(QWeb.render('JournalDashboardContent', {widget: self}));


            rpc.query({
                model: 'pam.dashboard.accounting',
                method: 'get_data',
                args: []
            })
            .then(function(result){
                self.journal =  result;

                if(result){
                    $('.o_hr_dashboard').html(QWeb.render('JournalDashboardContent', {widget: self}));

                    self.preview_journal_chart();

                }
                else{

                    // $('.o_hr_dashboard').html(QWeb.render('JournalDashboardWarning', {widget: self}));
                    return;
                }
            });

        },
        preview_journal_chart: function() {
            var self = this


            Highcharts.setOptions({
                lang: {
                  thousandsSep: '.',
                  decimalPoint: ','
              }
            })

            Highcharts.chart('container_journal_chart', {

                chart: {
                    type : 'column'
                },
                title: {
                    text: 'Perbandingan Pendapatan dan Biaya'
                },
                subtitle: {
                    text: 'Th. 2019'
                },

                xAxis: {
                    categories : self.journal['xAxis']
                },
                yAxis: {
                    labels: {
                        format: '{value:,.0f}'
                    }
                },
                series: self.journal['series'],
            });
        },
        act_ju: function(e) {
            this.do_action('pam_accounting.act_pam_journal_gl', {
                'clear_breadcrumbs': true,
            });
        },
        act_ap: function(e) {
            this.do_action('pam_accounting.act_pam_journal_voucher', {
                'clear_breadcrumbs': true,
            });
        },
        act_co: function(e) {
            this.do_action('pam_accounting.act_pam_journal_co', {
                'clear_breadcrumbs': true,
            });
        },
        act_ci: function(e) {
            this.do_action('pam_accounting.act_pam_journal_ci', {
                'clear_breadcrumbs': true,
            });
        },
        act_bl: function(e) {
            this.do_action('pam_accounting.act_pam_journal_bl', {
                'clear_breadcrumbs': true,
            });
        },
        act_in: function(e) {
            this.do_action('pam_accounting.act_pam_journal_in', {
                'clear_breadcrumbs': true,
            });
        },
        act_aj: function(e) {
            this.do_action('pam_accounting.act_pam_journal_aj', {
                'clear_breadcrumbs': true,
            });
        },

    });

    core.action_registry.add('pam_accounting.journal_dashboard', JournalDashboard);
    return JournalDashboard;

});