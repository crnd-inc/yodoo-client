import os
import string
import base64
import hashlib
import werkzeug
import logging
from functools import reduce

from uuid import uuid4 as uuid
from datetime import datetime, timedelta
from random import shuffle

from odoo import http, fields, registry, release, modules
from odoo.tools import config

SAAS_CLIENT_API_VERSION = 1
DEFAULT_TIME_TO_LOGIN = 3600
DEFAULT_LEN_TOKEN = 128

_logger = logging.getLogger(__name__)


def forbidden(description=None):
    """ Shortcut for a `HTTP 403
    <https://tools.ietf.org/html/rfc7231#section-6.5.3>`_ (Forbidden)
    response
    """
    return werkzeug.exceptions.Forbidden(description)


def bad_request(description=None):
    """ Shortcut for a `HTTP 400
    <https://tools.ietf.org/html/rfc7231#section-6.5.1>`_ (BadRequest)
    response
    """
    return werkzeug.exceptions.BadRequest(description)


def generate_random_password(length):
    letters = list(string.ascii_uppercase +
                   string.ascii_lowercase +
                   string.digits) * 3
    shuffle(letters)
    return ''.join(letters[:length])


def prepare_temporary_auth_data(ttl, db_name, token):
    ttl = ttl or DEFAULT_TIME_TO_LOGIN
    random_token = generate_random_password(DEFAULT_LEN_TOKEN)
    uri_token = '%s:%s:%s' % (db_name, random_token, token)
    uri_token = base64.b64encode(uri_token.encode("utf-8")).decode()
    return {'token_user': str(uuid()),
            'token_password': str(uuid()),
            'temp_url': '/saas_auth/%s' % uri_token,
            'expire': fields.Datetime.to_string(
                datetime.now() + timedelta(seconds=int(ttl))),
            'token_temp': random_token, }


def prepare_saas_client_version_data():
    admin_access_url, admin_access_credentials = (
        get_admin_access_options())
    module_version = modules.load_information_from_description_file(
        'odoo_infrastructure_client')['version'].split('.')
    # module_version is a list from the version string
    module_version_tail = '.'.join(
        module_version[-3:len(module_version)])
    # module_version_tail is a string from the last 3 version numbers
    module_version_head = '.'.join(
        module_version[0:2])
    # module_version_head is a string from the first 2 version numbers

    return {
        'odoo_version': release.version,
        'odoo_version_info': release.version_info,
        'odoo_serie': release.serie,
        # receives only the last 3 version numbers
        'saas_client_version': module_version_tail,
        # receives only the first 2 version numbers
        'saas_client_serie': module_version_head,
        'saas_client_api_version': SAAS_CLIENT_API_VERSION,
        'features_enabled': {
            'admin_access_url': admin_access_url,
            'admin_access_credentials': admin_access_credentials,
        }
    }


def check_saas_client_token(token_hash):
    """
    Returns True or correct response. Makes logging before returning a response

    :param token_hash: hash of odoo_infrastructure_token from server
    :return: response or True
    :rtype: werkzeug.exceptions response instance or boolean
    """

    desc_no_token = 'Instance token does not exist, please configure it.'
    desc_token_not_match = 'The hashes of the tokens do not match.'

    token = config.get('odoo_infrastructure_token', False)
    if not token:
        _logger.info(desc_no_token)
        return http.request.not_found(desc_no_token)
    token_instance_hash = hashlib.sha256(token.encode('utf8')).hexdigest()
    if not token_instance_hash == token_hash:
        _logger.info(desc_token_not_match)
        return forbidden(desc_token_not_match)
    return True


def get_admin_access_options():
    """
        Returns the admin_access options from config.
        By default this is True.
    :return: tuple of booleans
            first element: admin_access_url from config or default
            second element: admin_access_credentials from config or default
    :rtype: tuple(boolean, boolean)
    """
    return (config.get('admin_access_url', True),
            config.get('admin_access_credentials', True))


def get_size_storage(start_path='.'):
    total_size = 0
    for storage_data in os.walk(start_path):
        for f in storage_data[2]:
            fp = os.path.join(storage_data[0], f)
            total_size += os.path.getsize(fp)
    return total_size


def get_size_db(db):
    with registry(db).cursor() as cr:
        cr.execute(
            "SELECT pg_database_size('%s')", db)
        res = cr.fetchone()[0]
    return res


def get_active_users_generator(db):
    with registry(db).cursor() as cr:
        cr.execute("""
            SELECT share
            FROM res_users
            WHERE active;
        """)
        user = True
        while user:
            user = cr.fetchone()
            yield user


def prepare_db_statistic_data(db):
    active_users = get_active_users_generator(db)
    internal_users, external_users = reduce(
        lambda a, x: (a[0] + 1, a[1]) if x[0] is False else (a[0], a[1] + 1),
        active_users,
        (0, 0)
    )
    total_users = internal_users + external_users
    data_dir = config['data_dir']
    file_storage_size = get_size_storage(
        '%s/filestore/%s' % (data_dir, db))
    db_storage_size = get_size_db(db)

    return {'db_storage': db_storage_size,
            'file_storage': file_storage_size,
            'total_users': total_users,
            'internal_users': internal_users,
            'external_users': external_users}
