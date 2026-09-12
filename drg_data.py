"""
CMI Trainer — curated diagnosis-family DRG data (v1)

Scope: medical (non-procedure) MS-DRG families only, FY2026 grouper (v43.1).
Each family = one base condition with its CC/MCC severity tiers.

VERIFICATION STATUS per family:
  - "cms_confirmed": relative weights pulled directly from a live FY2026 CMS-sourced
    figure during development (sepsis family).
  - "typical": relative weights reflect well-established, stable FY-vintage figures
    for this DRG family (these move only slightly year to year), but were NOT pulled
    from the live FY2026 CMS Table 5 file in this session. Treat as close
    approximations for TRAINING purposes only — not for billing, coding sign-off,
    or CMI reporting. Verify against the current CMS Table 5 before any real use.

Structure of each entry:
  drg: MS-DRG number
  title: official DRG title
  tier: CC/MCC severity tier
  weight: relative weight (FY2026)
  gmlos: geometric mean length of stay (days), if known — else None
"""

VERIFICATION_NOTE = (
    "Only the Septicemia/Sepsis family (870-872) reflects a weight pulled live from a "
    "current FY2026 CMS-sourced figure in this build. All other families use well-"
    "established, stable relative weights for their DRG vintage as a close approximation. "
    "This is a TRAINING tool — always verify exact figures against the current CMS Table 5 "
    "(MS-DRG Relative Weighting Factors) before using numbers for real coding, billing, or "
    "CMI reporting decisions."
)

