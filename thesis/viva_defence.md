# Viva defence narrative

Prepared 2026-08-27 for Selar's defence. Built on an external proposal, with its
one dangerous claim corrected, its overreach trimmed, and the two strongest
assets it omitted added: the power analysis and the attribution mechanism.

Every citation below has been checked against the actual chapter text. Numbers
are from the three-seed campaign; a seven-seed campaign is running and the
figures marked [3-SEED] should be refreshed before the defence.

---

## 0. Posture

**Lead with findings, not with shields.**

The external proposal was four consecutive defensive manoeuvres. That is the
wrong shape for a viva: a candidate who opens by explaining why failure is
acceptable has conceded that failure is the frame. The findings *are* the
result. Present them as such and the defences become unnecessary in most of the
room.

The single most useful reframe is this. The thesis did not fail to show that its
mechanisms work. **It succeeded in determining that most of them do not, and
established why.** That is what Chapter 1 said it would do, in advance, at
line 523:

> The aim is intentionally phrased as a determination rather than a promise of
> superiority.

---

## 1. The opening ninety seconds

Something close to:

> This thesis asked whether explicit anatomical structure improves automated
> lumbar stenosis grading. The complete system improves on a single-sequence
> baseline by 0.0172 quadratic weighted kappa, reproducibly across seeds and
> surviving correction for multiple comparisons.
>
> But when each mechanism was tested against a control matched in capacity, most
> of the anatomical structure turned out not to be what produced the gain.
> Anatomically correct graph topology performs no better than a degree-preserving
> random shuffle. Disease-conditioned routing learns the clinically correct
> sequence weights, yet a router-free model shows identical behaviour under
> intervention.
>
> Attribution analysis explains why: the convolutional encoder already
> concentrates 2.4 times the chance share of its attention on the annotated
> lesion before any structural prior is added. The localisation these priors were
> designed to supply is largely accomplished without them.
>
> The contribution of this thesis is therefore the controlled determination
> itself, and the finding that anatomical priors buy less than the field assumes
> at this data scale.

Do not apologise anywhere in this passage. It is a result.

---

## 2. The four claims

### Claim 1 — The system works

+0.0172 QWK, 95% CI [+0.0064, +0.0285], every seed, the only pre-specified
comparison surviving FDR correction. Not in dispute; state it once and move on.

### Claim 2 — The negative results were planned for, not rationalised

The methodology pre-committed to this outcome in three separate places, all
verified:

- Chapter 3 has a dedicated `\subsection{Negative Results}` (ch3:2368).
- Chapter 3's *Mapping Research Questions to Evidence* table (ch3:3094) already
  supplies the interpretation for exactly these outcomes: for RQ2, **"anatomy-
  defined positives do not improve transferable representation"**; for RQ3,
  **"fixed fusion is sufficient or learned routing is unstable"** (ch3:3107-3108).
- Chapter 1 forbids rewriting hypotheses after results: *"The hypotheses will not
  be rewritten after inspection of the held-out public or Rizgary test results."*

The strongest form of this point is not "we were allowed to fail." It is: **the
conclusions we reached are the ones the protocol wrote down in advance as the
interpretation of these results.** Nothing was reinterpreted.

If asked when the shuffled-edge control was specified: it is in Chapter 3 as the
decisive comparison for H3, and the git history dates every specification. Invite
the check rather than deflecting it.

### Claim 3 — The study could detect real effects, so its nulls mean something

This is the claim the external proposal gestured at and could not support. The
quantitative version:

| Effect | Δ QWK | sd(seeds) | Seeds for 80% power |
| :-- | --: | --: | --: |
| Full system vs baseline | +0.0172 | 0.0029 | **1** |
| Ordinal head (RQ5) | +0.0099 | 0.0017 | **1** |
| Typed edges (RQ1) | +0.0123 | 0.0129 | 10 |
| Anatomical topology (RQ1) | +0.0051 | 0.0094 | 29 |
| Cross-sequence SSL (RQ2) | +0.0051 | 0.0258 | 216 |
| Disease routing (RQ3) | +0.0010 | 0.0208 | **3,467** |

