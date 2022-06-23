from odoo import models, fields, api
from datetime import datetime
from dateutil.relativedelta import relativedelta
from odoo.exceptions import ValidationError
import pandas as pd


class OnpointGunungulinReport(models.TransientModel):
    _name = 'onpoint.gunung.ulin.report'

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
    report_header = fields.Html()
    report_body = fields.Html()
    report_html = fields.Html()
    report_qweb = fields.Html()
    line_ids = fields.One2many('onpoint.gunung.ulin.line.report', 'report_id')

    def generate_dataframe(self, df, column_name, unit_line_id, start_date, end_date):
        unit_lines = self.env['onpoint.scada.unit.detail'].search([('unit_line_id', '=', unit_line_id),
                                                                   ('sensor_date', '>=', start_date),
                                                                   ('sensor_date', '<=', end_date)])

        data = []
        if unit_lines:
            for unit_line in unit_lines:
                row = {
                    'sensor_date': unit_line.sensor_date,
                    'sensor_value': unit_line.sensor_value
                }
                data.append(row)
            unit_line_dataframe = pd.DataFrame(data)
            unit_line_dataframe.sensor_date = pd.to_datetime(unit_line_dataframe.sensor_date)
            unit_line_dataframe.set_index('sensor_date', inplace=True)
            unit_line_dataframe = unit_line_dataframe.rename(columns={'sensor_value': column_name})
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
        df = self.generate_dataframe(df, 'flow_in8', 1, start_date, end_date)
        df = self.generate_dataframe(df, 'flow_out12', 8, start_date, end_date)
        df = self.generate_dataframe(df, 'flow_out8', 12, start_date, end_date)
        df = self.generate_dataframe(df, 'flow_out6', 14, start_date, end_date)
        df = self.generate_dataframe(df, 'pressure_out12', 10, start_date, end_date)
        df = self.generate_dataframe(df, 'pressure_out8', 13, start_date, end_date)
        df = self.generate_dataframe(df, 'pressure_out6', 15, start_date, end_date)
        df = self.generate_dataframe(df, 'turbidity', 2, start_date, end_date)
        df = self.generate_dataframe(df, 'ph', 3, start_date, end_date)
        df = self.generate_dataframe(df, 'scm', 4, start_date, end_date)
        df = self.generate_dataframe(df, 'dosing', 6, start_date, end_date)
        df = self.generate_dataframe(df, 'level', 7, start_date, end_date)
        df = df.fillna(0)

        interval = dict(self._fields['interval'].selection).get(self.interval)

        # report_body = "<html>"
        # report_body += "<body>"
        # report_header = "<table style='width: 100%'>"
        report_header = "<tr class='report-row-header' rowspan='2'>"
        report_header += "<td class='report-cell-header' style='width:16%;' rowspan='2'>Tanggal</td>"
        report_header += "<td class='report-cell-header' colspan='4'>Flow</td>"
        report_header += "<td class='report-cell-header' colspan='3'>Pressure</td>"
        report_header += "<td class='report-cell-header'>Level</td>"
        report_header += "<td class='report-cell-header' colspan='4'>Quality</td>"
        report_header += "</tr>"
        report_header += "<tr class='report-row-header2' >"
        report_header += "<td class='report-cell-header' style='width:7%;'>Air Baku</td>"
        report_header += "<td class='report-cell-header' style='width:7%;'>Outlet 12''</td>"
        report_header += "<td class='report-cell-header' style='width:7%;'>Outlet 8''</td>"
        report_header += "<td class='report-cell-header' style='width:7%;'>Outlet 6''</td>"
        report_header += "<td class='report-cell-header' style='width:7%;'>Outlet 12''</td>"
        report_header += "<td class='report-cell-header' style='width:7%;'>Outlet 8''</td>"
        report_header += "<td class='report-cell-header' style='width:7%;'>Outlet 6''</td>"
        report_header += "<td class='report-cell-header' style='width:7%;'>Reservoir</td>"
        report_header += "<td class='report-cell-header' style='width:7%;'>Turbidity</td>"
        report_header += "<td class='report-cell-header' style='width:7%;'>PH</td>"
        report_header += "<td class='report-cell-header' style='width:7%;'>SCM</td>"
        report_header += "<td class='report-cell-header' style='width:7%;'>Dosing</td>"
        report_header += "</tr>"

        self.line_ids.unlink()

        for i in range(df.shape[0]):
            line_id = self.env['onpoint.gunung.ulin.line.report'].create({
                'report_id': self.id,
                'tanggal': df.index[i],
                'flow_in8': df['flow_in8'][i] if 'flow_in8' in df.columns else 0,
                'flow_out12': df['flow_out12'][i] if 'flow_out12' in df.columns else 0,
                'flow_out8': df['flow_out8'][i] if 'flow_out8' in df.columns else 0,
                'flow_out6': df['flow_out6'][i] if 'flow_out6' in df.columns else 0,
                'pressure_out12': df['pressure_out12'][i] if 'pressure_out12' in df.columns else 0,
                'pressure_out8': df['pressure_out8'][i] if 'pressure_out8' in df.columns else 0,
                'pressure_out6': df['pressure_out6'][i] if 'pressure_out6' in df.columns else 0,
                'turbidity': df['turbidity'][i] if 'turbidity' in df.columns else 0,
                'ph': df['ph'][i] if 'ph' in df.columns else 0,
                'scm': df['scm'][i] if 'scm' in df.columns else 0,
                'dosing': df['dosing'][i] if 'dosing' in df.columns else 0,
                'level': df['level'][i] if 'level' in df.columns else 0,
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
            report_body += "<td class='report-cell-right'>" + str(round(line.flow_out12, 2)) + " l/s</td>"
            report_body += "<td class='report-cell-right'>" + str(round(line.flow_out8, 2)) + " l/s</td>"
            report_body += "<td class='report-cell-right'>" + str(round(line.flow_out6, 2)) + " l/s</td>"
            report_body += "<td class='report-cell-right'>" + str(round(line.pressure_out12, 2)) + " bar</td>"
            report_body += "<td class='report-cell-right'>" + str(round(line.pressure_out8, 2)) + " bar</td>"
            report_body += "<td class='report-cell-right'>" + str(round(line.pressure_out6, 2)) + " bar</td>"
            report_body += "<td class='report-cell-right'>" + str(round(line.level, 2)) + " m</td>"
            report_body += "<td class='report-cell-right'>" + str(round(line.turbidity, 2)) + " NTU</td>"
            report_body += "<td class='report-cell-right'>" + str(round(line.ph, 2)) + " pH</td>"
            report_body += "<td class='report-cell-right'>" + str(round(line.scm, 2)) + " SCU</td>"
            report_body += "<td class='report-cell-right'>" + str(round(line.dosing, 2)) + " Hz</td>"
            report_body += "</tr>"

            report_qweb += report_body
            report_html += report_body
            report_line += 1

        report_html += "</table>"
        report_qweb += "</table>"

        self.write({
            'report_header': report_header,
            'report_body': report_body,
            'report_html': report_html,
            'report_qweb': report_qweb
        })

    def generate_pdf_report(self):
        # lines = []
        # for line in self.line_ids:
        #     lines.append({
        #         'tanggal': line.tanggal.strftime('%d-%m-%Y %H:%M:%S'),
        #         'flow_in8': str(round(line.flow_in8, 2)) + " l/s",
        #         'flow_out12': str(round(line.flow_out12, 2)) + " l/s",
        #         'flow_out8': str(round(line.flow_out8, 2)) + " l/s",
        #         'flow_out6': str(round(line.flow_out6, 2)) + " l/s",
        #         'pressure_out12': str(round(line.pressure_out12, 2)) + " bar",
        #         'pressure_out8': str(round(line.pressure_out8, 2)) + " bar",
        #         'pressure_out6': str(round(line.pressure_out6, 2)) + " bar",
        #         'turbidity': str(round(line.turbidity, 2)) + " NTU",
        #         'ph': str(round(line.ph, 2)) + " pH",
        #         'scm': str(round(line.scm, 2)) + " SCU",
        #         'dosing': str(round(line.dosing, 2)) + " Hz",
        #         'level': str(round(line.level, 2)) + " m",
        #     })

        data = {
            'ids': self.ids,
            'model': self._name,
            'form': {
                'timestamp': (datetime.now() + relativedelta(hours=7)).strftime('%d/%m/%Y %H:%M:%S'),
                'report': {
                    'report_period': self.start_date.strftime('%d/%m/%Y') + ' - ' + self.end_date.strftime('%d/%m/%Y'),
                    'report_body': self.report_body,
                    'report_header': self.report_header,
                    'report_qweb': self.report_qweb,
                }
            },
        }

        return self.env.ref('onpoint_scada.act_onpoint_gunung_ulin_report1').report_action(self, data=data)


class OnpointGunungulinLineReport(models.TransientModel):
    _name = 'onpoint.gunung.ulin.line.report'

    report_id = fields.Many2one('onpoint.gunung.ulin.report', required=True, string='Report', ondelete='cascade',
                                index=True)
    tanggal = fields.Datetime(string='Tanggal', index=True)
    flow_in8 = fields.Float(string='In 8"')
    flow_out12 = fields.Float(string='Out 12"')
    flow_out8 = fields.Float(string='Out 8"')
    flow_out6 = fields.Float(string='Out 6"')
    pressure_out12 = fields.Float(string='Out 12"')
    pressure_out8 = fields.Float(string='Out 8"')
    pressure_out6 = fields.Float(string='Out 6"')
    turbidity = fields.Float(string='Turbidity')
    ph = fields.Float(string='PH')
    scm = fields.Float(string='SCM')
    dosing = fields.Float(string='Dosing')
    level = fields.Float(string='Level')


class OnpointGunungUlinRecapReport(models.AbstractModel):
    _name = 'report.onpoint_scada.onpoint_gunung_ulin_report_template'
    _template = 'onpoint_scada.onpoint_gunung_ulin_report_template'

    @api.model
    def _get_report_values(self, docids, data=None):
        docs = self.env['onpoint.gunung.ulin.report'].browse(docids)

        timestamp = data['form']['timestamp']
        report = data['form']['report']

        return {
            'doc_ids': data['ids'],
            'doc_model': data['model'],
            'docs': self,
            'report': report,
            'timestamp': timestamp,
        }
