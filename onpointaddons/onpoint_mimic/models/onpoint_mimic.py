from odoo import models, fields, api
import werkzeug.utils
from datetime import datetime, timezone, timedelta


class OnpointMimic(models.Model):
    _name = 'onpoint.mimic'
    _inherit = ['image.mixin']

    name = fields.Char(required=True, string='Name')
    template_mimic = fields.Binary(attachment=True)
    attachment_id = fields.Integer(compute='_get_attachment_id')

    line_ids = fields.One2many('onpoint.mimic.line', 'mimic_id')

    def _get_attachment_id(self):
        for record in self:
            attachment = self.env['ir.attachment'].sudo().search([('res_model', '=', 'onpoint.mimic'),
                                                                  ('res_field', '=', 'template_mimic'),
                                                                  ('res_id', '=', record.id)],
                                                                 limit=1)
            record.attachment_id = attachment.id

    def get_template(self, mimic_id):
        mimic = self.env['onpoint.mimic'].search([('id', '=', mimic_id)])

        attachment = self.env['ir.attachment'].sudo().search([('res_model', '=', 'onpoint.mimic'),
                                                              ('res_field', '=', 'template_mimic'),
                                                              ('res_id', '=', mimic.id)],
                                                             limit=1)
        attachment.sudo().write({
            'public': True
        })

        img_url = "/web/image/ir.attachment/%s/datas" % attachment.id

        info_boxes = ""

        for mimic_line in mimic.line_ids:
            style = 'cursor:pointer;background-color:' + mimic_line.background_color + '; ' + 'color:' + mimic_line.text_color + '; '
            for mimic_line_style in mimic_line.style_ids:
                if mimic_line_style.enable:
                    style += mimic_line_style.mimic_style_id.name + ': ' + mimic_line_style.mimic_style_value + ';'

            logger_name = mimic_line.logger_id.name
            channel_name = mimic_line.logger_channel_id.name
            channel_value = mimic_line.logger_channel_id.last_value
            channel_unit = mimic_line.logger_channel_id.value_unit_name

            info_boxes += "<div id='" + mimic_line.code + "' " + \
                          " class='text point-source mimic-tag' " + \
                          " data-logger_id='" + str(mimic_line.logger_id.id) + "' " + \
                          " data-channel_id='" + str(mimic_line.logger_channel_id.id) + "' " + \
                          "style='" + style + "'>" + \
                          "<div style='padding-bottom: 3px; font-weight: bold; text-align: center'>" + logger_name + "</div>" + \
                          "<div style='padding-bottom: 10px; font-weight: bold; text-align: center'>" + channel_name + "</div>" + \
                          channel_value + " " + channel_unit + "</div>"

        template = {
            'mimic': mimic,
            'attachment': attachment,
            'img_url': img_url,
            'info_boxes': info_boxes
        }

        return template

    def act_view_mimic(self):
        url_mimic = '/mimic/diagram/' + str(self.id)
        return {
            'type': 'ir.actions.act_url',
            'url': url_mimic,
            'target': 'self'
        }

    def get_chart(self, logger_id, channel_id):
        logger = self.env['onpoint.logger'].search([('id', '=', int(logger_id))])
        channel = self.env['onpoint.logger.channel'].search([('id', '=', int(channel_id))])
        end_date = datetime.now()
        start_date = end_date - timedelta(hours=24)

        data = self.env['onpoint.logger.value'].get_data(channel_id=int(channel_id),
                                                         start_date=start_date,
                                                         end_date=end_date)

        channel_values = []
        for value in data['values']:

            # Value
            channel_value = value.channel_value

            # value_date = datetime.strptime(value.dates, '%Y-%m-%d %H:%M:%S')
            value_dates = value.dates + timedelta(hours=7)
            unixtime = (value_dates - datetime(1970, 1, 1, 0, 0, 0)).total_seconds() * 1000

            data_val = [unixtime, round(channel_value, 3)]
            channel_values.append(data_val)

        return logger, channel, channel_values


class OnpointMimicLine(models.Model):
    _name = 'onpoint.mimic.line'

    mimic_id = fields.Many2one('onpoint.mimic', required=True, string='Mimic', ondelete='cascade', index=True)
    code = fields.Char(required=True)
    point_source = fields.Selection([
        ('logger', 'Logger')
    ], default='logger', required=True, index=True)
    logger_id = fields.Many2one('onpoint.logger', string='Logger', index=True)
    logger_channel_id = fields.Many2one('onpoint.logger.channel', string='Channel', index=True)
    logger_channel_name = fields.Char('onpoint.logger.channel', related='logger_channel_id.name')
    logger_channel_last_value = fields.Char('onpoint.logger.channel', related='logger_channel_id.last_value')
    logger_channel_value_unit_name = fields.Char('onpoint.logger.channel', related='logger_channel_id.value_unit_name')
    background_color = fields.Char(string='Background Color', default="#00A4D1")
    text_color = fields.Char(string='Text Color', default="#FFFFFF")

    # refers_to = fields.Reference([
    #     ('onpoint.logger', 'Logger'),
    # ], default='onpoint.logger', index=True)
    # refers_line_to = fields.Reference([
    #     ('onpoint.logger.channel', 'Logger Channel'),
    # ], index=True)

    style_ids = fields.One2many('onpoint.mimic.style', 'mimic_line_id')

    @api.onchange('logger_id')
    def domain_logger_id(self):
        if self.logger_id:
            return {'domain': {
                'logger_channel_id': [('logger_id', '=', self.logger_id.id), ('display_on_chart', '=', True)]}}
        else:
            return {'domain': {'logger_channel_id': [('logger_id', '=', 0)]}}


class OnpointMimicStyle(models.Model):
    _name = 'onpoint.mimic.style'

    mimic_line_id = fields.Many2one('onpoint.mimic.line', required=True, string='Mimic Line', ondelete='cascade',
                                    index=True)
    mimic_style_id = fields.Many2one('onpoint.style.sheet', required=True)
    mimic_style_value = fields.Char(string='Value', required=True)
    enable = fields.Boolean(default=True)
