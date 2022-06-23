from odoo import models, fields, api
from odoo.osv import expression
from datetime import datetime
from dateutil.relativedelta import relativedelta

import logging
_logger = logging.getLogger(__name__)


class PamClosing(models.TransientModel):
    _name = 'pam.closing'

    def _default_month(self):

        balance = self.env['pam.balance'].search([('state', '=', 'active')], limit=1, order='name desc')
        if balance:
            period_month = int(balance.period_month)

            if period_month == 12:
                period_month = 1
            else:
                period_month = period_month + 1
            
            return str(period_month).zfill(2)
        else:
            return str(datetime.today().month)

    def _default_year(self):

        balance = self.env['pam.balance'].search([('state', '=', 'active')], limit=1, order='name desc')
        if balance:
            period_year = int(balance.period_year)
            period_month = int(balance.period_month)

            if period_month == 12:
                period_year = period_year + 1
            
            return str(period_year)
        else:
            return str(datetime.today().year)

    def _get_years(self):
        current_year = int(self._default_year()) + 1
        min_year = current_year - 2
        results = []
        for year in range(min_year, current_year):
            str_year = str(year)
            results.append((str_year, str_year))
        return results

    name = fields.Selection([
        ('monthly', 'Tutup Buku Bulanan'),
        ('annualy', 'Tutup Buku Tahunan'),
    ], default='monthly')
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
    ], default=_default_month)
    years = fields.Selection(_get_years, string='Tahun Anggaran', default=_default_year)

    def closing(self):

        current_period = str(self.years) + str(self.months)
        
        previous_year = str(self.years)

        if self.months == '01':
            previous_month = '12'
            previous_year = str(int(self.years) - 1)
        else:
            previous_month = str(int(self.months) - 1).zfill(2)

        previous_period = previous_year + previous_month

        start_date = self.years + '-' + self.months + '-01'
        selected_month = self.years + '-' + self.months + '-01'
        next_month = datetime.strptime(selected_month, '%Y-%m-%d') + relativedelta(months=1)
        end_date = next_month - relativedelta(days=1)


        sql = """
            SELECT 
                raw.id, 
                raw.beginning_balance,
                raw.current_balance
            FROM (
                select 
                a.id, 
                a.code,
                coalesce((select y.ending_balance 
                from pam_balance x 
                inner join pam_balance_line y on x.id = y.balance_id
                where y.coa_id = a.id and x."name" = %s and x.state = 'active'),0) as beginning_balance,
                coalesce(
                case 
                    when b."position" = 'debit' then (select SUM(yy.debit - yy.credit) 
                                                    from pam_journal_entry xx 
                                                        inner join pam_journal_entry_line yy on xx.id = yy.journal_entry_id
                                                    where xx.state IN ('submit', 'posted') and yy.coa_id = a.id and xx.entry_date between %s and %s)
                    else (select SUM(yy.credit - yy.debit) 
                        from pam_journal_entry xx 
                            inner join pam_journal_entry_line yy on xx.id = yy.journal_entry_id
                        where xx.state IN ('submit', 'posted') and yy.coa_id = a.id and xx.entry_date between %s and %s)
                end
                ,0) as current_balance
                from pam_coa a
                inner join pam_coa_type b on b.id = a.coa_type_id
                where a.transactional = true

                UNION ALL

                select 
                a.id,
                a.code,
                coalesce((select y.ending_balance 
                from pam_balance x 
                inner join pam_balance_line y on x.id = y.balance_id
                where y.coa_id = a.id and x."name" = %s and x.state = 'active'),0) as beginning_balance,
                coalesce(
                case 
                    when b."position" = 'debit' then (select SUM(yy.debit - yy.credit) 
                                                    from pam_journal_entry xx 
                                                        inner join pam_journal_entry_line yy on xx.id = yy.journal_entry_id
                                                    where yy.coa_id IN (select id from pam_coa z where z.parent_left > a.parent_left and z.parent_right < a.parent_right and z.transactional = true) 
                                                        and xx.state IN ('submit', 'posted')
                                                        and xx.entry_date between %s and %s)
                    else (select SUM(yy.credit - yy.debit) 
                        from pam_journal_entry xx 
                            inner join pam_journal_entry_line yy on xx.id = yy.journal_entry_id
                        where yy.coa_id IN (select id from pam_coa z where z.parent_left > a.parent_left and z.parent_right < a.parent_right and z.transactional = true) 
                            and xx.state IN ('submit', 'posted')
                            and xx.entry_date between %s and %s)
                end
                ,0) as current_balance
                from pam_coa a
                inner join pam_coa_type  b on b.id = a.coa_type_id
                where transactional = false) as raw
            ORDER BY raw.code

        """

        # _logger.debug("Debug sql : %s", sql)
        # _logger.debug("Debug start_date : %s", start_date)
        # _logger.debug("Debug end_date : %s", end_date)

        self._cr.execute(sql, (previous_period, start_date, end_date, start_date, end_date, previous_period, start_date, end_date, start_date, end_date))
        transactionals = self._cr.fetchall()


        data = []
        for coa_id, beginning_balance, current_balance in transactionals:
            ending_balance = beginning_balance + current_balance
            vals = {
                'balance_id' : self.id,
                'coa_id' : coa_id,
                'beginning_balance' : beginning_balance,
                'current_balance' : current_balance,
                'ending_balance' : ending_balance
            }

            row = (0, 0, vals)
            data.append(row)

        balance_val = {
            'name': current_period,
            'period_month': self.months,
            'period_year': self.years,
            'line_ids': data
        }

        self.env['pam.balance'].create(balance_val)

        self.posting(start_date, end_date)

        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }        

    def posting(self, start_date, end_date):
        journals = self.env['pam.journal.entry'].search([('entry_date', '>=', start_date), ('entry_date', '<=', end_date), ('state', '=', 'submit')])
        journals.write({
            'state': 'posted'
        })


class PamOpen(models.TransientModel):
    _name = 'pam.open'

    def _compute_period(self):

        balance = self.env['pam.balance'].search([('state', '=', 'active')], limit=1, order='name desc')
        return balance.id

    balance_id  = fields.Many2one('pam.balance', default=_compute_period, string='Periode')
    balance_year = fields.Selection('pam.balance', related='balance_id.period_year')
    balance_month = fields.Selection('pam.balance', related='balance_id.period_month')
    
    def open(self):
        start_date = self.balance_year + '-' + self.balance_month + '-01'
        selected_month = self.balance_year + '-' + self.balance_month + '-01'
        next_month = datetime.strptime(selected_month, '%Y-%m-%d') + relativedelta(months=1)
        end_date = next_month - relativedelta(days=1)

        journals = self.env['pam.journal.entry'].search([('entry_date', '>=', start_date), ('entry_date', '<=', end_date), ('state', '=', 'posted')])
        journals.write({
            'state': 'submit'
        })

        self.env['pam.balance'].search([('id', '=', self.balance_id.id)]).write({
            'state': 'inactive'
        })

        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }        


