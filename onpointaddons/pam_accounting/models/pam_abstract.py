from odoo import models, fields, api
from odoo.http import request
from datetime import datetime, timezone, timedelta
from time import mktime
from datetime import datetime
from dateutil.relativedelta import relativedelta
from ast import literal_eval

import logging
_logger = logging.getLogger(__name__)


class PamBalanceSheet(models.AbstractModel):
    _name = 'pam.balance.sheet'
    _description = 'Balance Sheet'

    def calculate_balance_sheet(self, start_date, end_date, report_type_line_code, report_configuration_name):

        sql = """
            select coalesce(sum(b.debit),0) as debit, coalesce(sum(b.credit),0) as credit
            from pam_journal_entry a
            inner join pam_journal_entry_line b on a.id = b.journal_entry_id
            where a.state != 'draft' and a.entry_date between %s and %s and b.coa_id in (

            select d.coa_id 
            from pam_report_configuration a
            inner join pam_report_type b on b.id = a.report_type_id
            inner join pam_report_configuration_line c on a.id = c.report_id
            inner join pam_report_configuration_detail d on c.id = d.report_line_id
            inner join pam_report_type_line e on e.id = c.group_id
            where b.code = 'NRC'and e.code = %s and c.name LIKE %s

            )
            """

        self._cr.execute(sql, (start_date, end_date, report_type_line_code, report_configuration_name))
        result = self._cr.fetchone()
        debit = 0
        credit = 0

        if result:
            debit = result[0]
            credit = result[1]

        return debit, credit

    def get_last_balance(self, report_type_line_code, report_configuration_name, period=0, range_start_date='1900-01-01', range_end_date='1900-01-01'):

        # _logger.debug("Period : %s", self.period)
        # _logger.debug("Range Start Date : %s", self.range_start_date)
        # _logger.debug("Range End Date : %s", self.range_end_date)

        if period == 0:
            period = 3

        if range_start_date == '1900-01-01':
            range_start_date = self.range_start_date
            range_end_date = self.range_end_date

        # _logger.debug("Period2 : %s", period)
        # _logger.debug("Range Start Date2 : %s", range_start_date)
        # _logger.debug("Range End Date2 : %s", range_end_date)

        pam_balance = self.env['pam.balance'].search([('name', '<', period)], order='name desc', limit=1)

        if pam_balance:
            ending_balance = self._get_ending_balance(pam_balance.id, report_type_line_code, report_configuration_name)

            # _logger.debug("Period : %s", self.period)

            if range_start_date < range_end_date:
                debit, credit = self.calculate_balance_sheet(range_start_date, range_end_date, report_type_line_code, report_configuration_name)
                ending_balance = ending_balance + (debit - credit)
                
                # _logger.debug("Debit Ending : %s", debit)
                # _logger.debug("Credit Ending : %s", credit)
                # _logger.debug("Ending Balance : %s", ending_balance)

        else:
            ending_balance = 0
        
        return ending_balance

    def _get_ending_balance(self, pam_balance_id, report_type_line_code, report_configuration_name):

        # _logger.debug("Report Type Line Code : %s", report_type_line_code)
        # _logger.debug("Report Config Name : %s", report_configuration_name)

        sql = """
            select coalesce(sum(a.ending_balance),0) as ending_balance
            from pam_balance_line a
            inner join pam_coa b on b.id = a.coa_id
            where a.balance_id = %s and a.coa_id in (

            select d.coa_id 
            from pam_report_configuration a
            inner join pam_report_type b on b.id = a.report_type_id
            inner join pam_report_configuration_line c on a.id = c.report_id
            inner join pam_report_configuration_detail d on c.id = d.report_line_id
            inner join pam_report_type_line e on e.id = c.group_id
            where b.code = 'NRC'and e.code = %s and c.name LIKE %s

            )

            """

        self._cr.execute(sql, (pam_balance_id, report_type_line_code, report_configuration_name))
        result = self._cr.fetchone()
        ending_balance = 0

        if result:
            ending_balance = result[0]

        return ending_balance

    def calculate_current_asset(self, start_date, end_date):

        debit, credit = self.calculate_balance_sheet(start_date, end_date, 'AL', '%')
        ending_balance = self.get_last_balance('AL', '%')

        current_asset = (ending_balance + debit) - credit

        return current_asset

    def calculate_productive_assets(self, start_date, end_date):

        current_asset = self.calculate_current_asset(start_date, end_date)

        report_type = self.env['pam.report.type'].search([('code', '=', 'NRC')])
        report_type_lines = self.env['pam.report.type.line'].search([('report_id', '=', report_type.id), ('code', 'in', ('AT',))], order='sequence asc')

        for report_type_line in report_type_lines:
            report_configuration = self.env['pam.report.configuration'].search([('report_type_id', '=', report_type.id)])
            report_configuration_lines = self.env['pam.report.configuration.line'].search([('report_id', '=', report_configuration.id), ('group_id', '=', report_type_line.id)], order='sequence asc')

            total_ar_this_year = 0
            total_ar_last_year = 0
            total_ar_diff = 0

            total_this_year = 0
            total_last_year = 0
            total_diff = 0
            for report_configuration_line in report_configuration_lines:
                if report_type_line.is_show == True:

                    debit, credit = self.calculate_balance_sheet(start_date, end_date, report_type_line.code, report_configuration_line.name)
                    ending_balance = self.get_last_balance(report_type_line.code, report_configuration_line.name)
                    value_this_year = (ending_balance + debit) - credit

                    total_this_year = total_this_year + value_this_year

                    if report_configuration_line.sequence == 13:
                        fix_asset = total_this_year

        result = current_asset + fix_asset
        return result
            
    def calculate_current_liabilities(self, start_date, end_date):
        debit, credit = self.calculate_balance_sheet(start_date, end_date, 'KL', '%')
        ending_balance = self.get_last_balance('KL', '%')

        current_liabilities = (ending_balance + credit) - debit

        return current_liabilities

    def calculate_long_term_debt(self, start_date, end_date):
        debit, credit = self.calculate_balance_sheet(start_date, end_date, 'HJP', '%')
        ending_balance = self.get_last_balance('HJP', '%')

        long_term_debt = (ending_balance + credit) - debit        

        return long_term_debt

    def calculate_equity(self, start_date, end_date):

        report_type = self.env['pam.report.type'].search([('code', '=', 'NRC')])
        report_type_lines = self.env['pam.report.type.line'].search([('report_id', '=', report_type.id), ('code', 'in', ('ES',))], order='sequence asc')

        total_equity_this_year = 0
        for report_type_line in report_type_lines:
            report_configuration = self.env['pam.report.configuration'].search([('report_type_id', '=', report_type.id)])
            report_configuration_lines = self.env['pam.report.configuration.line'].search([('report_id', '=', report_configuration.id), ('group_id', '=', report_type_line.id), ('sequence', 'in', (32,33))], order='sequence asc')

            for report_configuration_line in report_configuration_lines:

                if report_type_line.is_show == True:

                    debit, credit = self.calculate_balance_sheet(self.start_date, self.end_date, report_type_line.code, report_configuration_line.name)
                    ending_balance = self.get_last_balance(report_type_line.code, report_configuration_line.name)
                    value_this_year = (ending_balance + credit) - debit

                    total_equity_this_year = total_equity_this_year + value_this_year

        return total_equity_this_year

    def calculate_total_asset(self, start_date, end_date, pam_balance_id):

        sql = """
            select coalesce(sum(b.debit),0) as debit, coalesce(sum(b.credit),0) as credit
            from pam_journal_entry a
            inner join pam_journal_entry_line b on a.id = b.journal_entry_id
            where a.state != 'draft' and a.entry_date between %s and %s and b.coa_id in (

            select d.coa_id 
            from pam_report_configuration a
            inner join pam_report_type b on b.id = a.report_type_id
            inner join pam_report_configuration_line c on a.id = c.report_id
            inner join pam_report_configuration_detail d on c.id = d.report_line_id
            inner join pam_report_type_line e on e.id = c.group_id
            where b.code = 'NRC'and e.code IN ('AL', 'AT', 'ALL', 'PI')

            )
            """

        self._cr.execute(sql, (start_date, end_date))
        result = self._cr.fetchone()
        debit = 0
        credit = 0

        if result:
            debit = result[0]
            credit = result[1]

        sql_balance = """
            select coalesce(sum(a.ending_balance),0) as ending_balance
            from pam_balance_line a
            inner join pam_coa b on b.id = a.coa_id
            where a.balance_id = %s and a.coa_id in (

            select d.coa_id 
            from pam_report_configuration a
            inner join pam_report_type b on b.id = a.report_type_id
            inner join pam_report_configuration_line c on a.id = c.report_id
            inner join pam_report_configuration_detail d on c.id = d.report_line_id
            inner join pam_report_type_line e on e.id = c.group_id
            where b.code = 'NRC'and e.code IN ('AL', 'AT', 'ALL', 'PI')

            )

            """

        self._cr.execute(sql_balance, (pam_balance_id,))
        result = self._cr.fetchone()
        ending_balance = 0

        if result:
            ending_balance = result[0]

        total_asset = (ending_balance + debit) - credit

        return total_asset

    def calculate_total_liabilites(self, start_date, end_date, pam_balance_id):

        sql = """
            select coalesce(sum(b.debit),0) as debit, coalesce(sum(b.credit),0) as credit
            from pam_journal_entry a
            inner join pam_journal_entry_line b on a.id = b.journal_entry_id
            where a.state != 'draft' and a.entry_date between %s and %s and b.coa_id in (

            select d.coa_id 
            from pam_report_configuration a
            inner join pam_report_type b on b.id = a.report_type_id
            inner join pam_report_configuration_line c on a.id = c.report_id
            inner join pam_report_configuration_detail d on c.id = d.report_line_id
            inner join pam_report_type_line e on e.id = c.group_id
            where b.code = 'NRC'and e.code IN ('KL', 'KLL', 'HJP')

            )
            """

        self._cr.execute(sql, (start_date, end_date))
        result = self._cr.fetchone()
        debit = 0
        credit = 0

        if result:
            debit = result[0]
            credit = result[1]

        sql_balance = """
            select coalesce(sum(a.ending_balance),0) as ending_balance
            from pam_balance_line a
            inner join pam_coa b on b.id = a.coa_id
            where a.balance_id = %s and a.coa_id in (

            select d.coa_id 
            from pam_report_configuration a
            inner join pam_report_type b on b.id = a.report_type_id
            inner join pam_report_configuration_line c on a.id = c.report_id
            inner join pam_report_configuration_detail d on c.id = d.report_line_id
            inner join pam_report_type_line e on e.id = c.group_id
            where b.code = 'NRC'and e.code IN ('KL', 'KLL', 'HJP')

            )

            """

        self._cr.execute(sql_balance, (pam_balance_id,))
        result = self._cr.fetchone()
        ending_balance = 0

        if result:
            ending_balance = result[0]

        total_liabilities = (ending_balance + credit) - debit

        return total_liabilities

    def calculate_account_receivable(self, start_date, end_date, pam_balance_id):

        sql = """
            select coalesce(sum(b.debit),0) as debit, coalesce(sum(b.credit),0) as credit
            from pam_journal_entry a
            inner join pam_journal_entry_line b on a.id = b.journal_entry_id
            where a.state != 'draft' and a.entry_date between %s and %s and b.coa_id in (

            select d.coa_id 
            from pam_report_configuration a
            inner join pam_report_type b on b.id = a.report_type_id
            inner join pam_report_configuration_line c on a.id = c.report_id
            inner join pam_report_configuration_detail d on c.id = d.report_line_id
            inner join pam_report_type_line e on e.id = c.group_id
            where b.code = 'NRC'and e.code = 'AL' and c.sequence IN (3,4,5)

            )
            """

        self._cr.execute(sql, (start_date, end_date))
        result = self._cr.fetchone()
        debit = 0
        credit = 0

        if result:
            debit = result[0]
            credit = result[1]

        sql_balance = """
            select coalesce(sum(a.ending_balance),0) as ending_balance
            from pam_balance_line a
            inner join pam_coa b on b.id = a.coa_id
            where a.balance_id = %s and a.coa_id in (

            select d.coa_id 
            from pam_report_configuration a
            inner join pam_report_type b on b.id = a.report_type_id
            inner join pam_report_configuration_line c on a.id = c.report_id
            inner join pam_report_configuration_detail d on c.id = d.report_line_id
            inner join pam_report_type_line e on e.id = c.group_id
            where b.code = 'NRC'and e.code = 'AL' and c.sequence IN (3,4,5)

            )

            """

        self._cr.execute(sql_balance, (pam_balance_id,))
        result = self._cr.fetchone()
        ending_balance = 0

        if result:
            ending_balance = result[0]

        total_account_receivable = (ending_balance + debit) - credit

        return total_account_receivable

    def calculate_balance_sheet_by_coa(self, start_date, end_date, coa_ids):

        sql = """
            select coalesce(sum(b.debit),0) as debit, coalesce(sum(b.credit),0) as credit
            from pam_journal_entry a
            inner join pam_journal_entry_line b on a.id = b.journal_entry_id
            inner join pam_coa c on c.id = b.coa_id
            where a.state != 'draft' and a.entry_date between %s and %s and c.code in %s 
            """

        self._cr.execute(sql, (start_date, end_date, coa_ids))
        result = self._cr.fetchone()
        debit = 0
        credit = 0
        # _logger.debug("SQL Result : %s", result[0])

        if result:
            debit = result[0]
            credit = result[1]

        return debit, credit

    def get_last_balance_by_coa(self, coa_ids, period=0, range_start_date='1900-01-01', range_end_date='1900-01-01'):

        # _logger.debug("Period : %s", self.period)
        # _logger.debug("Range Start Date : %s", self.range_start_date)
        # _logger.debug("Range End Date : %s", self.range_end_date)

        if period == 0:
            period = '201901'
        else:
            period = self.period

        if range_start_date == '1900-01-01':
            range_start_date = self.range_start_date
            range_end_date = self.range_end_date

        pam_balance = self.env['pam.balance'].search([('name', '<', period)], order='name desc', limit=1)

        if pam_balance:
            ending_balance = self._get_ending_balance_by_coa(pam_balance.id, coa_ids)

            _logger.debug("Ending Balance : %s", ending_balance)

            if range_start_date < range_end_date:
                debit, credit = self.calculate_balance_sheet_by_coa(range_start_date, range_end_date, coa_ids)
                ending_balance = ending_balance + (debit - credit)
                
                # _logger.debug("Debit Ending : %s", debit)
                # _logger.debug("Credit Ending : %s", credit)

        else:
            ending_balance = 0
        
        return ending_balance

    def _get_ending_balance_by_coa(self, pam_balance_id, coa_ids):

        # _logger.debug("PAM Balance ID : %s", pam_balance_id)
        # _logger.debug("COA IDS : %s", coa_ids)

        sql = """
            select coalesce(sum(a.ending_balance),0) as ending_balance
            from pam_balance_line a
            inner join pam_coa b on b.id = a.coa_id
            where a.balance_id = %s and b.code in %s

            """

        self._cr.execute(sql, (pam_balance_id, coa_ids))
        result = self._cr.fetchone()
        ending_balance = 0

        if result:
            ending_balance = result[0]

        return ending_balance

    def calculate_profit_loss_last_year(self, start_date, end_date, period=0):

        result = 0

        profit_loss_last_year_coa = ('24181110', '71111110')
        profit_loss_comp = ('24191120',)

        debit, credit = self.calculate_balance_sheet_by_coa(self.start_date, self.end_date, profit_loss_last_year_coa)
        ending_balance = self.get_last_balance_by_coa(profit_loss_last_year_coa)
        result_profit_loss = (ending_balance + credit) - debit

        # _logger.debug("Debit Last Year : %s", debit)
        # _logger.debug("Credit Last Year : %s", credit)
        # _logger.debug("Ending Balance Last Year : %s", ending_balance)

        debit, credit = self.calculate_balance_sheet_by_coa(self.start_date, self.end_date, profit_loss_comp)
        ending_balance = self.get_last_balance_by_coa(profit_loss_comp)
        result_profit_loss_comp = (ending_balance + credit) - debit

        # _logger.debug("Debit Comp Last Year : %s", debit)
        # _logger.debug("Credit Comp Last Year : %s", credit)
        # _logger.debug("Ending Balance Comp Last Year : %s", ending_balance)

        if period == 0:
            period = '201901'
        else:
            period = self.period

        pam_balance = self.env['pam.balance'].search([('name', '<', period)], order='name desc', limit=1)

        before_month_start_date = str(int(self.years) - 1) + '-' + self.months + '-01'
        before_month_end_date = (datetime.strptime(str(int(self.years) - 1) + '-' + self.months + '-01', "%Y-%m-%d") + relativedelta(months=1) - relativedelta(days=1)).strftime("%Y-%m-%d")

        profit_loss_after_tax = self.calculate_profit_loss_after_tax(start_date, self.end_date)
        result_profit_loss_this_year = pam_balance.profit_after_tax + profit_loss_after_tax
        # value_last_year = self.calculate_profit_loss_after_tax(before_month_start_date, before_month_end_date)

        result = result_profit_loss + result_profit_loss_comp + result_profit_loss_this_year - profit_loss_after_tax 

        return result


