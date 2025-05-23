#!/bin/bash
set -e

cp /tmp/pg_hba.conf "$PGDATA/pg_hba.conf"
cp /tmp/postgresql.conf "$PGDATA/postgresql.conf"
cp /tmp/server.crt "$PGDATA/server.crt"
cp /tmp/server.key "$PGDATA/server.key"
chmod 600 "$PGDATA/server.key"
chown postgres:postgres "$PGDATA/server.key" "$PGDATA/server.crt" "$PGDATA/pg_hba.conf" "$PGDATA/postgresql.conf"
