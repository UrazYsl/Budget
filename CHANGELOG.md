# Changelog

All notable changes to this project are documented here. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the project uses [Semantic Versioning](https://semver.org/).

## [1.0.0] - 2026-11-03

First tagged release. Covers everything built in phases 1 to 7 of the roadmap.

### Added

- FastAPI backend with PostgreSQL: accounts, categories, transactions and recurring transactions, with full CRUD, filtering and pagination.
- Income and expense types on transactions and recurring transactions; expenses are subtracted from the selected account's balance.
- Receipt image attachments for transactions.
- Recurring transaction processor (APScheduler), runs daily at midnight Toronto time and on startup.
- Monthly budgets per category.
- Summary endpoints: monthly totals, account balances, category breakdown, upcoming recurring transactions.
- Configurable timezone without a restart.
- Alpine.js web frontend served by nginx: dashboard with income/expense ring, budget progress bars, month-over-month comparison, upcoming recurring transactions, CSV export, dark and light themes, responsive layout.
- Database backup download, plus a daily 2 AM backup cron job.
- `start.sh` one-script install for Ubuntu/Debian: Docker, avahi (`http://budget.local` on the LAN) and Tailscale for remote access.
- Alembic migrations and a pytest suite (168 tests) run in GitHub Actions.

### Fixed

- Account balance test updated for expense subtraction, so CI passes again.

### Security

- `.env` is no longer tracked in git. It was already listed in `.gitignore`; only the example file is committed now.

[1.0.0]: https://github.com/UrazYsl/Budget/releases/tag/v1.0.0
