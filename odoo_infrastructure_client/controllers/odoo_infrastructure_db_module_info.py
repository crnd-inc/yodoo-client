import json
import logging

from odoo import http
from odoo.http import Response
from ..utils import (require_saas_token,
                     require_db_param,
                     prepare_db_module_info_data)

_logger = logging.getLogger(__name__)


class OdooInfrastructureDBModuleInfo(http.Controller):

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
