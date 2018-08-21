import os
import string
import base64
import hashlib
import werkzeug
import logging
import platform
import psutil

from uuid import uuid4 as uuid
from datetime import datetime, timedelta
from random import shuffle

from odoo import http, fields, registry, release, modules
from odoo.tools import config
from odoo.modules import module

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


def get_count_db(user):
    with registry('postgres').cursor() as cr:
        cr.execute("""
            SELECT count(datname)
            FROM pg_database d
            LEFT JOIN pg_user u
            ON d.datdba = usesysid
            WHERE u.usename = %s;
        """, (user,))
        res = cr.fetchone()[0]
    return res


def get_size_db(db):
    with registry(db).cursor() as cr:
        cr.execute(
            "SELECT pg_database_size(%s)", (db,))
        res = cr.fetchone()[0]
    return res


def get_active_users_count(db):
    with registry(db).cursor() as cr:
        cr.execute("""
            SELECT share, count(*)
            FROM res_users
            WHERE active
            GROUP BY share;
        """)
        res = cr.fetchall()
    return res


def get_last_login_date(db):
    with registry(db).cursor() as cr:
        cr.execute("""
            SELECT max(create_date)
            FROM res_users_log;
        """)
        res = cr.fetchone()
    return res


def get_last_internal_login_date(db):
    with registry(db).cursor() as cr:
        cr.execute("""
            SELECT max(create_date)
            FROM res_users_log
            WHERE create_uid IN (
                SELECT id
                FROM res_users
                WHERE active = TRUE
                AND share = FALSE);
        """)
        res = cr.fetchone()
    return res


def get_installed_module_count(db):
    with registry(db).cursor() as cr:
        cr.execute("""
            SELECT application, count(*)
            FROM ir_module_module
            WHERE state = 'installed'
            GROUP BY application;
        """)
        res = cr.fetchall()
    return res


def get_db_module_data(db):
    with registry(db).cursor() as cr:
        cr.execute("""
            SELECT id, name, latest_version, application, write_date
            FROM ir_module_module
            WHERE state = 'installed';

        """)
        res = cr.dictfetchall()
    return res


def prepare_db_statistic_data(db):
    data_dir = config['data_dir']
    file_storage_size = get_size_storage(
        '%s/filestore/%s' % (data_dir, db))
    db_storage_size = get_size_db(db)
    active_users = dict(get_active_users_count(db))
    installed_modules = dict(get_installed_module_count(db))
    return {'db_storage': db_storage_size / (1024 * 1024),
            'file_storage': file_storage_size / (1024 * 1024),
            'users_total_count': sum([active_users[i] for i in active_users]),
            'users_internal_count': active_users.get(False, 0),
            'users_external_count': active_users.get(True, 0),
            'login_date': get_last_login_date(db),
            'login_internal_date': get_last_internal_login_date(db),
            'installed_apps_db_count': installed_modules.get(True, 0),
            'installed_modules_db_count':
                sum([installed_modules[i] for i in installed_modules])}


def prepare_server_slow_statistic_data():
    platform_data = platform.uname()._asdict()
    disc_data = psutil.disk_usage('/')._asdict()
    database_count = get_count_db(config['db_user'])
    return {'used_disc_space': disc_data['used'] / (1024 * 1024),
            'free_disc_space': disc_data['free'] / (1024 * 1024),
            'total_disc_space': disc_data['total'] / (1024 * 1024),
            'os_name': platform_data['system'],
            'os_machine': platform_data['machine'],
            'os_version': platform_data['version'],
            'os_node': platform_data['node'],
            'db_count': database_count}


def prepare_server_fast_statistic_data():
    cpu_data = psutil.cpu_times()._asdict()
    mem_data = psutil.virtual_memory()._asdict()
    swap_data = psutil.swap_memory()._asdict()
    cpu_load_average = os.getloadavg()
    return {'cpu_load_average_1': cpu_load_average[0],
            'cpu_load_average_5': cpu_load_average[1],
            'cpu_load_average_15': cpu_load_average[2],
            'cpu_us': cpu_data['user'],
            'cpu_sy': cpu_data['system'],
            'cpu_id': cpu_data['idle'],
            'cpu_ni': cpu_data.get('nice', None),
            'cpu_wa': cpu_data.get('iowait', None),
            'cpu_hi': cpu_data.get('irq', None),
            'cpu_si': cpu_data.get('softirq', None),
            'cpu_st': cpu_data.get('steal', None),
            'mem_total': mem_data['total'] / (1024 * 1024),
            'mem_free': mem_data['free'] / (1024 * 1024),
            'mem_used': mem_data['used'] / (1024 * 1024),
            'mem_buffers': mem_data['buffers'] / (1024 * 1024),
            'mem_available': mem_data['available'] / (1024 * 1024),
            'swap_total': swap_data['total'] / (1024 * 1024),
            'swap_free': swap_data['free'] / (1024 * 1024),
            'swap_used': swap_data['used'] / (1024 * 1024)}


def prepare_saas_module_info_data():
    """
    :return: dict {module_name: adapt_version}
    """
    return module.get_modules_with_version()


def prepare_db_module_info_data(db):
    """
    :param db: str name of database
    :return: list of dicts [{
        'id': module_id,
        'name': module_name,
        'latest_version': module_version,
        'application': True or False,
        'write_date': date_of_last_manipulations
    }]
    """
    return get_db_module_data(db)
