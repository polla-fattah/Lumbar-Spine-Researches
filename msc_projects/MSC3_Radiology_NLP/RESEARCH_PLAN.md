# Research Plan

## Working title

Benchmarking Rule-Based NLP and Open-Weight LLMs for Level-Resolved Information Extraction from English Lumbar MRI Reports at a Middle Eastern Teaching Hospital

## Research questions

1. How do deterministic rules, classical NLP, and open-weight instruction models compare?
2. Does constrained structured output reduce invalid or hallucinated entities?
3. What are the main errors in negation, hedging, multi-level spans, laterality, and level binding?
4. How does performance change under zero-shot, few-shot, and parameter-efficient fine-tuning?

## Local extraction schema

Level, bulge, protrusion, extrusion, dehydration, height loss, central canal stenosis, foraminal narrowing, explicit laterality, nerve-root pressure, ligamentum flavum hypertrophy, facet arthrosis, osteophytes, uncertainty/hedging, and negation.

Do not force the RSNA 25-target schema onto reports that do not contain those labels.

## Gold standard

Create an annotation manual first. Lock the test documents before model/prompt development. Use two reviewers and adjudication where feasible. Evaluate exact `(level, finding, laterality, status)` relations, not keyword presence alone.

## Extension space

Possible extensions include multilingual/translated reports, weak supervision, terminology normalisation, temporal report comparison, or privacy-preserving deployment—subject to approval.
