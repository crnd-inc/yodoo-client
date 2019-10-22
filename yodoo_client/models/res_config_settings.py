from odoo import models, fields, api, tools
from ..utils import prepare_db_statistic_data

STAT_FIELDS = [
    'users_total_count',
    'users_internal_count',
    'users_external_count',
    'file_storage',
    'db_storage',
]


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    users_total_count = fields.Integer(
        compute='_compute_db_statistics', readonly=True)
    users_internal_count = fields.Integer(
        compute='_compute_db_statistics', readonly=True)
    users_external_count = fields.Integer(
        compute='_compute_db_statistics', readonly=True)
    file_storage = fields.Char(
        compute='_compute_db_statistics', readonly=True)
    db_storage = fields.Char(
        compute='_compute_db_statistics', readonly=True)

    @api.depends('company_id')
    def _compute_db_statistics(self):
        for rec in self:
            data = prepare_db_statistic_data(self.env.cr.dbname)
            data.update({
                'db_storage': tools.human_size(data['db_storage']),
                'file_storage': tools.human_size(data['file_storage']),
            })
            import logging
            logging.getLogger(__name__).info("X: %s", data)
            data = {f: data[f] for f in STAT_FIELDS}
            rec.update(data)
