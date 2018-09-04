ARG ODOO_BASE_IMAGE=registry.crnd.pro/crnd/docker/odoo-simple
ARG ODOO_BASE_TAG=11.0
FROM ${ODOO_BASE_IMAGE}:${ODOO_BASE_TAG}
MAINTAINER CRnD

COPY ./odoo_infrastructure_client /opt/odoo/repositories/odoo_infrastructure_client

RUN odoo-helper link /opt/odoo/repositories && \
    odoo-helper exec python -m compileall -q /opt/odoo/repositories

