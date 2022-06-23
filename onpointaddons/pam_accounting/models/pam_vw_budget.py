from odoo import models, fields, api, tools


class PamVwBudget(models.Model):
    _name = 'pam.vw.budget'
    _auto = False

    years = fields.Char(string='Tahun Anggaran', index=True, readonly=True)
    budget_type = fields.Selection([
        ('ops', 'Biaya Operasi, Pemeliharaan dan Tenaga Kerja'),
        ('inv', 'Anggaran Kebutuhan Alat/alat dan Investasi (AKA)')
    ], readonly=True)
    department_id = fields.Many2one('hr.department', string='Department', index=True, readonly=True)
    coa_id = fields.Many2one('pam.coa', string='Kode Akun', index=True, readonly=True)
    job_id = fields.Many2one('hr.job', index=True, readonly=True)
    remark = fields.Char(string='Keterangan', readonly=True)
    month_1 = fields.Float(string='I', readonly=True)
    month_2 = fields.Float(string='II', readonly=True)
    month_3 = fields.Float(string='III', readonly=True)
    month_4 = fields.Float(string='IV', readonly=True)
    month_5 = fields.Float(string='V', readonly=True)
    month_6 = fields.Float(string='VI', readonly=True)
    month_7 = fields.Float(string='VII', readonly=True)
    month_8 = fields.Float(string='VIII', readonly=True)
    month_9 = fields.Float(string='IX', readonly=True)
    month_10 = fields.Float(string='X', readonly=True)
    month_11 = fields.Float(string='XI', readonly=True)
    month_12 = fields.Float(string='XII', readonly=True)
    month_1_entry = fields.Float(string='I', readonly=True)
    month_2_entry = fields.Float(string='II', readonly=True)
    month_3_entry = fields.Float(string='III', readonly=True)
    month_4_entry = fields.Float(string='IV', readonly=True)
    month_5_entry = fields.Float(string='V', readonly=True)
    month_6_entry = fields.Float(string='VI', readonly=True)
    month_7_entry = fields.Float(string='VII', readonly=True)
    month_8_entry = fields.Float(string='VIII', readonly=True)
    month_9_entry = fields.Float(string='IX', readonly=True)
    month_10_entry = fields.Float(string='X', readonly=True)
    month_11_entry = fields.Float(string='XI', readonly=True)
    month_12_entry = fields.Float(string='XII', readonly=True)


    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        sql = """
    		create or replace view pam_vw_budget as (
	    		select
	    			row_number()over() as id,
	    			a.years,
					a.budget_type,
					a.department_id,
					b.coa_id,
					a.job_id,
					b.remark,
				 	b.month_1,
				 	b.month_2,
				 	b.month_3,
				 	b.month_4,
				 	b.month_5,
				 	b.month_6,
				 	b.month_7,
				 	b.month_8,
				 	b.month_9,
				 	b.month_10,
				 	b.month_11,
				 	b.month_12,
                    b.month_1_entry,
                    b.month_2_entry,
                    b.month_3_entry,
                    b.month_4_entry,
                    b.month_5_entry,
                    b.month_6_entry,
                    b.month_7_entry,
                    b.month_8_entry,
                    b.month_9_entry,
                    b.month_10_entry,
                    b.month_11_entry,
                    b.month_12_entry
				from
					pam_budget_entry as a
					inner join pam_budget_entry_line as b on a.id = b.budget_entry_id
				where a.state = 'approved')
    	"""
        self.env.cr.execute(sql)
