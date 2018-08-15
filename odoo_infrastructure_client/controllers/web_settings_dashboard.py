import logging

from ..utils import prepare_db_statistic_data

from odoo import http
from odoo.http import request
from odoo.addons.web_settings_dashboard.controllers.main import (
    WebSettingsDashboard)

_logger = logging.getLogger(__name__)


class SaaSWebSettingsDashboard(WebSettingsDashboard):

    @http.route('/web_settings_dashboard/data', type='json', auth='user')
    def web_settings_dashboard_data(self, **kw):

        result = super(
            SaaSWebSettingsDashboard, self).web_settings_dashboard_data(**kw)

        data = prepare_db_statistic_data(request.env.cr.dbname)
        data.update(
            {'db_storage': int(data['db_storage'] / (1024 * 1024)),
             'file_storage': int(data['file_storage'] / (1024 * 1024))}
        )
        result.update({'saas': data})
        return result
