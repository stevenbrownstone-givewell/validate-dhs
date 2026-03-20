---
name: validate-dhs
description: "Validate DHS microdata computations against official STATcompiler API values. Use this skill whenever Claude notices DHS indicator computation in Stata logs, output tables, or conversation context -- including statistics like net ownership rates, vaccination coverage, fertility rates, child nutrition measures, or any percentage/mean that could correspond to a published DHS indicator. Also use when the user mentions STATcompiler, DHS validation, official indicators, or asks to verify computed statistics against published DHS estimates."
argument-hint: "[country-code] [survey-id-or-year] [indicator-ids-or-chapter]"
---

# Validate DHS Indicators

Detect computed DHS statistics in analysis outputs, compare them against the
STATcompiler API, and if they don't match, pull exact official definitions from
the DHS GitHub repo to diagnose the issue.

## When to Activate

Proactively invoke this skill when you notice any of:
- A Stata do-file was just run that computes statistics from DHS recode files (HR, PR, IR, KR, BR)
- Output tables (CSV, markdown) contain percentages or means that could be standard DHS indicators
- The user discusses computing a DHS indicator or shows code referencing DHS variables
- A computed value seems implausible for a standard DHS indicator
- The user mentions "STATcompiler", "DHS validation", "official indicators", or asks to verify results

If the user explicitly invokes `/validate-dhs`, parse `$ARGUMENTS` as:
- Arg 1: 2-letter country code (e.g., `CD` for DRC)
- Arg 2: Survey ID (`CD2023DHS`) or year (`2023`)
- Arg 3: Comma-separated indicator IDs (`ML_NETP_H_ITN,ML_NETC_C_ITN`) or chapter shorthand (`malaria_nets`)

See [references/indicator_chapters.md](references/indicator_chapters.md) to expand chapter shorthands to indicator IDs.

## Step 1: Detect Candidate Indicators

Scan for computed values that might correspond to DHS indicators:

### Stata logs
After a do-file runs, scan the log for printed statistics (means, proportions,
tabulations) computed from DHS variables. Look for:
- Variable names: `hv227`, `hml*`, `ml0`, `v459`, `v460`, `ch_*`, `fp_*`, `nt_*`
- Variable labels containing: "net", "ITN", "vaccin", "fever", "diarrhea", "stunting", "wasting", "contracepti"
- Commands: `svy: mean`, `svy: proportion`, `tab`, `summarize` applied to DHS variables

### Output tables
Scan CSV and markdown files in `output/tables/` or similar output directories for:
- Column headers matching known indicator labels (e.g., "% with ITN", "net ownership")
- Percentage values in plausible ranges for standard DHS indicators

### Conversation context
If the user is discussing or showing code that computes indicators from DHS files,
note which indicators and their computed values.

Build a list of: `(indicator_description, computed_value, country, survey)`.

Use `python3 ${CLAUDE_SKILL_DIR}/scripts/dhs_api.py indicators "<search>"` to
map variable names or descriptions to official DHS indicator IDs.

## Step 2: Query DHS API for Official Values

Run the API script to get official published values:

```bash
python3 ${CLAUDE_SKILL_DIR}/scripts/dhs_api.py data <country> <survey_id> <indicator_ids>
```

If the user provided a year instead of survey ID, the script resolves it automatically.

Display a comparison table:

```
Indicator        | Description                    | Computed | Official | Diff  | Status
ML_NETP_H_ITN    | % HH with >=1 ITN             |   69.4   |   69.4   |  0.0  |  PASS
ML_NETC_C_ITN    | % children <5 under ITN        |   56.2   |   57.0   | -0.8  |  FAIL
```

**Thresholds:**
- |Diff| <= 0.1pp: PASS
- 0.1 < |Diff| <= 0.5: WARN (may be rounding)
- |Diff| > 0.5: FAIL (likely a definition error)

If all PASS, report success and stop. If any FAIL or WARN, proceed to Step 3.

## Step 3: Debug Mismatches Using GitHub Repo

For each indicator that failed:

### 3a. Identify the chapter and do-file

Look up the indicator prefix in [references/indicator_chapters.md](references/indicator_chapters.md)
to find the GitHub directory and specific do-file names.

### 3b. Fetch the official Stata definition

Use WebFetch to pull the relevant do-file:
```
https://raw.githubusercontent.com/DHSProgram/DHS-Indicators-Stata/master/{github_dir}/{do_file}.do
```

For malaria net indicators, the key files are:
- `Chap12_ML/ML_NETS_HH.do` — household-level net ownership
- `Chap12_ML/ML_NETS_use.do` — person-level net usage (uses PR file)
- `Chap12_ML/ML_EXISTING_ITN.do` — net-level ITN usage
- `Chap12_ML/ML_NETS_access.do` — ITN access indicator
- `Chap12_ML/ML_tables.do` — tabulation code (shows age variable choice, filter conditions)

### 3c. Check known pitfalls

Read [references/pitfalls.md](references/pitfalls.md) for the relevant chapter.
Compare the user's computation against the official definition, checking:

1. **Correct DHS recode file** — Is the user loading HR when they need PR, or vice versa?
2. **Correct age variable** — e.g., `hml16` (corrected age from Individual file) not `hv105` (household listing age)
3. **Correct denominator** — De facto members (`hv103==1`) vs all listed members (`hv009`)
4. **Correct weight variable** — `hv005` for HR/PR, `v005` for IR/KR; divided by 1,000,000
5. **Correct filter conditions** — e.g., children 12-23 months for vaccination, de facto only
6. **Correct variable coding** — e.g., `hml12`: 1=only treated net, 2=both treated+untreated; `inlist(hml12,1,2)` for "under ITN"
7. **Survey design** — `svyset` with correct PSU, strata, and weight

### 3d. Report the diagnosis

For each mismatch, report:
- What the user's code does differently from the official definition
- The specific variable/filter/denominator that needs to change
- A code snippet showing the correction

## Edge Cases

**Survey not yet in API**: Some recent surveys have downloadable microdata but aren't
in STATcompiler yet. The script will return empty results. Note this to the user and
suggest checking the DHS website. Offer to proceed with computation-only mode.

**Subnational breakdowns**: If the user wants province/region-level validation:
```bash
python3 ${CLAUDE_SKILL_DIR}/scripts/dhs_api.py data <country> <survey> <indicators> --breakdown subnational
```
Warn that province name matching between API results and Stata labels may need a crosswalk.

**DHS phase detection**: Check the recode file prefix to determine the DHS phase:
- `71` in filename = DHS-VII
- `81` in filename = DHS-VIII
Some chapters have updated code in `DHS8/` subdirectories on GitHub. Check for phase-specific code.

**Multiple candidate matches**: If a computed value could match multiple indicators,
present all possibilities and ask the user to confirm.

**Indicator not available**: Some indicators exist in the API schema but have no data
for a particular survey (e.g., biomarker indicators when no testing was done). Report
which indicators had no official value.

## Reference Materials

- [references/pitfalls.md](references/pitfalls.md) — Common validation pitfalls by chapter
- [references/indicator_chapters.md](references/indicator_chapters.md) — Chapter/indicator mapping and DHS file requirements
