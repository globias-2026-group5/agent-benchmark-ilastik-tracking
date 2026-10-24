# GloBIAS 2026 Session 6, Group 5 (Consensus): MitoCheck + ilastik

**Model:** claude-sonnet-5-5 (Claude Sonnet 5.5), configured and last served model, per the session record. **Effort level:** medium (session setting `effort_level`). Both are as reported by the session metadata. I cannot verify them independently.

Question: *Can consensus become ground truth? Is consensus sufficient to define ground truth?*

## Important caveats (read first)
- **No human annotators were used.** The "annotators" are 5 **simulated** annotators: random-forest pixel classifiers, each trained on a random 60% of the 27 label patches (5,157 labelled pixels, frames 0, 22, 39, 40) stored in `pixelClassification.ilp`. Real annotators would differ more than these do. All five see the same images, features and labels, so their errors are strongly correlated. The agreement numbers are therefore **optimistic**.
- ilastik was **not run** (not installed here, GUI-based). I re-implemented its pixel-classification idea with scikit-learn. [Inference] The features approximate ilastik's (Gaussian, LoG, gradient magnitude, DoG, structure tensor, Hessian at sigma 1.6 and 3.5). They are not identical to ilastik's own.
- The "expert" in *expert adjudication* is the ilastik project's saved result (`_export.h5`, channel 1 > 0.5), which was trained on all 27 patches. Comparing against it is circular (see below).
- **There is no true ground truth for this dataset.** All comparisons are between methods.
- Only one movie (MitoCheck 94570, 53 frames, 1344x1024). I analysed 7 frames: 0, 22, 39, 40 (contain labels) and 10, 30, 52 (no labels).

## Findings (measured; numbers are in `results.json`)
| | frame 0 | 22 | 39 | 52 (unlabelled) |
|---|---|---|---|---|
| Fleiss kappa (5 annotators) | 0.868 | 0.869 | 0.883 | 0.881 |
| Mean pairwise Dice | 0.888 | 0.891 | 0.903 | 0.904 |
| Pixels where annotators disagree | 1.9% | 2.9% | 3.7% | 4.8% |

1. **Annotators agree strongly on nuclei interiors and disagree on boundaries.** The votes figure (`consensus_frame30.png`) shows a ring of 1-4 votes around every nucleus. Disagreement grows with cell density: 1.9% of pixels in frame 0 (77 nuclei) up to 4.8% in frame 52 (about 222).
2. **The rule changes the measurement by a few percent.** In frame 0, majority vote gives nucleus area 37,712 px, unanimity 36,043 px (-4.4%), expert adjudication 37,702 px. Nucleus counts differ by at most 2 per frame (e.g. 174 vs 176 in frame 39). So for counting, the rule barely matters. For **size/area** measurements it adds a systematic bias of about 4-5%.
3. **Weighted expertise gave results identical to majority vote.** The weights (0.92, 0.96, 0.75, 0.90, 0.93) were too similar to change any pixel. Weighting only matters if annotator skill differs a lot.
4. **Unanimity can reject real signal.** In frame 39, unanimity scores 46% on the labelled pixels versus 100% for majority vote. I did **not** investigate why. [Speculation] Dim nuclei that one annotator misses would explain it.
5. **Consensus does not equal agreement with an independent method.** Every consensus mask agrees with a simple Otsu threshold (background-subtracted, smoothed) only at Dice about 0.65-0.75, versus 0.99 against the ilastik export. [Unverified] I did not check which of the two is closer to the biology. The gap shows that annotators who agree with each other can still disagree with a different, equally reasonable method.
6. **Exclusion of uncertain pixels** drops 1.9-4.8% of pixels. The kept region is cleaner, but the removed pixels are exactly the boundary pixels that determine nucleus size. Any area measurement on it has the same bias as unanimity, and the excluded pixels are not measured at all.
7. **Expert adjudication scores about 1.00 against the ilastik export** (frame 0: 0.999). This is circular, because the adjudicator is the reference. It shows nothing about correctness.

**Answer to the key question (my interpretation, from this simulated setup only):** consensus is necessary for measuring reliability, but not sufficient to define ground truth. It resolves random disagreement, such as the boundary ring. It cannot detect errors that all annotators share (they all use the same images, features and labels), and the rule chosen is itself a modelling decision that shifts area by about 4-5%. A consensus label should therefore be stored together with the rule used, the per-pixel vote count, and an uncertainty mask, which is the output the assignment asks for. [Inference] Conclusions from real human annotators may differ.

## Math in the code, in plain terms
All of this is in `consensus.py`.

**Dice score (`dice`, line 100).** It measures how much two masks overlap, from 0 (nothing shared) to 1 (identical). Formula: 2 x (pixels both masks call nucleus) / (nucleus pixels in mask A + nucleus pixels in mask B). Example: if A and B each have 100 nucleus pixels and 90 are shared, Dice = 2 x 90 / 200 = 0.9. It is used for annotator-vs-annotator agreement and for comparing each consensus with the ilastik export and Otsu.

**Fleiss kappa (`fleiss_kappa`, lines 104-112).** It measures agreement among several raters beyond what luck would produce. For one pixel with 5 raters, count how many pairs of raters agree: P_i = (pos^2 + neg^2 - 5) / (5 x 4). (`pos` = votes for nucleus, `neg` = votes for background.) If all 5 vote the same, P_i = 1; for a 3-2 split, P_i = 0.4. `P_bar` (line 109) is the average over all pixels = observed agreement. `P_e` (line 111) = p^2 + (1-p)^2, where p is the overall fraction of nucleus votes. This is the agreement you would get if raters guessed at random with that nucleus rate. Kappa = (P_bar - P_e) / (1 - P_e): 0 means no better than chance, 1 means perfect. Our 0.87-0.88 is "very high" by the usual rough scale, but see the caveat about correlated simulated annotators.

