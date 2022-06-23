from odoo import models, fields, api
from datetime import datetime, timedelta


class OnpointDmaBilling(models.Model):
    _name = 'onpoint.dma.billing'

    def _default_year(self):
        return str(datetime.today().year)

    months = fields.Selection([
        ('01', 'January'),
        ('02', 'February'),
        ('03', 'March'),
        ('04', 'April'),
        ('05', 'May'),
        ('06', 'June'),
        ('07', 'July'),
        ('08', 'August'),
        ('09', 'September'),
        ('10', 'October'),
        ('11', 'November'),
        ('12', 'December'),
    ], default='01', required=True)
    years = fields.Char(default=_default_year, required=True)
    name = fields.Char(compute='_compute_name')
    line_ids = fields.One2many('onpoint.dma.billing.line', 'dma_billing_id')

    @api.depends('years', 'months')
    def _compute_name(self):
        self.name = self.years + self.months

    def act_get_dmas(self):
        if self.months:
            data = []

            dmas = self.env['onpoint.dma'].search([])
            for dma in dmas:
                vals = {
                    'dma_id': dma.id,
                }
                row = (0, 0, vals)
                data.append(row)

            self.line_ids = [(6, 0, [])]

            self.write({
                'line_ids': data
            })


class OnpointDmaBillingLine(models.Model):
    _name = 'onpoint.dma.billing.line'

    dma_billing_id = fields.Many2one('onpoint.dma.billing', required=True, string='DMA Billing', ondelete='cascade', index=True)
    dma_id = fields.Many2one('onpoint.dma', required=True, string='DMA', ondelete='cascade', index=True)
    customer_count = fields.Integer(string='Customer', default=0)
    consumption = fields.Float(string='Consumption', default=0)
