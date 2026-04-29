"""
cohort_definitions.py
=====================
Domain constants for the WC Knowledge Graph demo.
- Stage catalog (IAIABC MTC-aligned codes, grouped into 6 phases)
- Body part, injury cause, employer NAICS catalogs
- Cohort sub-trajectory state machines (deterministic duration distributions)
- Hero claim specifications with scripted talk tracks
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple

# ---------------------------------------------------------------------------
# STAGE CATALOG  (maps to :Stage nodes)
# code -> {label, phase, mtc, typical_duration_days: (mean, std, min, max)}
# ---------------------------------------------------------------------------

PHASES = ["Intake", "Investigation", "Coverage Decision", "Active Treatment", "Resolution", "Post-Closure"]

STAGE_CATALOG = {
    # ── Intake ──────────────────────────────────────────────────────────────
    "FROI_00":  {"label": "First Report of Injury",     "phase": "Intake",               "mtc": "FROI-00", "duration": (3,   2,   1,   10)},
    "TRIAGE":   {"label": "Initial Triage & Assignment","phase": "Intake",               "mtc": None,      "duration": (5,   3,   1,   14)},
    # ── Investigation ───────────────────────────────────────────────────────
    "INVEST":   {"label": "Investigation",              "phase": "Investigation",         "mtc": "FROI-02", "duration": (14,  7,   5,   45)},
    "IME_ORD":  {"label": "IME Ordered",                "phase": "Investigation",         "mtc": None,      "duration": (21,  10,  7,   60)},
    "IME_COMP": {"label": "IME Completed",              "phase": "Investigation",         "mtc": None,      "duration": (14,  7,   7,   30)},
    "QME_ORD":  {"label": "QME Ordered (CA)",           "phase": "Investigation",         "mtc": None,      "duration": (30,  15,  14,  90)},
    "QME_COMP": {"label": "QME Completed (CA)",         "phase": "Investigation",         "mtc": None,      "duration": (21,  10,  14,  45)},
    # ── Coverage Decision ───────────────────────────────────────────────────
    "ACCEPTED": {"label": "Claim Accepted",             "phase": "Coverage Decision",     "mtc": "SROI-IP", "duration": (3,   2,   1,   7)},
    "DENIED":   {"label": "Claim Denied",               "phase": "Coverage Decision",     "mtc": "FROI-04", "duration": (3,   2,   1,   7)},
    "DELAY_NTC":{"label": "Delay Notice Issued (CA 90d)","phase": "Coverage Decision",   "mtc": "FROI-02", "duration": (7,   3,   1,   14)},
    # ── Active Treatment ────────────────────────────────────────────────────
    "TTD_START":{"label": "TTD Payments Initiated",     "phase": "Active Treatment",      "mtc": "SROI-IP", "duration": (5,   2,   1,   14)},
    "MED_TX":   {"label": "Medical Treatment",          "phase": "Active Treatment",      "mtc": "SROI-PY", "duration": (45,  30,  14,  180)},
    "PT":       {"label": "Physical Therapy",           "phase": "Active Treatment",      "mtc": "SROI-PY", "duration": (42,  21,  14,  120)},
    "SURGERY":  {"label": "Surgery Authorized & Performed","phase": "Active Treatment",   "mtc": "SROI-CA", "duration": (30,  14,  14,  60)},
    "POST_SURG":{"label": "Post-Surgery Recovery",      "phase": "Active Treatment",      "mtc": "SROI-PY", "duration": (90,  45,  45,  270)},
    "NCM":      {"label": "Nurse Case Management",      "phase": "Active Treatment",      "mtc": None,      "duration": (60,  30,  14,  180)},
    "RTW_MOD":  {"label": "Return to Work (Modified Duty)","phase": "Active Treatment",   "mtc": "SROI-SU", "duration": (30,  20,  7,   90)},
    "TTD_REIN": {"label": "TTD Reinstated (Re-injury)", "phase": "Active Treatment",      "mtc": "SROI-RB", "duration": (30,  15,  14,  90)},
    # ── Resolution ──────────────────────────────────────────────────────────
    "MMI":      {"label": "Maximum Medical Improvement","phase": "Resolution",            "mtc": None,      "duration": (14,  7,   7,   45)},
    "PPD_RATE": {"label": "PPD Rating",                 "phase": "Resolution",            "mtc": "SROI-CA", "duration": (30,  15,  14,  90)},
    "MEDIATION":{"label": "Mediation",                  "phase": "Resolution",            "mtc": None,      "duration": (45,  20,  21,  90)},
    "LITIGATION":{"label": "Litigation Filed",          "phase": "Resolution",            "mtc": None,      "duration": (180, 90,  90,  540)},
    "SETTLE":   {"label": "Settlement / C&R",           "phase": "Resolution",            "mtc": "SROI-FN", "duration": (21,  10,  7,   60)},
    "STIP":     {"label": "Stipulated Award",           "phase": "Resolution",            "mtc": "SROI-FN", "duration": (14,  7,   7,   30)},
    # ── Post-Closure ────────────────────────────────────────────────────────
    "CLOSED_FN":{"label": "Claim Closed (Final)",       "phase": "Post-Closure",          "mtc": "SROI-FN", "duration": (1,   0,   1,   1)},
    "CLOSED_DN":{"label": "Claim Closed (Denied)",      "phase": "Post-Closure",          "mtc": "FROI-04", "duration": (1,   0,   1,   1)},
}

# ---------------------------------------------------------------------------
# BODY PART CATALOG  (WCIO codes subset)
# ---------------------------------------------------------------------------

BODY_PARTS = {
    "LUMBAR":    {"label": "Lumbar / Lower Back",   "region": "Trunk"},
    "KNEE":      {"label": "Knee",                  "region": "Lower Extremity"},
    "SHOULDER":  {"label": "Shoulder / Rotator Cuff","region": "Upper Extremity"},
    "WRIST":     {"label": "Wrist / Carpal Tunnel",  "region": "Upper Extremity"},
    "HEAD":      {"label": "Head / Concussion",      "region": "Head"},
    "ANKLE":     {"label": "Ankle / Foot",           "region": "Lower Extremity"},
    "HAND":      {"label": "Hand / Fingers",         "region": "Upper Extremity"},
    "NECK":      {"label": "Neck / Cervical",        "region": "Trunk"},
    "HIP":       {"label": "Hip / Pelvis",           "region": "Lower Extremity"},
    "MULTI":     {"label": "Multiple Body Parts",    "region": "Multiple"},
}

# ---------------------------------------------------------------------------
# INJURY CAUSE CATALOG  (NCCI codes subset)
# ---------------------------------------------------------------------------

INJURY_CAUSES = {
    "STRAIN_OE": {"label": "Strain / Overexertion"},
    "FALL_SAME": {"label": "Fall on Same Level"},
    "FALL_DIFF": {"label": "Fall to Different Level"},
    "CAUGHT":    {"label": "Caught In/Between/Under"},
    "REP_MOTION":{"label": "Repetitive Motion"},
    "MVA":       {"label": "Motor Vehicle Accident"},
    "STRUCK_BY": {"label": "Struck By Object"},
    "BURN":      {"label": "Burn / Scald"},
    "OCC_DIS":   {"label": "Occupational Disease"},
    "CUT_PUNC":  {"label": "Cut / Puncture / Scrape"},
}

# ---------------------------------------------------------------------------
# EMPLOYER NAICS GROUPS
# ---------------------------------------------------------------------------

EMPLOYER_GROUPS = {
    "WAREHOUSE":     {"label": "Warehouse / Logistics",    "naics": "493"},
    "RETAIL":        {"label": "Retail / Hospitality",     "naics": "44-45"},
    "CONSTRUCTION":  {"label": "Construction",             "naics": "23"},
    "CLERICAL":      {"label": "Clerical / Office",        "naics": "561"},
    "MANUFACTURING": {"label": "Manufacturing",            "naics": "31-33"},
    "HEALTHCARE":    {"label": "Healthcare Support",       "naics": "621"},
    "TRANSPORT":     {"label": "Transportation",           "naics": "484"},
    "FOOD_SVC":      {"label": "Food Service",             "naics": "722"},
}

# ---------------------------------------------------------------------------
# SUB-TRAJECTORY STATE MACHINES
# Each sub-trajectory is an ordered list of stage codes.
# Branches are expressed as separate sub-trajectories within a cohort.
# duration_override: (mean, std, min, max) — overrides STAGE_CATALOG default
# ---------------------------------------------------------------------------

@dataclass
class SubTrajectory:
    """A deterministic claim lifecycle path."""
    code: str                              # e.g. "A1"
    cohort: str                            # e.g. "A"
    label: str
    stages: List[str]                      # ordered stage codes
    cost_range: Tuple[int, int]            # (min_total_paid, max_total_paid)
    body_part: str
    injury_cause: str
    employer_group: str
    attorney_probability: float            # 0.0–1.0
    ncm_probability: float
    surgery_involved: bool
    notes: str = ""


SUB_TRAJECTORIES: Dict[str, SubTrajectory] = {

    # ========================================================================
    # COHORT A — Lumbar Strain, Warehouse/Logistics
    # ========================================================================

    "A1": SubTrajectory(
        code="A1", cohort="A",
        label="Lumbar — Quick Recovery (Medical Only)",
        stages=["FROI_00","TRIAGE","INVEST","DELAY_NTC","ACCEPTED",
                "MED_TX","PT","RTW_MOD","CLOSED_FN"],
        cost_range=(4_000, 15_000),
        body_part="LUMBAR", injury_cause="STRAIN_OE",
        employer_group="WAREHOUSE",
        attorney_probability=0.05, ncm_probability=0.10,
        surgery_involved=False,
        notes="4–8 week PT, full RTW, minimal indemnity"
    ),

    "A2": SubTrajectory(
        code="A2", cohort="A",
        label="Lumbar — Extended Conservative Care",
        stages=["FROI_00","TRIAGE","INVEST","DELAY_NTC","ACCEPTED",
                "TTD_START","MED_TX","PT","IME_ORD","IME_COMP",
                "MMI","PPD_RATE","RTW_MOD","CLOSED_FN"],
        cost_range=(25_000, 60_000),
        body_part="LUMBAR", injury_cause="STRAIN_OE",
        employer_group="WAREHOUSE",
        attorney_probability=0.20, ncm_probability=0.30,
        surgery_involved=False,
        notes="12–20 week PT, RTW with restrictions, mild PPD rating"
    ),

    "A3": SubTrajectory(
        code="A3", cohort="A",
        label="Lumbar — Surgical Path",
        stages=["FROI_00","TRIAGE","INVEST","DELAY_NTC","ACCEPTED",
                "TTD_START","MED_TX","PT","IME_ORD","IME_COMP",
                "SURGERY","POST_SURG","NCM","MMI","PPD_RATE",
                "SETTLE","CLOSED_FN"],
        cost_range=(80_000, 180_000),
        body_part="LUMBAR", injury_cause="STRAIN_OE",
        employer_group="WAREHOUSE",
        attorney_probability=0.40, ncm_probability=0.60,
        surgery_involved=True,
        notes="MRI → spine consult → discectomy/fusion → 6-9 month recovery"
    ),

    "A4": SubTrajectory(
        code="A4", cohort="A",
        label="Lumbar — Disputed / Litigated",
        stages=["FROI_00","TRIAGE","INVEST","DELAY_NTC","ACCEPTED",
                "TTD_START","MED_TX","IME_ORD","IME_COMP",
                "QME_ORD","QME_COMP","MMI","PPD_RATE",
                "LITIGATION","MEDIATION","STIP","CLOSED_FN"],
        cost_range=(60_000, 140_000),
        body_part="LUMBAR", injury_cause="STRAIN_OE",
        employer_group="WAREHOUSE",
        attorney_probability=0.95, ncm_probability=0.25,
        surgery_involved=False,
        notes="IME conflicts with treating physician, QME (CA), eventual stipulation"
    ),

    "A5": SubTrajectory(
        code="A5", cohort="A",
        label="Lumbar — Catastrophic (Failed Surgery / PTD)",
        stages=["FROI_00","TRIAGE","INVEST","DELAY_NTC","ACCEPTED",
                "TTD_START","MED_TX","IME_ORD","IME_COMP",
                "SURGERY","POST_SURG","TTD_REIN","NCM",
                "QME_ORD","QME_COMP","MMI","PPD_RATE",
                "LITIGATION","SETTLE","CLOSED_FN"],
        cost_range=(250_000, 420_000),
        body_part="LUMBAR", injury_cause="STRAIN_OE",
        employer_group="WAREHOUSE",
        attorney_probability=1.0, ncm_probability=0.70,
        surgery_involved=True,
        notes="Failed surgery, complications, permanent total or large C&R"
    ),

    # ========================================================================
    # COHORT B — Knee Injury, Retail/Hospitality
    # ========================================================================

    "B1": SubTrajectory(
        code="B1", cohort="B",
        label="Knee — Arthroscopic, Quick RTW",
        stages=["FROI_00","TRIAGE","INVEST","ACCEPTED",
                "TTD_START","MED_TX","SURGERY","POST_SURG",
                "PT","RTW_MOD","CLOSED_FN"],
        cost_range=(8_000, 45_000),
        body_part="KNEE", injury_cause="FALL_SAME",
        employer_group="RETAIL",
        attorney_probability=0.10, ncm_probability=0.20,
        surgery_involved=True,
        notes="Arthroscopic repair, 3-4 month recovery, full RTW"
    ),

    "B2": SubTrajectory(
        code="B2", cohort="B",
        label="Knee — ACL Reconstruction, Extended Rehab",
        stages=["FROI_00","TRIAGE","INVEST","ACCEPTED",
                "TTD_START","MED_TX","IME_ORD","IME_COMP",
                "SURGERY","POST_SURG","NCM","PT","MMI","PPD_RATE",
                "RTW_MOD","CLOSED_FN"],
        cost_range=(45_000, 120_000),
        body_part="KNEE", injury_cause="FALL_SAME",
        employer_group="RETAIL",
        attorney_probability=0.30, ncm_probability=0.50,
        surgery_involved=True,
        notes="ACL reconstruction, 6-month rehab, partial permanent restrictions"
    ),

    "B3": SubTrajectory(
        code="B3", cohort="B",
        label="Knee — ACL + Complications / Retraining",
        stages=["FROI_00","TRIAGE","INVEST","ACCEPTED",
                "TTD_START","MED_TX","SURGERY","POST_SURG",
                "TTD_REIN","NCM","QME_ORD","QME_COMP","MMI",
                "LITIGATION","SETTLE","CLOSED_FN"],
        cost_range=(100_000, 200_000),
        body_part="KNEE", injury_cause="FALL_SAME",
        employer_group="RETAIL",
        attorney_probability=0.80, ncm_probability=0.60,
        surgery_involved=True,
        notes="ACL with complications, permanent restrictions, vocational retraining"
    ),

    # ========================================================================
    # COHORT C — Carpal Tunnel / Repetitive Motion, Clerical/Manufacturing
    # ========================================================================

    "C1": SubTrajectory(
        code="C1", cohort="C",
        label="Carpal Tunnel — Accepted Occupational",
        stages=["FROI_00","TRIAGE","INVEST","DELAY_NTC","ACCEPTED",
                "MED_TX","PT","SURGERY","POST_SURG","RTW_MOD",
                "MMI","PPD_RATE","CLOSED_FN"],
        cost_range=(10_000, 50_000),
        body_part="WRIST", injury_cause="REP_MOTION",
        employer_group="CLERICAL",
        attorney_probability=0.15, ncm_probability=0.20,
        surgery_involved=True,
        notes="Causation accepted, carpal tunnel release, modified duty"
    ),

    "C2": SubTrajectory(
        code="C2", cohort="C",
        label="Carpal Tunnel — Contested Causation",
        stages=["FROI_00","TRIAGE","INVEST","DELAY_NTC","INVEST",
                "IME_ORD","IME_COMP","QME_ORD","QME_COMP",
                "ACCEPTED","MED_TX","SURGERY","POST_SURG",
                "MMI","MEDIATION","STIP","CLOSED_FN"],
        cost_range=(30_000, 120_000),
        body_part="WRIST", injury_cause="REP_MOTION",
        employer_group="CLERICAL",
        attorney_probability=0.70, ncm_probability=0.30,
        surgery_involved=True,
        notes="Occupational disease dispute, IME/QME battle, eventual stipulation"
    ),

    # ========================================================================
    # COHORT D — Shoulder Rotator Cuff, Construction/Manufacturing
    # ========================================================================

    "D1": SubTrajectory(
        code="D1", cohort="D",
        label="Shoulder — Rotator Cuff Repair, Good Recovery",
        stages=["FROI_00","TRIAGE","INVEST","ACCEPTED",
                "TTD_START","MED_TX","IME_ORD","IME_COMP",
                "SURGERY","POST_SURG","NCM","PT","MMI",
                "PPD_RATE","RTW_MOD","CLOSED_FN"],
        cost_range=(20_000, 90_000),
        body_part="SHOULDER", injury_cause="STRAIN_OE",
        employer_group="CONSTRUCTION",
        attorney_probability=0.25, ncm_probability=0.50,
        surgery_involved=True,
        notes="Standard rotator cuff repair, predictable 6-month recovery"
    ),

    "D2": SubTrajectory(
        code="D2", cohort="D",
        label="Shoulder — Re-injury / Complications",
        stages=["FROI_00","TRIAGE","INVEST","ACCEPTED",
                "TTD_START","MED_TX","SURGERY","POST_SURG",
                "RTW_MOD","TTD_REIN","NCM","IME_ORD","IME_COMP",
                "QME_ORD","QME_COMP","MMI","LITIGATION",
                "SETTLE","CLOSED_FN"],
        cost_range=(100_000, 260_000),
        body_part="SHOULDER", injury_cause="STRAIN_OE",
        employer_group="CONSTRUCTION",
        attorney_probability=0.85, ncm_probability=0.65,
        surgery_involved=True,
        notes="Re-injury after RTW attempt, protracted dispute, large settlement"
    ),

    # ========================================================================
    # COHORT E — Background / Mixed (multiple sub-types collapsed into one
    #             lightweight trajectory; randomized per-claim)
    # ========================================================================

    "E_MINOR": SubTrajectory(
        code="E_MINOR", cohort="E",
        label="Background — Minor / Medical Only",
        stages=["FROI_00","TRIAGE","ACCEPTED","MED_TX","CLOSED_FN"],
        cost_range=(500, 8_000),
        body_part="MULTI", injury_cause="STRUCK_BY",
        employer_group="RETAIL",
        attorney_probability=0.05, ncm_probability=0.02,
        surgery_involved=False,
        notes="Low-severity background claim — the haystack"
    ),

    "E_MID": SubTrajectory(
        code="E_MID", cohort="E",
        label="Background — Moderate",
        stages=["FROI_00","TRIAGE","INVEST","ACCEPTED",
                "TTD_START","MED_TX","PT","MMI","CLOSED_FN"],
        cost_range=(8_000, 40_000),
        body_part="MULTI", injury_cause="FALL_SAME",
        employer_group="MANUFACTURING",
        attorney_probability=0.12, ncm_probability=0.10,
        surgery_involved=False,
        notes="Mid-severity background claim"
    ),
}

# Count how many claims to generate per sub-trajectory
COHORT_COUNTS = {
    "A1": 25, "A2": 20, "A3": 15, "A4": 12, "A5": 8,
    "B1": 20, "B2": 22, "B3": 18,
    "C1": 28, "C2": 22,
    "D1": 28, "D2": 22,
    "E_MINOR": 90, "E_MID": 70,
}
# Total: 400 claims

# ---------------------------------------------------------------------------
# HERO CLAIM SPECIFICATIONS
# ---------------------------------------------------------------------------

HERO_CLAIMS = [
    {
        "hero_id": "CLM-HERO-01",
        "sub_trajectory": "A4",
        "status": "OPEN",
        "truncate_at_stage": "IME_ORD",   # claim is currently at this stage
        "days_elapsed": 98,
        "current_reserve": 25_000,
        "talk_track": (
            "Open lumbar strain, 14 weeks post-DOI. Currently at IME Ordered. "
            "Similar closed claims forked hard: those who got NCM + adjuster reassignment "
            "settled ~$55K; those who went to litigation averaged $180K. "
            "The differentiator is visible in the graph neighborhood."
        ),
    },
    {
        "hero_id": "CLM-HERO-02",
        "sub_trajectory": "D1",
        "status": "OPEN",
        "truncate_at_stage": "POST_SURG",
        "days_elapsed": 90,
        "current_reserve": 55_000,
        "talk_track": (
            "Open shoulder rotator cuff, day 90 post-DOI, just finished surgery. "
            "Similar closed claims cluster tightly at $65–85K, "
            "with one high-cost outlier subgroup correlated with a specific high-billing PT provider."
        ),
    },
    {
        "hero_id": "CLM-HERO-03",
        "sub_trajectory": "A5",
        "status": "CLOSED",
        "truncate_at_stage": None,
        "days_elapsed": 820,
        "current_reserve": 0,
        "talk_track": (
            "Closed catastrophic lumbar claim, settled at $310K. "
            "Compare to other A5 claims: those with NCM enrolled before week 8 "
            "averaged $265K; those without NCM averaged $370K. "
            "Reserve staircase shows 4 step-ups — the IME finding was the inflection point."
        ),
    },
    {
        "hero_id": "CLM-HERO-04",
        "sub_trajectory": "C2",
        "status": "OPEN",
        "truncate_at_stage": "QME_ORD",
        "days_elapsed": 142,
        "current_reserve": 45_000,
        "talk_track": (
            "Open carpal tunnel dispute, QME just ordered. "
            "In-progress similar claims show 70% will go to mediation; "
            "the 30% that resolve here are those with defense-side QME + no attorney."
        ),
    },
    {
        "hero_id": "CLM-HERO-05",
        "sub_trajectory": "A4",
        "status": "CLOSED",
        "truncate_at_stage": None,
        "days_elapsed": 395,
        "current_reserve": 0,
        "talk_track": (
            "GOOD OUTCOME comparator for HERO-01. "
            "Same lumbar / IME trajectory but NCM enrolled week 6, adjuster reassigned. "
            "Settled at $48K. Use as the 'what could have been' panel."
        ),
    },
    {
        "hero_id": "CLM-HERO-06",
        "sub_trajectory": "A4",
        "status": "CLOSED",
        "truncate_at_stage": None,
        "days_elapsed": 560,
        "current_reserve": 0,
        "talk_track": (
            "BAD OUTCOME comparator for HERO-01. "
            "Same lumbar / IME trajectory, no NCM, no reassignment, went to litigation. "
            "Settled at $172K. Side-by-side with HERO-05 makes the intervention value concrete."
        ),
    },
    {
        "hero_id": "CLM-HERO-07",
        "sub_trajectory": "B2",
        "status": "OPEN",
        "truncate_at_stage": "PT",
        "days_elapsed": 210,
        "current_reserve": 75_000,
        "talk_track": (
            "Open knee ACL, in physical therapy post-reconstruction. "
            "Similar claims: those with specialist PT provider averaged 185 days to RTW; "
            "those with generalist PT averaged 240 days. Provider matters here."
        ),
    },
    {
        "hero_id": "CLM-HERO-08",
        "sub_trajectory": "D1",
        "status": "CLOSED",
        "truncate_at_stage": None,
        "days_elapsed": 320,
        "current_reserve": 0,
        "talk_track": (
            "ANCHOR comparator for HERO-02. "
            "Closed shoulder D1, settled at $78K after NCM + standard PT provider. "
            "Trajectory aligns perfectly with HERO-02's first 90 days."
        ),
    },
]

# ---------------------------------------------------------------------------
# RESERVE TRIGGER RULES  (which stages reset the reserve)
# Tuples of (stage_code, reserve_multiplier_of_initial, narrative)
# These are applied during event chain generation.
# ---------------------------------------------------------------------------

RESERVE_TRIGGERS = {
    "ACCEPTED":  (1.0,  "Initial reserve set at acceptance"),
    "IME_ORD":   (1.4,  "Reserve bumped on IME order — exposure uncertainty"),
    "SURGERY":   (2.5,  "Reserve step-up on surgery authorization"),
    "TTD_REIN":  (2.0,  "Reserve increased on re-injury / TTD reinstatement"),
    "QME_ORD":   (1.6,  "Reserve adjusted on QME order (CA dispute signal)"),
    "LITIGATION":(3.5,  "Reserve jump on litigation filing"),
    "MMI":       (1.0,  "Reserve recalibrated at MMI — final picture"),
    "SETTLE":    (0.95, "Reserve finalized at settlement"),
    "STIP":      (0.95, "Reserve finalized at stipulated award"),
}

# ---------------------------------------------------------------------------
# DOCUMENT STUBS  (which stages generate a Document node)
# ---------------------------------------------------------------------------

DOCUMENT_TRIGGERS = {
    "FROI_00":   ("FROI Report",          "First report of injury filed by employer"),
    "IME_COMP":  ("IME Report",           "Independent medical examination findings"),
    "QME_COMP":  ("QME Report",           "Qualified medical evaluation (CA)"),
    "SURGERY":   ("Surgery Auth Letter",  "Authorization for surgical procedure"),
    "MMI":       ("MMI Declaration",      "Maximum medical improvement letter"),
    "LITIGATION":("Complaint Filed",      "Legal complaint / application for adjudication"),
    "SETTLE":    ("Settlement Agreement", "Compromise and release agreement"),
    "STIP":      ("Stipulated Award",     "Stipulated findings and award"),
}
