from datetime import datetime, timedelta

from odoo import models, fields, api


class OdooInfrasstructureClientAuth(models.Model):
    _name = 'odoo.infrastructure.client.auth'
    _description = 'Odoo Infrastructure Client Auth'

    _log_access = False

    token_user = fields.Char()
    token_password = fields.Char()
    expire = fields.Datetime(
        required=True,
        default=(fields.Datetime.to_string(datetime.now()+timedelta(hours=1))))

    @api.model
    def _scheduler_clear_non_valid_temporary_auth_data(self):
        self.search([('expire', '<', fields.Datetime.now())]).unlink()
