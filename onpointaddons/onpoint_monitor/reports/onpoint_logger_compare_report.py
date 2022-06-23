from odoo import models, fields, api, _
from datetime import datetime, timezone, timedelta
from dateutil.relativedelta import relativedelta


class OnpointLoggerCompareReport(models.TransientModel):
    _name = 'onpoint.logger.compare.report'
    _inherit = 'onpoint.monitor'

    logger_compare_id = fields.Many2one('onpoint.logger.compare', required=True, string='Logger', ondelete='cascade', index=True)
    report_period = fields.Char()
    start_date = fields.Date()
    end_date = fields.Date()
    image_url = fields.Char()
    remarks = fields.Text()

    def generate_pdf_report(self):

        logger_compares = self.env['onpoint.logger.compare'].get_data(self.logger_compare_id.id, self.report_period)

        channels = []
        rows = []
        counter = 0
        logger_ids = []
        profiles = []
        number = 1
        loggers = logger_compares['loggers']
        for logger in loggers:
            logger_datas = self.env['onpoint.logger'].search([('id', '=', logger['logger_id'])])
            for logger_data in logger_datas:
                if logger_data.id not in logger_ids:
                    val_data = {
                        'number': number,
                        'name': logger_data.name,
                        'identifier': logger_data.identifier,
                        'brand': logger_data.brand_id.name,
                        'logger_type': logger_data.logger_type_id.name,
                        'department': logger_data.department_id.name,
                        'wtp': logger_data.wtp_id.name,
                        'zone': logger_data.zone_id.name,
                        'dma': logger_data.dma_id.name,
                        'simcard': logger_data.simcard,
                        'nosal': logger_data.nosal,
                        'address': logger_data.address,
                    }
                    profiles.append(val_data)
                    logger_ids.append(logger_data.id)
                    number += 1

            val = {
                'name': logger['logger_name'],
                'channel_name': logger['channel_name'],
                'value_unit_name': logger['unit_value_name'],
                'last_date': logger['last_date'],
                'last_value': logger['last_value'],
                'min_date': logger['min_date'],
                'min_value': logger['min_value'],
                'max_date': logger['max_date'],
                'max_value': logger['max_value']
            }
            rows.append(val)
            counter += 1

            if counter == 3:
                counter = 0
                channels.append(rows)
                rows = []

        channels.append(rows)

        logger = {
            'id': self.logger_compare_id.id,
            'report_period': self.report_period,
            'name': self.logger_compare_id.name,
            'channels': channels,
            'remarks': self.remarks if self.remarks else '',
            'print_date': datetime.now().strftime('%Y-%m-%d')
        }

        data = {
            'ids': self.ids,
            'model': self._name,
            'form': {
                'timestamp': (datetime.now() + relativedelta(hours=7)).strftime('%d/%m/%Y %H:%M:%S'),
                'image_url': self.image_url,
                'logger': logger,
                'profiles': profiles
            },
        }

        return self.env.ref('onpoint_monitor.act_onpoint_logger_compare_report').report_action(self, data=data)


class OnpointLoggerCompareRecapReport(models.AbstractModel):
    _name = 'report.onpoint_monitor.onpoint_logger_compare_report_template'
    _template = 'onpoint_monitor.onpoint_logger_compare_report_template'

    @api.model
    def _get_report_values(self, docids, data=None):
        docs = self.env['onpoint.logger.compare.report'].browse(docids)

        timestamp = data['form']['timestamp']
        image_url = data['form']['image_url']
        logger = data['form']['logger']
        profiles = data['form']['profiles']

        return {
            'doc_ids': data['ids'],
            'doc_model': data['model'],
            'docs': self,
            'timestamp': timestamp,
            'image_url': image_url,
            'logger': logger,
            'profiles': profiles
        }
