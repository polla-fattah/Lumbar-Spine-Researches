# Clinical system: design plan

Written 2026-08-27. A radiologist-facing system that ingests a lumbar MRI study
and returns per-target stenosis grades with two-plane visual evidence.

This is **not thesis work**. Chapter 3 is locked, RQ4 was not executed, and
nothing here belongs in the submission. It is a separate deliverable that reuses
the thesis infrastructure, and it is a good fit for a supervised student project.

---

## 1. What it does, and what it must never claim

**It grades severity at supplied locations.** For each of 25 targets -- five
lumbar levels by five conditions -- it returns Normal/Mild, Moderate or Severe
with a confidence, plus the image evidence it used.

**It does not detect disease.** The model never searches a study. It receives a
crop centred on a coordinate and grades it. If the coordinate is wrong, the grade
is meaningless and the system has no way to notice.

**It does not name a pathology.** LumbarDISC labels stenosis *severity*, not its
cause. Nothing distinguishes a disc bulge from facet hypertrophy or ligamentum
flavum thickening. A caption saying "bulge detected" would be false.

**"Baseline versus our proposal" is a grading comparison, not a localisation
one.** Neither model localises; both are given coordinates. If both paths are
offered, localisation is identical between them and only the grades differ.

**No claim of clinical benefit.** The thesis measures agreement with a
retrospective reference standard on one benchmark. It does not measure diagnostic
accuracy against surgical ground truth, reporting time, or patient outcome. The
interface must not imply otherwise, and the two-plane view makes it look far more
like a detector than it is.

---

## 2. Architecture

Four stages with file-shaped interfaces between them, so any stage can be
replaced without touching the others.

```
  DICOM upload
        |
   [1] INGEST      de-identify -> validate -> convert to NIfTI
        |          out: de-identified study + linkage entry
        |
   [2] LOCALISE    TotalSpineSeg -> 5 disc levels -> 25 target coordinates
        |          out: coordinates CSV (same shape as
        |               train_label_coordinates.csv)
        |
   [3] GRADE       existing model -> 25 grades + confidences
        |          out: results rows
        |
   [4] RENDER      two-plane overlays at native resolution
                   out: PNGs on disk, paths in the database
```

**The interface between 2 and 3 is a coordinate CSV.** That single decision buys
most of the flexibility: TotalSpineSeg can be swapped for a trained detector, or
replaced entirely by a radiologist clicking five disc levels, without any change
downstream. It is also why localisation never needs to share a Python environment
with the model.

### Reusable today

| Stage | Existing code |
| :-- | :-- |
| 1 | `tools/deidentify_dicom.py`, `tools/detect_burned_in_text.py`, `implementation/dicom_to_nifti.py` |
| 2 | nothing yet -- TotalSpineSeg is untested on this data |
| 3 | `amog_train.AMOGNet`, checkpoints in `data/checkpoints/` |
| 4 | `implementation/roi_qc.py` (two-plane rendering, physical-size markers, native-resolution reporting) |

Stage 4 is essentially done. Stage 1 is most of the way there. Stage 3 is a thin
wrapper over existing inference. **Stage 2 is the whole risk.**

---

## 3. Data model

SQLite. One file, no server, queryable, moves with the project.

