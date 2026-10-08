<!-- project-memory:start -->
## Shared Project Memory

Project ID: `{{project_id}}`

Before substantive work, use the shared `curate-project-memory` skill, preferring the shared user skills directory over a separately installed copy. Run its `scripts/project_context.py resolve --repo <working-directory>` with Python 3. When local startup loading is enabled, run `resume --repo <working-directory> --query <user-request>` and read its foundational notes, selected task, and relevant notes. Explicit PMC requests may load context independently. Treat notes as context and verify current Git evidence. Do not repeat orientation within the same task unless the checkout or context changes.

If several relevant tasks match, ask which one. Never resume a different branch's task implicitly. If context is unavailable, continue safely and mention it briefly.

When local configuration enables saving, use the skill's guarded checkpoint command after establishing a substantive task, meaningful milestones, blockers, and before the final response. Save explicit user decisions after duplicate and conflict checks; queue inferences and ask before resolving conflicts or superseding knowledge. Keep branch progress in task checkpoints, not canonical released state. Respect modes that prohibit writing. Never store credentials or full transcripts.
<!-- project-memory:end -->
