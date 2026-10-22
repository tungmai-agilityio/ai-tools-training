# Clinic Booking security rules

- Admin endpoints must depend on `routes.require_admin`. It must fail closed when `ADMIN_TOKEN` is empty and compare with `hmac.compare_digest`, never `==`.
- `ADMIN_TOKEN` and other secrets come from the environment only. Flag any hardcoded token, a real `.env`, or a default token value in code, tests or docs.
- SQL in `app/store.py` must use `?` placeholders with stdlib `sqlite3`. Flag any f-string, `%` or `+` built query.
- Flag anything that looks like real patient or client data (real names, phone numbers, emails, IDs) in code, seeds, fixtures or the UI. Only fake data is allowed.
- Business-rule failures raise `DomainError`, not `HTTPException`. Do not let error messages echo raw user input or internal paths.
- `app/static/index.html` must not render API data through `innerHTML`; use `textContent` or escape it.
