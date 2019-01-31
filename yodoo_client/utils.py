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
from contextlib import closing

from odoo import fields, sql_db
from odoo.tools import config
from odoo.modules import module
from odoo.service.db import exp_db_exist

SAAS_CLIENT_API_VERSION = 1
DEFAULT_TIME_TO_LOGIN = 3600
DEFAULT_LEN_TOKEN = 128
SAAS_TOKEN_FIELD = 'yodoo_token'

_logger = logging.getLogger(__name__)


class DatabaseNotExists(werkzeug.exceptions.HTTPException):
    code = 440
    description = (
        "Database not found"
    )


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


def check_saas_client_token(token_hash):
    """
    Returns True or correct response. Makes logging before returning a response

    :param token_hash: hash of SaaS token from server
    :return: response or True
    :raises werkzeug.exceptions.*: raised in case when no/wrong token
    """
    token = config.get(SAAS_TOKEN_FIELD, False)
    if not token:
        _logger.info('Instance token does not exist, please configure it.')
        raise werkzeug.exceptions.NotFound(description='Token not configured')

    token_instance_hash = hashlib.sha256(token.encode('utf8')).hexdigest()
    if not token_instance_hash == token_hash:
        _logger.info('The hashes of the tokens do not match.')
        raise werkzeug.exceptions.Forbidden(description='Token not match')


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
    db = sql_db.db_connect('postgres')
    with closing(db.cursor()) as cr:
        cr.execute("""
            SELECT count(datname)
            FROM pg_database d
            LEFT JOIN pg_user u ON d.datdba = usesysid
            WHERE u.usename = %s;
        """, (user,))
        res = cr.fetchone()[0]
    return res


def prepare_db_statistic_data(db):
    data_dir = config['data_dir']
    file_storage_size = get_size_storage(
        os.path.join(data_dir, 'filestore', db))

    with closing(sql_db.db_connect(db).cursor()) as cr:
        cr.execute(
            "SELECT pg_database_size(%s)", (db,))
        db_storage_size = cr.fetchone()[0]

        cr.execute("""
            SELECT
                max(rul.create_date) AS last_login,
                max(rul.create_date) FILTER (
                   WHERE ru.share = False) AS last_internal_login
            FROM res_users_log AS rul
            LEFT JOIN res_users AS ru ON ru.id = rul.create_uid
            WHERE ru.active = True
        """)
        last_login_date, last_internal_login_date = cr.fetchone()

        cr.execute("""
            SELECT
                count(*) AS total,
                count(*) FILTER (WHERE share = True) AS external,
                count(*) FILTER (WHERE share = False) AS internal
            FROM res_users
            WHERE active = True
        """)
        active_users = cr.dictfetchone()

        cr.execute("""
            SELECT
                count(*) AS total,
                count(*) FILTER (WHERE application = True) AS apps
            FROM ir_module_module
            WHERE state = 'installed'
        """)
        installed_modules = cr.dictfetchone()

    return {
        'db_storage': db_storage_size,
        'file_storage': file_storage_size,
        'users_total_count': active_users['total'],
        'users_internal_count': active_users['internal'],
        'users_external_count': active_users['external'],
        'login_date': fields.Datetime.to_string(
            last_login_date),
        'login_internal_date': fields.Datetime.to_string(
            last_internal_login_date),
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
    return {
        mod: module.load_information_from_description_file(mod)
        for mod in module.get_modules()
    }


def require_saas_token(func):
    """
    Decorate the controller method that requires check_saas_client_token.
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        token_hash = kwargs.get('token_hash', None)
        check_saas_client_token(token_hash)
        return func(*args, **kwargs)

    return wrapper


def require_db_param(func):
    """
    Decorate the controller method that requires exp_db_exist.
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        db = kwargs.get('db', None)
        if not db:
            raise werkzeug.exceptions.BadRequest("Database not specified")
        if not exp_db_exist(db):
            _logger.info(
                'Database %s is not found.', db)
            raise DatabaseNotExists()
        return func(*args, **kwargs)

    return wrapper
