Yodoo Client
============


.. |badge3| image:: https://img.shields.io/badge/powered%20by-yodoo.systems-00a09d.png
    :target: https://yodoo.systems
    
.. |badge5| image:: https://img.shields.io/badge/maintainer-CR&D-purple.png
    :target: https://crnd.pro/

.. |badge4| image:: https://img.shields.io/badge/docs-Odoo_Infrastructure_Client-yellowgreen.png
    :target: http://review-docs.10.100.34.40.xip.io/review/doc-odoo-infrastructure/11.0/en/odoo_infrastructure_admin/


|badge4| |badge5|

The Yodoo Client application is the client addon for the yodoo.systems. Connect your Odoo instance to yodoo.systems and get the SaaS portal for your clients.

Requirements
''''''''''''

Minimal postgres version required: 9.5


Configuration
'''''''''''''
The configuration has several steps.

1. Set `yodoo_token` to the `odoo.conf` file.
    This is a series of random ascii characters.
    This is the same as the `odoo_instance_token` field on the remote server.
    
    .. code:: 
    
        yodoo_token = Your_random_token

2. Set `admin_access_url` and `admin_access_credentials` to the `odoo.conf` file.
    Enables full administrator access from the remote server via the button.

    .. code::

        admin_access_url = True
        admin_access_credentials = True

    Enables administrator access from the remote server via a temporary login and password.

    .. code::

        admin_access_url = False
        admin_access_credentials = True

    Disabled administrator access from the remote server.

    .. code::

        admin_access_url = False
        admin_access_credentials = False

3. Set `server_wide_modules` to `odoo.conf` file.

    .. code::

        server_wide_modules = base,web,yodoo_client


Installation
''''''''''''
This module is automatically installed with the base module.


Read the `Odoo-Infrastructure <http://review-docs.10.100.34.40.xip.io/review/doc-odoo-infrastructure/11.0/en/odoo_infrastructure_admin/>`__ Guide for more information.


Launching SaaS is fast and easy:
''''''''''''''''''''''''''''''''


|badge3|


Bug Tracker
===========

Bugs are tracked on `https://crnd.pro/requests <https://crnd.pro/requests>`_.
In case of trouble, please report there.


Maintainer
''''''''''
.. image:: https://crnd.pro/web/image/3699/300x140/crnd.png

Our web site: https://crnd.pro/

This module is maintained by the Center of Research & Development company.

We can provide you further Odoo Support, Odoo implementation, Odoo customization, Odoo 3rd Party development and integration software, consulting services. Our main goal is to provide the best quality product for you. 

For any questions `contact us <mailto:info@crnd.pro>`__.
