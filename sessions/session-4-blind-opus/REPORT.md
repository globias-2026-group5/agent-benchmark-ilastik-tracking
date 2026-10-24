# GloBIAS 2026 Session 6 — Group 5 (Consensus): "Can consensus become ground truth?"

Tool: ilastik 1.4.2 (Pixel Classification, headless). Data: ilastik's mitocheck example
(`mitocheck_94570_2D+t_01-53.h5`, 53 frames, 1344×1024 px, fluorescent nuclei; data courtesy of the Mitocheck project).

## 1. What was done

1. **Annotators.** 6 ilastik Pixel Classification projects that differ **only in their brush labels**
   (same features, same random forest):

   | ID | Source | Labelling style |
   |---|---|---|
   | A0 | **Real human labels** shipped with the ilastik example project (2014), frames 0/22/39 | as drawn by its author |
   | A1 | simulated | tight boundary, includes dim nuclei |
   | A2 | simulated | counts a 2-px halo around nuclei as nucleus |
   | A3 | simulated | calls dim nuclei background ("bright-only") |
   | A4 | simulated | very sparse (3 nuclei, 1 frame) |
   | A5 | simulated | standard style, only late frames (45, 52) |
   | A3b, A3c | simulated | two more "bright-only" annotators (for the bias experiment) |

   A1–A5, A3b, A3c are **my construction**, not people. They encode biases I chose on purpose, so the
   results show *mechanisms*, not real-world inter-annotator statistics.
2. Each project was retrained headless in ilastik and exported nucleus probabilities for all 53 frames.
   Binary mask = probability > 0.5, holes filled, objects ≤ 20 px removed.
3. Consensus rules compared: union, majority vote, unanimity, mean probability, weighted vote (A0 ×2),
   STAPLE, and a 3-class reference (unanimous nucleus / unanimous background / *ignore*).
4. **Bias experiment:** pool {A0, A1, A3, A3b, A3c} → 3 of 5 share the "bright-only" convention.
5. **Independent check** (not based on votes): do the objects that the majority rejects persist over time,
   and how bright are they relative to noise?

## 2. Findings

### 2a. Main pool (A0–A5): the rule changes the numbers a biologist would report

| | nuclei / frame | mean area (px) | flicker rate* |
|---|---|---|---|
| A0 (human) | 138.3 | 498 | 0.007 |
| A1 tight | 96.7 | 555 | 0.007 |
| A2 generous | 123.1 | 880 | 0.008 |
| A3 bright-only | 77.3 | 641 | 0.014 |
| A4 sparse | 107.8 | 661 | 0.026 |
| A5 late frames | 109.3 | 628 | 0.011 |
| **union (≥1/6)** | 124.3 | 889 | 0.008 |
| **majority (≥4/6)** | 110.7 | 573 | 0.028 |
| **unanimity (6/6)** | 79.1 | 475 | 0.016 |
| **mean probability > 0.5** | 113.8 | 585 | 0.024 |
| **weighted vote (A0 ×2)** | 111.7 | 596 | 0.011 |
| **STAPLE** | 108.8 | 680 | 0.011 |

\*fraction of objects that exist in a frame but in neither neighbouring frame (nuclei should not blink).

- Annotator-level counts span 77–138 per frame (1.8×); consensus rules still span 79–124 (1.6×), mean area 475–889 px (1.9×).
  Consensus narrows the spread but **the choice of rule is itself a result-changing decision**.
- Pairwise Dice between annotators: 0.63–0.94. Lowest pairs all involve A3 (bright-only) or A2 (halo).
- 3-class reference: **66 % of all pixels that any annotator called "nucleus" are disputed** (orange in
  `out/votes_A0_A1_A2_A3_A4_A5.png`): object boundaries plus whole dim nuclei. A unanimous core is small.
- Union has a lower count than A0 but the largest area: A2's halo merges touching nuclei. Union inherits the most generous annotator's error.
- Object-level votes: 462 objects were seen by only 1 annotator, median size 71 px (mostly specks) → excluding single-vote objects is reasonable; 2255 objects were seen by all 6.
- [Estimate, read from `out/counts_*.png`, not computed] Relative growth over the movie (~2.8–3× from frame 0 to 52) is similar for all rules; absolute counts and areas are not.

