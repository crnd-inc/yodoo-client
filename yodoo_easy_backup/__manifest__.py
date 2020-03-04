{
    'name': "Yodoo Easy Backup",

    'summary': """
        This is simple module, that allows to do database backup,
        if usual means not availables.
    """,

    'author': "Center of Research and Development",
    'website': "https://crnd.pro",
    'license': 'Other proprietary',

    'version': '13.0.0.0.1',

    # any module necessary for this one to work correctly
    'depends': [
        'base',
        'web',
        'base_setup',
    ],

    # always loaded
    'data': [
        'views/res_config_settings.xml',
    ],
    # only loaded in demonstration mode
    'demo': [],
    'qweb': [],
    'category': 'Administration',
    'installable': True,
    'auto_install': False,
    'images': [],
}
