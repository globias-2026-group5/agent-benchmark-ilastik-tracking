# RUNBOOK: scripts reconstructed from two blind sessions

Source: the transcripts of `session_011SCsdnthiNPCWauAmaxhD3` (s4_opus, Opus) and `session_01WSPbtbnNNzupbojYXHnMRf` (s3_sonnet, Sonnet). Both were read in full with `list_events` (kinds user and assistant, limit 100, paged with before_id until has_more was false): 5 pages for s4 and 3 pages for s3. Every file below was rebuilt from the Write/Edit tool inputs and from the Bash heredoc and sed commands, applied in order. Replacements were applied by extracting the literal old/new strings (Python `ast` parse, no execution). None of the sessions' code was run. All times are UTC, 2026-10-23, and are the time of the tool_use event (the result time is given where it matters).

Layout:
- `s4_opus/scripts/make_annotators.py`, `run_ilastik.sh`, `consensus.py`, `disputed_objects.py`: final versions.
- `s4_opus/scripts/*.v1_*`, `*.v2_*`: intermediate versions, kept for reference only. The original session had no such files.
- `s4_opus/session_scratchpad/dbg.py`: debug script written to the session scratchpad (`/tmp/claude-0/-home-user/3f83cace-4401-582f-aaa5-024fb50ca6e5/scratchpad/dbg.py`).
- `s4_opus/inline_not_a_file/make_bias_annotators_inline.py`: the inline heredoc that built A3b/A3c. **It was never a file in the original session.**
- `s4_opus/REPORT.md` and `s3_sonnet/group5/report.md`: the sessions' reports, with later edits applied.

---------------------------------------------------------------------
## s4_opus (`session_011SCsdnthiNPCWauAmaxhD3`), root `/home/user/g5`

### Commands, in the order they ran (cwd = working directory when the command started)
Exploration-only commands (pdftotext, curl -I, h5py inspection, preview PNGs) are left out unless noted.

1. 09:09:07, cwd /tmp. Download the data:
   `mkdir -p /home/user/g5/data /home/user/g5/tools && cd /home/user/g5/data && curl -sSLO https://data.ilastik.org/mitocheck.zip && unzip -o -q mitocheck.zip -d mitocheck && find mitocheck -type f | head -50 && du -sh mitocheck`
2. 09:09:08, run in the background, cwd /home/user/g5/data. **Download and unpack ilastik 1.4.2:**
   `cd /home/user/g5/tools && curl -sSLO https://files.ilastik.org/ilastik-1.4.2-Linux.tar.bz2 && tar xjf ilastik-1.4.2-Linux.tar.bz2 && rm ilastik-1.4.2-Linux.tar.bz2 && ls`
   It finished with exit code 0, notified at 09:12:06. The result is `/home/user/g5/tools/ilastik-1.4.2-Linux/`.
3. 09:09:24, cwd /home/user/g5/data/mitocheck/mitocheck_2d+t: `pip install -q h5py scikit-image scipy matplotlib tifffile`. numpy 2.5.3 was already installed.
4. 09:10:24: `mkdir -p /home/user/g5/out /home/user/g5/scripts && cd /home/user/g5 && python3 -I - <<'EOF' ...`. This is an inline label overlay (`out/inspect_frame0.png`). It found label 1 (background) = 4565 px on frames 0 and 22, and label 2 (nucleus) = 592 px on frames 0 and 39. **The cwd is /home/user/g5 from here on**, except where noted.
5. 09:11:31: Write `scripts/make_annotators.py` (v1).
6. 09:11:34: `python3 -I scripts/make_annotators.py && ls -la projects; ...` built `projects/A0..A5*.ilp`.
7. 09:12:06: Write `scripts/run_ilastik.sh` (v1).
8. 09:12:09: single-project test:
   `mkdir -p out/probs && export LAZYFLOW_THREADS=4 LAZYFLOW_TOTAL_RAM_MB=12000 && time tools/ilastik-1.4.2-Linux/run_ilastik.sh --headless --project=projects/A4_sparse.ilp --retrain --export_source="Probabilities" --output_format=hdf5 --output_filename_format=out/probs/A4_sparse.h5 --output_internal_path=probs data/mitocheck/mitocheck_2d+t/mitocheck_94570_2D+t_01-53.h5/volume/data 2>&1 | tail -25`
   It failed with `AssertionError: Can't save a read-only project`, because headless mode opens projects read-only by default.
9. 09:12:36, cwd `.../site-packages/ilastik`, absolute path. **Read-only fix (sed on the script):**
   `sed -i 's/--headless --project="$ilp" --retrain/--headless --readonly=False --project="$ilp" --retrain/' /home/user/g5/scripts/run_ilastik.sh`