### 2b. Bias experiment: majority vote reproduces the majority's convention

Pool {A0, A1, A3, A3b, A3c}:
- Majority vote: **84 nuclei/frame vs 138 for A0**. STAPLE: 83.
- Agreement-based quality scores rank the **dissenting real human (A0) as the worst annotator**:
  leave-one-out Dice A0 = 0.66 (others 0.87–0.93); STAPLE sensitivity A0 = 0.78 (lowest; others 0.88–1.00).
- Of 7036 A0 objects (frames 1–51), **3065 are rejected by the majority**. These rejected objects:
  - median area 512 px vs 547 px for accepted ones → nucleus-sized, not debris;
  - median signal above background 76 vs 517 grey levels; background noise SD ≈ 7.8 → ~10× above noise
    [noise SD estimated from a 50×50 corner only — rough];
  - 94 % are present at the same place in both neighbouring frames (accepted: 97 %).
  So they are real, persistent, nucleus-sized structures — dim nuclei. Whether they *count* as nuclei
  (e.g. different cell-cycle stage, out of focus, dying) is a biological-definition question that no vote answers.
  See `out/bias_majority_frame26.png` (red circles = nuclei removed by the majority).

### 2c. Answer to the key question

**Consensus is not sufficient to define ground truth.** [Inference from the above, on simulated annotators]
- Consensus measures *agreement* (reproducibility), not *correctness* (validity). Shared bias passes through
  every rule tested (majority, mean, weighted, STAPLE); STAPLE and leave-one-out scores even penalise the correct minority.
- Rules disagree with each other enough to change cell counts and areas by >50 %.
- What makes a consensus *more* trustworthy:
  1. A written annotation protocol defining the object (do dim nuclei count? where is the boundary?) before annotating.
  2. Independent and diverse annotators (different training/backgrounds), not clones of one convention.
  3. Publish the rule **and** the disagreement map; keep an "ignore/uncertain" class instead of forcing a binary answer.
  4. Validate with evidence outside the votes: temporal consistency (used here), a second marker, higher-resolution
     imaging, or synthetic images with known truth.
  5. Test whether the downstream measurement is sensitive to the rule; report it if it is.

## 3. Formulas in the code (plain language)

All in `scripts/consensus.py` unless noted.

- **Dice score** (lines 37–39): `2 × (pixels both masks share) / (pixels in mask A + pixels in mask B)`.
  1 = identical outlines, 0 = no overlap. Example: two 100-px masks that share 80 px → 2·80/200 = 0.8.
- **Vote count**: for each pixel, the number of annotators who called it nucleus (0…N).
  - Union (line 106): votes ≥ 1. Majority (line 107): votes ≥ ⌊N/2⌋+1 (4 of 6, 3 of 5). Unanimity (line 108): votes = N.
- **Mean probability** (line 109): ilastik gives each pixel a 0–1 "how sure is it a nucleus" value per annotator; average them, call it nucleus if the average > 0.5.
- **Weighted vote** (line 110): A0 counts 2, others 1; nucleus if the weighted sum is more than half the total weight (with 6 annotators: > 3.5 of 7). The weight 2 is an arbitrary choice of mine.
- **STAPLE** (lines 42–58): estimates the truth and each annotator's reliability at the same time.
  - Each annotator gets two unknown scores: *sensitivity* p = how often they say "nucleus" when it is one;
    *specificity* q = how often they say "background" when it is background. Start with 0.9 for both.
  - Line 47: each pixel's pattern of votes is written as a 6-digit binary number (e.g. 101101), so only 2⁶ = 64 different cases need computing instead of 73 million pixels.
  - Line 50: *prior* = overall fraction of nucleus votes.
  - Lines 53–55 (E-step): for a vote pattern, `a` = prior × product over annotators of "chance this annotator would vote this way if the pixel were nucleus"; `b` = same assuming background. `W = a / (a + b)` = probability the pixel truly is nucleus.
  - Lines 56–57 (M-step): new p = share of the "probably nucleus" weight that each annotator marked as nucleus; new q likewise for background.
  - Repeat 50×; pixel is nucleus if W > 0.5 (line 58). Key limitation shown here: "reliable" is learned only from agreement with others.
