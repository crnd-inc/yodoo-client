import json
import logging

from odoo import http
from odoo.http import Response
from ..utils import require_saas_token, prepare_server_fast_statistic_data

_logger = logging.getLogger(__name__)


class SAASClientServerFastStat(http.Controller):

    @http.route(
        '/saas/client/server/fast/stat',
        type='http',
        auth='none',
        metods=['POST'],
        csrf=False
    )
    @require_saas_token
    def get_server_fast_statistic(self, **params):
        data = prepare_server_fast_statistic_data()
        return Response(json.dumps(data), status=200)
