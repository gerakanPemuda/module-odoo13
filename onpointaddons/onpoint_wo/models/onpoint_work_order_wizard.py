from odoo import models, fields, api
from datetime import datetime
from dateutil.relativedelta import relativedelta


class OnpointWorkOrderWizard(models.TransientModel):
    _name = 'onpoint.work.order.wizard'
    _inherit = ['image.mixin']

    wo_id = fields.Many2one('onpoint.work.order')
    state_from = fields.Selection([
        ('draft', 'Draf'),
        ('submit', 'Submit'),
        ('confirm', 'Confirm'),
        ('en_route', 'En Route'),
        ('in_progress', 'In Progress'),
        ('pending', 'Pending'),
        ('complete', 'Complete'),
    ], 'State From', default='draft')
    state_to = fields.Selection([
        ('draft', 'Draf'),
        ('submit', 'Submit'),
        ('confirm', 'Confirm'),
        ('en_route', 'En Route'),
        ('in_progress', 'In Progress'),
        ('pending', 'Pending'),
        ('complete', 'Complete'),
    ], 'State To', default='draft')
    remark = fields.Text('Remark')

    def to_save(self):
        line_ids = self.wo_id.line_ids
        for line in line_ids:
            line.create({
                'image_1920': self.image_1920,
                'remark': self.remark
            })