class PamProfitLoss(models.AbstractModel):
    _name = 'pam.profit.loss'
    _description = 'Profit / Loss'

    def calculate_profit_loss(self, start_date, end_date, report_type_line_code, report_configuration_name, coa_type):
        sql = """
            select coalesce(sum(b.debit),0) as debit, coalesce(sum(b.credit),0) as credit
            from pam_journal_entry a
            inner join pam_journal_entry_line b on a.id = b.journal_entry_id
            where a.state != 'draft' and a.entry_date between %s and %s and b.coa_id in (

            select d.coa_id 
            from pam_report_configuration a
            inner join pam_report_type b on b.id = a.report_type_id
            inner join pam_report_configuration_line c on a.id = c.report_id
            inner join pam_report_configuration_detail d on c.id = d.report_line_id
            inner join pam_report_type_line e on e.id = c.group_id
            where b.code = 'LRB' and e.code = %s and c.name LIKE %s

            )
            """

        self._cr.execute(sql, (start_date, end_date, report_type_line_code, report_configuration_name))
        result = self._cr.fetchone()
        debit = 0
        credit = 0
        # _logger.debug("SQL Result : %s", result[0])

        if result:
            debit = result[0]
            credit = result[1]

        value = 0
        if coa_type == 'debit':
            value = debit - credit
        else:
            value = credit - debit

        return value

    def calculate_gross_profit_loss(self, start_date, end_date):

        report_type = self.env['pam.report.type'].search([('code', '=', 'LRB')])
        report_type_line = self.env['pam.report.type.line'].search([('report_id', '=', report_type.id), ('code', '=', 'PU')])

        operating_revenues = self.calculate_profit_loss(start_date, end_date, report_type_line.code, "%", report_type_line.coa_type)

        report_type = self.env['pam.report.type'].search([('code', '=', 'LRB')])
        report_type_line = self.env['pam.report.type.line'].search([('report_id', '=', report_type.id), ('code', '=', 'BLU')])

        direct_business_cost = self.calculate_profit_loss(start_date, end_date, report_type_line.code, "%", report_type_line.coa_type)

        result = operating_revenues - direct_business_cost

        return result

    def calculate_profit_loss_business(self, start_date, end_date):

        gross_profit_loss = self.calculate_gross_profit_loss(start_date, end_date)

        report_type = self.env['pam.report.type'].search([('code', '=', 'LRB')])
        report_type_line = self.env['pam.report.type.line'].search([('report_id', '=', report_type.id), ('code', '=', 'BTU')])

        indirect_business_cost = self.calculate_profit_loss(start_date, end_date, report_type_line.code, "%", report_type_line.coa_type)

        result = gross_profit_loss - indirect_business_cost
        
        return result

    def calculate_profit_loss_before_tax(self, start_date, end_date):

        profit_loss_business = self.calculate_profit_loss_business(start_date, end_date)

        report_type = self.env['pam.report.type'].search([('code', '=', 'LRB')])
        report_type_line = self.env['pam.report.type.line'].search([('report_id', '=', report_type.id), ('code', '=', 'PLL')])

        other_income_cost = self.calculate_profit_loss(start_date, end_date, report_type_line.code, "%", report_type_line.coa_type)

        result = profit_loss_business + other_income_cost
        
        return result

    def calculate_profit_loss_after_tax(self, start_date, end_date):

        profit_loss_before_tax = self.calculate_profit_loss_before_tax(start_date, end_date)

        report_type = self.env['pam.report.type'].search([('code', '=', 'LRB')])
        report_type_line = self.env['pam.report.type.line'].search([('report_id', '=', report_type.id), ('code', '=', 'TPP')])

        tax = self.calculate_profit_loss(start_date, end_date, report_type_line.code, "%", report_type_line.coa_type)

        result = profit_loss_before_tax - tax
        
        return result

    def calculate_direct_operation_cost(self, start_date, end_date):
        sql = """
            select coalesce(sum(b.debit),0) as debit, coalesce(sum(b.credit),0) as credit
            from pam_journal_entry a
            inner join pam_journal_entry_line b on a.id = b.journal_entry_id
            where a.state != 'draft' and a.entry_date between %s and %s and b.coa_id in (

            select d.coa_id 
            from pam_report_configuration a
            inner join pam_report_type b on b.id = a.report_type_id
            inner join pam_report_configuration_line c on a.id = c.report_id
            inner join pam_report_configuration_detail d on c.id = d.report_line_id
            inner join pam_report_type_line e on e.id = c.group_id
            where b.code = 'LRB' and e.code in ('BLU')
            )
            """

        self._cr.execute(sql, (start_date, end_date))
        result = self._cr.fetchone()
        debit = 0
        credit = 0
        # _logger.debug("SQL Result : %s", result[0])

        if result:
            debit = result[0]
            credit = result[1]

        value = debit - credit

        return value

    def calculate_indirect_operation_cost(self, start_date, end_date):
        sql = """
            select coalesce(sum(b.debit),0) as debit, coalesce(sum(b.credit),0) as credit
            from pam_journal_entry a
            inner join pam_journal_entry_line b on a.id = b.journal_entry_id
            where a.state != 'draft' and a.entry_date between %s and %s and b.coa_id in (

            select d.coa_id 
            from pam_report_configuration a
            inner join pam_report_type b on b.id = a.report_type_id
            inner join pam_report_configuration_line c on a.id = c.report_id
            inner join pam_report_configuration_detail d on c.id = d.report_line_id
            inner join pam_report_type_line e on e.id = c.group_id
            where b.code = 'LRB' and e.code in ('BTU')
            )
            """

        self._cr.execute(sql, (start_date, end_date))
        result = self._cr.fetchone()
        debit = 0
        credit = 0
        # _logger.debug("SQL Result : %s", result[0])

        if result:
            debit = result[0]
            credit = result[1]

        value = debit - credit


        return value


    def calculate_operation_cost(self, start_date, end_date):
        sql = """
            select coalesce(sum(b.debit),0) as debit, coalesce(sum(b.credit),0) as credit
            from pam_journal_entry a
            inner join pam_journal_entry_line b on a.id = b.journal_entry_id
            where a.state != 'draft' and a.entry_date between %s and %s and b.coa_id in (

            select d.coa_id 
            from pam_report_configuration a
            inner join pam_report_type b on b.id = a.report_type_id
            inner join pam_report_configuration_line c on a.id = c.report_id
            inner join pam_report_configuration_detail d on c.id = d.report_line_id
            inner join pam_report_type_line e on e.id = c.group_id
            where b.code = 'LRB' and e.code in ('BLU', 'BTU')
            )
            """

        self._cr.execute(sql, (start_date, end_date))
        result = self._cr.fetchone()
        debit = 0
        credit = 0
        # _logger.debug("SQL Result : %s", result[0])

        if result:
            debit = result[0]
            credit = result[1]

        value = debit - credit


        return value

    def calculate_water_price(self, start_date, end_date, coa_type):
        sql = """
            select coalesce(sum(b.debit),0) as debit, coalesce(sum(b.credit),0) as credit
            from pam_journal_entry a
            inner join pam_journal_entry_line b on a.id = b.journal_entry_id
            inner join pam_coa c on c.id = b.coa_id
            where a.state != 'draft' and a.entry_date between %s and %s and c.code = '31111110'
            """


        self._cr.execute(sql, (start_date, end_date))
        result = self._cr.fetchone()
        debit = 0
        credit = 0
        # _logger.debug("SQL Result : %s", result[0])

        if result:
            debit = result[0]
            credit = result[1]

        value = 0
        if coa_type == 'debit':
            value = debit - credit
        else:
            value = credit - debit

        return value


