from odoo import models, fields, api
from datetime import datetime
from dateutil.relativedelta import relativedelta
from odoo.exceptions import ValidationError
import pandas as pd


class OnpointGunungrelyReport(models.TransientModel):
    _name = 'onpoint.gunung.rely.report'

    def default_end_date(self):
        return (datetime.strptime(((datetime.today()).strftime("%Y-%m-01")), "%Y-%m-%d") + relativedelta(
            months=1) - relativedelta(days=1)).strftime("%Y-%m-%d")

    start_date = fields.Date(default=fields.Datetime.now())
    end_date = fields.Date(default=fields.Datetime.now())
    interval = fields.Selection([
        ('15T', '15 minutes'),
        ('H', 'Hourly'),
        ('D', 'Daily'),
        ('W', 'Weekly'),
        ('M', 'Monthly'),
    ], default='15T', string='Interval')
    report_html = fields.Html()
    report_qweb = fields.Html()
    line_ids = fields.One2many('onpoint.gunung.rely.line.report', 'report_id')

    def generate_dataframe(self, df, column_name, logger_id, channel_id, start_date, end_date):
        unit_lines = self.env['onpoint.logger.value'].search([('logger_id', '=', logger_id),
                                                              ('channel_id', '=', channel_id),
                                                              ('dates', '>=', start_date),
                                                              ('dates', '<=', end_date)])

        data = []
        if unit_lines:
            for unit_line in unit_lines:
                row = {
                    'dates': unit_line.dates,
                    'channel_value': unit_line.channel_value
                }
                data.append(row)
            unit_line_dataframe = pd.DataFrame(data)
            unit_line_dataframe.dates = pd.to_datetime(unit_line_dataframe.dates)
            unit_line_dataframe.set_index('dates', inplace=True)
            unit_line_dataframe = unit_line_dataframe.rename(columns={'channel_value': column_name})
            unit_line_dataframe = unit_line_dataframe.resample(self.interval, closed='right', label='right').mean()
            if df.empty:
                df = unit_line_dataframe
            else:
                df = pd.concat([df, unit_line_dataframe], axis=1)
        else:
            df[column_name] = 0
        return df

    def get_data(self):
        start_time = ' 00:00:00'
        start_date = self.start_date.strftime('%Y-%m-%d') + start_time
        end_date = self.end_date.strftime('%Y-%m-%d') + start_time
        df = pd.DataFrame()
        df = self.generate_dataframe(df, 'flow_in8', 2, 12, start_date, end_date)
        df = self.generate_dataframe(df, 'flow_out8', 1, 1, start_date, end_date)
        df = self.generate_dataframe(df, 'pressure_out8', 1, 9, start_date, end_date)
        df = self.generate_dataframe(df, 'level_res1', 2, 21, start_date, end_date)
        df = self.generate_dataframe(df, 'pressure_in', 3, 24, start_date, end_date)
        df = self.generate_dataframe(df, 'pressure_out', 3, 25, start_date, end_date)
        df = df.fillna(0)

        interval = dict(self._fields['interval'].selection).get(self.interval)

        # report_body = "<html>"
        # report_body += "<body>"
        # report_header = "<table style='width: 100%'>"
        report_header = "<tr class='report-row-header' rowspan='2'>"
        report_header += "<td class='report-cell-header' style='width:16%;' rowspan='2'>Tanggal</td>"
        report_header += "<td class='report-cell-header' colspan='2'>Flow</td>"
        report_header += "<td class='report-cell-header' rowspan='2'>Pressure Out 8''</td>"
        report_header += "<td class='report-cell-header' rowspan='2'>Level Res</td>"
        report_header += "<td class='report-cell-header' colspan='2'>Pressure PRV Mandin</td>"
        report_header += "</tr>"
        report_header += "<tr class='report-row-header' >"
        report_header += "<td class='report-cell-header' style='width:10%;'>Inlet 8''</td>"
        report_header += "<td class='report-cell-header' style='width:10%;'>Outlet 8''</td>"
        report_header += "<td class='report-cell-header' style='width:10%;'>Inlet</td>"
        report_header += "<td class='report-cell-header' style='width:10%;'>Outlet</td>"
        report_header += "</tr>"

        self.line_ids.unlink()

        for i in range(df.shape[0]):
            line_id = self.env['onpoint.gunung.rely.line.report'].create({
                'report_id': self.id,
                'tanggal': df.index[i],
                'flow_in8': df['flow_in8'][i] if 'flow_in8' in df.columns else 0,
                'flow_out8': df['flow_out8'][i] if 'flow_out8' in df.columns else 0,
                'pressure_out8': df['pressure_out8'][i] if 'pressure_out8' in df.columns else 0,
                'level_res1': df['level_res1'][i] if 'level_res1' in df.columns else 0,
                'pressure_in': df['pressure_in'][i] if 'pressure_in' in df.columns else 0,
                'pressure_out': df['pressure_out'][i] if 'pressure_out' in df.columns else 0,
            })

        report_body = ''
        report_line = 1
        report_qweb = "<table style='width: 100%; font-size: smaller;'>"
        report_qweb += report_header

        report_html = "<table style='width: 100%'>"
        report_html += report_header

        for line in self.line_ids:
            if report_line > 20:
                report_qweb += "</table>"
                report_qweb += "<p style='page-break-after:always;'/>"
                report_qweb += "<table style='width: 100%'>"
                report_qweb += report_header
                report_line = 1

            report_body = "<tr style='font-size: 12px; border: 1px solid #000'>"
            report_body += "<td style='width:16%;padding: 5px'>" + line.tanggal.strftime('%d-%m-%Y %H:%M:%S') + "</td>"
            report_body += "<td class='report-cell-right'>" + str(round(line.flow_in8, 2)) + " l/s</td>"
            report_body += "<td class='report-cell-right'>" + str(round(line.flow_out8, 2)) + " l/s</td>"
            report_body += "<td class='report-cell-right'>" + str(round(line.pressure_out8, 2)) + " bar</td>"
            report_body += "<td class='report-cell-right'>" + str(round(line.level_res1, 2)) + " m</td>"
            report_body += "<td class='report-cell-right'>" + str(round(line.pressure_in, 2)) + " bar</td>"
            report_body += "<td class='report-cell-right'>" + str(round(line.pressure_out, 2)) + " bar</td>"
            report_body += "</tr>"

            report_qweb += report_body
            report_html += report_body
            report_line += 1

        report_html += "</table>"
        report_qweb += "</table>"

        self.write({
            'report_html': report_html,
            'report_qweb': report_qweb
        })

    def generate_pdf_report(self):
        data = {
            'ids': self.ids,
            'model': self._name,
            'form': {
                'timestamp': (datetime.now() + relativedelta(hours=7)).strftime('%d/%m/%Y %H:%M:%S'),
                'report': {
                    'report_period': self.start_date.strftime('%d/%m/%Y') + ' - ' + self.end_date.strftime('%d/%m/%Y'),
                    'report_qweb': self.report_qweb,
                    'interval': 'interval: ' + dict(self._fields['interval'].selection).get(self.interval)
                }
            },
        }

        return self.env.ref('onpoint_scada.act_onpoint_gunung_rely_report1').report_action(self, data=data)