10. 09:12:39: `cd /home/user/g5 && time bash scripts/run_ilastik.sh 2>&1 | tail -40; ls -la out/probs`. A0 failed with `Rois do not intersect` (the shipped 64x64 label blocks).
11. 09:13:00: an inline `python3 -I - <<'EOF'` patch of make_annotators.py. It added `read_shipped_labels`, so A0's shipped blocks are rewritten as full-frame blocks, and changed `mean_intensity` to `intensity_mean` and `remove_small_objects(..., 30)` to `max_size=30`. It also patched run_ilastik.sh (`set -euo` became `set -uo`). Then `python3 -I scripts/make_annotators.py && time bash scripts/run_ilastik.sh ...`, which moved to the background after 600 s. **Applied** (later output shows that make_annotators ran). These ilastik outputs were later deleted and were not used.
12. 09:24:05: `mkdir -p projects_bias && python3 -I - <<'EOF'` with the bias-annotator heredoc (first version, before the transpose fix; superseded by step 16).
13. 09:24:17: `python3 -I scripts/consensus.py A0_ilastik_human A1_tight` (debug run on the untransposed outputs). The probabilities were garbage, and the session then diagnosed the problem with dbg.py.
14. 09:26:26: `cd /home/user/g5 && cp projects/A4_sparse.ilp $S/t.ilp && cat > $S/dbg.py <<'EOF' ... ; tools/ilastik-1.4.2-Linux/bin/python $S/dbg.py $S/t.ilp`, where $S is the session scratchpad. ilastik reports raw/labels as (53,1024,1344) t,y,x,c, while the file labels were written as (1344,1024), so the labels were transposed.
15. 09:27:01: `pkill -f run_ilastik; pkill -f "ilastik"; ...` plus the transpose patch. It **exited 144 and was NOT applied**: the second pkill killed its own shell, which also killed the 09:13 background batch. Evidence: at 09:27:12, grep still shows the old line 135.
16. 09:27:12, result at 09:27:53. **Transpose fix applied (printed "patched")**: an inline python replace in `write_project`, giving `data=lab.T[None, :, :, None]` and `blockSlice [t:t+1,0:W,0:H,0:1]`. Then:
    `rm -rf out/probs/* projects/*.ilp projects_bias/*.ilp && python3 -I scripts/make_annotators.py 2>&1 | grep -v Warn && python3 -I - <<'EOF'` (bias heredoc, identical to step 12) `EOF`, and then dbg.py on a copy of A4_sparse.ilp. The verification was `equal True`, with 734 background and 188 foreground pixels. A `sed -i "s/^mine=.*/.../"` on dbg.py in the same command is a **no-op** (the replacement equals the original line).
17. 09:28:02, run in the background: **`cat > scripts/run_ilastik.sh <<'EOF'` rewrites the whole script (final version)**, then
    `bash scripts/run_ilastik.sh projects/*.ilp projects_bias/*.ilp`. It ran from 09:28:03 to 09:36:43 and exited 0. Training label counts (bg, fg): A0 (4565, 592), A1 (4815, 1012), A2 (4002, 3220), A3 (9008, 695), A4 (734, 188), A5 (2873, 785), A3b (7763, 1009), A3c (8281, 627).
18. 09:37:02: main pool, in the background: `python3 -I scripts/consensus.py A0_ilastik_human A1_tight A2_generous A3_bright_only A4_sparse A5_late_frames > out/log_main.txt 2>&1 &` (it completed), and concurrently the **bias pool**: `cd /home/user/g5 && python3 -I scripts/consensus.py A0_ilastik_human A1_tight A3_bright_only A3b_bright_only A3c_bright_only > out/log_bias.txt 2>&1` (it was killed for running out of memory).
19. 09:39:07: `rm -f out/*A0_A1.* out/consensus/consensus_A0_A1.h5 out/debug_probs.png && python3 -I scripts/consensus.py A0_ilastik_human A1_tight A3_bright_only A3b_bright_only A3c_bright_only > out/log_bias.txt 2>&1` (exit 0). **This is the bias pool run.**
20. 09:41:17: `cat > scripts/disputed_objects.py <<'EOF' ... EOF` and then `python3 -I scripts/disputed_objects.py`.
21. 09:42:46: Write REPORT.md. 09:42:49: `sed -i` corrects the STAPLE sentence (applied).

### The label-order and read-only fixes: in the scripts or separate?
- Read-only: first applied as a separate `sed -i` (09:12:36). It is **inside the final `run_ilastik.sh`** (`--readonly=False`) because of the 09:28 heredoc rewrite.
- Transposed labels: applied by a separate inline python string-replace (09:27:12). The result is **inside the final `make_annotators.py`** (`write_project`, with a comment), so it also covers A0 (through `read_shipped_labels`) and A3b/A3c.
- A3b/A3c are **not** produced by any script file. They come from an inline heredoc that imports `make_annotators` (see `inline_not_a_file/`).

