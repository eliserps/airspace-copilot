# 🤝 Contributing

## Setup

Follow the [quick start](README.md#quick-start), then install the git hooks: `pip install pre-commit && pre-commit install`

## Before opening a PR

🧪 **Backend** (from `backend/`): `uv run ruff check . && uv run mypy app tests scripts && uv run pytest`

🧪 **Frontend** (from `frontend/`): `npm run lint && npm run typecheck && npm test`

🌐 **UI changes**: `npm run test:e2e` (includes the accessibility audit)

📜 **API changes**: regenerate the contract. See [frontend/README.md](frontend/README.md#api-types)

`make check` runs all of the above except e2e.

## Conventions

✍️ **Commits**: [Conventional Commits](https://www.conventionalcommits.org/) (`feat:`, `fix:`, `refactor:`, `docs:`, `test:`, `chore:`)

🧩 **Backend**: new endpoints go in the matching `app/<domain>/router.py`; logic goes in a service that receives its clients by injection

🧩 **Frontend**: components live in the folder of the screen area that shows them (`header/`, `globe/`, `sidebar/<tab>/`); data access goes in `src/api/`

🌐 **Texts**: every user-facing string goes in both `lib/i18n/locales/en.ts` and `pt.ts` (TypeScript fails if one is missing)

📐 **Bigger decisions**: add an ADR in [docs/adr/](docs/adr/README.md)
