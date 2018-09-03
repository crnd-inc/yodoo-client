FROM registry.crnd.pro/crnd/docker/odoo-simple:11.0
MAINTAINER CRnD

COPY ./odoo_infrastructure_client /opt/odoo/repositories/odoo_infrastructure_client

RUN odoo-helper link /opt/odoo/repositories && \
    odoo-helper exec python -m compileall -q /opt/odoo/repositories

