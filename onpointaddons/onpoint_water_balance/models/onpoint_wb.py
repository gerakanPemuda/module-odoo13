from odoo import fields, models, api
from datetime import datetime, date
import calendar
import numpy


class WaterBalanceAbstract(models.AbstractModel):
    _name = 'onpoint.water.balance.abstract'
    _description = 'Onpoint Water Balance Abstract Model'

    name = fields.Char()
    year_select = fields.Selection(selection=[(str(num), str(num)) for num in range(datetime.now().year - 10, datetime.now().year + 10)],
                                   string='Year',
                                   default=lambda self: str(fields.Datetime.now().year))
    year = fields.Integer(compute='_compute_year', store=True)
    period = fields.Selection(selection=[('1', 'January'),
                                         ('2', 'February'),
                                         ('3', 'March'),
                                         ('4', 'April'),
                                         ('5', 'May'),
                                         ('6', 'June'),
                                         ('7', 'July'),
                                         ('8', 'August'),
                                         ('9', 'September'),
                                         ('10', 'October'),
                                         ('11', 'November'),
                                         ('12', 'December')],
                              string='Period',
                              default=lambda self: str(fields.Datetime.now().month))
    period_duration = fields.Integer(compute='_compute_period_duration', store=True)

    system_input_line_ids = fields.One2many('onpoint.water.balance.system.input', 'water_balance_id', string='System Input')
    system_input_error_margin = fields.Float(compute='_compute_system_input_best_estimate', store=True, string='Error Margin')
    system_input_minimum = fields.Float(compute='_compute_system_input_best_estimate', store=True, string='Minimum')
    system_input_maximum = fields.Float(compute='_compute_system_input_best_estimate', store=True, string='Maximum')
    system_input_best_estimate = fields.Float(compute='_compute_system_input_best_estimate', store=True, string='Best Estimate')

    billed_meter_lines = fields.One2many('onpoint.water.balance.billed.meter.lines', 'water_balance_id')
    billed_meter_bulk_water = fields.Float(string='Bulk Water Supply (Export)')
    billed_meter_consumption_total = fields.Float(compute='_compute_billed_meter_consumption_total', store=True,
                                                  string='Billed Metered Consumption')
    billed_unmeter_lines = fields.One2many('onpoint.water.balance.billed.unmeter.lines', 'water_balance_id')
    billed_unmeter_bulk_water = fields.Float(string='Bulk Water Supply(Export)')
    billed_unmeter_consumption_total = fields.Float(compute='_compute_billed_meter_consumption_total', store=True,
                                                    string='Billed Unmetered Consumption')

    unbilled_meter_lines = fields.One2many('onpoint.water.balance.unbilled.meter.lines', 'water_balance_id')
    unbilled_meter_bulk_water = fields.Float(string='Bulk Water Supply(Export)')
    unbilled_meter_consumption_total = fields.Float(compute='_compute_unbilled_meter_consumption_total', store=True)
    unbilled_unmeter_lines = fields.One2many('onpoint.water.balance.unbilled.unmeter.lines', 'water_balance_id')
    unbilled_unmeter_error_margin = fields.Float(compute='_compute_unbilled_unmeter_best_estimate', store=True,
                                                 string='Error Margin')
    unbilled_unmeter_minimum = fields.Float(compute='_compute_unbilled_unmeter_best_estimate', store=True,
                                            string="Minimum")
    unbilled_unmeter_maximum = fields.Float(compute='_compute_unbilled_unmeter_best_estimate', store=True,
                                            string='Maximum')
    unbilled_unmeter_best_estimate = fields.Float(compute='_compute_unbilled_unmeter_best_estimate', store=True,
                                                  string='Best Estimate')

    unauth_consumption_illegal_domestic_estimate = fields.Float(string='Estimate Number')
    unauth_consumption_illegal_domestic_error_margin = fields.Float(string='Error Margin')
    unauth_consumption_illegal_domestic_person_per_house = fields.Float(string='Person Per House')
    unauth_consumption_illegal_domestic_person_consumption = fields.Float(string='Consumption')
    unauth_consumption_illegal_domestic_total = fields.Float(compute='_compute_unauth_consumption_illegal_domestic_total',
                                                             string='Total')
    unauth_consumption_illegal_other_estimate = fields.Float(string='Estimate Number')
    unauth_consumption_illegal_other_error_margin = fields.Float(string='Error Margin')
    unauth_consumption_illegal_other_connection_consumption = fields.Float(string='Consumption')
    unauth_consumption_illegal_other_total = fields.Float(compute='_compute_unauth_consumption_illegal_other_total', string='Total')
    unauth_consumption_illegal_tamper_estimate = fields.Float(string='Estimate Number')
    unauth_consumption_illegal_tamper_error_margin = fields.Float(string='Error Margin')
    unauth_consumption_illegal_tamper_customer_consumption = fields.Float(string='Consumption')
    unauth_consumption_illegal_tamper_total = fields.Float(compute='_compute_unauth_consumption_illegal_tamper_total',
                                                           string='Total')
    unauth_consumption_illegal_lines_ids = fields.One2many('onpoint.water.balance.unauthorized.consumption.lines', 'water_balance_id')
    unauth_consumption_illegal_lines_error_margin = fields.Float(compute='_compute_unauth_consumption_illegal_lines_estimate', store=True, string='Error Margin')
    unauth_consumption_illegal_lines_minimum = fields.Float(compute='_compute_unauth_consumption_illegal_lines_estimate',
                                                            store=True, string='Minimum')
    unauth_consumption_illegal_lines_maximum = fields.Float(compute='_compute_unauth_consumption_illegal_lines_estimate',
                                                            store=True, string='Maximum')
    unauth_consumption_illegal_lines_estimate = fields.Float(compute='_compute_unauth_consumption_illegal_lines_estimate',
                                                             store=True,
                                                             string='Best Estimate')

    meter_error_billed_meter_manual = fields.Boolean(default=False, string='Manual Entry',
                                                     help="Select for manual entering of volumes and under-registration of different meter or customer types.")
    meter_error_billed_meter_quantity = fields.Float(compute='_compute_meter_error_billed_meter_quantity', store=True, string='Total')
    meter_error_billed_meter_under_registration = fields.Float(string='Meter under-registration')
    meter_error_billed_meter_total = fields.Float(compute='_compute_meter_error_billed_meter_total', store=True, string='Total')
    meter_error_billed_meter_error_margin = fields.Float(string='Error Margin')
    meter_error_billed_meter_lines = fields.One2many('onpoint.water.balance.meter.error.billed.lines', 'water_balance_id')
    meter_error_bulk_supply_quantity = fields.Float(compute='_compute_meter_error_bulk_supply_quantity', store=True, string='Total')
    meter_error_bulk_supply_under_registration = fields.Float(string='Meter under-registration')
    meter_error_bulk_supply_total = fields.Float(compute='_compute_meter_error_bulk_supply_total', store=True, string='Total')
    meter_error_bulk_supply_error_margin = fields.Float(string='Error Margin')

    meter_error_unmeter_consumption_quantity = fields.Float(compute='_compute_meter_error_unmeter_consumption_quantity', store=True, string='Total')
    meter_error_unmeter_consumption_under_registration = fields.Float(string='Meter under-registration')
    meter_error_unmeter_consumption_total = fields.Float(compute='_compute_meter_error_unmeter_consumption_total', store=True, string='Total')
    meter_error_unmeter_consumption_error_margin = fields.Float(string='Error Margin')
    meter_error_corrupt_quantity = fields.Float(compute='_compute_meter_error_corrupt_quantity', store=True,  string='Total')
    meter_error_corrupt_under_reading = fields.Float(string='Estimated of under-reading')
    meter_error_corrupt_total = fields.Float(compute='_compute_meter_error_corrupt_total', store=True,  string='Total')
    meter_error_corrupt_error_margin = fields.Float(string='Error Margin')
    meter_error_data_handling_total = fields.Float(string='Total')
    meter_error_data_handling_error_margin = fields.Float(string='Error Margin')
    meter_error_error_margin = fields.Float(compute='_compute_meter_error_best_estimate', store=True, string='Error Margin')
    meter_error_minimum = fields.Float(compute='_compute_meter_error_best_estimate', store=True, string='Minimum')
    meter_error_maximum = fields.Float(compute='_compute_meter_error_best_estimate', store=True, string='Maximum')
    meter_error_best_estimate = fields.Float(compute='_compute_meter_error_best_estimate', store=True, string='Best Estimate')

    network_distribution_lines = fields.One2many('onpoint.water.balance.network.distribution.lines', 'water_balance_id')
    network_distribution_total = fields.Float(compute='_compute_network_distribution_total', store=True, string='True')
    network_distribution_underestimation = fields.Float(string='Possible underestimation')
    network_distribution_length_minimum = fields.Float(compute='_compute_network_distribution_total', store=True, string='Minimum')
    network_distribution_length_maximum = fields.Float(compute='_compute_network_distribution_total', store=True, string='Maxmium')
    network_distribution_length_best_estimate = fields.Float(compute='_compute_network_distribution_total', store=True, string='Best Estimate')
    network_service_connection_register_number = fields.Float(string='Number')
    network_service_connection_register_error_margin = fields.Float(string='Error Margin')
    network_service_connection_inactive_number = fields.Float(string='Number')
    network_service_connection_inactive_error_margin = fields.Float(string='Error Margin')
    network_service_connection_illegal_estimate = fields.Float(compute='_compute_network_service_connection_illegal_estimate', store=True, string='Number')
    network_service_connection_illegal_error_margin = fields.Float(compute='_compute_network_service_connection_illegal_estimate', store=True, string='Error Margin')
    network_service_connection_error_margin = fields.Float(compute='_compute_network_service_connection_best_estimate', store=True, string='Error Margin')
    network_service_connection_minimum = fields.Float(compute='_compute_network_service_connection_best_estimate', store=True, string='Minimum')
    network_service_connection_maximum = fields.Float(compute='_compute_network_service_connection_best_estimate', store=True, string='Maximum')
    network_service_connection_best_estimate = fields.Float(compute='_compute_network_service_connection_best_estimate', store=True, string='Best Estimate')
    network_service_connection_property_number = fields.Float(string='Number')
    network_service_connection_property_error_margin = fields.Float(string='Error Margin')
    network_service_connection_property_total_number = fields.Float(compute='_compute_network_service_connection_property_total_number', store=True, string='Number')
    network_service_connection_property_total_error_margin = fields.Float(compute='_compute_network_service_connection_property_total_number', store=True, string='Number')

    pressure_lines = fields.One2many('onpoint.water.balance.pressure.lines', 'water_balance_id')
    pressure_error_margin = fields.Float(string='Error Margin')
    pressure_minimum = fields.Float(compute='_compute_pressure_best_estimate', store=True, string='Minimum')
    pressure_maximum = fields.Float(compute='_compute_pressure_best_estimate', store=True, string='Maximum')
    pressure_best_estimate = fields.Float(compute='_compute_pressure_best_estimate', store=True)

    intermittent_lines = fields.One2many('onpoint.water.balance.intermittent.lines', 'water_balance_id')
    intermittent_error_margin = fields.Float(string='Error margin')
    intermittent_minimum = fields.Float(compute='_compute_intermittent_best_estimate', store=True, string='Minimum')
    intermittent_maximum = fields.Float(compute='_compute_intermittent_best_estimate', store=True, string='Maximum')
    intermittent_best_estimate = fields.Float(compute='_compute_intermittent_best_estimate', store=True, string='Best Estimate')

    finance_tariff_average = fields.Float(string='per m3')
    finance_tariff_currency = fields.Many2one('res.currency', string='Currency')
    finance_variable_cost = fields.Float(string='per m3')
    finance_unbilled_meter_consumption = fields.Float(compute='_compute_finance_unbilled_meter_consumption', store=True, string='Annual Value')
    finance_unbilled_meter_consumption_is_variable = fields.Boolean(default=False)
    finance_unbilled_unmeter_consumption = fields.Float(compute='_compute_finance_unbilled_meter_consumption', store=True, string='Annual Value')
    finance_unbilled_unmeter_consumption_is_variable = fields.Boolean(default=False)
    finance_unbilled_commercial_losses = fields.Float(compute='_compute_finance_unbilled_meter_consumption', store=True, string='Annual Value')
    finance_unbilled_commercial_losses_is_variable = fields.Boolean(default=False)
    finance_unbilled_physical_losses = fields.Float(compute='_compute_finance_unbilled_meter_consumption', store=True, string='Annual Value')
    finance_unbilled_physical_losses_is_variable = fields.Boolean(default=False)
    finance_total_value = fields.Float(compute='_compute_finance_unbilled_meter_consumption', store=True, string='Total Value of NRW')
    finance_annual_operating_cost = fields.Float(string='Annual Operating Cost',
                                                 help='Annual Operating Cost (without Depreciation)')

    @api.depends('year_select')
    def _compute_year(self):
        if self.year_select:
            self.year = int(self.year_select)

    @api.depends('period', 'year')
    def _compute_period_duration(self):
        if self.period and self.year:
            eom = calendar.monthrange(self.year, int(self.period))[1]
            date_som = date(int(self.year), int(self.period), 1)
            date_eom = date(int(self.year), int(self.period), eom)
            period_duration = abs(date_eom - date_som).days
            self.period_duration = period_duration

    """system input computation"""
    @api.depends('system_input_line_ids')
    def _compute_system_input_best_estimate(self):
        total = 0.0
        square_total = 0.0
        for line in self.system_input_line_ids:
            square_total += numpy.square(line.quantity * line.error_margin / 1.96)
            total += line.quantity
        error_margin = numpy.sqrt(square_total) * 1.96 / total if total > 0.0 else 0.0
        minimum = total * (1 - error_margin)
        maximum = total * (1 + error_margin)
        self.system_input_error_margin = error_margin
        self.system_input_best_estimate = total
        self.system_input_minimum = minimum
        self.system_input_maximum = maximum

    """billed consumption"""
    @api.depends('billed_meter_bulk_water',
                 'billed_unmeter_bulk_water',
                 'billed_meter_lines',
                 'billed_unmeter_lines')
    def _compute_billed_meter_consumption_total(self):
        meter_bulk = self.billed_meter_bulk_water if self.billed_meter_bulk_water else 0.0
        unmeter_bulk = self.billed_unmeter_bulk_water if self.billed_unmeter_bulk_water else 0.0
        total_meter = total_unmeter = 0.0
        for line in self.billed_meter_lines:
            total_meter += line.quantity
        for line in self.billed_unmeter_lines:
            total_unmeter += line.quantity
        total_meter += meter_bulk
        total_unmeter += unmeter_bulk
        self.billed_meter_consumption_total = total_meter
        self.billed_unmeter_consumption_total = total_unmeter

    """unbilled consumption"""
    @api.depends('unbilled_meter_lines',
                 'unbilled_meter_bulk_water')
    def _compute_unbilled_meter_consumption_total(self):
        total = 0.0
        for line in self.unbilled_meter_lines:
            total += line.quantity
        bulk_water = self.unbilled_meter_bulk_water if self.unbilled_meter_bulk_water else 0.0
        self.unbilled_meter_consumption_total = total + bulk_water

    @api.depends('unbilled_unmeter_lines')
    def _compute_unbilled_unmeter_best_estimate(self):
        total = 0.0
        square_total = 0.0
        for line in self.unbilled_unmeter_lines:
            total += line.quantity
            square_total += numpy.square(line.quantity * line.error_margin / 1.96)
        error_margin = numpy.sqrt(square_total) * 1.96 / total if total > 0.0 else 0.0
        minimum = total * (1 - error_margin)
        maximum = total * (1 + error_margin)
        self.unbilled_unmeter_error_margin = error_margin
        self.unbilled_unmeter_minimum = minimum
        self.unbilled_unmeter_maximum = maximum
        self.unbilled_unmeter_best_estimate = total

    """unauthorized consumption"""
    @api.depends('unauth_consumption_illegal_domestic_estimate',
                 'unauth_consumption_illegal_domestic_person_per_house',
                 'unauth_consumption_illegal_domestic_person_consumption')
    def _compute_unauth_consumption_illegal_domestic_total(self):
        est = self.unauth_consumption_illegal_domestic_estimate
        pph = self.unauth_consumption_illegal_domestic_person_per_house
        con = self.unauth_consumption_illegal_domestic_person_consumption
        period = self.period_duration
        self.unauth_consumption_illegal_domestic_total = est * pph * con * period / 1000

    @api.depends('unauth_consumption_illegal_other_estimate',
                 'unauth_consumption_illegal_other_connection_consumption',
                 'period_duration')
    def _compute_unauth_consumption_illegal_other_total(self):
        est = self.unauth_consumption_illegal_other_estimate
        con = self.unauth_consumption_illegal_other_connection_consumption
        period = self.period_duration
        self.unauth_consumption_illegal_other_total = est * con * period / 1000

    @api.depends('unauth_consumption_illegal_tamper_estimate',
                 'unauth_consumption_illegal_tamper_customer_consumption',
                 'period_duration')
    def _compute_unauth_consumption_illegal_tamper_total(self):
        est = self.unauth_consumption_illegal_tamper_estimate
        con = self.unauth_consumption_illegal_tamper_customer_consumption
        period = self.period_duration
        self.unauth_consumption_illegal_tamper_total = est * con * period / 1000

    @api.depends('unauth_consumption_illegal_lines_ids',
                 'unauth_consumption_illegal_domestic_error_margin',
                 'unauth_consumption_illegal_domestic_total',
                 'unauth_consumption_illegal_other_error_margin',
                 'unauth_consumption_illegal_other_total',
                 'unauth_consumption_illegal_tamper_error_margin',
                 'unauth_consumption_illegal_tamper_total',
                 'period_duration')
    def _compute_unauth_consumption_illegal_lines_estimate(self):
        total = self.unauth_consumption_illegal_domestic_total + self.unauth_consumption_illegal_other_total + self.unauth_consumption_illegal_tamper_total
        em_lines = 0.0
        duration = self.period_duration
        em_domestic = numpy.square(self.unauth_consumption_illegal_domestic_error_margin * self.unauth_consumption_illegal_domestic_total / 1.96)
        em_others = numpy.square(self.unauth_consumption_illegal_other_error_margin * self.unauth_consumption_illegal_other_total / 1.96)
        em_tamper = numpy.square(self.unauth_consumption_illegal_tamper_error_margin * self.unauth_consumption_illegal_tamper_total / 1.96)

        for line in self.unauth_consumption_illegal_lines_ids:
            total += line.consumption * duration if line.total else 0.0
            em_lines += numpy.square(line.consumption * line.error_margin / 1.96)
        if total > 0.0:
            error_margin = numpy.sqrt(em_lines + em_domestic + em_others + em_tamper) * 1.96 / total
        else:
            error_margin = 0.0
        minimum = total * (1 - error_margin) if error_margin else 0.0
        maximum = total * (1 + error_margin) if error_margin else 0.0

        self.unauth_consumption_illegal_lines_error_margin = error_margin
        self.unauth_consumption_illegal_lines_minimum = minimum
        self.unauth_consumption_illegal_lines_maximum = maximum
        self.unauth_consumption_illegal_lines_estimate = total

    """meter errors"""
    @api.depends('billed_meter_consumption_total')
    def _compute_meter_error_billed_meter_quantity(self):
        self.meter_error_billed_meter_quantity = self.billed_meter_consumption_total

    @api.depends('meter_error_billed_meter_quantity',
                 'meter_error_billed_meter_under_registration')
    def _compute_meter_error_billed_meter_total(self):
        qty = self.meter_error_billed_meter_quantity
        mur = self.meter_error_billed_meter_under_registration
        total = qty / (1 - mur) - qty
        self.meter_error_billed_meter_total = total

    @api.depends('billed_meter_bulk_water',
                 'unbilled_meter_bulk_water')
    def _compute_meter_error_bulk_supply_quantity(self):
        self.meter_error_bulk_supply_quantity = self.billed_meter_bulk_water + self.unbilled_meter_bulk_water

    @api.depends('meter_error_bulk_supply_quantity',
                 'meter_error_bulk_supply_under_registration')
    def _compute_meter_error_bulk_supply_total(self):
        qty = self.meter_error_bulk_supply_quantity
        mur = self.meter_error_bulk_supply_under_registration
        total = qty / (1 - mur) - qty
        self.meter_error_bulk_supply_total = total

    @api.depends('unbilled_meter_lines')
    def _compute_meter_error_unmeter_consumption_quantity(self):
        total = 0.0
        for line in self.unbilled_meter_lines:
            total += line.quantity
        self.meter_error_unmeter_consumption_quantity = total

    @api.depends('meter_error_unmeter_consumption_quantity',
                 'meter_error_unmeter_consumption_under_registration')
    def _compute_meter_error_unmeter_consumption_total(self):
        qty = self.meter_error_unmeter_consumption_quantity
        mur = self.meter_error_unmeter_consumption_under_registration
        total = qty / (1 - mur) - qty
        self.meter_error_unmeter_consumption_total = total

    @api.depends('billed_meter_consumption_total',
                 'billed_unmeter_consumption_total')
    def _compute_meter_error_corrupt_quantity(self):
        self.meter_error_corrupt_quantity = self.billed_meter_consumption_total + self.billed_unmeter_consumption_total

    @api.depends('meter_error_corrupt_quantity',
                 'meter_error_corrupt_under_reading')
    def _compute_meter_error_corrupt_total(self):
        self.meter_error_corrupt_total = 0.0
        qty = self.meter_error_corrupt_quantity
        mur = self.meter_error_corrupt_under_reading
        total = qty / (1 - mur) - qty
        self.meter_error_corrupt_quantity = total

    def _compute_meter_error_billed_meter_manual(self):
        total = 0.0
        t_err = 0.0
        for l in self.meter_error_billed_meter_lines:
            l_tot = l.quantity / (1 - l.meter_under_registration) - l.quantity
            l_err = numpy.square(l.error_margin * l_tot / 1.96)
            total += l_tot
            t_err += l_err
        return total, t_err

    @api.depends('meter_error_billed_meter_total', 'meter_error_billed_meter_error_margin',
                 'meter_error_bulk_supply_total', 'meter_error_bulk_supply_error_margin',
                 'meter_error_unmeter_consumption_total', 'meter_error_unmeter_consumption_error_margin',
                 'meter_error_corrupt_total', 'meter_error_corrupt_error_margin',
                 'meter_error_data_handling_total', 'meter_error_data_handling_error_margin',
                 'meter_error_billed_meter_manual',
                 'meter_error_billed_meter_lines')
    def _compute_meter_error_best_estimate(self):
        if self.meter_error_billed_meter_manual:
            bm_mt, bm_bm = self._compute_meter_error_billed_meter_manual()
        else:
            bm_mt = self.meter_error_billed_meter_total
            bm_bm = self.meter_error_billed_meter_total * self.meter_error_billed_meter_error_margin / 1.96
        best_estimate = bm_mt + \
                        self.meter_error_bulk_supply_total + \
                        self.meter_error_unmeter_consumption_total + \
                        self.meter_error_corrupt_total + \
                        self.meter_error_data_handling_total
        # Compute error margin from previous totals
        bm_bs = self.meter_error_bulk_supply_total * self.meter_error_bulk_supply_error_margin / 1.96
        bm_uc = self.meter_error_unmeter_consumption_total * self.meter_error_unmeter_consumption_error_margin / 1.96
        bm_cr = self.meter_error_corrupt_total * self.meter_error_corrupt_error_margin / 1.96
        bm_dh = self.meter_error_data_handling_total * self.meter_error_data_handling_error_margin / 1.96
        total_em = bm_bm + bm_bs + bm_uc + bm_cr + bm_dh
        # Final computation
        error_margin = numpy.sqrt(total_em) * 1.96 / best_estimate if best_estimate > 0.0 else 0.0
        self.meter_error_error_margin = error_margin
        self.meter_error_minimum = best_estimate * (1 - error_margin)
        self.meter_error_maximum = best_estimate * (1 + error_margin)
        self.meter_error_best_estimate = best_estimate

    """network"""
    @api.depends('network_distribution_lines')
    def _compute_network_distribution_total(self):
        total = 0.0
        under_estimate = self.network_distribution_underestimation
        for line in self.network_distribution_lines:
            total += float(line.length)
        minimum = total
        maximum = total + under_estimate if under_estimate > 0.0 else total
        self.network_distribution_total = total
        self.network_distribution_length_minimum = total
        self.network_distribution_length_maximum = maximum
        self.network_distribution_length_best_estimate = (minimum + maximum) / 2

    @api.depends('unauth_consumption_illegal_domestic_estimate', 'unauth_consumption_illegal_other_estimate')
    def _compute_network_service_connection_illegal_estimate(self):
        total = self.unauth_consumption_illegal_domestic_estimate + self.unauth_consumption_illegal_other_estimate
        self.network_service_connection_illegal_estimate = total
        self.network_service_connection_illegal_error_margin = self.unauth_consumption_illegal_domestic_error_margin

    @api.depends('network_service_connection_register_number', 'network_service_connection_inactive_number',
                 'network_service_connection_illegal_estimate')
    def _compute_network_service_connection_best_estimate(self):
        reg_num = self.network_service_connection_register_number
        inact = self.network_service_connection_inactive_number
        ill_est = self.network_service_connection_illegal_estimate if self.network_service_connection_illegal_estimate else 0.0
        total = reg_num + inact + ill_est
        self.network_service_connection_best_estimate = total

        sq_reg_number = numpy.square(reg_num * self.network_service_connection_register_error_margin / 1.96)
        sq_inact = numpy.square(inact * self.network_service_connection_inactive_error_margin / 1.96)
        sq_ill_est = numpy.square(ill_est * self.network_service_connection_illegal_error_margin / 1.96)
        if total > 0.0:
            error_margin = numpy.sqrt(sq_reg_number + sq_inact + sq_ill_est) * 1.96 / total
        else:
            error_margin = 0.0
        minimum = total * (1 - error_margin) if total else 0.0
        maximum = total * (1 + error_margin) if total else 0.0
        self.network_service_connection_error_margin = 0.0  # need to replace this with calculation
        self.network_service_connection_minimum = minimum
        self.network_service_connection_maximum = maximum

    @api.depends('network_service_connection_property_number', 'network_service_connection_best_estimate',
                 'network_service_connection_error_margin', 'network_service_connection_property_error_margin')
    def _compute_network_service_connection_property_total_number(self):
        total = self.network_service_connection_property_number * self.network_service_connection_best_estimate / 1000
        err_margin = numpy.square(self.network_service_connection_error_margin) + numpy.square(self.network_service_connection_property_error_margin)
        self.network_service_connection_property_total_number = total
        self.network_service_connection_property_error_margin = err_margin

    """pressure"""
    @api.depends('pressure_lines')
    def _compute_pressure_best_estimate(self):
        total = 0.0
        for line in self.pressure_lines:
            total += (float(line.connection_number) * float(line.daily_average_pressure))
        self.pressure_best_estimate = total
        error_margin = self.pressure_error_margin
        minimum = total * (1 - error_margin) if total > 0.0 else 0.0
        maximum = total * (1 + error_margin) if total > 0.0 else 0.0
        self.pressure_minimum = minimum
        self.pressure_maximum = maximum

    """intermittent supply"""
    @api.depends('intermittent_lines')
    def _compute_intermittent_best_estimate(self):
        total = conn_total = supp_total = 0.0
        for line in self.intermittent_lines:
            total += line.supply_total
            conn_total += float(line.connection_number)
            supp_total += float(line.supply_hours_per_day)
        estimate = total / conn_total / 7 if supp_total > 0 else 24.0
        self.intermittent_best_estimate = estimate
        error_margin = self.intermittent_error_margin if self.intermittent_error_margin else 0.0
        minimum = estimate * (1 - error_margin)
        if estimate == 24.0 or estimate * (1 + error_margin) > 24.0:
            maximum = 24.0
        else:
            maximum = estimate * (1 + error_margin)
        self.intermittent_minimum = minimum
        self.intermittent_maximum = maximum

    """finance data"""
    def _compute_finance_unbilled_meter_consumption(self):
        # TODO Compute finance unbilled meter consumption
        self.finance_unbilled_meter_consumption = 0.0
        self.finance_unbilled_unmeter_consumption = 0.0
        self.finance_unbilled_commercial_losses = 0.0
        self.finance_unbilled_physical_losses = 0.0
        self.finance_total_value = 0.0

    # @api.depends('system_input_best_estimate',
    #              'system_input_error_margin',
    #              'period_duration')
    # def _compute_wb_system_input(self):
    #     raise NotImplementedError

    # @api.depends('billed_meter_consumption_total',
    #              'billed_unmeter_consumption_total',
    #              'period_duration')
    # def _compute_wb_billed_authorized_consumption(self):
    #     raise NotImplementedError


