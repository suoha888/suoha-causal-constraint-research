# Access contract

Access and rights are separate fields:

- `PUBLICLY_ACCESSIBLE`, `RESTRICTED_ACCESS`, `PRIVATE`, `SYNTHETIC`;
- redistribution rights: `ALLOWED`, `NOT_ALLOWED`, `UNKNOWN`;
- citation status: `CITABLE`, `RESTRICTED`, `UNKNOWN`.

The public compiler rejects a restricted or private evidence ID when it is used to support a public claim. A claim derived from private evidence must carry independent public support or remain `UNKNOWN`/`NOT_ESTABLISHED`.

No credential, cookie, browser storage, personal identifier, or raw source body belongs in a case file.
