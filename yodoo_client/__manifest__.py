{
    'name': "Yodoo Client",

    'summary': """
        It is the client addon for the yodoo.systems. Connect your Odoo
        instance to yodoo.systems and get the SaaS portal for
        your clients.
    """,

    'author': "Center of Research and Development",
    'website': "https://yodoo.systems",
    'license': 'Other proprietary',

    'version': '12.0.1.7.0',

    # any module necessary for this one to work correctly
    'depends': [
        'base',
        'web',
        'base_setup',
        'fetchmail',
    ],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'data/ir_cron_data.xml',
        'data/ir_config_parameter.xml',
        'views/yodoo_client_auth_log.xml',
        'views/saas_statistic.xml',
        'views/dbmanager.xml',
    ],
    # only loaded in demonstration mode
    'demo': [],
    'qweb': [],
    'category': 'Administration',
    'installable': True,
    'auto_install': True,
    'images': ['static/description/banner.png'],
    "post_load": "_post_load_hook",
}
