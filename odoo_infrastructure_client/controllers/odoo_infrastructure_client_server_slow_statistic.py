import json
import logging

from odoo import http
from odoo.http import Response
from ..utils import require_saas_token, prepare_server_slow_statistic_data

_logger = logging.getLogger(__name__)


class SAASClientServerSlowStat(http.Controller):

    @http.route(
        '/saas/client/server/slow/stat',
        type='http',
        auth='none',
        metods=['POST'],
        csrf=False
    )
    @require_saas_token
    def get_server_slow_statistic(self, **params):
        data = prepare_server_slow_statistic_data()
        return Response(json.dumps(data), status=200)
