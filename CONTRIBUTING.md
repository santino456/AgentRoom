# Contributing to AgentRoom

Thank you for your interest in contributing! This guide will help you get started.

## Development Setup

See [docs/development.md](docs/development.md) for detailed environment setup instructions.

Quick start:

```bash
make install
make dev        # Start backend
cd frontend && npm run dev   # Start frontend (separate terminal)
```

## Code Style

### Backend

- Follow PEP 8
- Use type hints where practical
- Run `ruff check .` before committing
- Run `ruff format .` to auto-format

### Frontend

- Use Prettier for formatting
- Functional components preferred
- Run `npx prettier --check .` before committing

## Testing

All changes should include tests:

```bash
# Backend
cd backend && ../.venv/bin/python -m pytest tests/ -v

# Frontend
cd frontend && npx vitest run
```

## Commit Messages

We follow [Conventional Commits](https://www.conventionalcommits.org/):

- `feat:` — New feature
- `fix:` — Bug fix
- `docs:` — Documentation changes
- `test:` — Test changes
- `refactor:` — Code refactoring
- `chore:` — Maintenance tasks

Example: `feat: add message reply support`

## Pull Request Process

1. Fork the repository
2. Create a feature branch (`git checkout -b feat/my-feature`)
3. Make your changes with tests
4. Ensure CI passes (`make test`)
5. Submit a pull request with a clear description

## Questions?

Open an issue or start a discussion. We're happy to help!
