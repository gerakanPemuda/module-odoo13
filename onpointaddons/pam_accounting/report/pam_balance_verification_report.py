from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from odoo.osv import expression
import time
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta


class PamBalanceVerificationReport(models.TransientModel):
    _name = 'pam.balance.verification.report'

    def _default_year(self):
        return str(datetime.today().year)

    def _get_years(self):
        current_year = self._default_year() + 1
        min_year = current_year - 3
        results = []
        for year in range(min_year, current_year):
            results.append((year, year))
        return results

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
    years = fields.Selection(_get_years, string='Tahun Anggaran', default=_default_year)
    
    line_ids = fields.One2many('pam.balance.verification.report.line', 'balance_verification_report_id')

    def _record(self, beginning_period, start_date, end_date):
        sql = """
                SELECT 
                    a.code as coa_number, 
                    a.name as coa_name,
                    coalesce((
						select yy.beginning_balance 
						from pam_balance xx
						inner join pam_balance_line yy on xx.id = yy.balance_id
						where xx.name = %s and yy.coa_id = a.id 
                    ),0) as beginning_balance,
                    coalesce((CASE 
                        WHEN b."position" = 'debit' then (SELECT sum(y.debit - y.credit) 
                                                        FROM pam_journal_entry x 
                                                        INNER JOIN pam_journal_entry_line y on x.id = y.journal_entry_id
                                                        WHERE y.coa_id = a.id and x.entry_date between %s and %s)
                        ELSE (SELECT sum(y.credit - y.debit) 
                            FROM pam_journal_entry x 
                            INNER JOIN pam_journal_entry_line y on x.id = y.journal_entry_id
                            WHERE y.coa_id = a.id  and x.entry_date between %s and %s)
                    END),0) as current_balance
                FROM pam_coa a
                INNER JOIN pam_coa_type b on b.id = a.coa_type_id
                WHERE transactional = true
            """

        self._cr.execute(sql, (beginning_period, start_date, end_date, start_date, end_date))
        result = self._cr.fetchall()

        return result

    def get_data(self):

        period = self.years + '01'

        start_date = self.years + '-01-01'
        selected_month = self.years + '-' + self.months + '-01'
        next_month = datetime.strptime(selected_month, '%Y-%m-%d') + relativedelta(months=1)
        end_date = next_month - relativedelta(days=1)

        records = self._record(period, start_date, end_date)

        self.env['pam.balance.verification.report.line'].search([('balance_verification_report_id','=', self.id)]).unlink()

        data = []
        for coa_number, coa_name, beginning_balance, current_balance in records:
            ending_balance = beginning_balance + current_balance
            vals = {
                'balance_verification_report_id' : self.id,
                'coa_number' : coa_number,
                'coa_name' : coa_name,
                'beginning_balance' : beginning_balance,
                'current_balance' : current_balance,
                'ending_balance' : ending_balance
            }

            row = (0, 0, vals)
            data.append(row)

        verification_report = self.env['pam.balance.verification.report'].search([('id', '=', self.id)])
        verification_report.update({
            'line_ids': data
        })


class PamBalanceCurrentAsset(models.TransientModel):
    _name = 'pam.balance.current.asset'

    balance_verification_report_id = fields.Many2one('pam.balance.verification.report', required=True, index=True)
    name = fields.Char(string='Uraian')
    beginning = fields.Float(default=0)
    current = fields.Float(default=0)
    ending = fields.Float(default=0)


