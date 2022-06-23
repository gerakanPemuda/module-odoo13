from odoo import api, models, fields, _
from odoo.exceptions import ValidationError
from datetime import datetime
from dateutil.relativedelta import relativedelta


class PamAssetDepreciationWizard(models.TransientModel):
    _name = 'pam.asset.depreciation.wizard'

    name = fields.Char()

    def generate_depreciation(self):

        assets = self.env['pam.asset'].search([('depreciation_id', '!=', False)])

        for asset in assets:

            self.env['pam.asset.line'].search([('asset_id','=', asset.id)]).unlink()

            if asset.years:
                depreciation_year = int(asset.years)
                if asset.months:
                    depreciation_month = int(asset.months)
                else:
                    depreciation_month = 1
                
                end_year = depreciation_year + asset.use_max

                annual_depreciation = asset.price_nett / asset.use_max
                monthly_depreciation = annual_depreciation / 12

                line_ids = []
                while depreciation_year <= end_year:

                    detail_ids = []
                    month_idx = 1

                    annual_depreciation_price = 0

                    while month_idx <= 12:

                        monthly_depreciation_price = monthly_depreciation

                        if depreciation_year == int(asset.years):
                            if month_idx < depreciation_month:
                                monthly_depreciation_price = 0
                        else:
                            if depreciation_year == int(end_year):
                                if month_idx > depreciation_month - 1:
                                    monthly_depreciation_price = 0
            
                        detail_vals = {
                            'months' : (str(month_idx)).zfill(2),
                            'years' : str(depreciation_year),
                            'price' : monthly_depreciation_price
                        }

                        row_detail = (0, 0, detail_vals)
                        detail_ids.append(row_detail)
                    
                        annual_depreciation_price = annual_depreciation_price + monthly_depreciation_price
                        month_idx = month_idx + 1
                    

                    line_vals = {
                        'years' : str(depreciation_year),
                        'price' : annual_depreciation_price,
                        'detail_ids' : detail_ids
                    }

                    row_line = (0, 0, line_vals)
                    line_ids.append(row_line)

                    depreciation_year = depreciation_year + 1

                asset_data = asset.env['pam.asset'].search([('id', '=', asset.id)])

                asset_data.sudo().update({
                    'line_ids' : line_ids
                })