### Data read (original paths)
- make_annotators.py: `/home/user/g5/data/mitocheck/mitocheck_2d+t/mitocheck_94570_2D+t_01-53.h5` (`volume/data`, 53x1344x1024x1 uint16) and the template `/home/user/g5/data/mitocheck/mitocheck_2d+t/pixelClassification.ilp` (labels `PixelClassification/LabelSets/labels000`). It writes `/home/user/g5/projects/*.ilp`. Each project's raw filePath is set to the absolute `.../mitocheck_94570_2D+t_01-53.h5/volume/data`, and the trained forests are deleted.
- run_ilastik.sh: `/home/user/g5/tools/ilastik-1.4.2-Linux/run_ilastik.sh`, the .ilp files given as arguments, and the raw path above. It writes `/home/user/g5/out/probs/<name>.h5` (dataset `probs`, 53x1344x1024x2, channel 1 = nucleus).
- consensus.py: `/home/user/g5/out/probs/<name>.h5` and the raw frame 26. It writes `out/consensus_metrics_<tag>.json`, `out/consensus/consensus_<tag>.h5`, `out/counts_<tag>.png` and `out/votes_<tag>.png`.
- disputed_objects.py: the raw file, `out/probs/A0_ilastik_human.h5`, and `out/consensus/consensus_A0_A1_A3_A3b_A3c.h5` (dataset `majority (>=3of5)`). It writes `out/disputed_objects.json` and `out/bias_majority_frame26.png`.

### Edits after the first version
| file | edit | time | applied? |
|---|---|---|---|
| run_ilastik.sh | sed adds `--readonly=False` | 09:12:36 | yes |
| run_ilastik.sh | `set -euo` changed to `set -uo` | 09:13:00 | yes |
| make_annotators.py | `read_shipped_labels` for A0, `intensity_mean`, `max_size=30` | 09:13:00 | yes |
| make_annotators.py | transpose labels (attempt 1) | 09:27:01 | **no** (shell killed, exit 144) |
| make_annotators.py | transpose labels | 09:27:12 | yes ("patched") |
| run_ilastik.sh | full rewrite: args, timestamps, grep filter, "all done" | 09:28:02 | yes (this is the final file) |
| dbg.py | sed `^mine=` | 09:27:12 | ran, but no-op |
| REPORT.md | sed on the STAPLE sentence | 09:42:49 | yes |
consensus.py and disputed_objects.py were never edited.

### How the simulated annotators were made (from make_annotators.py)
- **Candidate nuclei**, used only to place strokes: Gaussian sigma 1, minus the frame median, triangle threshold, objects of 30 px or less removed, then labelled. "Dim" means a mean intensity below the 33rd percentile of the candidates.
- **Per frame**: `n_nuclei` random candidates. Each gets a nucleus (FG=2) brush stroke: a line between 2 random points of the 2-px-eroded core, dilated by 1 px and clipped to the core. `dim_as_background` labels whole dim candidates as background (BG=1). The boundary rule `boundary_px` works as follows:
  - +b: a b-px outer ring, with 50% of its pixels labelled FG (a halo), plus BG on 50% of the ring b+2..b+3 px outside the object.
  - -b: BG on 50% of a b-px inner ring.
  - 0: no inner ring labels.
  - For -b and 0, BG is placed on 50% of the ring 2..3 px outside the object.
  - The BG outer rings are restricted to pixels outside all candidates. The FG halo is not.
- `n_bg_strokes` background strokes inside random 80x80 windows, at least 10 px from any candidate.
- The styles:
  - A1_tight: frames 0 and 26, 12 nuclei, b=-1, 6 BG strokes.
  - A2_generous: frames 0 and 26, 12 nuclei, b=+2, 6 BG strokes.
  - A3_bright_only: frames 0 and 26, 15 nuclei, b=0, dim nuclei as background, 6 BG strokes.
  - A4_sparse: frame 10, 3 nuclei, b=0, 3 BG strokes.
  - A5_late_frames: frames 45 and 52, 12 nuclei, b=0, 6 BG strokes.
