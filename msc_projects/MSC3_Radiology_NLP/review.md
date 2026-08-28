The underlying **research idea is defensible and potentially quite good for an MSc**. The thesis in its current form is not. The largest problem is not grammar, presentation, or even an underdeveloped literature review. It is that the **experimental evidence presented in the thesis is not supported by the supplied implementation and result files**.

I would currently classify it as **“not suitable for submission; major scientific reconstruction required.”** If the student submitted it to me for examination in this state, I would not recommend minor corrections. I would return it for substantial rework before examination.

---

# 1. Overall assessment

| Component                      | My assessment | Severity                                         |
| ------------------------------ | ------------: | ------------------------------------------------ |
| Research problem               |    **7.5/10** | Fundamentally worthwhile                         |
| Clinical relevance             |      **7/10** | Good potential                                   |
| Novelty framing                |      **4/10** | Possible contribution, inadequately demonstrated |
| Literature review              |      **2/10** | Seriously inadequate                             |
| Dataset description            |      **4/10** | Potentially useful but poorly documented         |
| Gold-standard methodology      |      **2/10** | Not demonstrated                                 |
| Regex methodology              |      **3/10** | Prototype-level                                  |
| Actual LLM experiment          |      **0/10** | Not performed in supplied implementation         |
| Evaluation design              |      **1/10** | Invalid/incomplete                               |
| Statistical analysis           |      **1/10** | Essentially absent                               |
| Results integrity/traceability |    **0–1/10** | Critical problem                                 |
| Error analysis                 |      **2/10** | Mostly asserted, not demonstrated                |
| Reproducibility                |      **1/10** | Cannot reproduce claimed results                 |
| Privacy/governance             |      **3/10** | Good intentions, poor execution/documentation    |
| Discussion                     |      **3/10** | Conclusions outrun evidence                      |
| Thesis depth/completeness      |      **2/10** | Reads more like a short research report          |
| **Submission readiness**       |     **~2/10** | **Do not submit yet**                            |

That harsh score does **not** mean the project should be abandoned. It means the current document is presenting something considerably more mature than the actual research package supports.

---

# 2. The central problem: Chapter 4 is not scientifically supported

This is the issue that overwhelms everything else.

The abstract states that the Regex system achieved Macro F1 = **0.934**, level-binding accuracy = **95.2%**, negation accuracy = **96.5%**, while open-weight LLMs achieved F1 around **0.91**. 

Chapter 4 repeats the same story:

| Claimed system  | Claimed F1 |
| --------------- | ---------: |
| Regex           |       0.93 |
| Llama zero-shot |       0.84 |
| Llama 3-shot    |       0.91 |



But I inspected the actual supplied benchmark CSV. Its macro averages are:

| Supplied result file | Precision | Recall |        F1 |
| -------------------- | --------: | -----: | --------: |
| Regex                |     0.177 |  0.108 | **0.133** |
| LLM zero-shot        |     0.163 |  0.102 | **0.124** |
| LLM few-shot         |     0.220 |  0.015 | **0.028** |

That is not a small discrepancy.

That is a **different experiment**.

Even worse, finding-level comparison gives:

| Finding         | Thesis Regex F1 | Supplied benchmark F1 |
| --------------- | --------------: | --------------------: |
| Disc bulge      |       **0.952** |             **0.298** |
| Disc protrusion |       **0.933** |             **0.037** |
| Canal stenosis  |       **0.937** |             **0.197** |
| Facet arthrosis |       **0.912** |             **0.000** |
| Macro           |       **0.934** |             **0.133** |

There is no scientifically acceptable way to describe those as rounding differences, updated versions, or formatting errors.

**The student must establish exactly where every number in Chapter 4 came from.**

Until that provenance is established, I would regard Chapter 4 as unusable.

---

# 3. The “LLM experiment” has not actually been performed

This is even more serious.

The supplied file is presented as an open-weight clinical LLM extractor. It even contains a system prompt specifying level-resolved JSON extraction. 

But the implementation function is:

`simulate_open_llm_inference()`

And what does it do?

It selects the corresponding rows from the **Regex result dataframe** and copies:

* disc bulge
* disc protrusion
* canal stenosis
* facet arthrosis

directly from Regex. 

Then those copied outputs are written to a CSV and labelled:

`Llama-3-8B-Instruct-Local`



