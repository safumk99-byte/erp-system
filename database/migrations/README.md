# ALIF ERP Canonical Migrations

Run SQL files in filename order. Core identity is established by 019_core_identity_schema.sql in this recovered branch, while skill base schemas are created before their enhancement ALTER statements by the 006/007b/007c/008/009/010/011 files.

The migration chain is designed to fail fast when required core tables are missing. Do not run enhancement files in isolation.