class PamCostBreakdown(models.AbstractModel):
    _name = 'pam.cost.breakdown'
    _description = 'Cost Breakdown'


    def calculate_cost_breakdown(self, start_date, end_date, report_type_line_code, report_configuration_name):

        sql = """
            select coalesce(sum(b.debit),0) as debit, coalesce(sum(b.credit),0) as credit
            from pam_journal_entry a
            inner join pam_journal_entry_line b on a.id = b.journal_entry_id
            where a.state != 'draft' and a.entry_date between %s and %s and b.coa_id in (

            select d.coa_id 
            from pam_report_configuration a
            inner join pam_report_type b on b.id = a.report_type_id
            inner join pam_report_configuration_line c on a.id = c.report_id
            inner join pam_report_configuration_detail d on c.id = d.report_line_id
            inner join pam_report_type_line e on e.id = c.group_id
            where b.code = 'LPB'and e.code = %s and c.name LIKE %s

            )
            """


        self._cr.execute(sql, (start_date, end_date, report_type_line_code, report_configuration_name))
        result = self._cr.fetchone()
        debit = 0
        credit = 0

        if result:
            debit = result[0]
            credit = result[1]

        value = debit - credit

        return value

    def calculate_cost_breakdown_multiple(self, start_date, end_date, report_type_line_code, report_configuration_name):

        sql = """
            select coalesce(sum(b.debit),0) as debit, coalesce(sum(b.credit),0) as credit
            from pam_journal_entry a
            inner join pam_journal_entry_line b on a.id = b.journal_entry_id
            where a.state != 'draft' and a.entry_date between %s and %s and b.coa_id in (

            select d.coa_id 
            from pam_report_configuration a
            inner join pam_report_type b on b.id = a.report_type_id
            inner join pam_report_configuration_line c on a.id = c.report_id
            inner join pam_report_configuration_detail d on c.id = d.report_line_id
            inner join pam_report_type_line e on e.id = c.group_id
            where b.code = 'LPB'and e.code in %s and c.name in %s

            )
            """


        self._cr.execute(sql, (start_date, end_date, report_type_line_code, report_configuration_name))
        result = self._cr.fetchone()
        debit = 0
        credit = 0

        if result:
            debit = result[0]
            credit = result[1]

        value = debit - credit

        return value



    def calculate_reduction(self, start_date, end_date):

        sql = """
            select coalesce(sum(b.debit),0) as debit, coalesce(sum(b.credit),0) as credit
            from pam_journal_entry a
            inner join pam_journal_entry_line b on a.id = b.journal_entry_id
            where a.state != 'draft' and a.entry_date between %s and %s and b.coa_id in (

            select d.coa_id 
            from pam_report_configuration a
            inner join pam_report_type b on b.id = a.report_type_id
            inner join pam_report_configuration_line c on a.id = c.report_id
            inner join pam_report_configuration_detail d on c.id = d.report_line_id
            inner join pam_report_type_line e on e.id = c.group_id
            where b.code = 'LPB'and c.name = 'Biaya Penyusutan'
            )
            """


        self._cr.execute(sql, (start_date, end_date))
        result = self._cr.fetchone()
        debit = 0
        credit = 0

        if result:
            debit = result[0]
            credit = result[1]

        value = debit - credit

        return value        


