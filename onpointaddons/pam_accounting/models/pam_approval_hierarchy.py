from odoo import models, fields, api, exceptions, _
from odoo.exceptions import ValidationError
from odoo.osv import expression
from datetime import datetime
from dateutil.relativedelta import relativedelta

class PamApprovalHierarchy(models.Model):
    _name = 'pam.approval.hierarchy'

    approval_type = fields.Selection([
        ('ju', 'Jurnal Umum'),
        ('ap', 'Jurnal Voucher'),
        ('co', 'Jurnal Bayar Kas'),
        ('ci', 'Jurnal Penerimaan Kas'),
        ('bl', 'Jurnal Rekening'),
        ('in', 'Jurnal Instalasi dan Kimia'),
        ('aj', 'Jurnal Penyesuaian')
    ], default='ju', index=True, required=True)
    
    line_ids = fields.One2many('pam.approval.hierarchy.line', 'approval_hierarchy_id')

class PamApprovalHierarchyLine(models.Model):
    _name = 'pam.approval.hierarchy.line'

    approval_hierarchy_id = fields.Many2one('pam.approval.hierarchy')
    department_id = fields.Many2one('hr.department', required=True, string='Department', index=True)
    job_id = fields.Many2one('hr.job', index=True, required=True)
    sequence = fields.Char(string='Urutan', required=True)

    @api.onchange('department_id')
    def _onchange_department(self):
        if self.department_id:
            domain = [('department_id', '=', self.department_id.id)]
        else:
            domain = [('department_id', '=', False)]

        return {'domain': {'job_id': domain}}