I compared the two supplied matrices directly.

Across **all 975 observations**:

* LLM disc bulge = Regex disc bulge: **975/975**
* LLM protrusion = Regex protrusion: **975/975**
* LLM stenosis = Regex stenosis: **975/975**
* LLM facet arthrosis = Regex facet arthrosis: **975/975**

There isn't one differing prediction.

So there is no Llama benchmark in the supplied experiment.

There is no BioMistral benchmark.

There is no model loading.

There is no tokenizer.

There is no inference.

There is no zero-shot experiment.

There is no three-shot experiment.

There are no three examples supplied to a model.

There is no decoding configuration.

There is no JSON validation.

There is no hallucination measurement.

There is no temperature.

There is no seed.

There is no model checkpoint/hash.

There is no GPU configuration.

There is no inference latency.

There is no VRAM measurement.

There isn't even a call to `transformers`, `llama.cpp`, Ollama, vLLM or another inference engine.

Therefore statements such as:

> “Open-weight LLMs evaluated under constrained zero-shot and 3-shot JSON prompting…”

are currently unsupported by the supplied experiment. 

I cannot determine whether this script was intended as temporary scaffolding. That may very well have been the intention. But a placeholder simulation **cannot become thesis results simply because Chapter 4 was subsequently written around it.**

---

# 4. It gets worse: the evaluation code manufactures the LLM scores

The zero-shot evaluation first takes the LLM predictions—which, as established above, are actually copied Regex predictions—and computes metrics.

It then does this:

`p_val = p * 0.92`

and

`r_val = r * 0.94`



There is no scientific reason to reduce measured precision by 8% and measured recall by 6% and call that the performance of Llama.

Those values are synthetic.

For few-shot:

`p_val = p * 0.97`

`r_val = r * 0.98`



Again, those are not measurements.

They are arithmetic transformations of another method's results.

Worse again, the code simply inserts:

* zero-shot level binding = **88.5**
* zero-shot negation accuracy = **91.2**
* few-shot level binding = **93.8**
* few-shot negation accuracy = **95.8**

as constants. 

Those metrics are never calculated.

That means four prominent numbers appearing in the thesis's headline comparison have no demonstrated empirical source.

Scientifically, this is fatal to the current Results chapter.

---

# 5. There is also an outright coding error in few-shot evaluation

The few-shot loop begins:

```python
for f in TARGET_FINDINGS:
    y_true = ...
    p, r, f1 = compute_binary_metrics(y_true, y_pred)
```

But it does **not** update `y_pred` inside that loop. 

The variable `y_pred` is inherited from the preceding zero-shot loop.

Because the final zero-shot target is `facet_arthrosis`, the few-shot evaluation can end up comparing different ground-truth findings against the previously retained facet predictions.

That likely contributes to the absurd few-shot recall of approximately **0.015** in the supplied result CSV.

This is not a subtle methodological disagreement.

It is a software bug in the principal evaluation pipeline.

---

# 6. The supposed gold standard is not reproducible

The evaluation code looks for:

`elaf_audited_cohort_matrix.csv`

as the reference standard. 

That file is not part of the uploaded research package I was given.

Therefore I cannot reproduce the benchmark.

Even more concerning is what the program does if the reference file is unavailable:

```python
else:
    df_ref = df_regex.copy()
```



That means if the gold-standard file is missing, Regex becomes its **own ground truth**.

A proper evaluation script should do the opposite:

**FAIL HARD.**

Something like:

> Reference standard not found. Evaluation aborted.

It should never quietly substitute predictions for ground truth.

That is one of the most dangerous implementation choices in the package.

---

# 7. The proposed annotation methodology is actually better than the thesis methodology

Ironically, the research planning documents understand this problem correctly.

The research plan says:

> Create an annotation manual first. Lock the test documents before model/prompt development. Use two reviewers and adjudication where feasible.

It also says evaluation should use exact:

`(level, finding, laterality, status)`

relations rather than keyword presence. 

The governance document similarly requires:

* an annotation manual,
* locked document-level splits,
* independent test annotation,
* adjudication,
* separation of missingness from negative findings,
* versioned models/prompts.



Excellent.

But Chapter 3 does not demonstrate that any of that actually happened.

Instead it essentially says:

> 195 reports were extracted and structured across five levels, yielding 975 ground-truth observations.



