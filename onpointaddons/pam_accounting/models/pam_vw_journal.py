from odoo import models, fields, api, tools

import logging
_logger = logging.getLogger(__name__)


class PamVwBudget(models.Model):
    _name = 'pam.vw.journal'
    _auto = False

    start_of_month = fields.Date(index=True, readonly=True)
    end_of_month = fields.Date(index=True, readonly=True)
    month_name = fields.Char(readonly=True)
    income = fields.Float(readonlye=True)
    outcome = fields.Float(readonly=True)


    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        sql = """
    		create or replace view pam_vw_journal as (
                select 
	    			row_number()over() as id,
                    x.start_of_month,
                    x.end_of_month,
                    x.month_name,
                ((
                select coalesce(sum(b.credit - b.debit), 0)
                from pam_journal_entry a, pam_journal_entry_line b, pam_coa c
                where a.id = b.journal_entry_id and c.id = b.coa_id and a.state != 'draft'
                and c.parent_left > (select parent_left from pam_coa where code = '31110000') 
                and c.parent_right < (select parent_right from pam_coa where code = '31110000')
                and a.entry_date BETWEEN x.start_of_month and x.end_of_month
                )
                +
                (select coalesce(sum(b.credit - b.debit), 0)
                from pam_journal_entry a, pam_journal_entry_line b, pam_coa c
                where a.id = b.journal_entry_id and c.id = b.coa_id and a.state != 'draft' 
                and c.parent_left > (select parent_left from pam_coa where code = '31120000') 
                and c.parent_right < (select parent_right from pam_coa where code = '31120000')
                and a.entry_date BETWEEN x.start_of_month and x.end_of_month
                )) as income,
                ((select coalesce(sum(b.debit - b.credit), 0)
                from pam_journal_entry a, pam_journal_entry_line b, pam_coa c
                where a.id = b.journal_entry_id and c.id = b.coa_id and a.state != 'draft' 
                and c.parent_left > (select parent_left from pam_coa where code = '41110000') 
                and c.parent_right < (select parent_right from pam_coa where code = '41110000')
                and a.entry_date BETWEEN x.start_of_month and x.end_of_month
                )
                +
                --Beban Pengolahan Air
                (select coalesce(sum(b.debit - b.credit), 0)
                from pam_journal_entry a, pam_journal_entry_line b, pam_coa c
                where a.id = b.journal_entry_id and c.id = b.coa_id and a.state != 'draft' 
                and c.parent_left > (select parent_left from pam_coa where code = '41210000') 
                and c.parent_right < (select parent_right from pam_coa where code = '41210000')
                and a.entry_date BETWEEN x.start_of_month and x.end_of_month)
                +
                --Beban Transmisi dan Distribusi
                (select coalesce(sum(b.debit - b.credit), 0)
                from pam_journal_entry a, pam_journal_entry_line b, pam_coa c
                where a.id = b.journal_entry_id and c.id = b.coa_id and a.state != 'draft' 
                and c.parent_left > (select parent_left from pam_coa where code = '41310000') 
                and c.parent_right < (select parent_right from pam_coa where code = '41310000')
                and a.entry_date BETWEEN x.start_of_month and x.end_of_month)
                +
                --Beban Perpompaan
                (select coalesce(sum(b.debit - b.credit), 0)
                from pam_journal_entry a, pam_journal_entry_line b, pam_coa c
                where a.id = b.journal_entry_id and c.id = b.coa_id and a.state != 'draft' 
                and c.parent_left > (select parent_left from pam_coa where code = '41410000') 
                and c.parent_right < (select parent_right from pam_coa where code = '41410000')
                and a.entry_date BETWEEN x.start_of_month and x.end_of_month)
                +
                --Beban Perencanaan Teknik
                (select coalesce(sum(b.debit - b.credit), 0)
                from pam_journal_entry a, pam_journal_entry_line b, pam_coa c
                where a.id = b.journal_entry_id and c.id = b.coa_id and a.state != 'draft' 
                and c.parent_left > (select parent_left from pam_coa where code = '41510000') 
                and c.parent_right < (select parent_right from pam_coa where code = '41510000')
                and a.entry_date BETWEEN x.start_of_month and x.end_of_month)
                +
                --Beban Administrasi Umum
                (select coalesce(sum(b.debit - b.credit), 0)
                from pam_journal_entry a, pam_journal_entry_line b, pam_coa c
                where a.id = b.journal_entry_id and c.id = b.coa_id and a.state != 'draft' 
                and c.parent_left > (select parent_left from pam_coa where code = '42600000') 
                and c.parent_right < (select parent_right from pam_coa where code = '42600000')
                and a.entry_date BETWEEN x.start_of_month and x.end_of_month)
                +
                --Beban Hubungan Langganan
                (select coalesce(sum(b.debit - b.credit), 0)
                from pam_journal_entry a, pam_journal_entry_line b, pam_coa c
                where a.id = b.journal_entry_id and c.id = b.coa_id and a.state != 'draft' 
                and c.parent_left > (select parent_left from pam_coa where code = '42710000') 
                and c.parent_right < (select parent_right from pam_coa where code = '42710000')
                and a.entry_date BETWEEN x.start_of_month and x.end_of_month)
                +
                --Beban Lain-lain
                (select coalesce(sum(b.credit - b.debit), 0)
                from pam_journal_entry a, pam_journal_entry_line b, pam_coa c
                where a.id = b.journal_entry_id and c.id = b.coa_id and a.state != 'draft' 
                and c.parent_left > (select parent_left from pam_coa where code = '51121110') 
                and c.parent_right < (select parent_right from pam_coa where code = '51121110')
                and a.entry_date BETWEEN x.start_of_month and x.end_of_month)
                +
                (select coalesce(sum(b.credit - b.debit), 0)
                from pam_journal_entry a, pam_journal_entry_line b, pam_coa c
                where a.id = b.journal_entry_id and c.id = b.coa_id and a.state != 'draft' 
                and c.parent_left > (select parent_left from pam_coa where code = '51121120') 
                and c.parent_right < (select parent_right from pam_coa where code = '51121120')
                and a.entry_date BETWEEN x.start_of_month and x.end_of_month)
                +
                (select coalesce(sum(b.credit - b.debit), 0)
                from pam_journal_entry a, pam_journal_entry_line b, pam_coa c
                where a.id = b.journal_entry_id and c.id = b.coa_id and a.state != 'draft' 
                and c.parent_left > (select parent_left from pam_coa where code = '51121160') 
                and c.parent_right < (select parent_right from pam_coa where code = '51121160')
                and a.entry_date BETWEEN x.start_of_month and x.end_of_month)
                +
                (select coalesce(sum(b.credit - b.debit), 0)
                from pam_journal_entry a, pam_journal_entry_line b, pam_coa c
                where a.id = b.journal_entry_id and c.id = b.coa_id and a.state != 'draft' 
                and c.parent_left > (select parent_left from pam_coa where code = '51121170') 
                and c.parent_right < (select parent_right from pam_coa where code = '51121170')
                and a.entry_date BETWEEN x.start_of_month and x.end_of_month)
                +
                (select coalesce(sum(b.credit - b.debit), 0)
                from pam_journal_entry a, pam_journal_entry_line b, pam_coa c
                where a.id = b.journal_entry_id and c.id = b.coa_id and a.state != 'draft' 
                and c.parent_left > (select parent_left from pam_coa where code = '51121180') 
                and c.parent_right < (select parent_right from pam_coa where code = '51121180')
                and a.entry_date BETWEEN x.start_of_month and x.end_of_month)) as outcome
                from 
                (
                SELECT 
                    t.day::date as start_of_month, 
                    (date_trunc('month', t.day::date) + interval '1 month' - interval '1 day')::date AS end_of_month, 
                    upper(to_char(to_timestamp(extract(month from t.day)::text, 'MM'), 'TMmon')) as month_name
                FROM   generate_series(timestamp '2019-01-01'
                                    , timestamp '2019-12-31'
                                    , interval  '1 month') AS t(day)) as x)
    	"""
        self.env.cr.execute(sql)


    @api.model
    def get_data(self):

        journals = self.env['pam.vw.journal'].search([])

        xAxis = []
        income = []
        outcome = []

        for journal in journals:

            xAxis.append(journal.month_name)
            income.append(journal.income)
            outcome.append(journal.outcome)

        _logger.debug('journal : %s', xAxis)

        data = {
            'xAxis': xAxis,
            'series': [{
                'name' : 'Pendapatan',
                'data': income
                },
                {
                'name': 'Biaya',
                'data': outcome
                }]
        }

        return data