class WaterBalance(models.Model):
    _name = 'onpoint.water.balance'
    _inherit = 'onpoint.water.balance.abstract'

    wb_system_input_daily = fields.Float(compute='_compute_wb_system_input', store=True, string='Volume')
    wb_system_input_daily_error_margin = fields.Float(compute='_compute_wb_system_input', store=True, string='Error Margin')
    wb_system_input_period = fields.Float(compute='_compute_wb_system_input', store=True, string='Volume')
    wb_system_input_period_error_margin = fields.Float(compute='_compute_wb_system_input', store=True, string='Error Margin')
    wb_system_input_yearly = fields.Float(compute='_compute_wb_system_input', store=True, string='Volume')
    wb_system_input_yearly_error_margin = fields.Float(compute='_compute_wb_system_input', store=True, string='Error Margin')

    wb_authorized_consumption_daily = fields.Float(compute='_compute_wb_authorized_consumption', store=True, string='Consumption')
    wb_authorized_consumption_daily_error_margin = fields.Float(compute='_compute_wb_authorized_consumption', store=True, string='Error Margin')
    wb_authorized_consumption_period = fields.Float(compute='_compute_wb_authorized_consumption', store=True, string='Consumption')
    wb_authorized_consumption_period_error_margin = fields.Float(compute='_compute_wb_authorized_consumption', store=True, string='Error Margin')
    wb_authorized_consumption_yearly = fields.Float(compute='_compute_wb_authorized_consumption', store=True, string='Consumption')
    wb_authorized_consumption_yearly_error_margin = fields.Float(compute='_compute_wb_authorized_consumption', store=True, string='Error Margin')

    wb_water_losses_daily = fields.Float(compute='_compute_wb_water_losses', store=True, string='Losses')
    wb_water_losses_daily_error_margin = fields.Float(compute='_compute_wb_water_losses', store=True, string='Error Margin')
    wb_water_losses_period = fields.Float(compute='_compute_wb_billed_meter_consumption', store=True, string='Losses')
    wb_water_losses_period_error_margin = fields.Float(compute='_compute_wb_billed_meter_consumption', store=True, string='Billed Meter Consumption')
    wb_water_losses_yearly = fields.Float(compute='_compute_wb_billed_meter_consumption', store=True, string='Losses')
    wb_water_losses_yearly_error_margin = fields.Float(compute='_compute_wb_billed_meter_consumption', store=True, string='Error Margin')

    wb_billed_authorized_consumption_daily = fields.Float(compute='_compute_wb_billed_authorized_consumption', store=True, string='Consumption')
    wb_billed_authorized_consumption_period = fields.Float(compute='_compute_wb_billed_authorized_consumption', store=True, string='Consumption')
    wb_billed_authorized_consumption_yearly = fields.Float(compute='_compute_wb_billed_authorized_consumption', store=True, string='Consumption')

    wb_billed_meter_consumption_daily = fields.Float(compute='_compute_wb_billed_authorized_consumption', store=True, string='Consumption')
    wb_billed_meter_consumption_period = fields.Float(compute='_compute_wb_billed_authorized_consumption', store=True, string='Consumption')
    wb_billed_meter_consumption_yearly = fields.Float(compute='_compute_wb_billed_authorized_consumption', store=True, string='Consumption')

    wb_billed_unmeter_consumption_daily = fields.Float(compute='_compute_wb_billed_authorized_consumption', store=True, string='Consumption')
    wb_billed_unmeter_consumption_period = fields.Float(compute='_compute_wb_billed_authorized_consumption', store=True, string='Consumption')
    wb_billed_unmeter_consumption_yearly = fields.Float(compute='_compute_wb_billed_authorized_consumption', store=True, string='Consumption')

    wb_revenue_water_daily = fields.Float(compute='_compute_wb_billed_authorized_consumption', store=True, string='Revenue Water')
    wb_revenue_water_period = fields.Float(compute='_compute_wb_billed_authorized_consumption', store=True, string='Revenue Water')
    wb_revenue_water_yearly = fields.Float(compute='_compute_wb_billed_authorized_consumption', store=True, string='Revenue Water')

    wb_unbilled_authorized_consumption_daily = fields.Float(compute='_compute_wb_unbilled_authorized_consumption', store=True, string='Consumption')
    wb_unbilled_authorized_consumption_daily_error_margin = fields.Float(compute='_compute_wb_unbilled_authorized_consumption', store=True, string='Error Margin')
    wb_unbilled_authorized_consumption_period = fields.Float(compute='_compute_wb_unbilled_authorized_consumption', store=True, string='Consumption')
    wb_unbilled_authorized_consumption_period_error_margin = fields.Float(compute='_compute_wb_unbilled_authorized_consumption', store=True, string='Error Margin')
    wb_unbilled_authorized_consumption_yearly = fields.Float(compute='_compute_wb_unbilled_authorized_consumption', store=True, string='Consumption')
    wb_unbilled_authorized_consumption_yearly_error_margin = fields.Float(compute='_compute_wb_unbilled_authorized_consumption', store=True, string='Error Margin')

    wb_unbilled_meter_consumption_daily = fields.Float(compute='_compute_wb_unbilled_authorized_consumption', store=True, string='Consumption')
    wb_unbilled_meter_consumption_period = fields.Float(compute='_compute_wb_unbilled_authorized_consumption', store=True, string='Consumption')
    wb_unbilled_meter_consumption_yearly = fields.Float(compute='_compute_wb_unbilled_authorized_consumption', store=True, string='Consumption')

    wb_unbilled_unmeter_consumption_daily = fields.Float(compute='_compute_wb_unbilled_authorized_consumption', store=True, string='Consumption')
    wb_unbilled_unmeter_consumption_daily_error_margin = fields.Float(compute='_compute_wb_unbilled_authorized_consumption', store=True, string='Error Margin')
    wb_unbilled_unmeter_consumption_period = fields.Float(compute='_compute_wb_unbilled_authorized_consumption', store=True, string='Consumption')
    wb_unbilled_unmeter_consumption_period_error_margin = fields.Float(compute='_compute_wb_unbilled_authorized_consumption', store=True, string='Error Margin')
    wb_unbilled_unmeter_consumption_yearly = fields.Float(compute='_compute_wb_unbilled_authorized_consumption', store=True, string='Consumption')
    wb_unbilled_unmeter_consumption_yearly_error_margin = fields.Float(compute='_compute_wb_unbilled_authorized_consumption', store=True, string='Error Margin')

    wb_commercial_losses_daily = fields.Float(compute='_compute_wb_commercial_losses', store=True, string='Losses')
    wb_commercial_losses_daily_error_margin = fields.Float(compute='_compute_wb_commercial_losses', store=True, string='Error Margin')
    wb_commercial_losses_period = fields.Float(compute='_compute_wb_commercial_losses', store=True, string='Losses')
    wb_commercial_losses_period_error_margin = fields.Float(compute='_compute_wb_commercial_losses', store=True, string='Error Margin')
    wb_commercial_losses_yearly = fields.Float(compute='_compute_wb_commercial_losses', store=True, string='Losses')
    wb_commercial_losses_yearly_error_margin = fields.Float(compute='_compute_wb_commercial_losses', store=True, string='Error Margin')

    wb_unauthorized_consumption_daily = fields.Float(compute='_compute_wb_unauthorized_consumption', store=True, string='Consumption')
    wb_unauthorized_consumption_daily_error_margin = fields.Float(compute='_compute_wb_unauthorized_consumption', store=True, string='Error Margin')
    wb_unauthorized_consumption_period = fields.Float(compute='_compute_wb_unauthorized_consumption', store=True, string='Consumption')
    wb_unauthorized_consumption_period_error_margin = fields.Float(compute='_compute_wb_unauthorized_consumption', store=True, string='Error Margin')
    wb_unauthorized_consumption_yearly = fields.Float(compute='_compute_wb_unauthorized_consumption', store=True, string='Consumption')
    wb_unauthorized_consumption_yearly_error_margin = fields.Float(compute='_compute_wb_unauthorized_consumption', store=True, string='Error Margin')

    wb_meter_error_daily = fields.Float(compute='_compute_wb_meter_error', store=True, string='Meter Error')
    wb_meter_error_daily_error_margin = fields.Float(compute='_compute_wb_meter_error', store=True, string='Error Margin')
    wb_meter_error_period = fields.Float(compute='_compute_wb_meter_error', store=True, string='Meter Error')
    wb_meter_error_period_error_margin = fields.Float(compute='_compute_wb_meter_error', store=True, string='Error Margin')
    wb_meter_error_yearly = fields.Float(compute='_compute_wb_meter_error', store=True, string='Meter Error')
    wb_meter_error_yearly_error_margin = fields.Float(compute='_compute_wb_meter_error', store=True, string='Error Margin')

    wb_physical_losses_daily = fields.Float(compute='_compute_wb_physical_losses', store=True, string='Physical Losses')
    wb_physical_losses_daily_error_margin = fields.Float(compute='_compute_wb_physical_losses', store=True, string='Error Margin')
    wb_physical_losses_period = fields.Float(compute='_compute_wb_physical_losses', store=True, string='Physical Losses')
    wb_physical_losses_period_error_margin = fields.Float(compute='_compute_wb_physical_losses', store=True, string='Error Margin')
    wb_physical_losses_yearly = fields.Float(compute='_compute_wb_physical_losses', store=True, string='Physical Losses')
    wb_physical_losses_yearly_error_margin = fields.Float(compute='_compute_wb_physical_losses', store=True, string='Error Margin')

    wb_non_revenue_water_daily = fields.Float(compute='_compute_wb_non_revenue_water', store=True, string='Non-Revenue Water')
    wb_non_revenue_water_daily_error_margin = fields.Float(compute='_compute_wb_non_revenue_water', store=True, string='Error Margin')
    wb_non_revenue_water_period = fields.Float(compute='_compute_wb_non_revenue_water', store=True, string='Non-Revenue Water')
    wb_non_revenue_water_period_error_margin = fields.Float(compute='_compute_wb_non_revenue_water', store=True, string='Error Margin')
    wb_non_revenue_water_yearly = fields.Float(compute='_compute_wb_non_revenue_water', store=True, string='Non-Revenue Water')
    wb_non_revenue_water_yearly_error_margin = fields.Float(compute='_compute_wb_non_revenue_water', store=True, string='Error Margin')

    @api.depends('system_input_best_estimate',
                 'system_input_error_margin',
                 'period_duration')
    def _compute_wb_system_input(self):
        # super(WaterBalance, self)._compute_wb_system_input()
        best_estimate = self.system_input_best_estimate
        err_margin = self.system_input_error_margin
        duration = self.period_duration
        self.wb_system_input_daily = best_estimate / duration if duration > 0 else 0.0
        self.wb_system_input_period = best_estimate
        self.wb_system_input_yearly = best_estimate / duration * 365 if duration > 0 else 0.0
        self.wb_system_input_daily_error_margin = err_margin
        self.wb_system_input_period_error_margin = err_margin
        self.wb_system_input_yearly_error_margin = err_margin

    def _compute_wb_authorized_consumption(self):
        self.wb_authorized_consumption_daily = 0.0
        self.wb_authorized_consumption_period = 0.0
        self.wb_authorized_consumption_yearly = 0.0
        self.wb_authorized_consumption_daily_error_margin = 0.0
        self.wb_authorized_consumption_period_error_margin = 0.0
        self.wb_authorized_consumption_yearly_error_margin = 0.0

    @api.depends('billed_meter_consumption_total',
                 'billed_unmeter_consumption_total',
                 'period_duration')
    def _compute_wb_billed_authorized_consumption(self):
        # super(WaterBalance, self)._compute_wb_billed_authorized_consumption()
        billed_meter = self.billed_meter_consumption_total
        billed_unmeter = self.billed_unmeter_consumption_total
        duration = self.period_duration

        self.wb_billed_meter_consumption_daily = billed_meter / duration if duration > 0 else 0.0
        self.wb_billed_meter_consumption_period = billed_meter
        self.wb_billed_meter_consumption_yearly = billed_meter / duration * 365 if duration > 0 else 0

        self.wb_billed_unmeter_consumption_daily = billed_unmeter / duration if duration > 0 else 0.0
        self.wb_billed_unmeter_consumption_period = billed_unmeter
        self.wb_billed_unmeter_consumption_yearly = billed_unmeter / duration * 365 if duration > 0 else 0.0

        self.wb_billed_authorized_consumption_daily = self.wb_billed_meter_consumption_daily + self.wb_billed_unmeter_consumption_daily
        self.wb_billed_authorized_consumption_period = self.wb_billed_meter_consumption_period + self.wb_billed_unmeter_consumption_period
        self.wb_billed_authorized_consumption_yearly = self.wb_billed_meter_consumption_yearly + self.wb_billed_unmeter_consumption_yearly

        self.wb_revenue_water_daily = self.wb_billed_authorized_consumption_daily
        self.wb_revenue_water_period = self.wb_billed_authorized_consumption_period
        self.wb_revenue_water_yearly = self.wb_billed_authorized_consumption_yearly

    def _compute_wb_water_losses(self):
        self.wb_water_losses_daily = 0.0
        self.wb_water_losses_period = 0.0
        self.wb_water_losses_yearly = 0.0
        self.wb_water_losses_daily_error_margin = 0.0
        self.wb_water_losses_period_error_margin = 0.0
        self.wb_water_losses_yearly_error_margin = 0.0

    def _compute_wb_unbilled_authorized_consumption(self):
        unbilled_meter = self.unbilled_meter_consumption_total
        unbilled_unmeter = self.unbilled_unmeter_best_estimate
        err_margin = self.unbilled_unmeter_error_margin
        duration = self.period_duration

        self.wb_unbilled_meter_consumption_daily = unbilled_meter / duration if duration > 0 else 0.0
        self.wb_unbilled_meter_consumption_period = unbilled_meter
        self.wb_unbilled_meter_consumption_yearly = unbilled_meter / duration * 365 if duration > 0 else 0.0
        self.wb_unbilled_unmeter_consumption_daily = unbilled_unmeter / duration if duration > 0 else 0.0
        self.wb_unbilled_unmeter_consumption_period = unbilled_unmeter
        self.wb_unbilled_unmeter_consumption_yearly = unbilled_unmeter / duration * 365 if duration > 0 else 0.0

        self.wb_unbilled_unmeter_consumption_daily_error_margin = err_margin
        self.wb_unbilled_unmeter_consumption_period_error_margin = err_margin
        self.wb_unbilled_unmeter_consumption_yearly_error_margin = err_margin

        uac_daily = self.wb_unbilled_meter_consumption_daily + self.wb_unbilled_unmeter_consumption_daily
        uac_period = self.wb_unbilled_meter_consumption_period + self.wb_unbilled_unmeter_consumption_period
        uac_yearly = self.wb_unbilled_meter_consumption_yearly + self.wb_unbilled_unmeter_consumption_yearly

        self.wb_unbilled_authorized_consumption_daily = uac_daily
        self.wb_unbilled_authorized_consumption_period = uac_period
        self.wb_unbilled_authorized_consumption_yearly = uac_yearly

        self.wb_unbilled_authorized_consumption_daily_error_margin = 0.0  #this need special fields to calculate
        self.wb_unbilled_authorized_consumption_period_error_margin = err_margin
        self.wb_unbilled_authorized_consumption_yearly_error_margin = err_margin

    def _compute_wb_commercial_losses(self):
        self.wb_commercial_losses_daily = 0.0
        self.wb_commercial_losses_period = 0.0
        self.wb_commercial_losses_yearly = 0.0
        self.wb_commercial_losses_daily_error_margin = 0.0
        self.wb_commercial_losses_period_error_margin = 0.0
        self.wb_commercial_losses_yearly_error_margin = 0.0

    def _compute_wb_unauthorized_consumption(self):
        self.wb_unauthorized_consumption_daily = 0.0
        self.wb_unauthorized_consumption_period = 0.0
        self.wb_unauthorized_consumption_yearly = 0.0
        self.wb_unauthorized_consumption_daily_error_margin = 0.0
        self.wb_unauthorized_consumption_period_error_margin = 0.0
        self.wb_unauthorized_consumption_yearly_error_margin = 0.0

    def _compute_wb_meter_error(self):
        self.wb_meter_error_daily = 0.0
        self.wb_meter_error_period = 0.0
        self.wb_meter_error_yearly = 0.0
        self.wb_meter_error_daily_error_margin = 0.0
        self.wb_meter_error_period_error_margin = 0.0
        self.wb_meter_error_yearly_error_margin = 0.0

    def _compute_wb_physical_losses(self):
        self.wb_physical_losses_daily = 0.0
        self.wb_physical_losses_period = 0.0
        self.wb_physical_losses_yearly = 0.0
        self.wb_physical_losses_daily_error_margin = 0.0
        self.wb_physical_losses_period_error_margin = 0.0
        self.wb_physical_losses_yearly_error_margin = 0.0

    def _compute_wb_non_revenue_water(self):
        self.wb_non_revenue_water_daily = 0.0
        self.wb_non_revenue_water_period = 0.0
        self.wb_non_revenue_water_yearly = 0.0
        self.wb_non_revenue_water_daily_error_margin = 0.0
        self.wb_non_revenue_water_period_error_margin = 0.0
        self.wb_non_revenue_water_yearly_error_margin = 0.0

    def action_system_input_wizard(self):
        period = datetime(int(self.year_select), int(self.period), 1)
        end_of_period = fields.Datetime.end_of(period, 'month')
        vals = {
            'water_balance_id': self.id,
            'end_of_period': end_of_period,
        }
        wizard = self.env['system.input.wizard'].create(vals)
        view = self.env.ref('onpoint_water_balance.system_input_wizard_form')
        action = {'type': 'ir.actions.act_window',
                  'name': 'System Input Wizard',
                  'res_model': 'system.input.wizard',
                  'res_id': wizard.id,
                  'view_mode': 'form',
                  'view_id': view.id,
                  'domain': [],
                  'target': 'new',
                  'key2': 'client_action_multi'
                  }
        return action

    def action_import_billed_wizard(self):
        vals = {
            'water_balance_id': self.id,
        }
        wizard = self.env['billed.consumption.wizard'].create(vals)
        view = self.env.ref('onpoint_water_balance.billed_consumption_wizard_form')
        action = {'type': 'ir.actions.act_window',
                  'name': 'System Input Wizard',
                  'res_model': 'billed.consumption.wizard',
                  'res_id': wizard.id,
                  'view_mode': 'form',
                  'view_id': view.id,
                  'domain': [],
                  'target': 'new',
                  'key2': 'client_action_multi'
                  }
        return action
