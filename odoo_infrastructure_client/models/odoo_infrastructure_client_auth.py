from datetime import datetime, timedelta

from odoo import models, fields, api


def get_default_expire():
    return fields.Datetime.to_string(datetime.now()+timedelta(hours=1))


class OdooInfrasstructureClientAuth(models.Model):
    _name = 'odoo.infrastructure.client.auth'
    _description = 'Odoo Infrastructure Client Auth'

    _log_access = False

    token_user = fields.Char()
    token_password = fields.Char()
    expire = fields.Datetime(
        required=True,
        default=get_default_expire)
    token_temp = fields.Char()

    @api.model
    def scheduler_cleanup_expired_entries(self):
        self.search([('expire', '<', fields.Datetime.now())]).unlink()
        return True
