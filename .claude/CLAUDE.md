<!-- project-memory:start -->
## Shared Project Memory

Before substantive work in a Git checkout, use the shared `curate-project-memory` skill, preferring `~/.agents/skills/curate-project-memory` or `~/.claude/skills/curate-project-memory` over a separately installed copy. Run its `scripts/project_context.py resolve --repo <working-directory>` with Python 3. If the project is registered and startup loading is enabled, run `resume --repo <working-directory> --query <user-request>` and follow the skill's resume and checkpoint workflow. An unregistered repository needs no setup unless requested. Load context once per task; preserve task identity across milestones. Respect modes that prohibit writing and report unavailable registered context briefly.
<!-- project-memory:end -->

## Writing Style: Simplified Technical English

STE style mode is on by default in every session. Write all answers, commit messages, code comments and documents in ASD-STE100 Simplified Technical English at about 80% weight. Stop only when the user says "stop ste" or "normal mode", and only for that session. The full rules, rewrite mode and word list are in the `ste-output` skill; load it when you rewrite a file or are unsure of a word.

- One topic per sentence. At most 20 words (25 for a procedure step).
- Active voice and simple tenses. Name the actor.
- Start each step with a verb. One instruction per step.
- Use simple approved words ("use", "make sure", "start"). No idioms, filler, hedging or marketing words.
- One word, one meaning. Give a reason in a separate short sentence.
- Keep code, commands, paths, config keys, error messages and quoted text exactly as they are.
- Warnings and destructive-action confirmations keep their full detail.

# graphify
- **graphify** (`~/.claude/skills/graphify/SKILL.md`) - any input to knowledge graph. Trigger: `/graphify`
When the user types `/graphify`, use the installed graphify skill or instructions before doing anything else.
