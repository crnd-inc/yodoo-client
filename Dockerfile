ARG ODOO_BASE_IMAGE=registry.crnd.pro/crnd-opensource/docker/odoo-simple
ARG ODOO_BASE_TAG=13.0
FROM ${ODOO_BASE_IMAGE}:${ODOO_BASE_TAG}
MAINTAINER CRnD

COPY ./yodoo_client /opt/odoo/repositories/yodoo_client

RUN odoo-helper link /opt/odoo/repositories && \
    odoo-helper exec python -m compileall -q /opt/odoo/repositories

ENV ODOO_SERVER_WIDE_MODULES='base,web,yodoo_client' \
    ODOO_EXTRA_CONFIG='yodoo_token = tokenZ'
