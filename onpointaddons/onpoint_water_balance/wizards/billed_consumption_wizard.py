import xlrd
import tempfile
import binascii
import time
from datetime import date, datetime
from odoo.exceptions import Warning, UserError
from odoo import models, fields, exceptions, api, _


class BilledConsumptionWizard(models.TransientModel):
    _name = 'billed.consumption.wizard'
    _description = 'Billed Consumption Import Wizard'

    water_balance_id = fields.Many2one('onpoint.water.balance')
    worksheet = fields.Binary(string='Excel File', help='Upload your Excel file')

    def action_billed_consumption_import(self):
        try:
            fp = tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx")
            fp.write(binascii.a2b_base64(self.worksheet))
            fp.seek(0)
            values = {}
            workbook = xlrd.open_workbook(fp.name)
            sheet = workbook.sheet_by_index(0)

        except:
            raise Warning(_("Invalid file!"))
        for row_no in range(sheet.nrows):
            val = {}
            if row_no <= 0:
                fields = map(lambda row: row.value.encode('utf-8'), sheet.row(row_no))
            else:
                line = list(
                    map(lambda row: isinstance(row.value, bytes) and row.value.encode('utf-8') or str(row.value),
                        sheet.row(row_no)))
                values.update({
                    'water_balance_id': self.water_balance_id.id,
                    'name': line[0],
                    'quantity': line[1]
                })
                self.env['onpoint.water.balance.billed.meter.lines'].create(values)
