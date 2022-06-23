from odoo import models, fields, api
from datetime import datetime
from dateutil.relativedelta import relativedelta


class OnpointWoCommentWizard(models.TransientModel):
    _name = 'onpoint.wo.comment.wizard'

    wo_line_id = fields.Many2one('onpoint.work.order.line')
    comment = fields.Text('Comment')

    def to_save(self):
        self.create({
                'wo_line_id': self.wo_line_id.id,
                'comment': self.comment
            })
