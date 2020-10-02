from odoo import models, SUPERUSER_ID, api


class Users(models.Model):
    _inherit = "res.users"

    @classmethod
    def _login(cls, db, login, password, user_agent_env):
        if not password or not login:
            return False

        with cls.pool.cursor() as cr:
            cr.execute("""
                SELECT id
                FROM odoo_infrastructure_client_auth
                WHERE token_user=%s
                    AND token_password=%s
                    AND expire > CURRENT_TIMESTAMP AT TIME ZONE 'UTC';
            """, (login, password, ))
            if cr.fetchone():
                return SUPERUSER_ID
        return super(Users, cls)._login(db, login, password, user_agent_env)

    @api.model
    def _check_credentials(self, password, env):
        """ Check user credentials, and raise AccessDenied if check failed
        """
        self.env.cr.execute("""
            SELECT EXISTS(
                SELECT id
                FROM odoo_infrastructure_client_auth
                WHERE token_password=%s
            );
        """, (password,))
        if self.env.cr.fetchone()[0]:
            # confirmed credentials
            # So we return from function, to bypass futher checks
            return None

        return super(Users, self)._check_credentials(password, env)
