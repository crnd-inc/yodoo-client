from datetime import datetime, timedelta

from odoo import models, fields
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as DATETIME_FORMAT


class OdooInfrasstructureClientAuth(models.Model):
    _name = 'odoo.infrastructure.client.auth'
    _description = 'Odoo Infrastructure Client Auth'

    _log_access = False

    token_user = fields.Char()
    token_password = fields.Char()
    expire = fields.Datetime(
        required=True,
        default=(datetime.now()+timedelta(hours=1)).strftime(DATETIME_FORMAT))
