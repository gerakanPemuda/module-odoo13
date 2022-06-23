from odoo import fields, models, api
from datetime import datetime


class SystemInputWizard(models.TransientModel):
    _name = 'system.input.wizard'
    _description = 'Wizard'

    name = fields.Char()
    water_balance_id = fields.Many2one('onpoint.water.balance')
    end_of_period = fields.Datetime()
    system_input_template_id = fields.Many2one('onpoint.water.balance.config.system.input.template')
    system_input_lines = fields.One2many('system.input.line.wizard', 'system_input_wizard_id')

    @api.onchange('system_input_template_id')
    def _onchange_system_input_template_id(self):
        template = self.system_input_template_id
        line_wizard = self.env['system.input.line.wizard']
        line_ids = []
        if template:
            for line in template.config_system_input_lines:
                log_values = self.env['onpoint.logger.value'].search([('logger_id', '=', line.logger_id.id),
                                                                      ('channel_id', '=', line.channel_id.id),
                                                                      ('dates', '<=', self.end_of_period)], limit=1)
                val = {
                    'logger_id': line.logger_id.id,
                    'quantity': float(log_values.channel_value),
                    'error_margin': 0.0
                    }
                line_ids.append(line_wizard.new(val).id)
        self.system_input_lines = [(6, 0, line_ids)]

    def action_system_input_process(self):
        for line in self.system_input_lines:
            values = {
                'water_balance_id': self.water_balance_id.id,
                'name': line.name,
                'wtp_id': line.wtp_id.id,
                'zone_id': line.zone_id.id,
                'dma_id': line.dma_id.id,
                'quantity': line.quantity,
                'error_margin': line.error_margin
            }
            self.env['onpoint.water.balance.system.input'].create(values)


class SystemInputLineWizard(models.TransientModel):
    _name = 'system.input.line.wizard'

    name = fields.Char()
    system_input_wizard_id = fields.Many2one('system.input.wizard', ondelete='cascade')
    logger_id = fields.Many2one('onpoint.logger')
    name = fields.Char(related='logger_id.name', readonly=True)
    wtp_id = fields.Many2one(related='logger_id.wtp_id', readonly=True)
    zone_id = fields.Many2one(related='logger_id.zone_id', readonly=True)
    dma_id = fields.Many2one(related='logger_id.dma_id', readonly=True)
    quantity = fields.Float()
    error_margin = fields.Float()
