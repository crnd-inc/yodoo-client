import json
import logging

from odoo import http
from odoo.http import Response
from ..utils import check_saas_client_token, prepare_saas_module_info_data

_logger = logging.getLogger(__name__)


class OdooInfrastructureClientModuleInfo(http.Controller):

    @http.route(
        '/saas/client/module/info',
        type='http',
        auth='none',
        metods=['POST'],
        csrf=False
    )
    def get_client_module_info(self, token_hash=None, **params):
        result = check_saas_client_token(token_hash)
        # result is True or response (not_found, forbidden)
        if result is not True:
            return result
        data = prepare_saas_module_info_data()
        return Response(json.dumps(data), status=200)
