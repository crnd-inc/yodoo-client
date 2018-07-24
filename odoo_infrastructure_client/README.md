**Odoo Infrastructure Auth**

Provides the ability to configure administrator access from the server in various ways.

**Configuration**

The configuration has several steps.

1. Set `odoo_infrastructure_token` to the `odoo.conf` file.
   This is a series of random ascii characters.
   This is the same as the `odoo_instance_token` field on the remote server.
   
   ```ini
   odoo_instance_token = Your_random_token
   ```
   
2. Set `admin_access_url` and `admin_access_credentials` to the `odoo.conf` file.

   Enables full administrator access from the remote server via the button.
    
   ```ini
   admin_access_url = True
   admin_access_credentials = True
   ```
   
   Enables administrator access from the remote server via a temporary login and password.
    
   ```ini
   admin_access_url = False
   admin_access_credentials = True
   ```
   
   Disabled administrator access from the remote server.
    
   ```ini
   admin_access_url = False
   admin_access_credentials = False
   ```   

**Installation**

This module is automatically installed with the base module.