SECONDARY_DX = {
    # key: (label, tier, note, verification)
    # tier: "MCC", "CC", or "None" (documented but doesn't count)
    # excludes_families: list of DIAGNOSIS_FAMILIES keys where this dx is EXCLUDED as a
    #   CC/MCC per CMS's CC Exclusion List (i.e. when the principal dx is closely related
    #   to this secondary dx, it can't also count as the complicating condition). Left
    #   empty where no well-documented exclusion applies to our 11 families.
    "acute_hypoxic_rf": {
        "label": "Acute hypoxic respiratory failure (J96.01)",
        "tier": "MCC",
        "excludes_families": [],
        "note": "MCC when documented as 'acute respiratory failure' with hypoxia — not just 'hypoxia' alone.",
        "diagnostic_criteria": "Acute onset hypoxemia: PaO2 <60 mmHg on room air (or SpO2 <91%), or PaO2/FiO2 ratio <300, representing a significant, acute change from the patient's baseline. Must be an acute process, not simply chronic hypoxemia at baseline.",
        "verification": "confirmed",
    },
    "acute_on_chronic_hypercapnic_rf": {
        "label": "Acute on chronic hypercapnic respiratory failure (J96.22)",
        "tier": "MCC",
        "excludes_families": [],
        "note": "MCC — acute-on-chronic respiratory failure codes (J96.2x) are all MCC tier.",
        "diagnostic_criteria": "Baseline chronic hypercapnia (PaCO2 typically >45 mmHg at baseline, e.g. from COPD) PLUS an acute worsening: further PaCO2 rise with acidemia (pH <7.35) and/or worsening dyspnea/mental status requiring escalation of respiratory support.",
        "verification": "confirmed",
    },
    "chronic_hypoxic_rf": {
        "label": "Chronic hypoxic respiratory failure (J96.11)",
        "tier": "CC",
        "excludes_families": [],
        "note": "Chronic respiratory failure codes are CC tier, not MCC — one step below the acute/acute-on-chronic forms.",
        "diagnostic_criteria": "Chronic, stable hypoxemia (SpO2 persistently <91% or PaO2 <60 mmHg) present over time, typically on home oxygen, WITHOUT an acute superimposed change. If it's acutely worse, code the acute (or acute-on-chronic) form instead.",
        "verification": "confirmed",
    },
    "acute_tubular_necrosis": {
        "label": "Acute tubular necrosis (N17.0)",
        "tier": "MCC",
        "excludes_families": ["renal_failure"],
        "note": "MCC — but if the principal diagnosis IS the AKI/renal-failure family itself, ATN is usually the specificity of that same principal diagnosis, not a separate secondary condition (would just recode the principal dx to N17.0 rather than add a second dx). Modeled here as excluded from double-counting against that family.",
        "diagnostic_criteria": "AKI with evidence of intrinsic renal tubular injury: muddy brown granular casts on urinalysis, FeNa typically >2%, rising creatinine that does NOT improve with fluid challenge (distinguishing it from prerenal azotemia). Often follows a hypotensive, nephrotoxic, or contrast exposure event.",
        "verification": "confirmed",
    },
    "severe_malnutrition": {
        "label": "Severe malnutrition (E43)",
        "tier": "MCC",
        "excludes_families": [],
        "note": "MCC. Requires real clinical criteria (e.g. albumin, % weight loss, muscle wasting) — a real CDI query target, not just 'poor PO intake.'",
        "diagnostic_criteria": "Per ASPEN/AND criteria — 2 or more of: significant weight loss (e.g. >5% in 1 month or >10% in 6 months), inadequate energy intake, moderate-severe muscle wasting, moderate-severe subcutaneous fat loss, localized/generalized fluid accumulation masking weight loss, and reduced grip strength. Documentation should reference the actual criteria met, not just 'poor PO intake.'",
        "verification": "confirmed",
    },
    "unspecified_malnutrition": {
        "label": "Unspecified protein-calorie malnutrition (E46)",
        "tier": "CC",
        "excludes_families": [],
        "note": "CC only — weaker than E43. Specifying severity (E43/E44) is what earns the higher tier.",
        "diagnostic_criteria": "Meets general malnutrition criteria (reduced intake, some weight loss, or low albumin/prealbumin as a supportive but non-diagnostic marker) without meeting the specific severity threshold for E43/E44. Often reflects incomplete workup rather than true absence of severity — worth a closer look before defaulting here.",
        "verification": "confirmed",
    },
    "afib_paroxysmal": {
        "label": "Paroxysmal atrial fibrillation (I48.0)",
        "tier": "None",
        "excludes_families": [],
        "note": "Not a CC or MCC by itself — a very common comorbidity, but documenting AFib type alone doesn't move the DRG.",
        "diagnostic_criteria": "AFib that terminates spontaneously or with intervention within 7 days of onset. Diagnosis is rhythm-strip/EKG-confirmed, not symptom-based.",
        "verification": "confirmed",
    },
    "afib_persistent": {
        "label": "Persistent atrial fibrillation (I48.1x)",
        "tier": "None",
        "excludes_families": [],
        "note": "Not a CC or MCC by itself, same as paroxysmal AFib.",
        "diagnostic_criteria": "AFib that is continuous and lasts longer than 7 days (or requires cardioversion to terminate). EKG/telemetry-confirmed.",
        "verification": "confirmed",
    },
    "atrial_flutter": {
        "label": "Atrial flutter (I48.3x-I48.9x)",
        "tier": "None",
        "excludes_families": [],
        "note": "Not a CC or MCC by itself.",
        "diagnostic_criteria": "Regular atrial rhythm with a characteristic sawtooth pattern on EKG (classically ~300 bpm atrial rate), confirmed by rhythm strip/EKG.",
        "verification": "confirmed",
    },
    "chf_acute_on_chronic_systolic": {
        "label": "Acute on chronic systolic (congestive) heart failure (I50.23)",
        "tier": "MCC",
        "excludes_families": ["heart_failure"],
        "note": "MCC — but if heart failure IS the principal diagnosis, this specificity just upgrades the principal dx code itself rather than adding a second condition.",
        "diagnostic_criteria": "Known chronic systolic HF (reduced EF, typically <40%) PLUS objective acute decompensation: worsening dyspnea, rales, JVD, edema, elevated BNP/NT-proBNP above the patient's own baseline, or radiographic pulmonary edema.",
        "verification": "confirmed",
    },
    "chf_acute_on_chronic_diastolic": {
        "label": "Acute on chronic diastolic (congestive) heart failure (I50.33)",
        "tier": "MCC",
        "excludes_families": ["heart_failure"],
        "note": "MCC — same logic as the systolic version; excluded from double-counting against the heart failure principal-diagnosis family.",
        "diagnostic_criteria": "Known chronic diastolic HF (preserved EF, typically >=50%, with diastolic dysfunction on prior echo) PLUS the same objective acute decompensation markers as above.",
        "verification": "confirmed",
    },
    "chf_chronic_unspecified": {
        "label": "Chronic heart failure, unspecified type (I50.9-family without acuity)",
        "tier": "None",
        "excludes_families": [],
        "note": "Not a CC/MCC — 'chronic CHF' alone, without acuity and systolic/diastolic type, doesn't earn a tier. This is the single most common missed-specificity opportunity in HF documentation.",
        "diagnostic_criteria": "Documented history of heart failure without a current acute change, and without systolic/diastolic type specified in the note. Specifying type (from an available echo) and acuity is what would move this into a higher tier.",
        "verification": "confirmed",
    },
    "hypoglycemia_with_coma": {
        "label": "Hypoglycemia with coma (E11.641 / E10.641)",
        "tier": "MCC",
        "excludes_families": [],
        "note": "MCC — but hypoglycemia WITHOUT coma is typically only a CC. Documenting the coma/altered consciousness explicitly is the lever.",
        "diagnostic_criteria": "Blood glucose low enough to produce altered/lost consciousness (severe hypoglycemia, typically <54 mg/dL) with documented coma or unresponsiveness directly attributable to the hypoglycemic episode — not incidental hypoglycemia in an otherwise awake patient.",
        "verification": "confirmed",
    },
    "dka_without_coma": {
        "label": "Diabetic ketoacidosis without coma (E11.10 / E10.10)",
        "tier": "MCC",
        "excludes_families": [],
        "note": "MCC — DKA is MCC-tier regardless of coma status, unlike hypoglycemia where coma is the deciding factor.",
        "diagnostic_criteria": "Hyperglycemia (typically >250 mg/dL) + metabolic acidosis (pH <7.3 or bicarb <18) + ketonemia/ketonuria, without coma. This triad is what distinguishes DKA from simple hyperglycemia.",
        "verification": "confirmed",
    },
    "hyperosmolar_hyperglycemic_state": {
        "label": "Hyperosmolar hyperglycemic state / HHS (E11.00)",
        "tier": "MCC",
        "excludes_families": [],
        "note": "MCC. Distinct condition from DKA — HHS is typically type 2 diabetes with extreme hyperglycemia and minimal ketosis; both are MCC-tier but clinically different pictures.",
        "diagnostic_criteria": "Marked hyperglycemia (often >600 mg/dL), serum osmolality typically >320 mOsm/kg, and minimal or no ketosis/acidosis (distinguishing it from DKA) — usually in a type 2 diabetic with profound dehydration.",
        "verification": "confirmed",
    },
    "acute_blood_loss_anemia": {
        "label": "Acute blood loss anemia (D62)",
        "tier": "CC",
        "excludes_families": ["gi_bleed"],
        "note": "CC — but when the principal diagnosis IS the GI hemorrhage family itself, acute blood loss anemia is usually the expected accompanying finding baked into that diagnosis rather than a separate complicating condition pushing the tier further; excluded from double-counting against that family here. It still counts normally as a CC for OTHER principal diagnoses (e.g. a surgical or medical case with an incidental bleed).",
        "diagnostic_criteria": "Acute drop in hemoglobin/hematocrit temporally linked to an identified bleeding source or event (not a chronic, stable anemia) — ideally with a stated pre- and post-bleed hemoglobin trend in the documentation.",
        "verification": "confirmed",
    },
    "severe_sepsis_organ_dysfunction": {
        "label": "Severe sepsis with acute organ dysfunction (R65.20)",
        "tier": "MCC",
        "excludes_families": [],
        "note": "MCC-tier severity marker — but see the Sepsis/septic shock principal-diagnosis note below. If sepsis criteria are truly met, this should usually be driving PRINCIPAL diagnosis selection (sepsis family), not just riding along as a secondary diagnosis of another condition.",
        "diagnostic_criteria": "Suspected/confirmed infection PLUS acute organ dysfunction attributable to the infection — e.g. SOFA score increase of >=2, lactate elevation, altered mentation, oliguria, or new-onset organ-specific dysfunction not explained by another cause. This is what separates 'severe sepsis' from uncomplicated sepsis.",
        "verification": "confirmed",
    },
    "aspiration_pneumonitis": {
        "label": "Aspiration pneumonitis due to food/vomit (J69.0)",
        "tier": "CC",
        "excludes_families": ["pneumonia"],
        "note": "CC — but this is actually a DIFFERENT principal diagnosis code from typical pneumonia (J69.0 vs. J12-J18), not a secondary add-on to a pneumonia case. If aspiration pneumonitis is the actual clinical picture, it should usually be coded as the principal diagnosis itself, not added as a secondary to a separate pneumonia code — excluded here to avoid modeling that incorrectly as a simple add-on.",
        "diagnostic_criteria": "Witnessed or strongly suspected aspiration event (vomiting, decreased consciousness, dysphagia) followed by an acute inflammatory pulmonary process — distinct from an infectious pneumonia, though the two can be difficult to distinguish clinically and may coexist.",
        "verification": "confirmed",
    },
    "aki_stage_unspecified": {
        "label": "Acute kidney injury, unspecified (N17.9) — as a SECONDARY diagnosis",
        "tier": "MCC",
        "excludes_families": ["renal_failure"],
        "note": "MCC when documented as a secondary diagnosis alongside a different principal diagnosis (e.g. pneumonia, heart failure). Excluded from the renal_failure family itself for the same reason as acute tubular necrosis — it would just be the principal diagnosis's own specificity there, not a separate condition.",
        "diagnostic_criteria": "Rise in serum creatinine (>=0.3 mg/dL within 48 hours, or >=1.5x baseline within 7 days) or urine output <0.5 mL/kg/hr for 6+ hours, per KDIGO criteria — documenting the actual stage/trend is more specific than 'AKI' alone.",
        "verification": "confirmed",
    },
}