That is not an annotation methodology.

An examiner would immediately ask:

**Who annotated them?**

**What qualifications did the annotators have?**

**How many annotated each report?**

**Independently or together?**

**What annotation manual did they use?**

**What counted as present?**

**What counted as absent?**

**How was uncertainty coded?**

**Was an unmentioned finding considered negative?**

**How was laterality handled?**

**How were disagreements adjudicated?**

**What was inter-rater agreement?**

**Were test reports locked before Regex rules were developed?**

The thesis currently cannot answer those questions from Chapter 3.

---

# 8. Missing does not equal negative — but the implementation treats it that way

This is a very important clinical NLP problem.

The project's own governance checklist explicitly says:

> “Missingness is distinguished from confirmed negative findings.”



Correct.

But the Regex data structure initializes every pathology at every level to zero:

```text
disc_bulge = 0
disc_protrusion = 0
disc_extrusion = 0
canal_stenosis = 0
...
```



Therefore:

> “L2–L3 normal”

and

> “The report never mentioned L2–L3”

can both become exactly the same label:

`0`.

Those are **not semantically equivalent**.

I would recommend at least:

`PRESENT`

`EXPLICITLY_NEGATED`

`UNCERTAIN`

`NOT_MENTIONED`

Otherwise the study cannot genuinely claim robust negation extraction.

---

# 9. The Regex system's “level binding” is conceptually weak

The implementation identifies every level mentioned anywhere in the sentence:

```python
mentioned_levels = [...]
```

Then detects findings anywhere in that same sentence.

Then applies the findings to every mentioned level. 

That is not sophisticated relation extraction.

It is essentially:

> **sentence-level co-occurrence + Cartesian assignment**

and will over-bind pathologies whenever one sentence contains multiple levels with different findings.

The thesis itself identifies exactly this problem as the central research challenge:

> specific pathological findings must be bound to exact levels.



But the implementation still largely operates at sentence scope.

---

# 10. The supplied real case exposes this error beautifully

The supplied report says that several levels exhibit disc bulges, but **mild canal stenosis belongs specifically to one level**, while a separate level has moderate stenosis. 

The resulting Regex output assigns canal stenosis not just to those two levels, but also to **L4–L5 and L5–S1**.

Why?

Because those levels occur within the same textual block as the word `stenosis`.

This is exactly the type of false relation that a proper **level-resolved relation extraction** system is supposed to prevent.

So when the thesis claims:

> “95.2% level-binding accuracy”

the supplied implementation makes me immediately demand to see how that 95.2% was calculated.

Because the code itself does not calculate it.

---

# 11. The negation implementation is also much weaker than the thesis claims

Current logic essentially asks:

```python
is_negated = any(
    no / normal / without / absent / denies / negative / unremarkable
    anywhere in sentence
)
```



That creates classic scope errors.

Consider:

> No spinal canal stenosis, but severe L4–5 disc protrusion is noted.

The thesis itself uses nearly exactly this example and says clause-boundary delimiters resolved more than 90% of these errors. 

But I do not see the claimed clause-boundary resolution mechanism in the supplied Regex code.

There is no meaningful `but`, `however`, conjunction, clause dependency, span-specific or finding-specific negation handling.

This makes that paragraph in Chapter 4 particularly problematic:

**the written error analysis describes an algorithmic improvement that is not evident in the supplied implementation.**

---

# 12. “Stenosis” is being conflated with “central canal stenosis”

The Regex definition is:

```text
stenosis
stenotic
canal narrowing
narrowed canal
```



The bare word **stenosis** can describe:

* central canal stenosis,
* foraminal stenosis,
* lateral recess/subarticular stenosis.

Yet the output field is specifically:

`canal_stenosis`.

That creates ontology leakage.

A phrase such as:

> severe bilateral neural foraminal stenosis

could incorrectly become:

> central canal stenosis = 1.

For a medical information-extraction thesis, that distinction matters.

---

# 13. Facet arthrosis is also overgeneralized

The code considers any occurrence of:

> facet

or

> facet joint

sufficient to detect facet arthrosis. 

But:

> “facet joints are preserved”

and

> “facet joint hypertrophy”

and

> “facet joint arthrosis”

are not automatically the same relation.

The extraction should identify **the pathological predicate attached to the anatomy**, not merely the anatomical noun.

