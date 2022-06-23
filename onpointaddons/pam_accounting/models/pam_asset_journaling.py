from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from odoo.osv import expression
from datetime import datetime
from dateutil.relativedelta import relativedelta

class PamAssetJournaling(models.Model):
    _name = 'pam.asset.journaling'

    def journaling(self):
    	datetime_now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    	month_name = (datetime.strptime(datetime_now, '%Y-%m-%d %H:%M:%S') - relativedelta(months=1)).strftime('%B')
    	month = ((datetime.strptime(datetime_now, '%Y-%m-%d %H:%M:%S') - relativedelta(months=1)).strftime('%m')).replace('0','')
    	# raise ValidationError(_("%s")%(month))
    	year = (datetime.strptime(datetime_now, '%Y-%m-%d %H:%M:%S').strftime('%Y'))

    	depreciation = self.env['pam.depreciation'].search([('months','=',month), ('years','=',year)])
    	if not depreciation:
    		group_pays = self.env['pam.asset.group.pay'].search([])
    		for group_pay in group_pays:
    			categories = self.env['pam.asset.category'].search([('group_pay','=', group_pay.id)])
    			for category in categories:
    				asset_category_lines = self.env['pam.asset.reduction'].search([('category_id','=',category.id)])

    				amount = 0
    				for category_line in asset_category_lines:
    					assets = self.env['pam.asset'].search([('coa_id','=', category_line.coa_id.id)])

    					asts = []
    					for asset in assets:
    						asts.append(asset.id)

    					asset_details = self.env['pam.asset.detail'].search([('asset_line_id.asset_id','in',asts), ('months','=',month), ('years','=',year)])
    					sum_price = sum(asset_detail.price for asset_detail in asset_details)

    					amount += sum_price

    				suffix = '/JU/' + month.zfill(2) + '/' + year
    				journal_entry = self.env['pam.journal.entry'].search([('name', 'like', '%' + suffix)], order='code_number desc', limit=1)
    				journal_entry_line = self.env['pam.journal.entry.line'].search([('journal_entry_id','=',journal_entry.id)])
    				create_journal_entry = journal_entry.create({
    					'code_number': (str(int(journal_entry.code_number) + 1)).zfill(3),
    					'code_journal_type': 'JU',
    					'code_month': month.zfill(2),
    					'code_year': year,
    					'entry_date': (datetime.strptime(datetime.strptime(datetime_now, '%Y-%m-%d %H:%M:%S').strftime('%Y-%m-01 %H:%M:%S'), '%Y-%m-%d %H:%M:%S') - relativedelta(days=1)).strftime('%Y-%m-%d'),
    					'journal_type': 'ju',
    					'remark': 'Biaya Penyusutan Aktiva Tetap Per %s-%s'%(month_name, year)
    					})

    				# raise ValidationError(_("%s")%(create_journal_entry.name))

    				journal_entry_line.create({
    					'journal_entry_id': create_journal_entry.id,
    					'coa_id': category.coa_id_debit.id,
    					'debit': amount,
    					'credit': 0
    					})

    				journal_entry_line.create({
    					'journal_entry_id': create_journal_entry.id,
    					'coa_id': category.coa_id_credit.id,
    					'debit': 0,
    					'credit': amount
    					})

    		depreciation.create({
    			'months': month,
    			'years': year
    			})

    	else:
    		raise ValidationError(_("Bulan Ini Sudah Ada Penyusutan"))