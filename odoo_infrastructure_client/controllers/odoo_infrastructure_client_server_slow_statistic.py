import json
import logging

from odoo import http
from odoo.http import Response
from ..utils import check_saas_client_token, prepare_server_slow_statistic_data

_logger = logging.getLogger(__name__)


class OdooInfrastructureClientServerSlowStatistic(http.Controller):

    @http.route(
        '/saas/client/server/slow/stat',
        type='http',
        auth='none',
        metods=['POST'],
        csrf=False
    )
    def get_server_slow_statistic(self, token_hash=None, **params):
        result = check_saas_client_token(token_hash)
        # result is True or response (not_found, forbidden)
        if result is not True:
            return result
        data = prepare_server_slow_statistic_data()
        return Response(json.dumps(data), status=200)
