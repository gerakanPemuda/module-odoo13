from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import datetime
from dateutil.relativedelta import relativedelta


class PamReportMonth(models.Model):
    _name = 'pam.report.month'

    report_type_id = fields.Many2one('pam.report.configuration', string='Tipe Report')
    line_ids = fields.One2many('pam.report.month.line', 'report_month_id')

    @api.onchange('report_type_id')
    def onchange_transaction_id(self):
        if self.report_type_id:
            report = self.env['pam.report.configuration'].search([('id','=', self.report_type_id.id)])
            report_lines = self.env['pam.report.configuration.line'].search([('report_id','=',report.id)])
            line_ids = []
            for line in report_lines:
                # raise ValidationError(_("%s")%(line.item_id.id))
                vals = {
                    'name': line.name
                    }

                row = (0, 0, vals)
                line_ids.append(row)


            self.update({
                'line_ids': line_ids
                })
        else:
            self.update({
                'line_ids': []
                })


class PamReportMonthLine(models.Model):
    _name = 'pam.report.month.line'

    report_month_id = fields.Many2one('pam.report.month')
    name = fields.Char(string='Nama')
    month_1 = fields.Float(string='Januari', default=0)
    month_2 = fields.Float(string='Februari', default=0)
    month_3 = fields.Float(string='Maret', default=0)
    month_4 = fields.Float(string='April', default=0)
    month_5 = fields.Float(string='Mei', default=0)
    month_6 = fields.Float(string='Juni', default=0)
    month_7 = fields.Float(string='Juli', default=0)
    month_8 = fields.Float(string='Agustus', default=0)
    month_9 = fields.Float(string='September', default=0)
    month_10 = fields.Float(string='Oktober', default=0)
    month_11 = fields.Float(string='November', default=0)
    month_12 = fields.Float(string='Desember', default=0)