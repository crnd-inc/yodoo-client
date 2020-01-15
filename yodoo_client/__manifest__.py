# -*- coding: utf-8 -*-
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

    'version': '10.0.1.6.0',

    # any module necessary for this one to work correctly
    'depends': [
        'base',
        'web',
        'web_settings_dashboard',
        'fetchmail',
    ],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'data/ir_cron_data.xml',
        'views/saas_statistic.xml',
    ],
    # only loaded in demonstration mode
    'demo': [],
    'qweb': [
        'static/src/xml/saas_dashboard.xml',
    ],
    'category': 'Administration',
    'installable': True,
    'auto_install': True,
    'images': ['static/description/banner.png'],
    "post_load": "_post_load_hook",
}
