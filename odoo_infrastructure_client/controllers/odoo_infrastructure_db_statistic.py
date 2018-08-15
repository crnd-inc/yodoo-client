import json
import logging

from odoo import http
from odoo.http import Response
from odoo.service.db import exp_db_exist
from ..utils import check_saas_client_token, prepare_db_statistic_data

_logger = logging.getLogger(__name__)


class OdooInfrastructureDBStatistic(http.Controller):

    @http.route(
        '/saas/client/db/stat',
        type='http',
        auth='none',
        metods=['POST'],
        csrf=False
    )
    def get_db_statistic(self, db=None, token_hash=None, **params):
        result = check_saas_client_token(token_hash)
        # result is True or response (not_found, forbidden)
        if result is not True:
            return result
        if not exp_db_exist(db):
            _logger.info(
                'Database %s is not found.', db)
            return http.request.not_found()
        data = prepare_db_statistic_data(db)
        return Response(json.dumps(data), status=200)