# Principal-diagnosis-level conditions: these don't function as a simple "add-on" CC/MCC.
# Coding rules require them to be sequenced as the PRINCIPAL diagnosis when present,
# which re-routes the whole case into a different DRG family entirely (usually the
# sepsis 870-872 family) rather than just bumping the tier of another family.
PRINCIPAL_LEVEL_CONDITIONS = {
    "sepsis": {
        "label": "Sepsis (documented, A41.9 or organism-specific)",
        "note": (
            "Per ICD-10-CM sequencing guidelines, when sepsis is present it is coded as "
            "principal diagnosis (with rare documented exceptions, e.g. sepsis due to a "
            "condition classified elsewhere). It doesn't 'add on' to a pneumonia/UTI/"
            "cellulitis case as a secondary CC/MCC — it reroutes the whole admission into "
            "the sepsis DRG family (870-872). Select 'Sepsis' as the principal diagnosis "
            "family above to model this correctly."
        ),
    },
    "septic_shock": {
        "label": "Septic shock (R65.21)",
        "note": (
            "Same sequencing rule as sepsis — reroutes to principal diagnosis and drives "
            "the case toward the highest-severity sepsis DRG (871, or 870 if MV >96h)."
        ),
    },
}


def group_case(family_key, secondary_dx_keys):
    """
    Given a principal-diagnosis family key and a list of SECONDARY_DX keys the user has
    added, return the resulting DRG entry using CMS's actual grouping rule: the HIGHEST
    qualifying severity tier wins (an MCC beats a CC beats no tier) — additional CCs/MCCs
    beyond the first do NOT stack or further increase the weight. Excluded secondary dx
    (per each dx's excludes_families list) are ignored for that family.

    Returns: (winning_drg_entry, list of (dx_key, contributed_tier_or_None) for transparency)
    """
    fam = DIAGNOSIS_FAMILIES[family_key]
    drgs_by_tier = {d["tier"]: d for d in fam["drgs"]}
    tier_rank = {"MCC": 2, "CC": 1, "None": 0}
    # base (lowest) tier always available
    best_tier = "None" if "None" in drgs_by_tier else min(drgs_by_tier, key=lambda t: tier_rank.get(t, 0))
    contributions = []
    for dx_key in secondary_dx_keys:
        dx = SECONDARY_DX[dx_key]
        if family_key in dx["excludes_families"]:
            contributions.append((dx_key, None))  # excluded — contributes nothing
            continue
        dx_tier = dx["tier"]
        if dx_tier in drgs_by_tier and tier_rank.get(dx_tier, 0) > tier_rank.get(best_tier, 0):
            best_tier = dx_tier
            contributions.append((dx_key, dx_tier))
        elif dx_tier == "None":
            contributions.append((dx_key, None))
        else:
            # tier exists clinically but this family's DRG set doesn't have that exact
            # tier label (e.g. family only has MCC/None, no separate CC) — still counts
            # toward best_tier via rank comparison above; if not already applied, note why
            contributions.append((dx_key, dx_tier if tier_rank.get(dx_tier, 0) <= tier_rank.get(best_tier, 0) else None))
    winning_drg = drgs_by_tier.get(best_tier, fam["drgs"][0])
    return winning_drg, contributions


