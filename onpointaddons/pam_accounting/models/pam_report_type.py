from odoo import models, fields, api


class PamReportType(models.Model):
    _name = 'pam.report.type'

    name = fields.Char(index=True, string='Nama', required=True)
    code = fields.Char(index=True, string='Kode', required=True)
    line_ids = fields.One2many('pam.report.type.line', 'report_id')
    ttd_ids = fields.One2many('pam.report.type.ttd', 'report_id')


class PamReportTypeLine(models.Model):
    _name = 'pam.report.type.line'

    report_id = fields.Many2one('pam.report.type', index=True, ondelete='cascade')
    name = fields.Char(index=True, string='Nama', required=True)
    code = fields.Char(index=True, string='Kode', required=True)
    sequence = fields.Integer(index=True, string='Urutan', required=True)
    is_show = fields.Boolean(default=True, string='Tampilkan')
    coa_type = fields.Selection([
        ('debit', 'Debit'),
        ('credit', 'Credit')
    ], default='debit')


class PamReportTypeTtd(models.Model):
    _name = 'pam.report.type.ttd'

    report_id = fields.Many2one('pam.report.type')
    code = fields.Char(string='Kode Bagian')
    name = fields.Char(string='Nama Bagian')
    position = fields.Char(string='Jabatan')
    name_ttd = fields.Char(string='Nama Penanda Tangan')