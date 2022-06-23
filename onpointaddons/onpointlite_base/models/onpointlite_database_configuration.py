from odoo import api, fields, models

class OnpointliteDatabaseConfiguration(models.Model):
    _name = 'onpointlite.database.configuration'

    name = fields.Char(required=True)
    url = fields.Char(string='URL', required=True)
    database = fields.Char(string='Database', required=True)

    def get_data(self, name):
        database_configuration = self.sudo().search([('name', '=', name)])

        datas = {
        	'name': database_configuration.name,
        	'url': database_configuration.url,
        	'database': database_configuration.database,
        }

        return datas