Two effects are detectable with a single seed. The instrument is not blind.
Where it reports nothing, that is a statement about the effect.

For routing specifically: 3,467 training runs at 22 minutes each is roughly three
years of continuous computation. The effect is not merely unproven — it is
unprovable at any plausible scale, and +0.0010 on a 0.7276 baseline would carry
no clinical meaning even if established.

Chapter 3 mandated repeated seeds for exactly this reason (ch3:2807, 2813):
*"a one-off training run is insufficient to attribute a small improvement to a
method."*

### Claim 4 — There is a mechanism, not just a p-value

The attribution result is the scientific centrepiece and the external proposal
omitted it entirely.

| Configuration | CAM mass in disc | vs untrained |
| :-- | --: | --: |
| E0 single sequence | 0.490 | +0.286 |
| E1 multi-sequence | 0.578 | +0.374 |
| E4 + ACSSL | 0.462 | +0.258 |
| Untrained, same architecture | 0.204 | — |
| Uniform map (disc = 19.7% of frame) | 0.197 | — |

**E0 — a plain single-sequence CNN with no routing, no SSL and no graph — already
reaches 0.490.** The priors were motivated by the premise that anatomical context
is needed to find the lesion. The encoder finds it unaided.

This converts "our mechanisms did not help" into "our mechanisms had little left
to contribute, and here is the measurement." The first is a disappointment; the
second is a finding that generalises past this architecture.

---

## 3. The correction: what NOT to claim about Contribution III

The external proposal advised:

> "Winning this specific ablation validates the hypothesis that anatomical
> topology (the specific relations between targets) carries useful information."

**Do not say this. It is the opposite of what the evidence shows, and it is the
single most damaging sentence available in this defence.**

- Typed edges beat a **homogeneous** graph: +0.0123 QWK, 3/3 seeds. Supported.
- Anatomically correct edges do **not** beat a **degree-preserving shuffle**:
  +0.0051, 2/3 seeds, p(FDR) 0.570. Refuted.

H3 predicted that *"performance under a shuffled-edge control should deteriorate
if the topology itself matters."* It did not deteriorate. Claiming anatomical
topology is validated contradicts the decisive comparison in the methodology, and
any examiner who has read Chapter 3 will know it.

**Correct wording:**

> Relational typing carries information; anatomical adjacency does not. What the
> graph supplies is a structured parameterisation of interaction between targets,
> not the specific adjacency of levels, compartments and bilateral pairs that
> motivated it.

This is a sharper and more publishable claim than the one originally proposed. It
tells the field something it does not know.

---

## 4. Hardest questions

**"If your three contributions failed, what is the contribution?"**
Three things. A verified system that beats its baseline reproducibly. A
controlled ablation protocol in which every mechanism is tested against a
capacity-matched control — which is why these results are trustworthy and why
three analyses that initially produced positive conclusions were caught and
corrected. And the finding that anatomical priors do not pay at this scale, with
a measured mechanism for why.

**"Isn't +0.0172 QWK clinically negligible?"**
As an aggregate, it is small. The clinically material quantity is recall on
Severe targets, which rises from 62.7% to 65.0%, and that improvement comes from
the cost-sensitive objective specifically. No claim of patient benefit is made:
the study measures agreement with a reference standard on a retrospective
benchmark and does not measure any clinical outcome. That limit is stated in
Chapter 4 rather than left to be discovered.

**"Your best-performing component is a standard ordinal head. Where is the
novelty?"**
It is RQ5, a research question fixed prospectively, not an incidental choice.
Chapter 2 documents that this was an open question: Niemeyer et al. found
explicitly ordinal objectives did not reliably improve on cross-entropy
(ch2:607, 708, 1266). Finding that a cost-sensitive ordinal objective *does*
improve both aggregate agreement and Severe recall closes a documented gap. It is
a smaller claim than the architectural ones, and it is the one that replicated.

**"Only three seeds?"**
Seven at the time of the defence. And Table 4.3 in Chapter 4 states exactly what
seven seeds can and cannot resolve: they will settle typed edges, and they cannot
settle RQ2 or RQ3, which need 216 and 3,467 respectively. The seed count is
reported as a limitation with its consequences quantified rather than as a
caveat.