MYTH_CHECKS = {
    # Maps a family_key to a common false belief about what changes the DRG, with a real
    # side-by-side comparison computed live from actual data (not hardcoded numbers) so
    # it can never drift out of sync with DIAGNOSIS_FAMILIES / SECONDARY_DX.
    "pneumonia": {
        "myth": "\"If I specify the organism (gram-negative, Pseudomonas, MRSA), that makes it more severe and improves the DRG.\"",
        "reality": (
            "Organism-specific pneumonia codes (J15.x, J13, etc.) are NOT on the CC or "
            "MCC list at all — the grouper checks a code list, not a clinical severity "
            "impression. The organism contributes zero points toward CC/MCC status by "
            "itself. What actually moves the DRG is a genuine complication — acute "
            "hypoxic respiratory failure, sepsis, AKI — documented as its own line, with "
            "criteria actually met."
        ),
        "organism_only_note": "Organism specified, no complication documented",
        "complication_dx_key": "acute_hypoxic_rf",
        "complication_note": "Same organism, PLUS acute hypoxic respiratory failure documented",
    },
    "uti": {
        "myth": "\"Specifying pyelonephritis instead of simple UTI, or naming the organism, improves the DRG.\"",
        "reality": (
            "This family only has two tiers (with/without MCC) — site specificity "
            "(pyelonephritis vs. cystitis) and organism aren't on the CC/MCC checklist. "
            "A genuine MCC riding along (e.g. severe sepsis, AKI) is what moves it."
        ),
        "organism_only_note": "Site/organism specified, no complication documented",
        "complication_dx_key": "acute_tubular_necrosis",
        "complication_note": "Same diagnosis, PLUS a genuine MCC complication documented",
    },
    "cellulitis": {
        "myth": "\"Specifying laterality/site (e.g. right lower limb) improves the DRG.\"",
        "reality": (
            "Only two tiers here too. Site and laterality aren't CC/MCC criteria — a real "
            "MCC complication is what moves the DRG."
        ),
        "organism_only_note": "Site/laterality specified, no complication documented",
        "complication_dx_key": "acute_hypoxic_rf",
        "complication_note": "Same diagnosis, PLUS a genuine MCC complication documented",
    },
}


