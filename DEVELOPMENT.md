# Gopnik Development Guide

This is the private development branch containing the complete project specifications and development artifacts.

## Branch Structure

- **`main`**: Public branch with clean codebase (no Kiro specs)
- **`development`**: Private branch with full development context including:
  - Kiro specification files (`.kiro/specs/`)
  - Development documentation
  - Complete project history
  - Internal development notes

## Kiro Specifications

This branch contains the complete Kiro specification files:

- **Requirements**: `.kiro/specs/gopnik-deidentification-toolkit/requirements.md`
- **Design**: `.kiro/specs/gopnik-deidentification-toolkit/design.md`
- **Tasks**: `.kiro/specs/gopnik-deidentification-toolkit/tasks.md`

## Development Workflow

1. **Feature Development**: Work on the `development` branch
2. **Clean Commits**: Cherry-pick or merge clean commits to `main`
3. **Public Releases**: Push only production-ready code to `main`
4. **Private Context**: Keep all Kiro specs and internal docs on `development`

## Task Progress

Track implementation progress using the tasks.md file. Use Kiro's task management features to:
- Mark tasks as in-progress or completed
- Execute individual tasks
- Maintain development context

## Security Notes

- This branch contains the complete development context
- Do not push this branch to public repositories
- Keep sensitive development information private
- Use the main branch for public collaboration

## Next Steps

Continue implementing tasks from the specification:
1. Data models and validation (Task 2)
2. Storage mechanism (Task 3)
3. AI engine integration (Task 4)
4. And so on...

Refer to the tasks.md file for the complete implementation plan.