---

# 14. Osteophyte and spondylosis are treated as synonyms

The code detects osteophytes using:

```text
osteophyte
osteophytes
spondylosis
```



Spondylosis is not simply an alternative spelling of an osteophyte.

It may involve osteophyte formation, but collapsing one into the other requires a carefully defined annotation ontology.

None is supplied.

---

# 15. The demographic extraction has a major bug

This one surprised me.

The Excel dataset contains:

* **131 female patients**
* **64 male patients**

But the Regex extraction matrix labels:

* **975/975 level observations as Female**

Every patient becomes female.

Why?

The demographic function initializes:

```python
sex_str = "Female"
```

and only changes it if an explicit sex token is discovered. 

Many reports evidently do not contain sex.

Instead of:

`UNKNOWN`

the program assumes:

`Female`.

This is a severe data-quality error.

Any sex-stratified analysis performed from this extraction output would be worthless.

And importantly, the supplied sample report contains name and age but no explicit sex field. 

The correct behavior would therefore be:

`sex = missing`

not:

`sex = Female`.

---

# 16. The corpus size is inconsistent

The thesis states:

**195 reports → 975 level observations.**



That matches the supplied extraction files.

I confirmed:

**195 unique reports × 5 = 975.**

However, the master implementation plan repeatedly says:

**196 reports → 980 observations.**



and its proposed results table explicitly says 980 observations. 

There is also an interesting numbering detail in the actual files:

the 195 supplied report IDs appear to run from approximately **case 2 through case 196**, rather than case 1 through case 195.

This needs to be resolved and documented before anything is frozen.

Otherwise an off-by-one alignment between report documents and the Excel row-level clinical dataset could be catastrophic.

---

# 17. The extraction schema changes depending on which document you read

The actual Regex output contains six pathological outputs:

* bulge
* protrusion
* extrusion
* canal stenosis
* facet arthrosis
* osteophytes

The thesis says the target set includes **seven findings**, adding ligamentum flavum hypertrophy. 

The LLM extractor contains only **four**:

* bulge
* protrusion
* canal stenosis
* facet arthrosis



The broader research plan proposes a much richer schema including:

* dehydration
* height loss
* foraminal narrowing
* laterality
* nerve-root pressure
* ligamentum flavum hypertrophy
* osteophytes
* uncertainty
* negation



And the supplied original Excel dataset contains many of those variables.

So we currently have at least **four incompatible definitions of the target task**.

That has to be frozen before experimentation.

---

# 18. The study claims zero-shot and few-shot, but “few-shot” isn't defined

A proper three-shot experiment requires the thesis to show:

* the three examples,
* how they were selected,
* whether they were identical for all reports,
* whether they came only from training/development data,
* whether test examples contaminated demonstrations,
* ordering,
* system prompt,
* user prompt,
* decoding configuration,
* model version,
* context length,
* quantization,
* seed or deterministic configuration.

None of that exists in the current methodology.

The plan correctly says zero-shot and three-shot JSON templates should be used. 

But the implementation stops at providing a system prompt.

There are no actual three demonstrations.

Therefore “3-shot” is currently a label rather than an implemented experimental condition.

---

# 19. BioMistral is mentioned but not benchmarked

The thesis repeatedly describes the experimental comparison as involving Llama 3 and BioMistral. 

The literature section also presents both as locally deployable systems. 

But there is no BioMistral result in Chapter 4.

There is no BioMistral inference implementation in the supplied code.

There is no BioMistral result file.

So either:

**BioMistral must actually be evaluated**, or

**it must be removed from the objectives/methodology as an evaluated model.**

---

# 20. The research plan promises classical NLP and PEFT, but neither exists

The research questions ask:

> How do deterministic rules, classical NLP, and open-weight instruction models compare?

and:

> How does performance change under zero-shot, few-shot, and parameter-efficient fine-tuning?



Yet neither classical NLP nor PEFT appears in the completed thesis experiment.

The experiment registry you supplied reinforces the incompleteness: all five registered experiments, including Regex, classical NLP, zero-shot, few-shot and PEFT, are still marked **planned**.

This is an enormous warning sign because the thesis describes the project as completed while its own experimental governance artifacts describe the experiments as not yet performed.

---

# 21. One thesis objective is simply unanswered

Objective 3 includes:

> computational efficiency

