from odoo import models, fields, api, tools

import logging
_logger = logging.getLogger(__name__)


class PamVwDhhd(models.Model):
    _name = 'pam.vw.dhhd'
    _auto = False

    period_month_year = fields.Char(readonly=True)
    period = fields.Char(readonly=True)
    entry_date = fields.Date(index=True, readonly=True)
    name = fields.Char(readonly=True)
    supplier_name = fields.Char(readonly=True)
    coa_code = fields.Char(index=True, readonly=True)
    coa_name = fields.Char(readonly=True)
    amount = fields.Float(readonlye=True)
    account_payable = fields.Float(readonlye=True)
    other_debt = fields.Float(readonly=True)
    accrued_cost = fields.Float(readonly=True)
    payment_date = fields.Date(index=True, readonly=True)
    state = fields.Char(readonly=True)

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        sql = """
            create or replace view pam_vw_dhhd as (
                select 
                    row_number()over() as id,
                    concat(to_char(a.entry_date, 'MM'),(EXTRACT(year FROM a.entry_date))) as period_month_year,
                    concat(to_char(a.entry_date, 'Month'), (EXTRACT(year FROM a.entry_date))) as period,
                    a.entry_date,
                    a.name,
                    d.name as supplier_name,
                    c.code as coa_code,
                    c.name as coa_name,
                    (case
                        when c.code not in ('21111110', '21121110', '21131110') then (b.debit + b.credit)
                        else 0
                    end) as amount,
                    (case 
                        when c.code = '21111110' then (b.debit + b.credit)
                        else 0
                    end) as account_payable,
                    (case 
                        when c.code = '21121110' then (b.debit + b.credit)
                        else 0
                    end) as other_debt,
                    (case 
                        when c.code = '21131110' then (b.debit + b.credit)
                        else 0
                    end) as accrued_cost,
                    a.payment_date,
                    a.state                
                from 
                    pam_journal_entry a
                    inner join pam_journal_entry_line b on a.id = b.journal_entry_id
                    inner join pam_coa c on c.id = b.coa_id
                    inner join pam_vendor d on d.id = a.vendor_id
                where 
                    a.journal_type = 'ap' and a.state != 'draft')
            """
        self.env.cr.execute(sql)
