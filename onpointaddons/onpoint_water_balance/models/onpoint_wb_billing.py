from odoo import fields, models, api


class WaterBalanceBilling(models.Model):
    _name = 'onpoint.water.balance.billing'
    _description = 'Description'

    name = fields.Char(string='Customer Name')
    water_balance_id = fields.Many2one('onpoint.water.balance', ondelete='cascade', index=True)
    customer_id = fields.Char(string='Customer ID', index=True)
    quantity = fields.Float(string='Usage Quantity')
    uom = fields.Char(string='UoM')
    date = fields.Date(string='Billing Date')
    print_date = fields.Date(string='Print Date')
    note = fields.Char(string='Note', size=256)

