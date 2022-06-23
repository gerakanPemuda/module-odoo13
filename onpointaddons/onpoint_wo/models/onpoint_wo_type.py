from odoo import models, fields, api
from datetime import datetime
from dateutil.relativedelta import relativedelta


class OnpointWoType(models.Model):
    _name = 'onpoint.wo.type'
    _inherit = 'mail.thread'

    name = fields.Char('Name', required=True)
    department_id = fields.Many2one('hr.department', index=True, string='Department', required=True)
    pic_id = fields.Many2one('hr.employee', domain="[('department_id', '=', department_id)]", string='PIC', required=True)
    work_time = fields.Integer('Work Time', required=True)
    uom = fields.Selection([
        ('minute', 'Minute'),
        ('hour', 'Hour'),
        ('day', 'Day'),
        ('month', 'Month'),
    ], string='Unit', required=True)
    line_ids = fields.One2many('onpoint.wo.type.line', 'wo_type_id')
    checklist_ids = fields.One2many('onpoint.wo.type.checklist', 'wo_type_id')


class OnpointWoTypeLine(models.Model):
    _name = 'onpoint.wo.type.line'

    wo_type_id = fields.Many2one('onpoint.wo.type')
    employee_id = fields.Many2one('hr.employee', string='Employee', required=True)
    state = fields.Selection([
        ('available', 'Available'),
        ('not_available', 'Not Available')
    ], default='available', str='State')


class OnpointWoTypeChecklist(models.Model):
    _name = 'onpoint.wo.type.checklist'

    wo_type_id = fields.Many2one('onpoint.wo.type')
    name = fields.Char(required=True)

