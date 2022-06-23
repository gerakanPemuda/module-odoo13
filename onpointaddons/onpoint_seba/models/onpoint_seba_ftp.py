from odoo import models, fields, api
from odoo.http import request
from datetime import datetime, timezone, timedelta
from time import mktime
from ast import literal_eval

import logging

_logger = logging.getLogger(__name__)


class OnpointSebaFTP(models.Model):
    _name = 'onpoint.seba.ftp'

    name = fields.Char(required=True)
    username = fields.Char(required=True)
    password = fields.Char(required=True)
