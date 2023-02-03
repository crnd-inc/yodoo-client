from odoo import models, api, exceptions


class Users(models.Model):
    _inherit = "res.users"

    @classmethod
    def _login(cls, db, login, password, user_agent_env):
        if not password:
            raise exceptions.AccessDenied()

        with cls.pool.cursor() as cr:
            cr.execute("""
                SELECT id, user_id
                FROM odoo_infrastructure_client_auth
                WHERE token_user=%s
                    AND token_password=%s
                    AND expire > CURRENT_TIMESTAMP AT TIME ZONE 'UTC';
            """, (login, password, ))
            res = cr.fetchone()
            if res and res[1]:
                return res[1]
        return super(Users, cls)._login(db, login, password, user_agent_env)

    @classmethod
    def check(cls, db, uid, passwd):
        if not (passwd and db and uid):
            return super().check(db, uid, passwd)

        with cls.pool.cursor() as cr:
            cr.execute("""
                SELECT EXISTS (
                    SELECT 1
                    FROM odoo_infrastructure_client_auth
                    WHERE user_id=%s
                        AND token_password=%s
                        AND expire > CURRENT_TIMESTAMP AT TIME ZONE 'UTC');
            """, (uid, passwd, ))
            if cr.fetchone()[0]:
                return None
        return super().check(db, uid, passwd)

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