**Majority vote (line 121).** A pixel is nucleus if at least 3 of 5 annotators say so.

**Unanimity (line 122).** A pixel is nucleus only if all 5 say so. It is stricter, so areas shrink.

**Weighted expertise (lines 116, 123).** Each annotator's weight is w = 2 x accuracy - 1, where accuracy is measured on label patches that annotator did not train on (line 89). Accuracy 0.5 (coin flip) gives weight 0, and 1.0 gives weight 1. A pixel is nucleus if the sum of the weights of annotators voting "nucleus" exceeds half of the total weight. With equal weights this is plain majority vote.

**Expert adjudication (line 124).** Where all 5 agree, keep their answer. Where they split, use the ilastik project's own output as the judge.

**Exclude uncertain (line 125).** Keep only pixels where all 5 agree (all nucleus or all background). Split pixels are marked "unknown" and left out of every statistic.

**Features (`features`, lines 30-50).** For each pixel the classifier sees numbers describing the local image. Gaussian smoothing is a local blurred average (brightness). Laplacian of Gaussian (LoG) responds to blob-like shapes. Gradient magnitude measures how fast brightness changes (edges). Difference of Gaussians (line 37) subtracts a more-blurred copy from a less-blurred one to highlight features of a particular size. Structure tensor and Hessian eigenvalues (lines 43 and 50) are two numbers describing the strength of change in the strongest and weakest directions, to tell edges from blobs. Sigma is the blur width in pixels (1.6 = fine, 3.5 = coarser).

**Otsu threshold (`otsu_ref`, line 138).** It picks the brightness cut-off that best separates the image into two groups (dark background, bright nuclei) by minimising the spread within each group. I subtract a heavily blurred copy of the image first, to flatten uneven background.

**Nucleus counting (line 134).** Touching nucleus pixels are grouped into objects. Objects below `MIN_SIZE` = 30 pixels are ignored as noise. Touching nuclei would be counted as one.

## Files
- `consensus.py`: the full analysis. Run with `python3 -I consensus.py <data folder> <output folder>`.
- `results.json`: all numbers per frame and rule.
- `consensus_frame30.png`: raw image, vote map, the five consensus masks and the ilastik export.

## Session chronicle
1. You uploaded the GloBIAS PDF and asked to answer the Group 5 task using ilastik and MitoCheck.
2. The first PDF read returned no text. I re-read it by page and found the task: "Consensus: Can consensus become ground truth?".
3. I checked the environment: ilastik not installed, IDR and ilastik.org reachable, scikit-image missing. A web search for MitoCheck did not find the ilastik-hosted data.
4. I proposed a workflow and asked 3 questions. In that answer I said I believed (unverified) that the dataset was on IDR (`idr0013`).
5. **You told me the dataset is on ilastik's website.** I fetched the download page, confirmed `https://data.ilastik.org/mitocheck.zip`, and downloaded it (118 MB, extracted 276 MB).
6. I inspected the contents. It holds one H2B-GFP movie (53 frames), an ilastik probability export, three `.ilp` projects, and no phenotype labels or multiple annotators. I installed `h5py`, `scikit-image`, `scikit-learn` and `matplotlib`, and viewed a frame.
7. I read the label patches in `pixelClassification.ilp` (27 patches, 5,157 pixels, frames 0/22/39/40) and its feature settings.
8. I proposed a plan and asked whether you had annotators.
9. **You said: run it with the existing labels, no human annotators, and report.**
10. I wrote and ran `consensus.py` (about 1 minute). The run printed which label is "nucleus" (label 2, verified against the probability map: label-1 pixels have mean nucleus probability 0.00). I looked at the results and the figure, and wrote this report.

Mistakes and friction: the first PDF read returned nothing and had to be repeated; a first Python call failed on a missing package; my claim that the dataset was probably on IDR was wrong or at least not the right source for this task, and you had to correct it.

## Your interventions vs. my own decisions
This is my own count and is subjective, since the boundary between "decision" and "step" is a judgement.

**Your messages: 3.**
| # | Message | Type |
|---|---|---|
| 1 | Original request | Task definition |
| 2 | "the mitocheck dataset is on ilastik's website" | **Correction.** I had not found the data. |
| 3 | "just run it with the existing labels. no human annotators." | **Answer to my question**, plus the report request |

So you intervened twice after the original request: 1 correction and 1 answer to a question I asked. I stopped to ask you twice (turn 1 with 3 questions, and turn 2 with 1 decision). That is 2 stops where I handed the decision to you, and 1 of them (the data location) you answered without being asked.

**Decisions I made without asking: about 14.**
1. Reading the PDF by page after the first read returned nothing
2. Checking the environment (ilastik, network, packages) before proposing a plan
3. Web-searching for the MitoCheck data
4. Proposing the 5-step workflow
5. Downloading the zip and extracting it
6. Installing Python packages
7. Choosing nucleus-vs-background pixel segmentation as the task
8. Simulating 5 annotators (5 chosen arbitrarily)
9. Giving each annotator a random 60% of label patches (60% chosen arbitrarily)
10. Approximating ilastik's features and settings with scipy
11. Weight formula 2 x accuracy - 1 for weighted expertise
12. Using the ilastik project export as the "expert" adjudicator
13. Adding an independent Otsu reference
14. Choosing the 7 frames, the 30-pixel minimum object size, and frame 30 for the figure

Decisions 8, 9, 11, 12 and 14 can change the numbers above, so you may want to review them before using the results.
