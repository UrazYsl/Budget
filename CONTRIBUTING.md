# Contributing to Budget

Thanks for taking the time to help. Budget is a small self-hosted app, so the process is simple.

## Reporting bugs and requesting features

Open an issue using the bug report or feature request template. For bugs, include your OS, how you run the app (start.sh or docker compose), and the steps to reproduce.

## Development setup

1. Fork and clone the repo.
2. Copy `.env.example` to `.env` and set a password and timezone.
3. Start the stack:

   ```bash
   docker compose up -d --build
   ```

4. The frontend is served by nginx, the API by FastAPI in the `backend` container.

## Running tests

Tests need a PostgreSQL database. The easiest way is a throwaway container:

```bash
docker run -d --rm --name budget-test-pg \
  -e POSTGRES_USER=budget_user -e POSTGRES_PASSWORD=budget_pass -e POSTGRES_DB=budget_db \
  -p 55432:5432 postgres:16

cd backend
pip install -r requirements.txt pytest python-dotenv
TEST_DATABASE_URL=postgresql+psycopg://budget_user:budget_pass@localhost:55432/budget_test \
  python -m pytest tests/ -q

docker stop budget-test-pg
```

CI runs the same suite on every push and pull request. Please make sure it passes before asking for review.

## Pull requests

- Branch from `main` and keep each pull request focused on one change.
- Add or update tests for any behavior change.
- If you change database models, add an Alembic migration (see "If You Change Database Models" in the README).
- Describe what changed and why in the pull request description, and link the related issue.

## Code style

- Python: follow the style of the surrounding code, type hints where they help.
- Frontend: plain Alpine.js and CSS, no build step. Keep it that way unless there is a strong reason.

## License

By contributing, you agree that your contributions are licensed under the MIT License of this project.
