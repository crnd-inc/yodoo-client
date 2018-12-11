-- Migrate module data --
UPDATE ir_model_data
SET module = 'yodoo_client'
WHERE module = 'odoo_infrastructure_client';

-- Rename modules --
UPDATE ir_module_module imm
SET name = 'yodoo_client'
WHERE imm.name = 'odoo_infrastructure_client';
