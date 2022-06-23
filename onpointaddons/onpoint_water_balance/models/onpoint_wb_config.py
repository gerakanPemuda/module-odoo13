from odoo import fields, models, api, _
from odoo.exceptions import ValidationError


class ConfigSystemInputTemplate(models.Model):
    _name = 'onpoint.water.balance.config.system.input.template'
    _description = 'System Input Templates'

    name = fields.Char(string='Description')
    config_system_input_lines = fields.One2many('onpoint.water.balance.config.system.input.lines', 'config_id')


class ConfigSystemInputLines(models.Model):
    _name = 'onpoint.water.balance.config.system.input.lines'
    _description = 'System Input Configuration Lines'

    config_id = fields.Many2one('onpoint.water.balance.config.system.input.template')
    logger_id = fields.Many2one('onpoint.logger', string='Logger')
    value_type_id = fields.Many2one('onpoint.value.type', string='Channel/Value Type')
    channel_id = fields.Many2one('onpoint.logger.channel', string='Channel')

    @api.constrains('logger_id')
    def check_logger_id(self):
        for r in self:
            rec = self.env['onpoint.water.balance.config.system.input.lines'].search([('logger_id', '=', r.logger_id.id),
                                                                                      ('config_id', '=', r.config_id.id)])
            if len(rec) > 1:
                raise ValidationError(_('You have put a logger more than once'))
            else:
                pass