class OnpointGunungrelyLineReport(models.TransientModel):
    _name = 'onpoint.gunung.rely.line.report'

    report_id = fields.Many2one('onpoint.gunung.rely.report', required=True, string='Report', ondelete='cascade',
                                index=True)
    tanggal = fields.Datetime(string='Tanggal', index=True)
    flow_in8 = fields.Float(string='In 8"')
    flow_out8 = fields.Float(string='Out 8"')
    pressure_out8 = fields.Float(string='Out 8"')
    level_res1 = fields.Float(string='Level Res 1')
    level_res2 = fields.Float(string='Level Res 2')
    pressure_in = fields.Float(string='Pressure In')
    pressure_out = fields.Float(string='Pressure Out')


class OnpointGunungRelyRecapReport(models.AbstractModel):
    _name = 'report.onpoint_scada.onpoint_gunung_rely_report_template'
    _template = 'onpoint_scada.onpoint_gunung_rely_report_template'

    @api.model
    def _get_report_values(self, docids, data=None):
        docs = self.env['onpoint.gunung.rely.report'].browse(docids)

        timestamp = data['form']['timestamp']
        report = data['form']['report']

        return {
            'doc_ids': data['ids'],
            'doc_model': data['model'],
            'docs': self,
            'report': report,
            'timestamp': timestamp,
        }
