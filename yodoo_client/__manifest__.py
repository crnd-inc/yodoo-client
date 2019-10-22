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

    'version': '13.0.1.3.3',

    # any module necessary for this one to work correctly
    'depends': [
        'base',
        'web',
        'base_setup',
    ],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'data/ir_cron_data.xml',
        'views/saas_statistic.xml',
        'views/dbmanager.xml',
    ],
    # only loaded in demonstration mode
    'demo': [],
    'category': 'Administration',
    'installable': True,
    'auto_install': True,
    'images': ['static/description/banner.png'],
    "post_load": "_post_load_hook",
}