# Issue policy

The tracker is the list of what is wrong with this corpus and what is
outstanding. If something is a known defect in the published data, or work this
repo intends to do, it belongs here rather than in a comment, a note file, or my
head. Nothing else is a tracker: `data/corpus_changes/` and the commit log are an
audit trail, a reversible record of what was done to which rows, and they answer
a different question.

## What goes in

- A defect in the served data or in a published table, described so a user can
  see it themselves. Give the counts.
- A known limitation of a release, including anything a tag pins that has since
  been found wrong, until it is either repaired or accepted into the published
  known-limitations registry.
- Work this repo intends to do: a carve, a re-key, a source to bring in.
- A decision that has to be made before work can proceed, with the options.

One issue per thing a reader can observe, not per task it takes to fix. The
~40,000 wrong corrections are one issue, not forty.

## What does not

- Work being started immediately. Track that in the commit.
- Anything already fixed and unreleased, unless a tag pins the broken state.
- Refactors and ideas with no observable effect on the data.

## Labels

| label | meaning |
| --- | --- |
| `data-defect` | the published data is wrong |
| `limitation` | true of the data by construction, not a bug to fix |
| `work` | intended work, not itself a defect |
| `decision` | blocked on a call I have to make |

## Closing

Close a repaired defect only when the fix is in a tagged release, and name the
tag in the closing comment. Code landing on `main` is not enough: the tracker
describes what a consumer gets, and until there is a tag they get the old bytes.

A limitation may instead close as `not planned` when all of the following are
true:

- its current measurement is generated into `data/known_limitations.json` and
  exposed by the release's existing quality artifacts;
- every approved automatic repair class is exhausted;
- the remaining work needs a new evidence source, a new policy decision, or
  occurrence-level human review; and
- the closing comment names the tagged release and the condition that should
  reopen the issue.

That disposition does not mean the limitation stopped being true. It keeps the
release caveat visible without using an issue with no currently safe action as
an indefinite work queue.
