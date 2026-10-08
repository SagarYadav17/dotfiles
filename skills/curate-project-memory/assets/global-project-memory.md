<!-- project-memory:start -->
## Shared Project Memory

Before substantive work in a Git checkout, use the shared `curate-project-memory` skill, preferring `~/.agents/skills/curate-project-memory` or `~/.claude/skills/curate-project-memory` over a separately installed copy. Run its `scripts/project_context.py resolve --repo <working-directory>` with Python 3. If the project is registered and startup loading is enabled, run `resume --repo <working-directory> --query <user-request>` and follow the skill's resume and checkpoint workflow. An unregistered repository needs no setup unless requested. Load context once per task; preserve task identity across milestones. Respect modes that prohibit writing and report unavailable registered context briefly.
<!-- project-memory:end -->