**"You have no external validation."**
Correct, and it is stated plainly. E8 — the complete system under institutional
transfer, and the operational form of RQ4 — was specified in Chapter 3 and was
not executed. Cohort preparation is complete: the Rizgary data are surveyed,
reports parsed, records reconciled. Two blockers remain: sixteen cases with
conflicts between report-derived and reference labels awaiting reader
adjudication, and a de-identification routine that keys on a PatientID field that
is not unique in this cohort (45 distinct values across 346 cases), so applying
it would merge roughly eight patients per pseudonym. Neither is concealed and
neither is technical in the sense of needing new method.

**"Grad-CAM is unreliable. Why should we believe the mechanism?"**
Because the comparison is against floors, not in absolute terms. The identical
architecture with untrained weights scores 0.204 and a uniform map scores 0.197;
trained models reach 0.46-0.58. The attribution depth was fixed on resolution
grounds before results were compared — the final residual block is 4x4 at these
crop sizes, one cell spanning 15 mm, too coarse to resolve the disc — and all
three depths are reported so the dependence is visible. Grad-CAM's known failure
modes affect absolute values; they do not explain a gap of that size against a
matched floor.

**"Multi-sequence input improved attention but hurt accuracy. Explain."**
That dissociation is a finding, and the study is designed to separate the two
quantities. Additional sequences sharpen where the model looks (+0.089
concentration, 3/3 seeds) without improving what it concludes (-0.0055 QWK).
Attention concentration and grading accuracy are not the same thing, and this is
direct evidence that improving the former does not guarantee the latter.

**"Did you consider that your architecture is simply not good enough?"**
Yes, and it is testable rather than rhetorical. If the architecture were the
limit, the ladder would show no reliable effects anywhere. It shows two that
replicate on every seed and are detectable with a single seed. The instrument
resolves effects of this size; the mechanisms under test do not produce them.

---

## 5. Never say

- **"Viva-hardened."** It is a comment in the LaTeX source. Saying it aloud
  announces that failure was anticipated and is being managed.
- **"Lesser methodologies would have cherry-picked a lucky seed."** Arrogant, and
  it invites "so is your own effect clinically meaningful?" — the question with
  the weakest answer. State the seed protocol as a design choice, not as a
  comparison with unnamed inferior work.
- **"Anatomical topology carries useful information."** See section 3.
- **"The negative results are as valuable as positive ones."** True in principle,
  hollow as an assertion. Show the power table and the mechanism instead; they
  make the point without claiming it.
- Any suggestion that a hypothesis was refined after seeing results. It was not,
  Chapter 1 forbids it, and the git history is checkable.

---

## 6. Where each claim is evidenced

| Claim | Evidence |
| :-- | :-- |
| System beats baseline | `data/reports/chapter4_comparisons.csv`, E7 vs E0 |
| Negative results pre-planned | ch3:2368, ch3:3094-3108, ch1 hypotheses section |
| Power / detectability | `thesis/chapter4/ladder_results_full.md`, Table 4.4 |
| Routing fails under intervention | `thesis/chapter4/input_ablation.md` |
| Encoder already localises | `thesis/chapter4/attribution.md` |
| Typed edges work, anatomy does not | E6 vs E5 and E6 vs E6_shuffled, same CSV |
| Ordinal head closes a documented gap | ch2:607, 708, 1266; RQ5 in Chapter 4 |
| Three corrected analyses | Chapter 4, Threats to Validity |

---

## 7. One thing to be ready for

The most likely hostile line is not about any single result. It is:

> "You have written a thesis explaining why your own ideas did not work."

The answer is that this is what the protocol was built to determine, and that the
alternative — reporting three small positive effects from single seeds without
capacity-matched controls — was available and was rejected. Three analyses in
this thesis initially produced positive conclusions and were overturned by their
controls: a per-seed bootstrap that gave opposite significant signs on different
seeds, a routing result that a router-free model reproduced, and an attribution
probe that measured the wrong encoder. Each would have become a claim.

A thesis that catches its own false positives is worth more than one that
publishes them.
