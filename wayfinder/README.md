# Wayfinder tracker (GitHub Issues)

This repo's issue tracker is **GitHub Issues** on `mbarnfield63/MARVEL5`. This doc is the "Wayfinding operations" reference future sessions should consult.

## Wayfinding operations

- **Map** = an issue labelled `wayfinder:map`.
- **Ticket** = an issue labelled `wayfinder:research`, `wayfinder:prototype`, `wayfinder:grilling`, or `wayfinder:task`, linked as a **native GitHub sub-issue** of its map.
- **Claim** a ticket = `gh issue edit <n> --add-assignee @me`.
- **Blocking** = GitHub's native issue-dependency relation (`blocked by` / `blocking`), visible in the issue sidebar. Query/set via REST: `gh api repos/mbarnfield63/MARVEL5/issues/<n>/dependencies/blocked_by`.
- **Unblocked** = zero open issues in that dependency list.
- **Frontier** = open, unassigned, unblocked sub-issues of a map — e.g. `gh issue list --repo mbarnfield63/MARVEL5 --json number,title,assignees,labels`, cross-referenced against each issue's `issue_dependencies_summary`.
- **Resolve** a ticket = comment the answer, `gh issue close <n>`, then append a one-line entry to the map issue's `## Decisions so far` section (`gh issue edit <map-n> --body ...`).
- `/research` and `/domain-modeling` skills are not installed in this environment — substitute a general-purpose/Explore agent (research tickets) and `/grilling` alone (domain-modeling tickets).

## Current maps

- [MARVEL v5 Engine](https://github.com/mbarnfield63/MARVEL5/issues/3)
- [MARVEL v5 Viz App](https://github.com/mbarnfield63/MARVEL5/issues/4)
