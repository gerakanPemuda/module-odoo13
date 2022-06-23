from odoo import models, fields, api, _


class OnpointLoggerFile(models.TransientModel):
    _name = 'onpoint.logger.file'

    name = fields.Char(string='File Name', required=True)
    logger_id = fields.Many2one('onpoint.logger', required=True, string='Logger', ondelete='cascade', index=True)
    line_ids = fields.One2many('onpoint.logger.file.line', 'logger_file_id')


class OnpointLoggerFileLine(models.TransientModel):
    _name = 'onpoint.logger.file.line'

    logger_file_id = fields.Many2one('onpoint.logger.file', required=True, string='Logger', ondelete='cascade',
                                     index=True)
    point_code = fields.Char(string='Point Code')
    point_id = fields.Many2one('onpoint.logger.point', required=True, string='Logger', index=True)
    detail_ids = fields.One2many('onpoint.logger.file.detail', 'logger_file_line_id')


class OnpointLoggerFileDetail(models.TransientModel):
    _name = 'onpoint.logger.file.detail'

    logger_file_line_id = fields.Many2one('onpoint.logger.file.line', required=True, string='Logger',
                                          ondelete='cascade',
                                          index=True)
    logger_date = fields.Datetime(string='Date')
    logger_value = fields.Float(string='Value')
    logger_date_diff = fields.Float(string='Diff Date')
    logger_value_diff = fields.Float(string='Diff Value')
