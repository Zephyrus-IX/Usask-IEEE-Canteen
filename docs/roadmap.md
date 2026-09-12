# Roadmap

## Database backup export to removable USB storage

Status: deferred until after the public-deployment hardening work.

Build an executive-only workflow that creates a PostgreSQL logical backup and exports it to an explicitly selected removable USB drive.

Required safeguards:

- Detect removable storage and require an executive to select the destination; never guess a mount path.
- Run `pg_dump` in PostgreSQL custom format so restores can be validated with `pg_restore`.
- Encrypt every backup before it is written to removable storage; do not store the encryption key on the same USB drive.
- Use an IEEE-controlled password manager or recovery process for the encryption key.
- Name backups with an unambiguous UTC timestamp and deployment identifier.
- Create and verify a SHA-256 checksum after the encrypted file is copied.
- Write to a temporary filename and rename only after the copy and checksum succeed.
- Show success only after the destination file has been read back and verified.
- Provide safe-eject guidance and never unmount arbitrary filesystems automatically.
- Define retention rules for both local temporary files and USB copies.
- Keep backup files, passwords, and command output out of Git and application logs.
- Document and regularly test a restore into a separate disposable database before relying on the feature.
- Record the authorization boundary so only active staff/superusers can start or download a backup.

The restore procedure is part of this feature, not a later optional task. A backup is not considered working until a clean restore has been demonstrated.
