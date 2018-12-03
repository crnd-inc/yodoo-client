import json
import logging

from odoo import http, registry, SUPERUSER_ID
from odoo.http import Response
from odoo.api import Environment

from ..utils import (
    require_saas_token,
    require_db_param,
    prepare_db_module_info_data,
)

_logger = logging.getLogger(__name__)


class SAASClientDbModule(http.Controller):

    def _parse_modules(self, module_name, module_names):
        modules = []
        if module_name:
            modules.append(module_name.strip())
        if module_names:
            modules += [m.strip() for m in module_names.split(',')]
        return modules

    @http.route(
        '/saas/client/db/module/info',
        type='http',
        auth='none',
        metods=['POST'],
        csrf=False
    )
    @require_saas_token
    @require_db_param
    def get_client_db_module_info(self, db=None, **params):
        data = prepare_db_module_info_data(db)
        return Response(json.dumps(data), status=200)

    @http.route(
        '/saas/client/db/module/install',
        type='http',
        auth='none',
        metods=['POST'],
        csrf=False
    )
    @require_saas_token
    @require_db_param
    def client_db_module_install(self, db=None, module_name=None,
                                 module_names=None, **params):
        """Install single module or list of modules.

           :param str module_name: module name in case of single module install
           :param [str] module_names: coma-separated list of modules to install
        """
        modules = self._parse_modules(module_name, module_names)
        with registry(db).cursor() as cr:
            env = Environment(cr, SUPERUSER_ID, context={})
            env['ir.module.module'].search(
                [('name', 'in', modules),
                 ('state', 'in', ('uninstalled', 'to_install'))]
            ).button_immediate_install()
        return Response('successfully', status=200)

    @http.route(
        '/saas/client/db/module/upgrade',
        type='http',
        auth='none',
        metods=['POST'],
        csrf=False
    )
    @require_saas_token
    @require_db_param
    def client_db_module_upgrade(self, db=None, module_name=None,
                                 module_names=None, **params):
        """Upgrade single module or list of modules.

           :param str module_name: module name in case of single module upgrade
           :param [str] module_names: coma-separated list of modules to upgrade
        """
        modules = self._parse_modules(module_name, module_names)
        with registry(db).cursor() as cr:
            env = Environment(cr, SUPERUSER_ID, context={})
            env['ir.module.module'].search(
                [('name', 'in', modules),
                 ('state', '=', 'installed')]
            ).button_immediate_upgrade()
        return Response('successfully', status=200)

    @http.route(
        '/saas/client/db/module/uninstall',
        type='http',
        auth='none',
        metods=['POST'],
        csrf=False
    )
    @require_saas_token
    @require_db_param
    def client_db_module_uninstall(self, db=None, module_name=None,
                                   module_names=None, **params):
        """Uninstall single module or list of modules.

           :param str module_name: module name in case of single module uninst
           :param [str] module_names: coma-separated list of modules to uninst
        """
        modules = self._parse_modules(module_name, module_names)
        with registry(db).cursor() as cr:
            env = Environment(cr, SUPERUSER_ID, context={})
            env['ir.module.module'].search(
                [('name', 'in', modules),
                 ('state', '=', 'installed')]
            ).button_immediate_uninstall()
        return Response('successfully', status=200)
