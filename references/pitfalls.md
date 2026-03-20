# DHS Indicator Validation Pitfalls

Common sources of mismatch between microdata computations and official STATcompiler
values, organized by scope.

## Universal Pitfalls

### Weight variables
- HR and PR files: use `hv005`, divide by 1,000,000
- IR and KR files: use `v005`, divide by 1,000,000
- MR (men's) file: use `mv005`, divide by 1,000,000
- Never mix weight variables across recode files

### Denominator: de facto vs de jure
- Most DHS indicators use **de facto** population (people who slept in the HH last night)
- De facto indicator: `hv103 == 1` in PR file
- De jure: `hv102 == 1` (usual resident)
- The denominator choice affects person-level indicators significantly
- Household-level indicators (e.g., "% HH with net") use all HHs regardless

### Survey design
- Standard: `svyset hv001 [pw=wt], strata(hv023)`
- Some surveys use `hv022` instead of `hv023` for strata
- IR/KR: `svyset v001 [pw=wt], strata(v023)`
- Always use `svy:` prefix for estimates; use `svy, subpop()` for subgroup analysis
- Never use `if` conditions with `svy:` for subgroups — use `subpop()` instead

### DHS phase differences
- DHS-VIII (file prefix `81`) may have updated variable coding in some chapters
- Check for `DHS8/` subdirectories in the GitHub repo for phase-specific code
- Phase can be inferred from the recode file name (e.g., `CDHR81FL` = DHS-VIII)

---

## Chapter-Specific Pitfalls

### ML_ (Malaria / Nets) — FULLY VALIDATED (DRC 2023-24)

**Child age variable:**
Use `hml16` (corrected age transferred from the Individual Recode file), NOT `hv105`
(age from household listing). The official tabulation code in `ML_tables.do` uses
`hml16 < 5` for children under 5. Using `hv105` gives values ~0.1pp off.

**De facto household member count:**
For ML_NETP_H_IT2 (ITN per 2 people), the denominator is the count of de facto
members per HH — computed as `sum(hv103==1)` from the PR file, NOT `hv009` from HR.
Using `hv009` gives values ~1pp off.

**Person slept under net (`hml12` in PR):**
- 0 = no net
- 1 = slept under only a treated net (ITN)
- 2 = slept under both treated and untreated nets
- 3 = slept under only an untreated net
- "Slept under ITN" = `inlist(hml12, 1, 2)` (not just `hml12 == 1`)

**ITN access (ML_ITNA_P_ACC):**
Each ITN can cover up to 2 people. Per-person access ratio:
`min(n_itn * 2, defacto_hh_pop) / defacto_hh_pop`
This ratio is assigned to each de facto member, then averaged across the de facto
population using person weights.

**Net-level ITN usage (ML_ITNU_N_ITN):**
Computed as a weighted ratio across households:
`sum(ITNs_used * weight) / sum(total_ITNs * weight)`
An ITN is "used" if `hml10 == 1` (is ITN) AND `hml21 == 1` (someone slept under it).
This is NOT a simple household-level mean.

**Key DHS indicator codes:**

| Code | Description | File | Denominator |
|------|-------------|------|-------------|
| ML_NETP_H_ITN | % HH with >=1 ITN | HR | All HHs |
| ML_NETP_H_MNI | Mean ITNs per HH | HR | All HHs |
| ML_NETP_H_IT2 | % HH with >=1 ITN per 2 people | HR+PR | All HHs |
| ML_ITNA_P_ACC | % pop with ITN access | HR+PR | De facto pop |
| ML_NETU_P_ITN | % pop slept under ITN | PR | De facto pop |
| ML_NETU_P_IT1 | % pop under ITN (HHs w/ ITN) | PR | De facto in HHs with ITN |
| ML_ITNU_N_ITN | % existing ITNs used | HR | All ITNs |
| ML_NETC_C_ITN | % children <5 under ITN | PR | De facto children hml16<5 |
| ML_NETC_C_IT1 | % children <5 under ITN (HHs w/ ITN) | PR | De facto children hml16<5 in HHs with ITN |

**GitHub do-files for malaria/nets:**
- `Chap12_ML/ML_NETS_HH.do` — household-level ownership
- `Chap12_ML/ML_NETS_use.do` — person-level usage (PR file)
- `Chap12_ML/ML_EXISTING_ITN.do` — net-level ITN usage
- `Chap12_ML/ML_NETS_access.do` — ITN access
- `Chap12_ML/ML_tables.do` — tabulation with filter conditions

---

### CH_ (Child Health)

*Not yet validated. Check GitHub repo: `Chap10_CH/`*

Known considerations:
- Vaccination: card vs mother's report; age window 12-23 months for "full vaccination"
- ARI treatment: 2-week recall window
- Diarrhea: ORS/zinc treatment coding varies by DHS phase

### FP_ (Family Planning)

*Not yet validated. Check GitHub repo: `Chap07_FP/`*

Known considerations:
- Denominators differ: "currently married" vs "all women" vs "sexually active"
- Unmet need algorithm is complex and has changed across DHS phases
- Modern vs traditional method classification

### NT_ (Nutrition / Anthropometry)

*Not yet validated. Check GitHub repo: `Chap11_NT/`*

Known considerations:
- Anthropometric z-score flag filtering (WHO flags for biologically implausible values)
- WHO 2006 vs NCHS reference populations
- Height-for-age (stunting), weight-for-height (wasting), weight-for-age (underweight)
- Anemia: hemoglobin adjustment for altitude

### FE_ (Fertility)

*Not yet validated. Check GitHub repo: `Chap05_FE/`*

Known considerations:
- TFR uses 3-year window before survey
- ASFR age groups: 15-19, 20-24, ..., 45-49
- Birth history completeness checks