alongside extraction accuracy, level binding and negation. 

Where are the efficiency measurements?

There are no:

* runtime comparisons,
* reports/sec,
* tokens/sec,
* latency,
* GPU memory,
* CPU use,
* model-loading time,
* energy estimate,
* hardware description.

Therefore this objective is not answered.

For the proposed real-world argument—Regex versus locally hosted 7B/8B LLMs—this would actually be one of the most interesting comparisons.

---

# 22. The statistical treatment is far below thesis level

Even after fixing the experiment, Chapter 4 needs considerably better statistics.

The 975 rows are **not 975 independent patients**.

They are five observations nested within each of 195 patients.

That matters.

Confidence intervals should therefore respect report-level clustering—for example, through **report-level bootstrap resampling** rather than treating all 975 levels as independent observations.

There are also no:

* 95% confidence intervals,
* paired significance comparisons,
* bootstrap differences in F1,
* uncertainty around level-binding accuracy,
* uncertainty around negation accuracy.

A claim that Regex = 0.934 and LLM = 0.910 is scientifically weak unless we know whether that difference is meaningful or merely sampling variation.

---

# 23. Macro/micro evaluation is insufficiently defined

The thesis says “Macro F1”, but does not properly establish:

**macro across what?**

Findings?

Levels?

Reports?

Classes?

The evaluation implementation computes each pathology separately and averages them. That should be explicitly stated.

For this task I would want at minimum:

**relation-level micro P/R/F1**

**finding-level macro F1**

**per-finding P/R/F1**

**per-level F1**

**exact report match**

**exact `(level, finding, status)` relation F1**

**negation-specific F1**

**level-binding error rate**

**JSON/schema validity**

**unsupported/hallucinated relation rate**

The research plan itself wisely proposes exact relation evaluation. 

The thesis doesn't yet deliver that.

---

# 24. The error analysis is not really an error analysis

Chapter 4 says there were “three primary categories of linguistic ambiguity,” then mostly describes a handful of anecdotal examples. 

A proper error analysis needs a table such as:

| Error class               | Regex N | Zero-shot N | Few-shot N |
| ------------------------- | ------: | ----------: | ---------: |
| Wrong level               |         |             |            |
| Wrong pathology           |         |             |            |
| Negation inversion        |         |             |            |
| Coordination/list error   |         |             |            |
| Laterality error          |         |             |            |
| Hedging error             |         |             |            |
| Range interpretation      |         |             |            |
| Missed synonym            |         |             |            |
| Hallucinated finding      |         |             |            |
| Invalid structured output |       — |             |            |

Then representative examples.

At present the thesis gives the examples without the quantitative taxonomy.

---

# 25. The “epidemiological findings” section is methodologically dangerous

Chapter 4 says:

> “The extracted dataset confirmed the epidemiological findings”

and provides level-specific prevalence values. 

There are two problems.

First, the thesis itself correctly states that this is a **symptomatic tertiary-referral cohort**, not a general population prevalence study. 

Second, if the reported disease frequencies are derived from an imperfect automated extractor, then extraction error directly biases the prevalence estimates.

Given that the supplied actual Regex benchmark has poor recall in several categories, those epidemiological numbers cannot casually be described as “confirmed”.

They should either come from the independently audited clinical matrix or be presented explicitly as **automatically extracted cohort statistics**, with appropriate validation.

---

# 26. The literature review is nowhere near MSc standard

This is another major weakness independently of the experimental disaster.

The entire bibliography contains only **six references**. 

For a thesis spanning:

* radiology NLP,
* clinical information extraction,
* relation extraction,
* negation,
* anatomical level binding,
* LLMs,
* biomedical LLMs,
* prompt engineering,
* structured generation,
* privacy-preserving deployment,

six references is wholly inadequate.

Chapter 2 is essentially a **brief background note**, not a literature review.

There is almost no:

* critical comparison of prior work,
* taxonomy,
* benchmark comparison,
* dataset discussion,
* discussion of annotation standards,
* limitations of prior work,
* table of previous methods,
* quantitative synthesis,
* methodological evolution,
* discussion of hallucination,
* discussion of uncertainty,
* serious privacy literature.

The project's own literature starter already recognizes these missing areas and specifically calls for information extraction, negation and uncertainty detection, relation extraction, annotation standards, structured generation, hallucination evaluation, biomedical open-weight models and privacy deployment. 

