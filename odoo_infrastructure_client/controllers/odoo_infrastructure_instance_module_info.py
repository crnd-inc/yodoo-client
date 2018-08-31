import json
import logging

from odoo import http
from odoo.http import Response
from ..utils import require_saas_token, prepare_saas_module_info_data

_logger = logging.getLogger(__name__)


class OdooInfrastructureClientModuleInfo(http.Controller):

    @http.route(
        '/saas/client/module/info',
        type='http',
        auth='none',
        metods=['POST'],
        csrf=False
    )
    @require_saas_token
    def get_client_module_info(self, **params):
        data = prepare_saas_module_info_data()
        return Response(json.dumps(data), status=200)
