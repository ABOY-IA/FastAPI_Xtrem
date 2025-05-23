FROM postgres:15

COPY pg_hba.conf /tmp/pg_hba.conf
COPY postgresql.conf /tmp/postgresql.conf
COPY server.crt /tmp/server.crt
COPY server.key /tmp/server.key
COPY docker-entrypoint-init-custom.sh /docker-entrypoint-initdb.d/init-custom.sh

# Fixe les permissions sur la clé privée
RUN chmod 600 /tmp/server.key && \
    chown postgres:postgres /tmp/server.key /tmp/server.crt /tmp/pg_hba.conf /tmp/postgresql.conf

RUN chmod +x /docker-entrypoint-initdb.d/init-custom.sh
