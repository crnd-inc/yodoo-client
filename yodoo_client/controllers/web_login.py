import logging

import odoo
from odoo import http
from odoo.addons.web.controllers.main import Home

_logger = logging.getLogger(__name__)


class SaaSHome(Home):
    @http.route('/web/login')
    def web_login(self, *args, **kw):
        response = super(SaaSHome, self).web_login(*args, **kw)
        values = {}
        if odoo.tools.config.get('url_manage_db', False):
            values['url_manage_db'] = odoo.tools.config['url_manage_db']
        if odoo.tools.config.get('url_powered_by', False):
            values['url_powered_by'] = odoo.tools.config['url_powered_by']
        if odoo.tools.config.get('name_powered_by', False):
            values['name_powered_by'] = odoo.tools.config['name_powered_by']
        response.qcontext.update(values)
        return response