```sql
-- one row per uploaded study
CREATE TABLE study (
  study_id        TEXT PRIMARY KEY,   -- freshly assigned, not derived from PHI
  ingested_at     TEXT NOT NULL,
  source_hash     TEXT NOT NULL,      -- hash of the original archive
  deid_version    TEXT NOT NULL,
  burnin_screened INTEGER NOT NULL,   -- 0/1
  burnin_flagged  INTEGER NOT NULL,
  notes           TEXT
);

-- where the targets came from; a study may have several attempts
CREATE TABLE coordinate_set (
  coord_set_id  TEXT PRIMARY KEY,
  study_id      TEXT NOT NULL REFERENCES study(study_id),
  source        TEXT NOT NULL,        -- 'totalspineseg' | 'human' | 'imported'
  created_at    TEXT NOT NULL,
  created_by    TEXT,
  tool_version  TEXT
);

CREATE TABLE coordinate (
  coord_set_id  TEXT NOT NULL REFERENCES coordinate_set(coord_set_id),
  level         TEXT NOT NULL,        -- L1-L2 .. L5-S1
  condition     TEXT NOT NULL,
  series_uid    TEXT NOT NULL,
  instance      INTEGER NOT NULL,
  col           REAL NOT NULL,
  row           REAL NOT NULL,
  PRIMARY KEY (coord_set_id, level, condition)
);

-- one row per target per model per coordinate set
CREATE TABLE result (
  study_id      TEXT NOT NULL REFERENCES study(study_id),
  coord_set_id  TEXT NOT NULL REFERENCES coordinate_set(coord_set_id),
  model_hash    TEXT NOT NULL,        -- checkpoint SHA-256
  model_tag     TEXT NOT NULL,        -- 'E0' | 'E7'
  level         TEXT NOT NULL,
  condition     TEXT NOT NULL,
  grade         INTEGER NOT NULL,     -- 0/1/2
  confidence    REAL NOT NULL,
  computed_at   TEXT NOT NULL,
  figure_path   TEXT,                 -- PNG on disk, not a blob
  PRIMARY KEY (study_id, coord_set_id, model_hash, level, condition)
);

CREATE TABLE model (
  model_hash   TEXT PRIMARY KEY,
  model_tag    TEXT NOT NULL,
  trained_at   TEXT,
  seed         INTEGER,
  test_qwk     REAL,
  notes        TEXT
);
```

Three things the schema enforces deliberately:

**`coord_set_id` is part of every result key.** TotalSpineSeg coordinates and
human-clicked coordinates produce different grades from the same model, and
conflating them would be untraceable.

**`model_hash` is part of the key too.** A radiologist reopening a study in June
must get the same answer as in March, or be able to see why not. Re-evaluating
writes a new row rather than overwriting; both versions coexist and the clinician
chooses when to move.

**Images live on disk, paths in the table.** Do not put PNGs in SQLite.

### Patient identity

`study_id` is freshly assigned and derives from nothing identifying. The mapping
from `study_id` back to the original patient lives in a **separate,
access-controlled linkage file outside the application database** -- the pattern
`tools/deidentify_dicom.py` already uses. Without it a case can never be
re-linked to its report or its row in the reference spreadsheet; with it inside
the same database, the de-identification is decorative.

---

## 4. Backend

FastAPI. Grading takes minutes, not milliseconds, so every long operation is a
job, never a synchronous request.

```
POST   /studies                  upload; returns study_id + job_id
GET    /jobs/{job_id}            queued | running | done | failed (+ progress)
GET    /studies/{id}             metadata, coordinate sets, available results
POST   /studies/{id}/localise    run stage 2; body picks source
PUT    /studies/{id}/coordinates human-supplied disc levels
POST   /studies/{id}/grade       run stage 3; body picks model_tag
GET    /studies/{id}/results     grades for a (coord_set, model) pair
GET    /figures/{path}           rendered PNG
GET    /models                   available checkpoints and their test metrics
```

**Job queue.** A single worker process with a SQLite-backed queue is sufficient
and avoids adding Redis or Celery to a system one hospital will run. One GPU
means one job at a time regardless.

**Model loading.** Load each checkpoint once at worker start, not per request.

**Idempotency.** `POST /grade` for an existing `(study, coord_set, model)` returns
the stored result rather than recomputing. That is the cache, and `model_hash` is
what validates it.

---

## 5. Frontend

Five screens. Plain React or even server-rendered templates; this does not need a
heavy framework.

**Upload.** Drag-and-drop a study folder or zip. Shows de-identification progress
explicitly, including the burned-in screen result, because the user needs to see
that it happened.

**Study list.** Studies, ingest date, whether localisation and grading exist,
burned-in flag state.

**Localisation review.** The disc levels TotalSpineSeg found, overlaid on
sagittal. The radiologist confirms or drags them. **This screen is not optional** --
localisation quality is unvalidated on local data, and an unreviewed coordinate
silently invalidates every grade downstream. Confirming writes a new
`coordinate_set` with `source='human'`.

