## 2025-10-01 Use SQLite WAL

Chose WAL over rollback journal for concurrent reads during writes.

## 2026-01-15 Drop legacy retry middleware

Replaced ad-hoc retry decorator with the token-bucket pattern.
