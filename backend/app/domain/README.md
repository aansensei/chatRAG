# domain

Pure business rules — entities, value objects, repository interfaces.

`entities/` has real, in-use Pydantic models (see `entities/README.md`).
`enums/` is also real — `IngestJobStatus`, `ReviewStatus`, `SensitivityLevel`,
`DocumentStatus`, `UserRole`, imported by every entity. `events/` and
`repositories/` are still empty — no code depends on them.