- Seeds: `np.random.default_rng(i)` with i = 1..5 in that order.
- **A0** = the real shipped 2014 labels: 27 blocks of 64x64, 4565 bg / 592 fg px, with nonzero labels on frames 0, 22 and 39. They were rewritten as full-frame blocks and not modified.
- **A3b / A3c** use the A3_bright_only style: seed 31 on frames 5 and 30, and seed 32 on frames 15 and 40. Their projects are in `projects_bias/`.
- **Classifier**: each project is retrained by ilastik 1.4.2 headless (`--retrain`, the shipped project's feature selection, 16 feature channels per dbg.py, ilastik's Vigra random forest), and probabilities are exported for all 53 frames.
- **Masks in consensus.py**: p(nucleus) > 0.5, holes filled, objects of 20 px or less removed.
- **Consensus rules**:
  - union
  - majority (at least floor(n/2)+1 votes)
  - unanimity
  - mean probability > 0.5
  - weighted vote (A0 has weight 2)
  - binary STAPLE (EM, 50 iterations, starting p = q = 0.9)
  - a 3-class reference (unanimous nucleus / unanimous background / ignore)
- **Quality checks**: flicker rate (temporal plausibility) and per-object votes (an object counts as detected by an annotator at 50% or more overlap).

### UNCERTAIN (s4)
- The cwd before the first command is unknown; the first command does `cd /tmp`.
- Package versions installed by pip were not printed. scikit-image is at least 0.26, judging from its deprecation warnings.
- The ordering of the intermediate files v1/v2 is reconstructed. Only the final versions are certain to match disk, unless the files were changed outside the transcript.
- The exact cause of exit code 144 at 09:27:01 is inferred (self-kill by `pkill -f "ilastik"`, signal 16 = 144-128). That the patch was not applied is confirmed by the grep at 09:27:12.

---------------------------------------------------------------------
## s3_sonnet (`session_01WSPbtbnNNzupbojYXHnMRf`), root `/home/user/mitocheck_data`

### Commands
1. 09:11:37: `mkdir -p /home/user/mitocheck_data && cd /home/user/mitocheck_data && curl -sS -m 300 -O https://data.ilastik.org/mitocheck.zip && ls -la && unzip -o -q mitocheck.zip && find . -type f | head -50 && du -sh .`
2. 09:11:49, cwd /home/user/mitocheck_data/mitocheck_2d+t: `pip install -q h5py numpy scikit-image scikit-learn matplotlib` (versions not recorded).
3. 09:12:20 and 09:16:32: inline inspection of `pixelClassification.ilp` (27 label blocks, label sums {1: 4565, 2: 592}, feature selection matrix).
4. 09:17:07: Write `/home/user/mitocheck_data/group5/consensus.py`. It was the only version and was never edited.
5. 09:17:08: **`cd /home/user/mitocheck_data/group5 && time python3 -I consensus.py /home/user/mitocheck_data/mitocheck_2d+t /home/user/mitocheck_data/group5 2>&1 | tail -15`** (timeout 600 s, about 62 s). It printed "label that is nucleus: 2" and held-out accuracies [0.958 0.981 0.874 0.951 0.966].
6. 09:19:01: Write report.md. 09:34:49: an Edit adds the model/effort line (applied). ilastik itself was never downloaded or run.

### Data read
`/home/user/mitocheck_data/mitocheck_2d+t/mitocheck_94570_2D+t_01-53.h5` (raw), `.../mitocheck_94570_2D+t_01-53_export.h5` (the shipped ilastik probabilities; channel 1 > 0.5 is the "expert"), and `.../pixelClassification.ilp` (the label patches). It writes `/home/user/mitocheck_data/group5/results.json` and `consensus_frame30.png`.

### How the simulated annotators were made (from consensus.py)
- Five scikit-learn `RandomForestClassifier`s (100 trees, `random_state` = 0..4). Each is trained on a random 60% of the 27 label patches (int(0.6*27) = 16 patches, drawn without replacement with `np.random.default_rng(0)`, one sequential draw per annotator), and tested on the remaining 11 patches.
- Training pixels: those with label > 0; the target is label == NUC. NUC is chosen automatically by comparing with the export's channel 1 and came out as 2.
- Features (16 per pixel) at sigma 1.6 and 3.5:
  - Gaussian
  - LoG
  - gradient magnitude
  - DoG (sigma minus 0.66 sigma)
  - 2 structure-tensor eigenvalues (outer smoothing 0.5 sigma)
  - 2 Hessian eigenvalues
- Predicted on frames [0, 10, 22, 30, 39, 40, 52].
- Consensus rules:
  - majority (at least 3 of 5)
  - unanimity
  - weighted (w = max(2*acc-1, 1e-3), > half the weight)
  - expert adjudication (unanimous pixels keep the vote, split pixels take the export)
  - exclude-uncertain
- Reference: Otsu threshold after Gaussian sigma 1 minus Gaussian sigma 40. Objects below 30 px are not counted.

### UNCERTAIN (s3)
- The script's comment and the report say that labels sit on "frames 0, 22, 39, 40". s4's pixel overlay found nonzero labels only on frames 0, 22 and 39 (the frame-40 blocks appear to be all zero). Not verified here.
