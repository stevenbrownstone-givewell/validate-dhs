# DHS Indicator Chapters and Mappings

## Chapter Shorthands

Use these shorthands as the third argument to `/validate-dhs`:

| Shorthand | Chapter | Prefix | GitHub Directory | Primary Files | Key Do-Files |
|-----------|---------|--------|-----------------|---------------|--------------|
| malaria_nets | 12 | ML_ | Chap12_ML | HR, PR | ML_NETS_HH.do, ML_NETS_use.do, ML_EXISTING_ITN.do, ML_NETS_access.do |
| malaria_treatment | 12 | ML_ | Chap12_ML | KR, IR | ML_FEVER.do, ML_IPTP.do |
| malaria_biomarkers | 12 | ML_ | Chap12_ML | PR | ML_BIOMARKERS.do |
| child_health | 10 | CH_ | Chap10_CH | KR | CH_VAC.do, CH_DIAR.do, CH_ARI.do |
| family_planning | 07 | FP_ | Chap07_FP | IR | FP_USE.do, FP_NEED.do |
| nutrition | 11 | NT_ | Chap11_NT | KR, IR, PR | NT_CH_NUT.do, NT_WM_NUT.do, NT_BF.do |
| fertility | 05 | FE_ | Chap05_FE | IR, BR | FE_TFR.do, FE_ASFR.do |
| infant_mortality | 08 | CM_ | Chap08_CM | BR, IR | CM_CHILD.do |
| maternal_health | 09 | RH_ | Chap09_RH | IR | RH_ANC.do, RH_DEL.do, RH_PNC.do |
| household | 02 | PH_ | Chap02_PH | HR, PR | PH_HOUS.do, PH_POP.do |

## Indicator ID Expansion for Common Shorthands

### malaria_nets (9 indicators)
```
ML_NETP_H_ITN,ML_NETP_H_MNI,ML_NETP_H_IT2,ML_ITNA_P_ACC,ML_NETU_P_ITN,ML_NETU_P_IT1,ML_ITNU_N_ITN,ML_NETC_C_ITN,ML_NETC_C_IT1
```

### malaria_treatment (selected)
```
ML_FVRP_C_AML,ML_FVRP_C_ACT,ML_AMLD_C_ADQ,ML_IPTP_W_SPF
```

### child_health (vaccination core)
```
CH_VACC_C_BAS,CH_VACC_C_NON,CH_VACC_C_DP1,CH_VACC_C_DP3,CH_VACC_C_MSL
```

### family_planning (core)
```
FP_CUSA_W_MOD,FP_CUSA_W_ANY,FP_CUSA_W_TRD,FP_NADM_W_UNT,FP_NADM_W_ANY
```

### nutrition (child stunting/wasting)
```
NT_CH_NUT_SN2,NT_CH_NUT_WS2,NT_CH_NUT_UW2
```

## DHS Variable to Indicator ID Mapping

When detecting indicators from Stata code, use these mappings:

| Stata Variable | Likely Indicator(s) | Notes |
|---------------|---------------------|-------|
| hv227 | ML_NETP_H_MOS | % HH with at least one mosquito net |
| hml1, hml1a | ML_NETP_H_MNI | Mean number of nets/ITNs |
| hml10_* | ML_NETP_H_ITN | ITN indicator per net |
| hml12 | ML_NETU_P_ITN, ML_NETC_C_ITN | Person slept under net type |
| hml21_* | ML_ITNU_N_ITN | Someone slept under this net |
| ml0 | ML_NETC_C_ITN | Child slept under net (KR) |
| v459 | ML_NETP_H_MOS | HH has mosquito net (IR variable) |
| h2-h9 | CH_VACC_C_* | Vaccination variables |
| h11 | CH_DIAR_C_DIA | Diarrhea in last 2 weeks |
| h22 | CH_ARI_C_ARI | ARI symptoms |
| v312, v313 | FP_CUSA_W_* | Current contraceptive use |
| hw70, hw71, hw72 | NT_CH_NUT_* | Z-scores (stunting, wasting, underweight) |
| b5, b7 | CM_ECMR_C_* | Child survival, age at death |

## DHS Recode File Naming Convention

Files follow the pattern: `{CC}{RR}{PP}FL.DTA`
- CC = country code (e.g., CD)
- RR = recode type: HR (household), PR (person), IR (individual/women), KR (kids), BR (births), MR (men)
- PP = phase: 71 (DHS-VII), 81 (DHS-VIII)
- FL = flat file

Examples:
- `CDHR81FL.DTA` = DRC Household Recode, DHS-VIII
- `CDPR81FL.DTA` = DRC Person Recode, DHS-VIII
- `CDKR81FL.DTA` = DRC Kids Recode, DHS-VIII