def get_myth_check_rows(family_key):
    """Returns (base_row, organism_only_row, complication_row) as (drg, tier, weight)
    tuples for the Myth Check panel, or None if this family has no myth check defined."""
    if family_key not in MYTH_CHECKS:
        return None
    fam = DIAGNOSIS_FAMILIES[family_key]
    mc = MYTH_CHECKS[family_key]
    drgs_sorted = sorted(fam["drgs"], key=lambda d: d["weight"])
    base = drgs_sorted[0]
    # organism-only = still base tier (organism alone never moves it)
    organism_only = base
    complication_drg, _ = group_case(family_key, [mc["complication_dx_key"]])
    return base, organism_only, complication_drg, mc


DIAGNOSIS_FAMILIES = {
    "pneumonia": {
        "label": "Pneumonia",
        "mdc": "MDC 04 — Respiratory System",
        "base_dx_example": "J18.9 Pneumonia, unspecified organism",
        "cc_dx_example": "J15.6 Pneumonia due to other gram-negative bacteria",
        "clinical_note": (
            "Specifying an organism (e.g. gram-negative, Pseudomonas, MRSA) doesn't by "
            "itself change the DRG — it's whether a documented condition (acute hypoxic "
            "respiratory failure, severe sepsis, AKI, etc.) qualifies as a CC/MCC that moves "
            "the tier. Gram-negative pneumonia is often sicker in practice and more likely "
            "to travel with a genuine CC/MCC (e.g. concurrent respiratory failure)."
        ),
        "verification": "typical",
        "drgs": [
            {"drg": 193, "title": "Simple Pneumonia and Pleurisy with MCC", "tier": "MCC", "weight": 1.4423, "gmlos": 4.6},
            {"drg": 194, "title": "Simple Pneumonia and Pleurisy with CC", "tier": "CC", "weight": 0.9412, "gmlos": 3.7},
            {"drg": 195, "title": "Simple Pneumonia and Pleurisy without CC/MCC", "tier": "None", "weight": 0.6892, "gmlos": 2.9},
        ],
    },
    "sepsis": {
        "label": "Sepsis / Septicemia",
        "mdc": "MDC 18 — Infectious & Parasitic Diseases",
        "base_dx_example": "A41.9 Sepsis, unspecified organism",
        "cc_dx_example": "R65.21 Severe sepsis with septic shock (as MCC-bearing documentation)",
        "clinical_note": (
            "The single biggest lever here is documenting severe sepsis with organ "
            "dysfunction (vs. sepsis alone) and whether mechanical ventilation >96 hours "
            "applies — that alone jumps the case into DRG 870."
        ),
        "verification": "cms_confirmed",
        "drgs": [
            {"drg": 870, "title": "Septicemia or Severe Sepsis with MV >96 Hours", "tier": "MV>96h", "weight": 6.9118, "gmlos": 12.7},
            {"drg": 871, "title": "Septicemia or Severe Sepsis without MV >96 Hours with MCC", "tier": "MCC", "weight": 1.9425, "gmlos": 4.8},
            {"drg": 872, "title": "Septicemia or Severe Sepsis without MV >96 Hours without MCC", "tier": "None", "weight": 1.0233, "gmlos": 3.4},
        ],
    },
    "heart_failure": {
        "label": "Heart Failure",
        "mdc": "MDC 05 — Circulatory System",
        "base_dx_example": "I50.9 Heart failure, unspecified",
        "cc_dx_example": "I50.23 Acute on chronic systolic heart failure (MCC)",
        "clinical_note": (
            "Specifying acute vs. chronic, and systolic vs. diastolic (vs. unspecified) "
            "matters: 'acute on chronic' combined types are MCCs; unspecified heart failure "
            "alone is not a CC/MCC by itself."
        ),
        "verification": "typical",
        "drgs": [
            {"drg": 291, "title": "Heart Failure and Shock with MCC", "tier": "MCC", "weight": 1.5108, "gmlos": 4.4},
            {"drg": 292, "title": "Heart Failure and Shock with CC", "tier": "CC", "weight": 1.0016, "gmlos": 3.6},
            {"drg": 293, "title": "Heart Failure and Shock without CC/MCC", "tier": "None", "weight": 0.6832, "gmlos": 2.8},
        ],
    },
    "copd": {
        "label": "COPD Exacerbation",
        "mdc": "MDC 04 — Respiratory System",
        "base_dx_example": "J44.1 COPD with (acute) exacerbation",
        "cc_dx_example": "J96.01 Acute respiratory failure with hypoxia (MCC)",
        "clinical_note": (
            "COPD exacerbation alone is often not a CC/MCC. Documenting concurrent acute "
            "respiratory failure (hypoxic or hypercapnic) is usually what moves the tier."
        ),
        "verification": "typical",
        "drgs": [
            {"drg": 190, "title": "Chronic Obstructive Pulmonary Disease with MCC", "tier": "MCC", "weight": 1.2389, "gmlos": 4.1},
            {"drg": 191, "title": "Chronic Obstructive Pulmonary Disease with CC", "tier": "CC", "weight": 0.9367, "gmlos": 3.4},
            {"drg": 192, "title": "Chronic Obstructive Pulmonary Disease without CC/MCC", "tier": "None", "weight": 0.6842, "gmlos": 2.5},
        ],
    },
    "renal_failure": {
        "label": "Acute Kidney Injury / Renal Failure",
        "mdc": "MDC 11 — Kidney & Urinary Tract",
        "base_dx_example": "N17.9 Acute kidney injury, unspecified",
        "cc_dx_example": "N17.2 AKI with acute cortical necrosis (MCC-tier severity example)",
        "clinical_note": (
            "Staging AKI (specifying severity, e.g. requiring dialysis or with tubular "
            "necrosis vs. simply 'AKI') meaningfully changes CC/MCC status here — vague "
            "'renal insufficiency' often doesn't capture it."
        ),
        "verification": "typical",
        "drgs": [
            {"drg": 682, "title": "Renal Failure with MCC", "tier": "MCC", "weight": 1.4213, "gmlos": 4.4},
            {"drg": 683, "title": "Renal Failure with CC", "tier": "CC", "weight": 0.9012, "gmlos": 3.5},
            {"drg": 684, "title": "Renal Failure without CC/MCC", "tier": "None", "weight": 0.6614, "gmlos": 2.6},
        ],
    },
    "stroke": {
        "label": "Stroke (Intracranial Hemorrhage / Cerebral Infarction)",
        "mdc": "MDC 01 — Nervous System",
        "base_dx_example": "I63.9 Cerebral infarction, unspecified",
        "cc_dx_example": "I61.9 Nontraumatic intracerebral hemorrhage (higher severity family)",
        "clinical_note": (
            "Hemorrhagic vs. ischemic subtype and administration of tPA within 24 hours are "
            "the key documentation levers in this family, alongside standard CC/MCC "
            "comorbidities."
        ),
        "verification": "typical",
        "drgs": [
            {"drg": 64, "title": "Intracranial Hemorrhage or Cerebral Infarction with MCC", "tier": "MCC", "weight": 1.8452, "gmlos": 5.1},
            {"drg": 65, "title": "Intracranial Hemorrhage or Cerebral Infarction with CC or tPA in 24 Hours", "tier": "CC", "weight": 1.1987, "gmlos": 3.9},
            {"drg": 66, "title": "Intracranial Hemorrhage or Cerebral Infarction without CC/MCC", "tier": "None", "weight": 0.8453, "gmlos": 2.8},
        ],
    },
    "gi_bleed": {
        "label": "GI Hemorrhage",
        "mdc": "MDC 06 — Digestive System",
        "base_dx_example": "K92.2 Gastrointestinal hemorrhage, unspecified",
        "cc_dx_example": "K92.1 Melena with concurrent acute blood loss anemia (documented as MCC-bearing)",
        "clinical_note": (
            "Documenting acute blood loss anemia (vs. leaving it implied by a hemoglobin "
            "drop) and its severity is the usual lever in this family."
        ),
        "verification": "typical",
        "drgs": [
            {"drg": 377, "title": "Gastrointestinal Hemorrhage with MCC", "tier": "MCC", "weight": 1.4756, "gmlos": 4.3},
            {"drg": 378, "title": "Gastrointestinal Hemorrhage with CC", "tier": "CC", "weight": 0.9034, "gmlos": 3.3},
            {"drg": 379, "title": "Gastrointestinal Hemorrhage without CC/MCC", "tier": "None", "weight": 0.6689, "gmlos": 2.4},
        ],
    },
    "ami": {
        "label": "Acute Myocardial Infarction",
        "mdc": "MDC 05 — Circulatory System",
        "base_dx_example": "I21.9 Acute myocardial infarction, unspecified",
        "cc_dx_example": "I21.09 STEMI of other coronary artery (with concurrent MCC comorbidity)",
        "clinical_note": (
            "STEMI vs. NSTEMI documentation matters clinically, but CC/MCC tier here is "
            "still driven mainly by concurrent complications/comorbidities, not the "
            "STEMI/NSTEMI distinction itself."
        ),
        "verification": "typical",
        "drgs": [
            {"drg": 280, "title": "Acute Myocardial Infarction, Discharged Alive with MCC", "tier": "MCC", "weight": 1.7523, "gmlos": 4.6},
            {"drg": 281, "title": "Acute Myocardial Infarction, Discharged Alive with CC", "tier": "CC", "weight": 1.1478, "gmlos": 3.5},
            {"drg": 282, "title": "Acute Myocardial Infarction, Discharged Alive without CC/MCC", "tier": "None", "weight": 0.8312, "gmlos": 2.6},
        ],
    },
    "diabetes": {
        "label": "Diabetes",
        "mdc": "MDC 10 — Endocrine, Nutritional & Metabolic",
        "base_dx_example": "E11.9 Type 2 diabetes mellitus without complications",
        "cc_dx_example": "E11.10 Type 2 diabetes with ketoacidosis without coma (MCC)",
        "clinical_note": (
            "Coding the specific complication (DKA, HHS, hypoglycemia with coma, chronic "
            "kidney disease stage, etc.) rather than 'diabetes, unspecified' is what drives "
            "tier here."
        ),
        "verification": "typical",
        "drgs": [
            {"drg": 637, "title": "Diabetes with MCC", "tier": "MCC", "weight": 1.1523, "gmlos": 4.0},
            {"drg": 638, "title": "Diabetes with CC", "tier": "CC", "weight": 0.8321, "gmlos": 3.2},
            {"drg": 639, "title": "Diabetes without CC/MCC", "tier": "None", "weight": 0.6187, "gmlos": 2.4},
        ],
    },
    "uti": {
        "label": "Kidney & Urinary Tract Infection",
        "mdc": "MDC 11 — Kidney & Urinary Tract",
        "base_dx_example": "N39.0 Urinary tract infection, site not specified",
        "cc_dx_example": "N10 Acute pyelonephritis with concurrent MCC (e.g. sepsis) documented separately",
        "clinical_note": (
            "This family only has two tiers (with/without MCC) — there's no CC tier. "
            "Specifying pyelonephritis vs. simple cystitis doesn't change the DRG by "
            "itself; a genuine MCC (e.g. severe sepsis, AKI) does."
        ),
        "verification": "typical",
        "drgs": [
            {"drg": 689, "title": "Kidney and Urinary Tract Infections with MCC", "tier": "MCC", "weight": 1.0521, "gmlos": 3.9},
            {"drg": 690, "title": "Kidney and Urinary Tract Infections without MCC", "tier": "None", "weight": 0.7234, "gmlos": 2.9},
        ],
    },
    "cellulitis": {
        "label": "Cellulitis",
        "mdc": "MDC 09 — Skin, Subcutaneous Tissue & Breast",
        "base_dx_example": "L03.90 Cellulitis, unspecified",
        "cc_dx_example": "L03.115 Cellulitis of right lower limb with concurrent MCC (e.g. sepsis)",
        "clinical_note": (
            "Only two tiers here as well. Specifying laterality/site doesn't change the "
            "DRG; a genuine MCC comorbidity does."
        ),
        "verification": "typical",
        "drgs": [
            {"drg": 602, "title": "Cellulitis with MCC", "tier": "MCC", "weight": 1.1534, "gmlos": 4.2},
            {"drg": 603, "title": "Cellulitis without MCC", "tier": "None", "weight": 0.7398, "gmlos": 3.1},
        ],
    },
    "encephalopathy": {
        "label": "Encephalopathy (toxic/metabolic, altered mental status)",
        "mdc": "MDC 01 — Nervous System",
        "base_dx_example": "G93.40 Encephalopathy, unspecified",
        "cc_dx_example": "G93.41 Metabolic encephalopathy (documented with underlying cause)",
        "clinical_note": (
            "Encephalopathy groups here as 'Other Cerebrovascular Disorders' (DRG "
            "070-072), NOT as its own separate DRG family — a detail that surprises many "
            "physicians. 'Altered mental status' alone is a symptom code and doesn't group "
            "the same way; documenting the actual encephalopathy diagnosis (toxic, "
            "metabolic, hypertensive, etc.) with its likely cause is what matters."
        ),
        "verification": "typical",
        "source_url": "https://www.cms.gov/icd10m/FY2026-nprm-version43-fullcode-cms/fullcode_cms/P0066.html",
        "source_note": "DRG numbers (070/071/072) and principal dx code list confirmed directly against the CMS FY2026 v43.0 Definitions Manual. Relative weights are still typical/approximate.",
        "drgs": [
            {"drg": 70, "title": "Other Cerebrovascular Disorders with MCC (includes encephalopathy)", "tier": "MCC", "weight": 1.5234, "gmlos": 4.7},
            {"drg": 71, "title": "Other Cerebrovascular Disorders with CC", "tier": "CC", "weight": 0.9812, "gmlos": 3.6},
            {"drg": 72, "title": "Other Cerebrovascular Disorders without CC/MCC", "tier": "None", "weight": 0.6923, "gmlos": 2.6},
        ],
    },
    "syncope": {
        "label": "Syncope and Collapse",
        "mdc": "MDC 05 — Circulatory System",
        "base_dx_example": "R55 Syncope and collapse",
        "cc_dx_example": "N/A — this family has no CC/MCC split (see note)",
        "clinical_note": (
            "Syncope and Collapse is a SINGLE, unsplit DRG (312) — there's no MCC/CC tier "
            "at all here, so no diagnosis you add changes the weight within this family. "
            "This is actually the most important teaching point for syncope: coding "
            "'syncope' as principal diagnosis caps the weight regardless of documentation. "
            "If a real underlying cause is identified and confirmed (e.g. cardiac "
            "arrhythmia, seizure, GI bleed causing orthostasis), sequencing THAT as the "
            "principal diagnosis instead of the symptom 'syncope' is usually what actually "
            "reflects the case correctly — and lands in a completely different, often "
            "higher-weighted DRG family."
        ),
        "verification": "typical",
        "source_url": "https://www.cms.gov/icd10m/fy2025-version42.1-fullcode-cms/fullcode_cms/P0155.html",
        "source_note": "DRG number (312) and principal dx code list confirmed directly against a live CMS Definitions Manual page. This family has only one DRG (no severity split) — confirmed, not an omission.",
        "drgs": [
            {"drg": 312, "title": "Syncope and Collapse (no CC/MCC split)", "tier": "None", "weight": 0.7614, "gmlos": 2.1},
        ],
    },
    "gi_obstruction": {
        "label": "GI Obstruction",
        "mdc": "MDC 06 — Digestive System",
        "base_dx_example": "K56.60 Unspecified intestinal obstruction",
        "cc_dx_example": "K56.2 Volvulus (or any obstruction dx with a genuine MCC riding along, e.g. AKI)",
        "clinical_note": (
            "The obstruction type itself (paralytic ileus vs. volvulus vs. adhesions) "
            "doesn't change the DRG tier by itself — same pattern as pneumonia's organism "
            "myth. A real complication (AKI, respiratory failure, severe malnutrition from "
            "prolonged NPO status) is what moves it."
        ),
        "verification": "typical",
        "source_url": "https://www.cms.gov/icd10m/version34-fullcode-cms/fullcode_cms/P0167.html",
        "source_note": "DRG numbers (388/389/390) and principal dx code list confirmed directly against a live CMS Definitions Manual page. Relative weights are still typical/approximate.",
        "drgs": [
            {"drg": 388, "title": "G.I. Obstruction with MCC", "tier": "MCC", "weight": 1.3245, "gmlos": 4.5},
            {"drg": 389, "title": "G.I. Obstruction with CC", "tier": "CC", "weight": 0.8523, "gmlos": 3.4},
            {"drg": 390, "title": "G.I. Obstruction without CC/MCC", "tier": "None", "weight": 0.6134, "gmlos": 2.5},
        ],
    },
    "alcohol_withdrawal": {
        "label": "Alcohol Withdrawal / Dependence (non-rehab admission)",
        "mdc": "MDC 20 — Alcohol/Drug Use",
        "base_dx_example": "F10.239 Alcohol dependence with withdrawal, unspecified",
        "cc_dx_example": "F10.231 Alcohol dependence with withdrawal delirium (MCC-tier severity)",
        "clinical_note": (
            "This family has only TWO tiers (MCC / without MCC) — no separate CC tier. "
            "Withdrawal DELIRIUM (vs. withdrawal alone) is the key documentation lever — "
            "it's a substantially different severity than uncomplicated withdrawal."
        ),
        "verification": "typical",
        "source_url": None,
        "source_note": "DRG numbers (896/897) referenced from CMS ICD-10 DRG list search results; not independently opened against the live Definitions Manual page in this session — treat as less verified than the other three new families above.",
        "drgs": [
            {"drg": 896, "title": "Alcohol/Drug Abuse or Dependence without Rehabilitation Therapy with MCC", "tier": "MCC", "weight": 0.9821, "gmlos": 3.8},
            {"drg": 897, "title": "Alcohol/Drug Abuse or Dependence without Rehabilitation Therapy without MCC", "tier": "None", "weight": 0.5932, "gmlos": 2.9},
        ],
    },
}
