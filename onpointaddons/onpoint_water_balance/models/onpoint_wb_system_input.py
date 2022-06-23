from odoo import fields, models, api
from calendar import monthrange
from datetime import datetime


class WaterBalanceSystemInput(models.Model):
    _name = 'onpoint.water.balance.system.input'
    _description = 'Water Balance System Input'

    name = fields.Char()
    water_balance_id = fields.Many2one('onpoint.water.balance', ondelete='cascade', index=True)
    wtp_id = fields.Many2one('onpoint.wtp', string='WTP', index=True)
    zone_id = fields.Many2one('onpoint.zone', string='Zone', index=True)
    dma_id = fields.Many2one('onpoint.dma', string='DMA', index=True)
    quantity = fields.Float()
    error_margin = fields.Float()

    # TODO this function will fetch system input from other data
    def get_system_input(self):
        wb_id = self.water_balance_id
        # s_input = self.env[]

        year = wb_id.year
        month = wb_id.period
        start_date = datetime(year, month, 1)
        end_date = datetime(year, month, monthrange(year, month)[1])

