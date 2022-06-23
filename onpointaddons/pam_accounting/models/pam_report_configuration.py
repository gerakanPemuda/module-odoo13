from odoo import models, fields, api


class PamReportConfiguration(models.Model):
    _name = 'pam.report.configuration'
    _rec_name = 'report_type_id'

    report_type_id = fields.Many2one('pam.report.type', index=True, string='Tipe Report', required=True)    
    line_ids = fields.One2many('pam.report.configuration.line', 'report_id')


class PamReportConfigurationLine(models.Model):
    _name = 'pam.report.configuration.line'

    report_id = fields.Many2one('pam.report.configuration', index=True, ondelete='cascade')
    group_id = fields.Many2one('pam.report.type.line', index=True, string='Grup', required=True, domain="[('report_id.id', '=', parent.report_type_id)]")
    name = fields.Char(index=True, string='Nama', required=True)
    sequence = fields.Integer(string='Urutan', required=True)
    detail_ids = fields.One2many('pam.report.configuration.detail', 'report_line_id')


class PamReportConfigurationDetail(models.Model):
    _name = 'pam.report.configuration.detail'

    report_line_id = fields.Many2one('pam.report.configuration.line', index=True, ondelete='cascade')
    coa_id = fields.Many2one('pam.coa', index=True, string='Kode Akun', required=True)
    coa_name = fields.Char('pam.coa', related='coa_id.name')
    coa_type = fields.Selection([
        ('debit', 'Debit'),
        ('credit', 'Credit'),
        ('dc', 'Debit - Credit'),
        ('cd', 'Credit - Debit')
    ], default='dc')