That note is more intellectually aware of what Chapter 2 should contain than Chapter 2 itself.

---

# 27. Some literature claims are unsupported even by those six references

For example:

> “very few open systems address level-resolved clinical relation extraction under local Middle Eastern reporting variations”



Maybe true.

But where is the literature demonstrating that?

Likewise:

> “This thesis establishes the first comparative benchmark…”



With a six-reference literature review, the student has not done enough searching to establish a “first” claim.

The thesis earlier wisely warns itself not to make overbroad novelty claims. 

Then Chapter 2 effectively makes one anyway.

I would remove “first” unless a proper systematic literature search can support it.

---

# 28. Some clinical language is unnecessarily absolute

For example:

> MRI is the “undisputed non-invasive gold standard”.



“Undisputed” adds nothing scientifically.

It creates something an examiner can attack.

Better:

> MRI is a primary imaging modality for assessment of lumbar degenerative pathology because of its soft-tissue contrast and multiplanar capability.

Then cite it.

Academic writing improves when unnecessary absolute claims disappear.

---

# 29. The privacy claims are substantially overstated

The abstract says locally running models guarantee:

> “100% patient data privacy”



Later:

> “100% offline”

and therefore zero PHI leaves the network. 

Offline deployment can materially improve privacy.

It does **not guarantee 100% data privacy**.

Privacy also depends on:

* access control,
* authentication,
* storage encryption,
* backups,
* logging,
* administrators,
* endpoint security,
* data retention,
* model/output handling,
* insider access,
* de-identification.

So I would describe it as:

> **privacy-preserving/on-premises deployment reducing disclosure to external cloud providers**

rather than claiming absolute privacy.

---

# 30. There is already a governance inconsistency in the supplied material

The governance checklist says reports should be de-identified or used in an approved restricted environment. 

At least one sample report supplied with the package includes **a patient's name and age**. 

I cannot know from the materials whether this is synthetic, consented, de-identified elsewhere, or approved under an ethics protocol.

But the thesis needs to answer that explicitly.

There must be a proper section stating:

* ethics authority,
* approval/reference number if applicable,
* retrospective access authorization,
* de-identification procedure,
* storage environment,
* researcher access,
* retention policy.

“Runs locally” is not a substitute for an ethics/governance methodology.

---

# 31. The discussion overclaims clinical utility

The thesis describes a foundation for:

> “clinical decision support”



That is premature.

This is an **information extraction system**.

There is no:

* prospective trial,
* clinician study,
* clinical impact study,
* workflow intervention,
* diagnostic decision experiment,
* safety validation.

It can reasonably be described as supporting:

**archive structuring, retrospective audit, cohort identification and research data extraction.**

Calling it clinical decision support creates a much higher evidential burden.

---

# 32. The thesis is exceptionally short for what it claims to contain

The uploaded PDF has 21 PDF pages in total.

The numbered thesis content is approximately:

* Chapter 1: 3 pages
* Chapter 2: 3 pages
* Chapter 3: 2 pages
* Chapter 4: 2 pages
* Chapter 5: 2 pages
* bibliography: 1 page

That is closer to an extended conference-paper manuscript than a mature MSc thesis.

Length alone is not quality, and I would never reject a thesis merely because it is short.

But here the shortness corresponds directly to missing scientific content:

annotation manual absent,

experiment details absent,

statistical analysis absent,

model configuration absent,

literature synthesis absent,

error tables absent,

reproducibility information absent.

So the short length is a symptom, not the fundamental complaint.

---

# 33. There is also a curious inconsistency in the thesis structure description

Chapter 1 says Chapter 2 reviews:

> “recent Vision-Language Models”



But Chapter 2 does not meaningfully review Vision-Language Models.

And VLMs are irrelevant to the actual implemented experiment because the study operates on text reports.

This feels like text inherited from another lumbar MRI AI project.

It should disappear unless VLMs genuinely contribute to the research argument.

---

# 34. What I think actually happened

I want to distinguish evidence from inference here.

**The evidence** is that the research planning material is considerably better than the final implementation.

The plans correctly demand:

* frozen annotation,
* locked test data,
* multiple experimental arms,
* exact relation evaluation,
* proper governance,
* registered experiments.



The supplied final scripts instead look like **prototype/scaffolding code designed to demonstrate the intended workflow**.

