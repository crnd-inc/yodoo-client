from odoo import models, fields, registry, SUPERUSER_ID, api


class Users(models.Model):
    _inherit = "res.users"

    @classmethod
    def _login(cls, db, login, password):
        if not password or not login:
            return False

        with registry(db).cursor() as cr:
            cr.execute(
                'SELECT id FROM odoo_infrastructure_client_auth '
                'WHERE token_user=%s AND token_password=%s AND expire>%s;',
                (login, password, fields.Datetime.now())
            )
            if cr.fetchone():
                return SUPERUSER_ID
        return super(Users, cls)._login(db, login, password)

    @api.model
    def check_credentials(self, password):
        self.env.cr.execute(
            'SELECT id FROM odoo_infrastructure_client_auth '
            'WHERE token_password=%s', (password,)
        )
        if self.env.cr.fetchone():
            return

        return super(Users, self).check_credentials(password)