- **3-class reference** (lines 114, 150): 2 = all say nucleus, 1 = all say background, 0 = anything in between (ignore).
- **Flicker rate** (lines 68–81): an object at frame t counts as flicker if none of its pixels is covered by any object at t−1 *and* none at t+1. Rate = flicker objects / all objects not touching the image border.
- **Signal above background** (`scripts/disputed_objects.py:23`): object's mean intensity minus the frame's median intensity (the median pixel is background because nuclei cover <10 % of the image).

## 4. Session chronicle

1. Read the assignment PDF; Group 5 topic = Consensus.
2. Downloaded `data.ilastik.org/mitocheck.zip` and ilastik 1.4.2 Linux.
3. Inspected the shipped project: label 1 = background, label 2 = nucleus; sparse labels on frames 0, 22, 39; overlay checked visually.
4. Wrote `scripts/make_annotators.py` (copies the shipped .ilp, replaces labels) and `scripts/run_ilastik.sh`.
5. Error 1: headless ilastik opens projects read-only by default → added `--readonly=False`.
6. Error 2: A0's original 64×64 label blocks failed to load ("Rois do not intersect") → rewrote them as full-frame blocks.
7. Error 3 (important): outputs were garbage (ring-shaped artefact). Diagnosed via ilastik's own Python: ilastik reads this file as t,x,y,c and stores labels transposed (1024×1344), so labels landed in wrong places. Fixed by writing labels transposed; verified label counts/coordinates match (734/188 px).
8. My mistake: `pkill -f ilastik` killed my own shell command; recovered.
9. Retrained 8 projects (~1–1.5 min each); A0 OOB error 0.007; visual check OK.
10. Wrote `scripts/consensus.py`; ran main and bias pools. My mistake: running both in parallel ran out of RAM; reran sequentially.
11. Added `scripts/disputed_objects.py` (independent persistence/brightness check).

## 5. Your interventions vs. my proactive decisions

- **Your interventions: 2** — the initial request, and the mid-task request for this report. No corrections, no approvals, no clarifying questions answered.
- **Proactive decisions: ~14** (my count):
  1. Interpreted "group 5 task question" as the Consensus brainstorming topic (Assignment II). This whole session could also serve as Assignment I material (an LLM producing a bioimage workflow), but I did not benchmark other LLMs.
  2. Chose dataset source and ilastik version.
  3. Simulated annotators because no human annotations were provided (largest assumption).
  4. Defined the 5 annotator styles.
  5. Used the shipped human labels as A0.
  6. Chose the 6 consensus rules + 3-class reference.
  7. Chose thresholds: p > 0.5, min object 20 px, "dim" = bottom third of intensity, A0 weight 2.
  8. Added the bias experiment (A3b, A3c).
  9. Added temporal persistence as an independent check.
  10–12. Fixed three ilastik loading issues (read-only, block format, axis transposition).
  13. Reran the OOM-killed analysis sequentially.
  14. Added object-level vote histogram and brightness/size analysis of disputed nuclei.
- I did not ask any clarifying question. In hindsight, one was warranted: whether your group already has real human annotations to use instead of simulated ones.

## 6. Limitations

- Simulated annotators encode biases I designed; real annotators may disagree differently and less systematically.
- "Annotations" are ilastik classifier outputs trained on sparse scribbles, not dense manual masks; annotator variability is filtered through the random forest.
- No true ground truth exists for this movie; the persistence check shows rejected objects are real, persistent structures, not that they must be counted as nuclei.
- Results are from one movie, one field of view.

## 7. Reproduce / use with real annotators

```
bash scripts/run_ilastik.sh projects/*.ilp            # retrain + export probabilities
python3 scripts/consensus.py A0_ilastik_human A1_tight ...   # names of files in out/probs
python3 scripts/disputed_objects.py
```
For real group annotations: each member labels in the ilastik GUI (Pixel Classification, label 1 = background,
label 2 = nucleus), exports Probabilities as HDF5 to `out/probs/<name>.h5` with internal path `probs`,
then run `consensus.py` with those names.

Outputs: `out/consensus_metrics_*.json`, `out/counts_*.png`, `out/votes_*.png`, `out/bias_majority_frame26.png`,
`out/disputed_objects.json`, `out/consensus/consensus_*.h5` (masks for every rule + 3-class + vote count).
