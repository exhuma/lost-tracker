#!/bin/bash
set -e

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" <<-EOSQL
    CREATE USER ltrack PASSWORD 'ltrack';
    CREATE DATABASE lost_tracker OWNER ltrack;
EOSQL
