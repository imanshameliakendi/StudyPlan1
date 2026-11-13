# StudyPlan Copilot Instructions

## Architecture boundaries
- Frontend must only call the REST API and must not access the database directly.
- Planner code must remain independent from FastAPI, Streamlit, SQLite, and ORM frameworks.
- Business logic belongs in backend services rather than endpoint functions when it affects multiple routes.

## Security requirements
- Never hardcode secrets or admin credentials.
- Do not add a default administrator password; provision administrators from environment variables only.
- Use argon2 password hashing.
- Enforce ownership checks for each student-specific endpoint.
- Validate file content, types, sizes, and names before storing uploaded files.
- Keep uploaded data in private storage and never expose it directly.
- Remove course files when archiving and user files when deleting accounts; do not include personal data in audit details.

## Testing requirements
- Add focused automated tests for each major component.
- Run relevant tests after significant changes.
- Preserve completed-session immutability and historical records.
- Keep missed sessions as historical records and schedule their remaining work during replanning.

## Coding standards
- Prefer clear and small functions.
- Use type hints.
- Keep database and application configuration centralized.
- Favor deterministic algorithms in the planner.
- Do not add AI/LLM calls or machine learning at runtime.

## Documentation expectations
- Update README and SPEC when behavior changes materially.
- Record assumptions in code comments only if the reason is non-obvious.

## Incremental development practice
- Make progress in small, verifiable steps.
- Validate before expanding to broader features.
