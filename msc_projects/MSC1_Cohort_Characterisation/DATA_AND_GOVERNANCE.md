# Data and Governance Checklist

- [ ] Written hospital/ethics authority and reference recorded.
- [ ] Reports accessed only in the approved environment.
- [ ] Case identifiers replaced with study IDs.
- [ ] Linkage key stored separately with restricted access.
- [ ] Source reports preserved read-only.
- [ ] Codebook approved before extraction.
- [ ] Missingness and exclusions documented.
- [ ] Structured fields audited against source text.
- [ ] No population-prevalence or causal claims.

## Suggested data layers

`raw_reports_readonly/` → `working_extraction/` → `audited_analysis_dataset/`

Do not overwrite the source reports. The analysis dataset should contain only the minimum necessary de-identified fields.