class PamCashFlow(models.AbstractModel):
    _name = 'pam.cash.flow'
    _description = 'Cash Flow'


    def calculate_income(self, start_date, end_date, report_type_line_code, report_configuration_name, coa_type):
        sql = """
            select coalesce(sum(b.debit),0) as debit, coalesce(sum(b.credit),0) as credit
            from pam_journal_entry a
            inner join pam_journal_entry_line b on a.id = b.journal_entry_id
            where a.state != 'draft' and a.journal_type = 'ci' and a.entry_date between %s and %s and b.coa_id in (

            select d.coa_id 
            from pam_report_configuration a
            inner join pam_report_type b on b.id = a.report_type_id
            inner join pam_report_configuration_line c on a.id = c.report_id
            inner join pam_report_configuration_detail d on c.id = d.report_line_id
            inner join pam_report_type_line e on e.id = c.group_id
            where b.code = 'LAK'and e.code = %s and c.name LIKE %s

            )
            """

        _logger.debug("Start Date : %s", start_date)
        _logger.debug("End Date : %s", end_date)

        self._cr.execute(sql, (start_date, end_date, report_type_line_code, report_configuration_name))
        result = self._cr.fetchone()
        debit = 0
        credit = 0

        if result:
            debit = result[0]
            credit = result[1]

        value = 0
        if coa_type == 'debit':
            value = debit - credit
        else:
            value = credit - debit

        return value

    def calculate_other_income(self, start_date, end_date):
        sql = """
            select coalesce(SUM(x.balance), 0) as balance
            from (
            select c.code, c."name", c.parent_id, d."position", d.name as coa_type_name,
            case 
            when b.debit > 0 then (b.debit - b.credit)
            when b.credit > 0 then (b.credit - b.debit)
            end as balance
            from pam_journal_entry a
            inner join pam_journal_entry_line b on a.id = b.journal_entry_id
            inner join pam_coa c on c.id = b.coa_id
            inner join pam_coa_type d on d.id = c.coa_type_id
            where a.state != 'draft' and a.journal_type = 'ci' and a.entry_date between %s and %s and b.coa_id not in (

            select d.coa_id 
            from pam_report_configuration a
            inner join pam_report_type b on b.id = a.report_type_id
            inner join pam_report_configuration_line c on a.id = c.report_id
            inner join pam_report_configuration_detail d on c.id = d.report_line_id
            inner join pam_report_type_line e on e.id = c.group_id
            where b.code = 'LAK'and e.code in ('PO', 'PNO'))
            ) x
            inner join pam_coa y on y.id = x.parent_id
            where trim(lower(y.name)) not in ('kas', 'bank')

            """


        self._cr.execute(sql, (start_date, end_date))
        result = self._cr.fetchone()
        value = 0
        if result:
            value = result[0]

        return value


    def calculate_cost(self, start_date, end_date, report_type_line_code, report_configuration_name):
        sql = """
            select COALESCE(SUM(z.balance),0) as balance
            from (
            select c.code, c."name", c.parent_id, d."position", d.name as coa_type_name,
            b.debit, b.credit,
            case 
            when d."position" = 'debit' then (b.debit - b.credit)
            when d."position" = 'credit' then (b.credit - b.debit)
            end as balance
            from pam_journal_entry a
            inner join pam_journal_entry_line b on a.id = b.journal_entry_id
            inner join pam_coa c on c.id = b.coa_id
            inner join pam_coa_type d on d.id = c.coa_type_id
            where a.id in (
            select x.link_journal_id
            from pam_journal_entry x
            where x.journal_type = 'co' and x.entry_date between %s and %s
            ) 
            and a.journal_type = 'ap' 
            and b.coa_id in (

            select d.coa_id 
            from pam_report_configuration a
            inner join pam_report_type b on b.id = a.report_type_id
            inner join pam_report_configuration_line c on a.id = c.report_id
            inner join pam_report_configuration_detail d on c.id = d.report_line_id
            inner join pam_report_type_line e on e.id = c.group_id
            where b.code = 'LAK'and e.code = %s  and c.name LIKE %s
            )
            ) z
            """


        self._cr.execute(sql, (start_date, end_date, report_type_line_code, report_configuration_name))
        result = self._cr.fetchone()
        value = 0
        if result:
            value = result[0]

        return value


    def calculate_cash_turnover(self, report_type_code, current_month_start_date, current_month_end_date, before_month_start_date, before_month_end_date):

        report_type = self.env['pam.report.type'].search([('code', '=', 'LAK')])
        report_type_lines = self.env['pam.report.type.line'].search([('code', 'in', report_type_code)])

        total_value_this_year = 0
        total_value_last_year = 0
        total_budget_this_year = 0
        total_value_this_year_until_this_month = 0
        total_value_last_year_until_this_month = 0
        total_budget_this_year_until_this_month = 0

        for report_type_line in report_type_lines:
            report_configuration = self.env['pam.report.configuration'].search([('report_type_id', '=', report_type.id)])
            report_configuration_lines = self.env['pam.report.configuration.line'].search([('report_id', '=', report_configuration.id), ('group_id', '=', report_type_line.id)], order='sequence asc')

            for report_configuration_line in report_configuration_lines:

                if report_type_line.code in ('PO', 'PNO'):
                    if report_configuration_line.name == '- Penerimaan Kas rupa-rupa operasional':
                        value_this_year = self.calculate_other_income(current_month_start_date, current_month_end_date)
                        value_last_year = self.calculate_other_income(before_month_start_date, before_month_end_date)
                    else:
                        value_this_year = self.calculate_income(current_month_start_date, current_month_end_date, report_type_line.code, report_configuration_line.name, 'credit')
                        value_last_year = self.calculate_income(before_month_start_date, before_month_end_date, report_type_line.code, report_configuration_line.name, 'credit')
                else:
                    value_this_year = (self.calculate_cost(current_month_start_date, current_month_end_date, report_type_line.code, report_configuration_line.name)) * -1
                    value_last_year = (self.calculate_cost(before_month_start_date, before_month_end_date, report_type_line.code, report_configuration_line.name)) * -1


                total_value_this_year += value_this_year
                total_value_last_year += value_last_year
                total_budget_this_year = 0
                total_value_this_year_until_this_month += value_this_year
                total_value_last_year_until_this_month += value_last_year
                total_budget_this_year_until_this_month = 0
        
        return total_value_this_year, total_value_last_year, total_budget_this_year, total_value_this_year_until_this_month, total_value_last_year_until_this_month, total_budget_this_year_until_this_month


