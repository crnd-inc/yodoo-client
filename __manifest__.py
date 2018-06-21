{
    'name': "Odoo Infrastructure Client",

    'summary': """
    """,

    'author': "Management and Accounting Online",
    'website': "https://crnd.pro",
    'license': 'Other proprietary',

    'version': '11.0.0.0.1',

    # any module necessary for this one to work correctly
    'depends': ['base'],

    # always loaded
    'data': ['security/ir.model.access.csv'],
    # only loaded in demonstration mode
    'demo': [],
    'category': 'Odoo Infrastructure',
    'installable': True,
    'auto_install': False,
}
