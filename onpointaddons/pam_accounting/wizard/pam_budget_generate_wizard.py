from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

class PamBudgetGenerateWizard(models.TransientModel):
    _name = 'pam.budget.generate.wizard'

    def _default_year(self):
        return str(datetime.today().year)

    def _get_years(self):
        current_year = int(self._default_year()) + 1
        min_year = current_year - 3
        results = []
        for year in range(min_year, current_year):
            results.append((str(year), str(year)))
        return results

    years = fields.Selection(_get_years, string='Tahun Anggaran', default=_default_year, required=True)
    budget_type = fields.Selection([
        ('ops', 'Biaya Operasi, Pemeliharaan dan Tenaga Kerja'),
        ('inv', 'Anggaran Kebutuhan Alat/alat dan Investasi (AKA)')
    ], required=True)

    def budget_by_department(self):
        sql = """
            select 
                a.years,
                a.department_id,
                b.name as department_name
            from
                pam_vw_budget as a
                inner join hr_department as b on a.department_id = b.id
            where
                a.years = %s
                and a.budget_type = %s
            group by
                a.years, a.department_id, b.name
        """

        self._cr.execute(sql, (self.years, self.budget_type))
        result = self._cr.fetchall()

        return result

    def budget_by_coa(self, department_id):
        sql = """
            select 
                a.years,
                a.department_id,
                a.coa_id,
                concat(b.code, ' - ', b.name) as coa_name
            from
                pam_vw_budget as a
                inner join pam_coa as b on a.coa_id = b.id
            where
                a.years = %s
                and a.budget_type = %s
                and a.department_id = %s
            group by
                a.years, a.department_id, a.coa_id, b.code, b.name
        """

        self._cr.execute(sql, (self.years, self.budget_type, department_id))
        result = self._cr.fetchall()

        return result

    def budget_by_job(self, department_id, coa_id):
        sql = """
            select 
                a.job_id,
                a.remark,
                a.month_1_entry as month_1,
                a.month_2_entry as month_2,
                a.month_3_entry as month_3,
                a.month_4_entry as month_4,
                a.month_5_entry as month_5,
                a.month_6_entry as month_6,
                a.month_7_entry as month_7,
                a.month_8_entry as month_8,
                a.month_9_entry as month_9,
                a.month_10_entry as month_10,
                a.month_11_entry as month_11,
                a.month_12_entry as month_12
            from
                pam_vw_budget as a
                inner join hr_job as b on a.job_id = b.id
            where
                a.years = %s
                and a.budget_type = %s
                and a.department_id = %s
                and a.coa_id = %s
        """

        self._cr.execute(sql, (self.years, self.budget_type, department_id, coa_id))
        result = self._cr.fetchall()

        return result

    def generate_data(self):
        if self.budget_type == 'ops':
            budget_type = 'Biaya Operasi, Pemeliharaan dan Tenaga Kerja'
        else:
            budget_type = 'Anggaran Kebutuhan Alat/alat dan Investasi (AKA)'

        create_budget = self.env['pam.budget'].create({
            'name': self.years + ' (' + budget_type + ')',
            'years': self.years,
            'budget_type': self.budget_type
            })

        budget_by_departments = self.budget_by_department()
        # vw_budgets = self.env['pam.vw.budget'].search([('years', '=', self.years), ('budget_type', '=', self.budget_type)])
        # vw_budgets = self.env['pam.vw.budget'].read_group([('years', '=', self.years), ('budget_type', '=', self.budget_type)], ['years', 'department_id'], ['years', 'department_id'])
        # raise ValidationError(_("%s")%(vw_budgets))
        # for vw_budget in vw_budgets:
        # vw_budgets = self.env['pam.vw.budget'].read_group([('years', '=', self.years), ('budget_type', '=', self.budget_type)], ['years', 'department_id'], ['years', 'department_id', 'month_1:sum(x.month_1 for x in month_1)'])
            # raise ValidationError(_("%s")%(vw_budget))

        line1_ids = []
        for years, department_id, department_name in budget_by_departments:
            vals1 = {
                # 'budget_id': create_budget.id,
                'years': years,
                'name': department_name,
                'department_id': department_id
                }

            row1 = (0, 0, vals1)
            line1_ids.append(row1)

        create_budget.sudo().update({
            'line1_ids': line1_ids
            })

        for line1 in create_budget.line1_ids:
            budget_by_coas = self.budget_by_coa(line1.department_id.id)
            line2_ids = []
            for years, department_id, coa_id, coa_name in budget_by_coas:
                
                budget_by_jobs = self.budget_by_job(department_id, coa_id)
                
                line3_ids = []
                for job_id, remark, month_1, month_2, month_3, month_4, month_5, month_6, month_7, month_8, month_9, month_10, month_11, month_12 in budget_by_jobs:
                    vals3 = {
                        'job_id': job_id,
                        'remark': remark,
                        'month_1': month_1,
                        'month_2': month_2,
                        'month_3': month_3,
                        'month_4': month_4,
                        'month_5': month_5,
                        'month_6': month_6,
                        'month_7': month_7,
                        'month_8': month_8,
                        'month_9': month_9,
                        'month_10': month_10,
                        'month_11': month_11,
                        'month_12': month_12
                        }

                    row3 = (0, 0, vals3)
                    line3_ids.append(row3)

                vals2 = {
                    # 'budget_id': line1.id,
                    'years': years,
                    'name': coa_name,
                    'department_id': department_id,
                    'coa_id': coa_id,
                    'line3_ids': line3_ids
                    }

                row2 = (0, 0, vals2)
                line2_ids.append(row2)

            #     budget_by_coas = self.budget_by_coa(department_id)

            line1.sudo().update({
                'line2_ids': line2_ids
                })