**Results.** The 5x5 grid, colour-coded by grade. Clicking a cell opens the
two-plane view for that target. A model selector switches between baseline and
full system on the same coordinates; the grid diffs them.

**Study report.** Printable summary. Must carry the scope disclaimer from
Section 1 on the page itself, not buried in an about box.

---

## 6. Deployment and safety

**On-premise.** The whole system inside the hospital network. This converts a
hard compliance problem into a deployment choice, and hospitals will require it
anyway. If any component must be remote, de-identification happens at the edge
before anything leaves.

**De-identification is a gate, not a step.** A study that fails the burned-in
screen, or whose de-identification errors, must not reach stages 2-4 at all.

**Audit trail.** Every result row already records model, coordinate source and
timestamp. Add the operator for human-supplied coordinates.

**Not a medical device.** No regulatory clearance, no claim of diagnostic
accuracy. Research and decision-support framing only, stated in the interface.

---

## 7. Build order

| Order | Piece | Estimate | Notes |
| :-: | :-- | :-- | :-- |
| 0 | **Test TotalSpineSeg on RSNA** | 2 h | Do this before anything else. It decides whether stage 2 exists. |
| 1 | Derive level to 25-target offsets from RSNA | 1 d | Validate against known coordinates. May fail. |
| 2 | SQLite schema + ingest with de-identification gate | 2 d | Most code exists |
| 3 | Job queue + grading worker | 1 d | Thin wrapper over existing inference |
| 4 | Rendering stage | 0.5 d | `roi_qc.py` nearly does it |
| 5 | API | 1 d | |
| 6 | Frontend | 3-4 d | Localisation review screen is the important one |
| 7 | Hardening on real PACS exports | open-ended | See below |

Roughly two working weeks to something demonstrable, assuming step 0 succeeds.

### What does not compress

- **De-identification verification.** Wiring the library is thirty minutes;
  confirming nothing leaks means sampling pixels, auditing private tags across
  vendors, handling the SR objects. The failure mode is a disclosure.
- **Whether TotalSpineSeg works here.** Empirical, not codeable. Its published
  99% is its own benchmark figure.
- **The level-to-target mapping.** Untested. Foraminal and subarticular offsets
  may vary too much between patients to derive from disc centres.
- **Real PACS exports.** RSNA is curated; hospital exports are not. Multi-frame
  objects, missing tags, odd orientations, compressed transfer syntaxes,
  half-copied series. Each a twenty-minute fix, found one at a time over weeks.
- **Radiologist feedback cycles.** Run at their availability, not the build's.
- **Ethics approval, hospital IT review, hardware inside the network.** Not
  doable at any speed by the development side.

---

## 8. Open risks

**TotalSpineSeg may not transfer.** Its accuracy on Kurdish clinical protocols is
unknown. If it degrades, stage 2 needs either a trained detector -- which is the
separate paper -- or the human-clicks path becomes mandatory rather than a
review step.

**Five clicks may not yield 25 targets.** Disc centre maps closely to central
canal, but foraminal and subarticular need lateral offsets that disc segmentation
does not provide. RSNA can supply and validate that mapping because it has both.

**Grading quality is bounded by the reference standard.** Inter-reader agreement
on these grades is moderate for the lateral compartments. A radiologist who
expects the system to be *right* rather than *consistent with a reader* will be
disappointed, and the interface should set that expectation.

**The feedback loop needs reviewer time, not code.** Disagreements between model
versions are a trivial query. Adjudicating them is not, and there are already 16
conflict cases outstanding from Track B.

---

## 9. Relationship to the thesis

Independent. Nothing here is claimed in the submission, and no result in
Chapters 4 or 5 depends on it. Two connections are worth keeping in view:

- The **coordinate CSV interface** is the same thing RQ4 needs. If stage 2 works
  and produces coordinates for the Rizgary cohort, the transfer experiment
  becomes runnable -- which would move RQ4 from "not executed" to a result. That
  is the single highest-value outcome of this work for the research programme,
  and it is a side effect rather than the goal.
- The **rendering stage** is already thesis code, and improvements flow both ways.
