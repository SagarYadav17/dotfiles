# Notion project knowledge

Use this workflow when the user asks to keep project knowledge in Notion. The agent can be Claude, Codex, Gemini, or another agent with suitable local and Notion access. Use the Notion tools available in that agent's environment. Follow their current instructions and permissions. Do not assume a specific connector, tool name, workspace, or page ID.

## Storage and access

- Keep project overviews, priorities, product decisions, and open questions in the user's private Notion project page. Include enough context for the user to understand the project on a phone.
- Keep coding notes, branch progress, task checkpoints, detailed procedures, and debugging evidence in the local vault. The existing helper and its revision checks continue to manage local checkpoints.
- Treat each Notion page as the source for its project-level knowledge. Treat the local vault as the source for coding memory. Link related decisions when both need context. Do not set up automatic or two-way sync.
- A request to set up or update Notion authorizes the requested transfer. Inspect the material and send only relevant, curated content. Exclude credentials, private keys, tokens, raw logs, and unnecessary sensitive details.
- If Notion access is unavailable, report the limitation. Keep local work usable and do not claim that a remote update succeeded. A later authorized request can complete the update.

## Projects directory

1. Search the user's accessible Notion workspace for the existing private Projects hub and project page. Reuse them when the match is clear.
2. If the user asks to create a hub, use a private Projects page with a project database. Use Name, Status, Summary, and Repository properties. Use Active, Paused, and Archived status options. Leave unknown values empty.
3. Create a list view that shows the project name and status. Keep each project in its own database page.
4. Preserve existing page content and identifiers when moving or updating a page. Do not overwrite unrelated content or create duplicates.
5. Link the Notion page from the local `Project Home.md` when that file exists. Keep absolute machine paths out of durable notes.

## Populate and maintain knowledge

1. Inspect the local project home, project index, current state, and relevant accepted decisions. A project can have useful vault notes without a registered or available checkout.
2. Summarize the purpose, meaningful priorities, decisions, and open questions. Use source dates for time-sensitive claims. Label unverified, branch-only, and planned work accurately.
3. Preserve existing Notion content. Reconcile duplicates and conflicts against the source notes. Ask the user before resolving a conflict or removing an existing decision.
4. Use the available Notion tools to write only within the user's requested scope. Read back the page or directory when needed to verify the result. Report the page link and any unavailable source or unverified content.
5. Refresh Notion when the user asks. For ordinary coding tasks, keep the local checkpoint workflow and propose any worthwhile project-level update at a natural checkpoint. Do not assume that a local checkpoint authorizes a Notion write.
