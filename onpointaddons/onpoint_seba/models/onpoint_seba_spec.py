from odoo import models, fields, api
from odoo.http import request
from datetime import datetime, timezone, timedelta
from time import mktime
from ast import literal_eval

import logging
_logger = logging.getLogger(__name__)


class OnpointSebaSpec(models.Model):
    _name = 'onpoint.seba.spec'

    name = fields.Char(required=True)
    pos = fields.Integer()
    length = fields.Integer(default=1)
    function_name = fields.Char(required=True)
    table_name = fields.Char()
    field_name = fields.Char()
