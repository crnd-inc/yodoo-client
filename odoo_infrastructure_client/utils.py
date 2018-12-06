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
from functools import wraps

from odoo import http, fields, registry, release, modules
from odoo.tools import config
from odoo.modules import module
from odoo.service.db import exp_db_exist

SAAS_CLIENT_API_VERSION = 1
DEFAULT_TIME_TO_LOGIN = 3600
DEFAULT_LEN_TOKEN = 128
SAAS_TOKEN_FIELD = 'odoo_infrastructure_token'

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


def server_error(description=None):
    """ Shortcut for a `HTTP 500
    <https://tools.ietf.org/html/rfc7231#section-6.6.1>`_
     (Internal Server Error) response
    """
    return werkzeug.exceptions.InternalServerError(description)


def conflict(description=None):
    """ Shortcut for a `HTTP 409
        <https://tools.ietf.org/html/rfc7231#section-6.5.8>`_ (Conflict)
        response
        """
    return werkzeug.exceptions.Conflict(description)


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
    return {
        'token_user': str(uuid()),
        'token_password': str(uuid()),
        'temp_url': '/saas/client/auth/%s' % uri_token,
        'expire': fields.Datetime.to_string(
            datetime.now() + timedelta(seconds=int(ttl))),
        'token_temp': random_token,
    }


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
        },
    }


def check_saas_client_token(token_hash):
    """
    Returns True or correct response. Makes logging before returning a response

    :param token_hash: hash of SaaS token from server
    :return: response or True
    :rtype: werkzeug.exceptions response instance or boolean
    """

    desc_no_token = 'Instance token does not exist, please configure it.'
    desc_token_not_match = 'The hashes of the tokens do not match.'

    token = config.get(SAAS_TOKEN_FIELD, False)
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


def get_size_storage(start_path):
    total_size = 0
    os_path_join = os.path.join
    os_getsize = os.path.getsize
    for storage_data in os.walk(start_path):
        for f in storage_data[2]:
            fp = os_path_join(storage_data[0], f)
            total_size += os_getsize(fp)
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
    """
        Returns dict {
            'external: count_external_users(int),
            'internal: count_internal_users(int),
            'total: sum_of_internal_and_external_users(int)}.
        Makes calculation of internal, external and all active users
        for the database.
        :param db: str name of database
        :return: dict
        """
    with registry(db).cursor() as cr:
        cr.execute("""
            SELECT share, count(*)
            FROM res_users
            WHERE active
            GROUP BY share;
        """)
        res = cr.fetchall()  # res: tuple of tuples
    # res_dict: {True: external_users(int), False: internal_users(int)}
    res_dict = dict(res)
    return {
        'internal': res_dict.get(False, 0),
        'external': res_dict.get(True, 0),
        'total': sum([res_dict[i] for i in res_dict])
    }


def get_last_login_date(db):
    with registry(db).cursor() as cr:
        cr.execute("""
            SELECT max(create_date)
            FROM res_users_log;
        """)
        res = cr.fetchone()[0]
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
        res = cr.fetchone()[0]
    return res


def get_installed_module_count(db):
    """
    Returns dict {'apps': count_apps(int), 'total': sum_of_installed_modules}.
    Makes calculation of application modules, and all installed modules
    for the database.

    :param db: str name of database
    :return: dict
    """
    with registry(db).cursor() as cr:
        cr.execute("""
            SELECT application, count(*)
            FROM ir_module_module
            WHERE state = 'installed'
            GROUP BY application;
        """)
        res = cr.fetchall()  # res: tuple of tuples
    # res_dict: {True: apps(int), False: not_apps(int)}
    res_dict = dict(res)
    return {
        'apps': res_dict.get(True, 0),
        'total': sum([res_dict[i] for i in res_dict])
    }


def prepare_db_statistic_data(db):
    data_dir = config['data_dir']
    file_storage_size = get_size_storage(
        os.path.join(data_dir, 'filestore', db))
    db_storage_size = get_size_db(db)
    active_users = get_active_users_count(db)
    installed_modules = get_installed_module_count(db)
    return {
        'db_storage': db_storage_size,
        'file_storage': file_storage_size,
        'users_total_count': active_users['total'],
        'users_internal_count': active_users['internal'],
        'users_external_count': active_users['external'],
        'login_date': get_last_login_date(db),
        'login_internal_date': get_last_internal_login_date(db),
        'installed_apps_db_count': installed_modules['apps'],
        'installed_modules_db_count': installed_modules['total'],
    }


def prepare_server_slow_statistic_data():
    platform_data = platform.uname()._asdict()
    disk_data = psutil.disk_usage('/')._asdict()
    database_count = get_count_db(config['db_user'])
    return {
        'used_disk_space': disk_data['used'],
        'free_disk_space': disk_data['free'],
        'total_disk_space': disk_data['total'],
        'os_name': platform_data['system'],
        'os_machine': platform_data['machine'],
        'os_version': platform_data['version'],
        'os_node': platform_data['node'],
        'db_count': database_count,
    }


def prepare_server_fast_statistic_data():
    cpu_data = psutil.cpu_times()._asdict()
    mem_data = psutil.virtual_memory()._asdict()
    swap_data = psutil.swap_memory()._asdict()
    cpu_load_average = os.getloadavg()
    # returns triple of load average (1m, 5m 15m)
    return {
        'cpu_load_average_1': cpu_load_average[0],
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
        'mem_total': mem_data['total'],
        'mem_free': mem_data['free'],
        'mem_used': mem_data['used'],
        'mem_buffers': mem_data['buffers'],
        'mem_available': mem_data['available'],
        'swap_total': swap_data['total'],
        'swap_free': swap_data['free'],
        'swap_used': swap_data['used'],
    }


def prepare_saas_module_info_data():
    """
    :return: dict {module_name: {
                                'name': module_name,
                                'version': module_version,
                                'author': module_author,
                                etc...},
                    etc...}
    """
    return {mod:
            module.load_information_from_description_file(mod)
            for mod in module.get_modules()}


def require_saas_token(func):
    """
    Decorate the controller method that requires check_saas_client_token.
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        token_hash = kwargs.get('token_hash', None)
        result = check_saas_client_token(token_hash)
        if result is not True:
            return result
        return func(*args, **kwargs)

    return wrapper


def require_db_param(func):
    """
    Decorate the controller method that requires exp_db_exist.
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        db = kwargs.get('db', None)
        if not exp_db_exist(db):
            _logger.info(
                'Database %s is not found.', db)
            return http.request.not_found()
        return func(*args, **kwargs)

    return wrapper
