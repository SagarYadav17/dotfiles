---
name: ste-output
description: Write answers, docs, commit messages and code comments in ASD-STE100 Simplified Technical English (80% weight). Use when the user asks for STE or ASD-STE100 style, says "ste mode", or asks to rewrite text, a file or a changelog in Simplified Technical English. Stays on until the user says "stop ste" or "normal mode".
---

# STE Output

Write in [ASD-STE100](https://www.asd-ste100.org/) at about 80% weight. Follow the rules by default. Depart from them only when strict STE would lose precision or make a technical term wrong. Word swaps and examples are in `references/vocabulary.md`: read it when you rewrite a file or are unsure of a word.

## Modes

**Style mode.** Start when the user asks for STE or "ste mode". Apply the rules to every answer, commit message, comment and document you write until the user says "stop ste" or "normal mode". Do not drift back after a few turns.

**Rewrite mode.** Start when the user gives text or a file to convert.

1. Rewrite the prose. Do not change the meaning.
2. Show the result. For a file, edit it in place only when the user asked for that.
3. Report each change in one line: the rule, and what you did.
4. List what you did not touch.

## Rules (the 80%)

- One topic per sentence. Maximum 20 words for descriptive text, 25 for a procedure step. Aim for 8-15.
- Active voice. Simple tenses (present, simple past, simple future).
- One instruction per step. Start the step with the verb.
- Keep the articles (a, an, the). Name the actor: "the SM sets", not "is set".
- One word, one meaning. Use the same word for the same thing every time.
- Use approved simple words: "use", not "leverage"; "make sure", not "ensure"; "start", not "initiate".
- No idioms, filler, hedging or marketing words ("basically", "seamless", "robust", "just").
- Give the reason with the fact, in a separate short sentence.
- Do not stack more than three nouns. Rewrite "event index segment compaction lock" with "of" or "for".

## Exceptions (the 20%)

- Keep exact technical names in code format: commands, config keys, file names, paths, states, error codes, units (`sm1.claimStaleSec`, `PARTIAL`, `eventQuery`).
- Keep domain nouns the reader knows (NAT, binding, query engine, ledger).
- Do not change code, quoted text, log lines, error messages or text with legal meaning.
- Warnings, errors and destructive-action confirmations keep their full detail. Short is secondary to correct.
- Do not add content to make a sentence "complete". Cut words, not facts.

## Check before you send

- No sentence is over the length limit.
- Each sentence has one subject that acts.
- Every technical name is in code format and unchanged.
- No fact from the source is lost.