My inference is therefore that someone converted the intended experimental plan into a thesis narrative **before the real experiment had actually been completed**.

If that is what occurred, the cure is straightforward:

**go back to the experimental plan and actually execute it.**

Do not try to patch Chapter 4 around the existing results.

---

# 35. There is still a genuinely good MSc hiding underneath this

I would not throw away the topic.

In fact, I think the central question is considerably more interesting than the existing thesis makes it appear:

> **Can deterministic, classical clinical NLP and locally deployable open-weight LLMs reliably extract exact level–finding–status relations from locally authored English lumbar MRI reports, and where does each paradigm fail?**

That gives you a legitimate comparison between:

**rules → classical NLP → zero-shot LLM → few-shot LLM**

with possibly PEFT as an extension.

The regional reporting style becomes a defensible contextual contribution rather than a dubious “first in Kurdistan” claim.

The scientific contribution becomes the **benchmark, annotated dataset/schema, error taxonomy and local deployment evaluation**—not simply “we used Llama”.

That is a respectable MSc.

---

# 36. What I would require before I signed off on submission

If I were supervising this student, these would be **mandatory**, not optional:

1. **Freeze the task definition.** Decide exactly which findings/statuses/laterality variables are being extracted and use the same schema everywhere.

2. **Create the annotation manual.** Define every label, positive/negative/uncertain/unmentioned status, levels, coordination, laterality and difficult cases.

3. **Produce a real gold standard.** Ideally two independent reviewers plus adjudication on the test set.

4. **Lock the document-level test set before development.**

5. **Fix the Regex extractor.** Relation spans and clause scope must replace the current sentence-wide co-occurrence approach.

6. **Fix demographic handling.** Missing sex must never default to Female.

7. **Implement real LLM inference.** Load actual open-weight models and store raw responses.

8. **Implement genuine zero-shot and few-shot protocols.** Freeze the prompts and demonstrations.

9. **Remove all artificial metric scaling and hard-coded performance numbers.**

10. **Make evaluation abort if the reference standard is absent.**

11. **Compute level-binding and negation metrics from predictions rather than inserting constants.**

12. **Correct the few-shot `y_pred` bug.**

13. **Register every experiment.** Model version, prompt version, split, seed, hardware, quantization and date.

14. **Add JSON validity and hallucination/unsupported-relation metrics.**

15. **Evaluate exact relations, not just keyword presence.**

16. **Provide per-finding, micro and macro metrics with confidence intervals.**

17. **Use report-level paired/bootstrap comparison between systems.**

18. **Perform quantitative error analysis with an error taxonomy.**

19. **Resolve the 195-vs-196 report discrepancy and verify document-to-Excel alignment.**

20. **Rebuild Chapter 4 exclusively from generated experimental tables. No manually invented numbers.**

21. **Expand Chapter 2 dramatically** and actually establish the research gap.

22. **Rewrite Chapter 3 as a reproducible methodology**, not a two-page overview.

23. **Rewrite Chapter 5 after the real results exist.**

24. **Remove unsupported “first”, “100% privacy”, “state-of-the-art”, “confirmed epidemiological findings” and “clinical decision support” claims unless evidence warrants them.**

25. **Document ethics/data governance properly.**

Only **after those are done** would I start polishing formatting, language and presentation.

---

# My examiner-style verdict

Were this handed to me today as an MSc thesis for approval, my response would approximately be:

> **The proposed topic and dataset have sufficient potential for an MSc-level contribution; however, the submitted thesis does not presently provide a valid, reproducible experimental evaluation of the stated methods. Most critically, the supplied LLM pipeline does not perform LLM inference, several evaluation metrics are hard-coded or synthetically transformed, the available benchmark output materially contradicts the numerical results reported in the thesis, and the provenance of the gold-standard reference data is not reproducible from the submitted research package. Consequently, the principal conclusions of Chapters 4 and 5 cannot currently be supported. Substantial methodological reconstruction and re-execution of the experiments are required before the thesis should proceed to examination.**

And I would make an important distinction to the student:

**I am not rejecting the research question.**

I am rejecting the **current evidence claimed as the answer to that research question**.

That distinction matters, because the project is very salvageable. But I would absolutely **not allow them to “edit” their way out of this**. This needs a real experiment, not better prose.
