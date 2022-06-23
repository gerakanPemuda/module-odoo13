from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from odoo.osv import expression
from datetime import datetime
from dateutil.relativedelta import relativedelta



class OnpointWaterBalance(models.Model):
    _name = 'onpoint.water.balance'
    
    def _default_year(self):
        return str(datetime.today().year)

    def _get_years(self):
        current_year = int(self._default_year()) + 1
        min_year = current_year - 2
        results = []
        for year in range(min_year, current_year):
            str_year = str(year)
            results.append((str_year, str_year))
        return results


    name = fields.Char(index=True)
    months = fields.Selection([
        ('01', 'Januari'),
        ('02', 'Februari'),
        ('03', 'Maret'),
        ('04', 'April'),
        ('05', 'Mei'),
        ('06', 'Juni'),
        ('07', 'Juli'),
        ('08', 'Agustus'),
        ('09', 'September'),
        ('10', 'Oktober'),
        ('11', 'November'),
        ('12', 'Desember'),
    ], default='01')
    years = fields.Selection(_get_years, string='Tahun', default=_default_year)

    line_ids = fields.One2many('onpoint.water.balance.line', 'water_balance_id')

    @api.model
    def create(self, vals):
        name = str(vals['years']) + str(vals['months'])

        vals.update({
            'name': name
        })
        res = super(OnpointWaterBalance, self).create(vals)
        return res



class OnpointWaterBalanceLine(models.Model):
    _name = 'onpoint.water.balance.line'
    

    water_balance_id  = fields.Many2one('onpoint.water.balance', required=True, index=True, ondelete='cascade')
    logger_id = fields.Many2one('onpoint.logger', string='Logger', required=True, index=True)
    logger_dma_name = fields.Char('onpoint.logger', related='logger_id.dma_id.name')
    diameter = fields.Integer(string='Diameter')
    q_inlet = fields.Integer(required=True, default=0)
    q_outlet = fields.Integer(required=True, default=0)
    customer = fields.Integer(required=True, default=0)
    nrw = fields.Integer(string='NRW', compute='_compute_nrw')
    nrw_percentage = fields.Integer(string='NRW %', compute='_compute_nrw')
    nrw_state = fields.Char(compute='_compute_nrw')
    level_follow_up = fields.Selection([
        ('A', 'A'),
        ('B', 'B'),
        ('C', 'C'),
        ('D', 'D')
    ], default='A')
    mnf = fields.Float(required=True)
    dma_verification = fields.Boolean(string='DMA Boundary Verification')
    pipe_rehab = fields.Boolean(string='Pipe Rehab')
    dma_meter_verification = fields.Boolean(string='DMA Meter Verification')
    alc = fields.Boolean(string='ALC')


    @api.one
    @api.depends('q_inlet', 'q_outlet')
    def _compute_nrw(self):
        if self.q_inlet != 0:
            self.nrw = self.q_inlet - self.q_outlet
            self.nrw_percentage = ((self.q_inlet - self.q_outlet)/self.q_inlet) * 100
            if self.nrw_percentage < 0 or self.nrw_percentage >= 50:
                self.nrw_state = 'danger'
            elif self.nrw_percentage >= 20 and self.nrw_percentage < 50:
                self.nrw_state = 'warning'
            else:
                self.nrw_state = 'normal' 
        else:
            self.nrw = 0
            self.nrw_percentage = 0
            self.nrw_state = 'normal'