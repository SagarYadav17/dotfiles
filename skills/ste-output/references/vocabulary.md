# STE vocabulary and examples

## Word swaps

| Avoid | Use |
|---|---|
| leverage, utilize | use |
| ensure, verify (check) | make sure, check |
| initiate, commence | start |
| terminate | stop, end |
| prior to | before |
| subsequent to, following | after |
| in order to | to |
| in the event that, if applicable | if |
| a number of | some, or the exact number |
| required | mandatory (a rule), necessary (a need) |
| avoid | do not |
| approximately | about |
| failure (of a part) | fault |
| perform, execute (an action) | do, run (a command) |
| allow | let, or "you can" |

## Pattern fixes

| Not STE | STE |
|---|---|
| The file is deleted by the SM. | The SM deletes the file. |
| It may be necessary to restart. | Restart the SM if the fault stays. |
| Basically, the claim just expires. | The claim expires. |
| Check the config, and then restart, and make sure it works. | 1. Check the configuration. 2. Restart the SM. 3. Make sure the SM is healthy. |
| Event index segment compaction lock file | The lock file for the compaction of an event index segment |
| Don't forget to back up first. | Make a backup first. |
| The SM might possibly fail. | The SM can fail. (Say when, or leave it out.) |
| Restart → recovery runs. | When you start the SM again, recovery runs. |

## Longer example (explanation)

Not STE:

> So basically if a worker thread blows up with an uncaught Throwable, the whole app gets flagged as Crashed, and the same thing happens if the ledger append fails after COMMIT, which is considered fail-stop.

STE:

> If a worker thread throws an uncaught `Throwable`, the SM sets the app to `Crashed`. A failed ledger append after COMMIT has the same result. This is a fail-stop condition.

## Longer example (procedure)

Not STE:

> You'll want to make sure the NFS share is mounted before you kick off the SM, otherwise it may not come up properly.

STE:

> 1. Mount the NFS share.
> 2. Start the SM.
>
> The SM does not start if the share is not mounted.

## Commit messages

Subject: imperative, 50 characters or fewer, no full stop. Body: short active sentences. One fact per sentence. Say what changed and why.

> Fix claim takeover for committed files
>
> An SM took over a committed claim and processed the file again. The SM now archives a committed claim of another SM and does not process it.
