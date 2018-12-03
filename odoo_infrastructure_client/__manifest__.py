{
    'name': "Odoo Infrastructure Client",

    'summary': """
        It is the client addon for the yodoo.systems. Connect your Odoo
        instance to yodoo.systems and get the SaaS portal for
        your clients.
    """,

    'author': "Center of Research & Development",
    'website': "https://crnd.pro",
    'license': 'Other proprietary',

    'version': '11.0.0.6.0',

    # any module necessary for this one to work correctly
    'depends': [
        'base',
        'web',
        'web_settings_dashboard',
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
    'category': 'Odoo Infrastructure',
    'installable': True,
    'auto_install': True,
    'images': ['static/description/banner.png'],
}
