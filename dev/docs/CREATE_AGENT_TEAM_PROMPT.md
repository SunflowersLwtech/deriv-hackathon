# Create an Agent Team Prompt (Auth Module Refactor)

## Copy-Paste Prompt

```text
Create an agent team to refactor the auth module.
Spawn 3 teammates with strict ownership:

1) API Layer Teammate
- Refactor auth endpoints, request/response schemas, error handling, and middleware integration.
- Keep backward compatibility where possible.
- Document all endpoint contract changes.

2) Database Layer Teammate
- Refactor auth-related data models, migrations, indexing, and transactional integrity.
- Ensure safe migration path with rollback notes.
- Validate data consistency and performance impact.

3) Test Coverage Teammate
- Add/upgrade unit, integration, and regression tests for API + DB auth flows.
- Cover happy path, permission failures, token/session edge cases, and migration safety checks.
- Produce a coverage summary and unresolved risk list.

Team operating rules:
- Work in parallel when possible, then synchronize through a shared integration checklist.
- Do not break existing production auth behavior unless explicitly approved.
- Surface assumptions early and record decisions in a short decision log.
- Produce code changes with clear file-level summaries.
- Run lint/tests and report exact commands + results.

Final output format:
1) What changed (API / DB / Tests)
2) Compatibility risks
3) Validation evidence (test results)
4) Follow-up tasks
```

## Project-Specific Variant (TradeIQ)

```text
Create an agent team to refactor the TradeIQ auth module.
Spawn 3 teammates: API layer, database layer, test coverage.

Context:
- Backend: Django + DRF
- Auth target: Supabase JWT verification + Google Sign-In session flow integration
- Keep existing business modules stable (market/behavior/content/demo)

Teammate A: API Layer
- Implement/clean auth middleware wiring for protected endpoints.
- Standardize 401/403 responses and auth error payloads.
- Ensure Bearer token parsing + request user mapping are consistent.

Teammate B: Database Layer
- Ensure auth user mapping to `users` table is idempotent (create-on-first-login).
- Validate schema assumptions and migration safety.
- Add indexes/constraints only when justified by query paths.

Teammate C: Test Coverage
- Add tests for: valid JWT, expired JWT, invalid signature, missing token, first-login user creation.
- Add endpoint authorization tests for protected/unprotected routes.
- Provide a final auth test matrix and gaps.

Execution constraints:
- No OpenRouter usage.
- Read env from project root `.env`.
- Minimize invasive changes; keep interfaces stable.
- Report exact files changed and commands run.

Deliverables:
1) Unified PR-style summary
2) Risk assessment + rollback plan
3) Test evidence and remaining gaps
```
