from odoo import models, fields, api
from datetime import datetime, timedelta


class OnpointMeterType(models.Model):
    _name = 'onpoint.meter.type'

    name = fields.Char(required=True)


class OnpointMeterBrand(models.Model):
    _name = 'onpoint.meter.brand'

    name = fields.Char(required=True)


class OnpointMeterSize(models.Model):
    _name = 'onpoint.meter.size'

    name = fields.Char(required=True)


class OnpointPipeMaterial(models.Model):
    _name = 'onpoint.pipe.material'

    name = fields.Char(required=True)


class OnpointValveControl(models.Model):
    _name = 'onpoint.valve.control'

    name = fields.Char(required=True)
