# What each session was told

User messages are quoted verbatim, typos included. All sessions ran in the same Claude Code cloud
environment (4 CPU cores, 15 GB RAM). Sessions 1–4 already had network access to `data.ilastik.org`
and `files.ilastik.org`; Session 0 did not at first.

## Session 0: the original run (21 Oct 2026, Opus 5.5)

1. *"I want you tu run ilastik and create some results frombthe demo data"*
2. *"I want to run the mitocheck example workflow, and get the resulted labels at the end. Save
   everything from each step of what your work here, on the repo."*
3. *"you have network access now"* (after the user allowed ilastik's hosts in the environment settings)
4. *"ok, maybe run it on ilastik 1.3.1 post? if you have issues. I worked on it back then and it was
   fine."*

## Sessions 1 and 2: reproduction (23 Oct 2026; Opus 5.5 high, Sonnet 5.5 medium)

The same prompt for both, except for the branch name (`repro/opus-5.5-high`, `repro/sonnet-5.5-medium`):

```
Reproducibility test for GloBIAS 2026 Group 5. Several agents get this same task and we will compare their success rates, so report exactly what happened, including failures.

Task: reproduce the ilastik MitoCheck workflow in https://github.com/Daniel-Waiger/GLOBIAS-2026-GROUP-5 (README.md, docs/REFERENCE.md): run it headless on the MitoCheck example data and produce the final tracking labels.

Rules:
- Work on a new branch, repro/opus-5.5-high. Never push to main.
- Regenerate the results; don't copy the committed ones.
- If you get stuck, say where and why. Don't fake outputs.

When done, commit REPRO_REPORT.md with: model and effort; pass/fail for each step; wall-clock time; every error you hit and how you fixed it; any point where you needed my help; and how your results compare with results/version_comparison.txt in the repo.
```

Later messages asked them to write down their findings and open questions, a chronicle of the session,
the count of interventions vs. proactive decisions, and the model and effort at the top of the report.
The exact wording of those later messages is not recorded here; their reports show what they answered.
(The repository has since moved to `globias-2026-group5/ilastik-mitocheck-run`.)

## Sessions 3 and 4: blind (23 Oct 2026; Sonnet 5.5 medium, Opus 5.5 high)

No repository attached. The same first message for both, with the session's assignment PDF attached:

> *"I want to answer group 5 task question, use ilastik and the mitocheck dataset"*

Later messages, verbatim:

| | Session 3 (Sonnet) | Session 4 (Opus) |
|---|---|---|
| after its first questions | *"the mitocheck dataset is on ilastik's website"* | — (it asked none) |
| | *"just run it with the existing labels. no human annotators. you'll need to report your findings, and the chronicles of this session, and how many times you needed my intervention vs. how many times you took a proactive decisions"* | *"you'll need to report your findings, the chronicles of this session, and how many times you needed my intervention vs. how many times you made proactive decisions"* |
| at the end | *"at the start of the report add the model and effort"* | — |

Session 4 never received the two answers Session 3 got, because it never asked. This is one way the two
blind runs did not have identical conditions.
