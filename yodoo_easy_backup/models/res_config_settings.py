import uuid
from odoo import models, fields, api


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    yodoo_easy_backup_allow = fields.Boolean(
        string='Allow easy backup')
    yodoo_easy_backup_allow_public = fields.Boolean(
        string='Allow easy backup for public users')
    yodoo_easy_backup_url = fields.Char(
        compute="_compute_yodoo_easy_backup_url", readonly=True)

    @api.depends('yodoo_easy_backup_allow')
    def _compute_yodoo_easy_backup_url(self):
        Params = self.env['ir.config_parameter'].sudo()
        token = Params.get_param(
            'yodoo_easy_backup.backup_token', default=False)

        if token:
            self.update({
                'yodoo_easy_backup_url': '/yodoo_easy_backup/%s' % token,
            })
        else:
            self.update({
                'yodoo_easy_backup_url': False,
            })

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        params = self.env['ir.config_parameter'].sudo()
        res['yodoo_easy_backup_allow'] = bool(params.get_param(
            'yodoo_easy_backup.backup_token', default=False))
        res['yodoo_easy_backup_allow_public'] = params.get_param(
            'yodoo_easy_backup.backup_allow_public', default=False)
        return res

    def set_values(self):
        res = super(ResConfigSettings, self).set_values()
        params = self.env['ir.config_parameter'].sudo()
        params.set_param(
            'yodoo_easy_backup.backup_allow_public',
            self.yodoo_easy_backup_allow_public)
        if self.yodoo_easy_backup_allow:
            params.set_param(
                'yodoo_easy_backup.backup_token', str(uuid.uuid4()))
        else:
            params.set_param(
                'yodoo_easy_backup.backup_token', False)
        return res
