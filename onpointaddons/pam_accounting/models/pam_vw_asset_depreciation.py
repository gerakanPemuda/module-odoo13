from odoo import models, fields, api, tools

import logging
_logger = logging.getLogger(__name__)


class PamVwAssetDepreciation(models.Model):
    _name = 'pam.vw.asset.depreciation'
    _auto = False

    category_id = fields.Many2one('pam.asset.category', index=True, readonly=True)
    name = fields.Char(readonly=True)
    coa_id = fields.Many2one('pam.coa', index=True, readonly=True)
    months = fields.Char(index=True, readonly=True)
    years = fields.Char(index=True, readonly=True)
    price = fields.Float(readonly=True)
    depreciation_months = fields.Char(index=True, readonly=True)
    depreciation_years = fields.Char(index=True, readonly=True)
    depreciation_price = fields.Float(readonly=True)


    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        sql = """
    		create or replace view pam_vw_asset_depreciation as (
                select 
	    			row_number()over() as id,
                    a.category_id, 
                    a.name, 
                    a.coa_id, 
                    a.months, 
                    a.years, 
                    a.price, 
                    c.months as depreciation_months, 
                    c.years as depreciation_years, 
                    c.price as depreciation_price
                from pam_asset a
                inner join pam_asset_line b on a.id = b.asset_id
                inner join pam_asset_detail c on b.id = c.asset_line_id)
    	"""
        self.env.cr.execute(sql)
