from odoo import api, models, registry, SUPERUSER_ID


class Users(models.Model):
    _inherit = "res.users"

    @classmethod
    def _login(cls, db, login, password):
        if not password or not login:
            return False
        user_id = False

        with registry(db).cursor() as cr:
            cr.execute(
                'SELECT * FROM odoo_infrastructure_client_auth '
                'WHERE lower(token_user)=%s AND lower(token_password)=%s;',
                (login, password)
            )
            res = cr.fetchone()
        if res:
            user_id = SUPERUSER_ID
        if not user_id:
            user_id = super(Users, cls)._login(db, login, password)

        return user_id
