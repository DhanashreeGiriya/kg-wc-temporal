# Knowledge Graph Demo for US P&C Workers' Compensation: Deep Research Brief

This brief consolidates research to tighten the business case, backend implementation, and frontend UX of a Streamlit + Neo4j AuraDB demo pitching Knowledge Graph (KG) adoption to US P&C carriers. It is organized to feed directly into the next-phase build plan. Each section ends with concrete, "demo-safe vs. production-grade" recommendations and identified open questions.

---

## 1. Workers' Compensation Lifecycle and US Industry Practices

### 1.1 IAIABC EDI Release 3.1 — FROI/SROI Maintenance Type Codes (MTCs)

The IAIABC Claims Release 3.1 standard is the de facto reporting backbone for US WC claims. State jurisdictions (CA WCIS, NY WCB, MN DLI, ME WCB, TN BWC, NE NWCC, etc.) publish Element Requirement Tables and Edit Matrix Tables based on it. The full Implementation Guide is paywalled by IAIABC ($295 for non-members), but the MTC codes used in transactions are documented across state guides.

Key MTCs to use as `Stage` catalog nodes (FROI = First Report of Injury; SROI = Subsequent Report of Injury):

- **FROI MTCs**
 - **00 — Original**: First report of injury filed by claims administrator
 - **02 — Change**: Updates non-error fields (e.g., correcting date of injury)
 - **04 — Denial**: Denial of compensability
 - **AU — Acquired**: Existing claim transferred to a new claims administrator
 - **CO — Correction**: Correction in response to a TE (Transaction Accepted with Errors) acknowledgment
 - **UR — Upon Request**: Upon jurisdiction request (e.g., MN)
- **SROI MTCs (indemnity-relevant subset)**
 - **IP — Initial Payment**: First indemnity payment
 - **AP — Acquired Payment**: First payment by a new administrator on an acquired claim
 - **EP — Employer Paid**: Initial payment made by the employer rather than carrier
 - **PY — Payment Report**: Subsequent indemnity payment update
 - **CA — Change in Benefit Amount/Type**
 - **CB — Change in Benefit Type**
 - **RB — Reinstatement of Benefits** (e.g., re-injury after RTW)
 - **SA — Sub-Annual / periodic payment** (legacy in some jurisdictions; not accepted in CA)
 - **PD — Partial Denial** (4P in some jurisdictions = specific benefit denial)
 - **SU — Suspension of Benefits**
 - **SX — Suspension with reason code** (e.g., S8 = jurisdiction change)
 - **FN — Final Report**: Claim closed; cumulative payments to date
 - **AN — Annual Report** (cumulative non-indemnity payments for medical-only follow-up)
 - **QT — Quarterly Report** (used in some jurisdictions like TN if claim still open 90 days post-DOI)

**Realistic typical sequencing for an indemnity claim**: `FROI 00 → SROI IP → SROI PY (recurring) → SROI CA (e.g., wage rate corrected) → SROI SU (RTW attempt) → SROI RB (re-injury reinstatement) → SROI PY → SROI FN`. With litigation, `SROI 04` (denial) or `SROI PD` may inject early; with disputes, `SROI 02` corrections appear throughout. **This sequence is the "trajectory string" the demo will compare via similarity.**

### 1.2 Realistic Stage Transitions Including Back-and-Forth

Real WC trajectories are not monotonic. The schema must accommodate:

- **MMI → IME dispute → Re-IME**: Maximum Medical Improvement (also called "Permanent and Stationary" / P&S in California) is the medical determination that further improvement is unlikely. The carrier or claimant can dispute via Independent Medical Examination (IME) or Qualified Medical Evaluator (QME, CA-specific). In CA the QME is state-assigned; in most states the IME is insurer-selected. A disputed MMI can re-open temporary benefits.
- **TTD → RTW (modified duty) → Re-injury → TTD (RB)**: Temporary Total Disability ends when the worker returns to work or reaches MMI. Re-injury or aggravation triggers `SROI RB`. Washington L&I data shows the probability of RTW within 12 weeks is 92.2%, dropping to 55.4% at 13–26 weeks, 32.2% at 52–65 weeks, and only 4.9% beyond 104 weeks — illustrating why duration matters.
- **TTD → TPD → TTD**: A worker may shift to Temporary Partial Disability (modified duty at reduced wages) and revert to TTD if condition worsens.
- **Litigation injection at any point**: Attorney representation flag can flip mid-claim, materially changing the trajectory.

### 1.3 Typical Stage Durations by Jurisdiction (top WC states)

These ranges are useful for synthetic data generation and as displayed "norms" in the demo:

- **California**: TTD capped at **104 compensable weeks within 5 years** for most injuries; certain catastrophic conditions (amputations, severe burns, chronic lung disease) extend to **240 weeks**. Maximum TTD weekly rate in 2023 = $1,619.15; minimum = $242.86 (annual SAWW adjustments). CA has the longest payouts in the US — 56% of accident-year medical payments are paid more than 3 years after injury (national average 33%); CA takes ~11 years to settle 95% of indemnity claims. Statutory employer investigation period: 90 days before presumption of compensability; first medical authorization within 1 day up to $10,000 cap.
- **Texas**: ~99,850 claims reported in 2020 (vs 73,628 in 2019). Claim outcome data via TDI's claim query tool; TX uniquely has non-subscriber employers.
- **New York**: Mandatory IAIABC R3.1; aggregate data on Open NY portal. Claim adjudication via WCB judges with ~9-12 months for fully litigated cases.
- **Florida**: 73,254 claims in 2020, average benefit ~$20,146; data portal at fldfs.com.

For the synthetic dataset, use **median durations** like: FROI to IP = 14 days; IP to first PY recurrence = 14 days (biweekly cadence required); IP to MMI = 90–270 days for soft-tissue; IP to MMI = 270–730 days for surgical cases; MMI to FN = 30–365 days depending on PD rating dispute.

### 1.4 Reserve Setting and Adjustment Cadence

- **Initial reserve** is set by the adjuster within days of FROI based on (a) "guesstimate" from prior similar claims or (b) statistical reserve = average cost of the cohort. SOX (Sarbanes-Oxley 2002) compels accurate reserves; carriers are obligated to maintain adequate ones (NAIC Model Audit Rule).
- **Re-reserve triggers**: changes in medical treatment duration, work status changes (RTW or off-work extension), MMI declaration, surgery authorization, attorney representation, IME/QME findings, comorbidity discovery.
- **"Stair-step" reserving** (many small adjustments) is an industry anti-pattern indicating the adjuster is not identifying exposures up front. Best practice is annual re-reserving of future medical with appropriate medical inflation rate (WC medical inflation typically exceeds group health).
- **Hodes & Feldblum (Casualty Actuarial Society)** analyze WC reserve uncertainty: regulators allocate **reserving risk charges** to cover both unanticipated random adverse development and reserve inadequacies. NAIC P&C RBC formula uses reserving risk charges by line of business; WC has higher charges than short-tail lines.
- **Cost of inaccurate reserves**: under-reserving → adverse development on prior accident years (US P&C industry added **$16B to prior years' liability loss estimates in 2024 reviews**; commercial liability lines have $62B of cumulative adverse development over the past decade — equivalent to two major hurricanes). Over-reserving → capital lock-up and the operational tendency to "stair-step" to a number that justifies paying out vs. defending.

### 1.5 Claims Leakage Statistics

- **EY P&C Claims Transformation practice (2024 assessment)**: Indemnity leakage represents **7%–14% of carriers' total claims spend**, driven by (1) inaccurate damage evaluations, (2) missed settlement opportunities, (3) inadequate liability/causation investigations, (4) ineffective litigation strategies.
- **Industry consensus range**: 5–10% of total claims spend (vcasoftware.com, getregure.com). For a carrier paying $500M annually, that's $25–50M of avoidable payments.
- **Hard vs. soft leakage**: Hard = paid on claims that shouldn't be covered (lapsed policy, non-compensable). Soft = overpayment on valid claims (medical billing errors, missed subrogation, payments after denial). Vendor leakage = third party.
- For WC specifically, leakage drivers include: missed NCM enrollment, sub-optimal adjuster assignment, late RTW intervention, missed subrogation, unmanaged litigation. **These are the levers the KG demo targets.**

### 1.6 Adjuster Caseload & Reassignment Effects

- Typical workers' compensation adjuster caseloads run **150–300 active claims** (e.g., NY Black Car Fund cited 300 per adjuster as their starting baseline). CLARA Analytics' Treatment Summary product is positioned around reducing this burden.
- Adjuster experience drives outcomes; CLARA's "Next Best Reasoning" and Risk Notes products are designed to "close the experience gap and allow every adjuster to manage their caseload with the consistency and acumen of a top performer."
- One CLARA customer (large US WC carrier) reported a **12.8x ROI** from their integrated claims intelligence; CLARA reports most customers exceed **500% ROI**. (Note: vendor-published, but useful benchmarks for the pitch.)
- CLARA describes performance scoring across attorneys (defense panel benchmarking) and providers (medical provider scoring) — graph-natural problems.

### 1.7 Nurse Case Management (NCM) Impact

- **Mitchell/Enlyte mPower data**: NCM engagement saves an average of **$6,100 per claim in medical and indemnity costs, 8:1 ROI**.
- **Time-to-NCM matters**: claims referred to case management at week 2 cost **18% more** than claims referred earlier (Enlyte).
- **Home Depot study**: nurse-managed shoulder surgery cases had median 50 lost workdays vs. 115 for matched cases without NCM; 28% reduction in paid medical when nurse involved.
- **Other peer-reviewed style figures cited**: 18% lower medical costs, 26% lower overall claim costs with NCM.

### 1.8 Litigation Rates and Cost Differential

- **CLARA Analytics white paper (50,840 closed indemnity cases, 11 years across 46 states)**:
 - Overall attorney involvement rate: **28%**
 - Mean total claim paid **without** attorney: **$15,936** (median $5,768)
 - Mean total claim paid **with** attorney: **$77,807** (median $48,385) — i.e., **~5x higher mean**
 - Mean claim duration: 305 days without attorney vs. **901 days with** attorney
 - Litigation drove **284% more lost-time days**; total claim expenses 200%+ higher
- **California-specific**: litigated WC claims cost over **7x** non-litigated (preferredinsurance/peiwc). With attorney involvement, TTD avg $30,319 vs. $5,598 without; PD avg $66,208 vs. $25,300 without.
- **Aon LAMBDA tool** uses NLP on claim notes to predict attorney involvement — same premise as the KG demo: structural patterns predict litigation.

### 1.9 Outcomes by Body Part / Injury Type (NCCI 2022–2023 data)

Average **lost-time** WC claim cost = **$47,316**. Above-average cost categories:

- **By cause**: motor vehicle ($91,433); burns ($64,973); falls/slips ($54,499); caught ($47,749).
- **By nature**: amputations ($125,058); other trauma ($68,231); fractures/crush/dislocation ($66,467); burns ($64,019).
- **By body part**: head/CNS ($90,043); multiple parts ($77,614); neck ($70,575); hip/thigh/pelvis ($66,634); leg ($61,977); arm/shoulders ($55,115).

For the **synthetic cohorts** described (lumbar strain warehouse, knee retail, carpal tunnel clerical, rotator cuff construction), use these to calibrate target severity bands and "expected ultimate" benchmarks.

### 1.10 "Creeping Catastrophic" Claims — Early Indicators

This is a major industry talking point and the best frame for capability (b). Key sources: Mark Walls (Safety National), Michael Stack (Amaxx), Insurance Thought Leadership, WCI360.

- **Concept**: A small fraction (5–10%) of claims drive 70–90% of total cost. These rarely look catastrophic at FROI; they start as a back, knee, or shoulder injury and escalate.
- **Window of opportunity**: by 6 months the trajectory is "entrenched." The actual leverage point is **the first 6 weeks**.
- **Documented early indicators** (these become the features for similarity / risk scoring):
 1. **Delayed reporting**: gap between DOI and first medical treatment is the strongest predictor of complexity.
 2. **Missed appointments / no-shows** in early treatment.
 3. **Comorbidities**: obesity, diabetes, mental health, opioid history.
 4. **Psychosocial "yellow flags"**: fear of re-injury, job dissatisfaction, low recovery expectation. Free public-domain screening tools: **Örebro/REBRO Short Form** and **PHQ-4** predict long-term disability with up to **89% accuracy** (per Stack/Amaxx).
 5. **Attorney involvement** appearing early.
 6. **Prior similar claim** by same claimant.
 7. **Specific provider patterns** (high-cost prescribers, surgical-leaning chiropractors).
 8. **Specific employer environment** (no RTW program, high turnover).

These factors translate naturally into graph features (multi-hop neighborhoods around Person → Provider → Employer → Attorney).

---

## 2. Claim Similarity & Predictive Analytics Business Case

### 2.1 ROI of Early Intervention / RTW Programs

- **Crawford & Company**: workers in RTW programs recover 3x faster; employers save **up to 70%** in claims costs.
- **Johns Hopkins 10-year study**: WC costs decreased **54%** over a decade with structured RTW; lost-time claims decreased **73%**; TTD days paid per 100 employees fell from 163 to 37.
- **Reemployability "Transition2Work" Program**: $16.07 ROI per $1 spent.
- **Washington State Stay-at-Work program**: $2.40 ROI per $1; 84% of claims close within 66 days.
- **WorkCare benchmarks**: structured RTW yields **3:1 to 6:1 ROI**.
- **IBI**: a 2:1 ROI in wage replacement reflects 16:1 when full productivity costs are counted.

### 2.2 Iceberg / Indirect Cost Model

- **Liberty Mutual / Harvard study**: every $1 of direct WC cost generates **~$2.12 in indirect costs** (lost productivity, replacement labor, training, admin). This is the "iceberg" framing for the pitch.
- For the carrier audience (vs. employer), the parallel iceberg is **reserve mis-estimation cost**: a 10% reserve error on a $50M open-claim portfolio = $5M of capital mis-allocation, plus adverse-development risk if under-reserved.

### 2.3 How Carriers Currently Identify "Similar Claims"

- **Rules-based segmentation** by ICD-10/body part/jurisdiction/severity tier — coarse and largely manual.
- **Basic clustering** in actuarial models (k-means on numeric features only).
- **Manual triage / experience-based pattern recognition** by senior adjusters or NCMs.
- **Vendor predictive scores** (CLARA Triage, Risk Notes, Claim Event Indicators; Aon LAMBDA; Origami; Mitchell) — these are mostly opaque ML models trained on closed-claim data. They produce a score, not an explainable cohort.
- **Limitations the KG addresses**:
 1. Cross-system joins (claim system + medical bill review + provider directory + legal panel + HR/employer data) are slow and lossy in SQL.
 2. Entity resolution (same provider under two NPIs, same attorney across firms) requires multi-hop linking.
 3. Trajectory-shape comparison is not a native SQL primitive.
 4. Explainability — adjusters can be shown the actual neighbor claims and the path that drove the score, not a black-box probability.

### 2.4 Vendor Case Studies (use for pitch credibility)

- **CLARA Analytics** customers include companies "from the top 25 global insurance carriers." Specific named carriers: **Foresight Commercial Insurance** (MGU; uses CLARA Triage), **Eastern Alliance / ProAssurance** (uses CLARAty.ai for reserve accuracy and admin burden), **Black Car Fund** (NY for-hire driver WC; targeting reserve accuracy at 300 claims/adjuster), **RAS / Dakota Group** (largest voluntary WC writer in South Dakota, Ward's 50). CLARA discloses **12.8x ROI** at one large WC carrier and **>500% ROI** broadly.
- **Travelers**: predictive analytics on auto body damage claims produced **20% reduction in claim cycle time, 18% lift in CSAT**.
- **Liberty Mutual**: AI models to predict property claims that exceed initial estimates produced a **30% reduction in reserve adjustments**.
- **USAA**: claims cycle time improved from 12.5 → 8.2 days; error rate 8% → 1.3%; manual cost $47 → $18 per claim, a **180% Year-1 ROI**.
- **Nationwide**: intelligent document processing on medical bills/police reports/repair estimates.
- (Caution: maplesage/etc. blogs aggregate these; many are vendor-self-reported. Frame as "industry benchmarks" rather than peer-reviewed.)

---

## 3. Knowledge Graph Value Proposition for Insurance

### 3.1 KG Adoption Patterns in Insurance

- **Neo4j's stated insurance use cases**: claims fraud, ghost-broker detection, account takeover, transaction fraud rings, customer 360.
- **Neo4j fraud reference architecture** uses Claimant, MedicalProfessional, Claim, Vehicle nodes with HAS_CLAIM/TREATED_BY/OWNS/INVOLVED_IN relationships and runs WCC, Louvain, k-NN, and FastRP for embedding-based similarity. The "Whiplash for Cash" graphgist is a publicly available demonstration.
- **Neo4j Graph Analytics for Snowflake** (announced 2024): brings 65+ graph algorithms (including k-NN over embeddings) directly into Snowflake without moving data — a useful talking point if the prospect is already a Snowflake shop.
- **2023 UK insurance fraud stat (frequently cited)**: £1.1 billion in detected fraudulent claims (4% YoY increase; 16% increase in count of detected fraudulent claims).

### 3.2 SQL vs. Cypher: Concrete "Hard in SQL, Trivial in Cypher" Examples

For the demo's "before/after" framing, use these:

- **3-hop friend-of-friend / shared-attorney**:
 ```sql
 -- SQL: 6 joins
 SELECT p4.name FROM person p1
 JOIN knows k1 ON p1.id=k1.person_id
 JOIN person p2 ON k1.knows_person_id=p2.id
 JOIN knows k2 ON p2.id=k2.person_id
 JOIN person p3 ON k2.knows_person_id=p3.id
 JOIN knows k3 ON p3.id=k3.person_id
 JOIN person p4 ON k3.knows_person_id=p4.id
 WHERE p1.name='jeff';
 ```
 ```cypher
 // Cypher: one line
 MATCH (p1:Person {name:'jeff'})-[:KNOWS*3]->(p4) RETURN p4.name
 ```
- **"Find all claimants who saw provider X, were represented by attorney Y, AND worked at employers in NAICS 484"** — natively a 4-hop traversal in the KG; in a relational warehouse it's ~5 joins plus a CTE per business rule.
- **Trajectory pattern matching**: `MATCH (c:Claim)-[:FIRST_EVENT]->(e1)-[:NEXT*]->(e2 {stage:'IME'})-[:NEXT*]->(e3 {stage:'TTD_REINSTATE'})` — detecting "MMI dispute followed by RB" is a trivial Cypher traversal; in SQL it requires recursive CTEs or window-function gymnastics over an event log.
- **Path comparison**: project two claims' event chains as ordered sequences; compute alignment in Python from the Cypher result. Pure SQL cannot easily return *paths*; it returns rows.

### 3.3 GraphRAG / LLM Angle for Claims

- **Microsoft GraphRAG** (open-source) uses LLM-extracted KGs to perform community-aware RAG; published cases show large lifts on multi-hop QA where vector RAG fails.
- **MDPI 2024/2025 study** ("Claim Knowledge Graph Construction and GraphRAG-Based Question-Answering System") — construction-claims domain but directly analogous: GraphRAG outperforms baseline LLM and vector RAG on "explain why this claim escalated" queries.
- **Neo4j Aura Agent** (March 2026 release, GA-ish) generates ontology-driven agents directly from AuraDB knowledge graphs using "agentic GraphRAG" combining vector search and graph queries with multi-hop reasoning. Strong demo talking point: **once you have the WC KG, you get an adjuster copilot for free**.
- **Concrete adjuster-facing query** for the demo: *"Show me 5 closed claims most similar to this open lumbar strain, with the dollar amounts and what went wrong/right in each."* Neo4j retrieves the subgraph, the LLM verbalizes it.

### 3.4 The "Data Product" Angle — KG as Foundation for Many Downstream Uses

Argue that the same WC claims KG enables, in priority order:

1. **Similarity-based reserve and trajectory benchmarking** (this demo).
2. **Adjuster routing** (assign next claim to adjuster whose closed-claim cohort best matches the new claim's profile).
3. **NCM triage** (which claims to enroll in NCM; CLARA-style).
4. **Fraud rings** (provider-attorney-claimant cliques; well-documented Neo4j use case).
5. **Subrogation discovery** (third-party liability via path traversal).
6. **Litigation prediction** (Aon LAMBDA-style).
7. **GraphRAG adjuster copilot** (natural-language Q&A over the KG).
8. **Defense panel and provider scoring** (CLARA-style).

This gives the CDO the "build once, monetize many times" pitch.

### 3.5 Common CDO Objections and Pre-emptive Answers

| Objection | Pre-empt in demo |
|---|---|
| "We already have a data warehouse / lakehouse." | The KG is **not a replacement** — it's a federated view layer purpose-built for relationship queries. Snowflake + Neo4j Graph Analytics for Snowflake is now a supported pattern (no data movement). |
| "Yet another data store to govern." | AuraDB is a fully-managed service; SOC 2/GDPR/CCPA compliant; 99.95% SLA. Show the "deploy in 5 minutes" story. |
| "Skills gap — nobody knows Cypher." | Cypher is being formalized as ISO **GQL**; AI assistants generate it reliably; show the Aura Agent demo. |
| "Doesn't scale." | Neo4j has documented 200M+ node deployments; AuraDB Pro ranges 1GB–128GB RAM, Business Critical to 512GB. For this PoC, AuraDB Free's 200K/400K limits are 1000x what we need. |
| "ML models work fine on tabular features." | They lose the relational signal. Show that adding graph embeddings (FastRP) improves a downstream classifier (cite Neo4j AuraDS + Vertex AI demo). |
| "Black-box ML risk for regulators." | KG-based similarity is **explainable by construction** — show me the 10 nearest neighbors and the path that connected them. NAIC Model Audit Rule audit trails are easy. |

---

## 4. Streamlit + Neo4j UI/UX for Executive Demos

### 4.1 Embedded Graph Viz Library Comparison

Practical Streamlit-compatible options, ranked for this demo:

| Library | Pros | Cons | Demo-safe? |
|---|---|---|---|
| **streamlit-agraph** (ChrisDelClea) | Native Streamlit component; built-in physics, node images, ConfigBuilder; returns clicked node ID for interaction | Maintenance pace slowed; some 2.0-era TripleStore APIs broken; capped at ~few hundred nodes for smooth physics | Yes — best for **focused subgraph** views (≤200 nodes) |
| **PyVis** (via `streamlit.components.v1.html`) | Very mature; rich physics; HTML export embeds cleanly; works with NetworkX directly | No two-way Python interactions (clicks don't return to Streamlit easily); larger graphs jitter | Yes — good fallback; **best for "static" hero-shot subgraphs** |
| **neo4j-viz / NVL (Neo4j's own python-graph-visualization)** | Official Neo4j wrapper around the Neo4j Visualization JS Library; supports Streamlit; `render_widget()` provides anywidget two-way sync | Newer (2024–2025); fewer community examples; harder to style than agraph | **Production-grade**; aligns the demo with Neo4j's own stack |
| **Neovis.js (raw)** | Direct Bolt-to-browser; closest to Neo4j Bloom aesthetic | Embedding into Streamlit is fragile (community thread documents empty placeholder issues); requires session-token plumbing | Not recommended for a 15–20-minute exec demo |
| **Plotly + NetworkX** | Plotly play nicely with Streamlit; great for highlighting trajectory paths | Less compelling visually for "graph reveal" moments; better for charts than networks | Use only for **secondary** charts (timelines, similarity heatmaps) |
| **D3 custom component** | Best aesthetics | Build cost not justified for a PoC | Skip |

**Recommendation**: Build with **streamlit-agraph** as the primary view; render with **neo4j-viz** for the "official" hero shot; reserve **PyVis** for static export to slides if connectivity fails on demo day.

### 4.2 Performance with 100–500 Visible Nodes

- streamlit-agraph & PyVis comfortably handle ~200 nodes with physics on; beyond ~500 nodes, disable physics or switch to hierarchical layout.
- Cache subgraph queries with `@st.cache_data(ttl=60)` keyed on (claim_id, k-neighbors, hop-depth).
- **Demo-safe pattern**: never render the full graph (300–500 claims × ~10 events × supporting nodes ≈ thousands of nodes). Always render a **focused subgraph** of: selected claim + its k similar claims + shared entities (provider, attorney, employer).

### 4.3 "Graph Reveal" Interaction Patterns

Take inspiration from Neo4j Bloom and from fraud detection demos that have closed deals:

1. **Anchor-first reveal**: start with a single claim node centered. On click, expand to (a) its event chain, then (b) its claimant/provider/employer entities, then (c) its k-similar neighbors. Each reveal triggered by a button or step in the scripted scenario.
2. **Animated path traversal**: highlight the `(:Claim)-[:FIRST_EVENT]->(:ClaimEvent)-[:NEXT*]->()` chain by sequentially coloring edges. streamlit-agraph supports edge color/width updates; combine with `time.sleep(0.4)` per step.
3. **Sub-pattern highlighting**: show the "shared provider" pattern by coloring all claims that connect through Dr. X red while dimming the rest. This is the canonical KG "aha" moment.
4. **Side-by-side trajectory comparison**: anchor claim's event chain on top, neighbor's on bottom, with vertical alignment lines connecting matched stages (similar to Smith-Waterman alignment visualization).

### 4.4 Color, Size, Shape Semantics

Standard insurance-domain encoding (use consistently throughout the demo):

- **Node color** by entity type: Claim = blue, Person/Claimant = orange, Provider = teal, Attorney = red, Employer = gray, Policy = purple, ClaimEvent = light yellow.
- **Node size** by total claim cost (log scale) — instantly communicates severity.
- **Node border**: solid for closed/FN claims, dashed for in-progress, thick red for litigated.
- **Edge color**: black for structural edges (HAS_CLAIMANT, ASSIGNED_TO_ADJUSTER); blue gradient for `:NEXT` (faded for old, bright for recent); green for `:CURRENT_EVENT`; red for `:DENIED_BY`.
- **Edge width** by similarity score on `:SIMILAR_TO` relationships.

### 4.5 Showing Cypher Without Overwhelming Non-Technical Viewers

- Use Streamlit's `st.expander("📜 The Cypher behind this view")` so the query is **available but not assertive**.
- Display each Cypher block via `st.code(query, language="cypher")` with a prominent **Copy** button.
- Pair every visualization with a one-line plain-English caption ("This finds all claims in the last 12 months that share the same provider AND attorney as the selected claim").
- For the data-leader audience, have a "Show me how this would be in SQL" toggle that displays the painful equivalent — drives home the value.

### 4.6 When to Use Graph vs. Subgraph vs. Table

- **Full graph view**: only at the opening "this is your portfolio" hero shot, force-directed and slowly rotating, with cohort coloring. Don't make the audience interact here.
- **Focused subgraph (10–30 nodes)**: the workhorse view for hero scenarios. Always centered on a single claim plus its neighborhood.
- **Tabular view (Streamlit `st.dataframe`)**: similarity ranked lists with claim ID, similarity score, severity, status, jurisdiction. Use for the exploratory workbench — claims-ops leaders are comfortable with rows.
- **Timeline view (Plotly Gantt or vertical milestone strip)**: the alignment view comparing trajectory of selected claim to a chosen neighbor. This is the "killer chart" for delay prediction.

### 4.7 Streamlit Patterns That Work for Exec Demos (and What Falls Flat)

Works:
- **Pre-cached "scenario" state**: clicking a hero scenario button loads a pre-computed result; never wait on a live algorithm in front of a CDO.
- **Sidebar with scripted scenario buttons** plus a separate "Exploratory workbench" page (`pages/` directory).
- **Big KPI tiles** at the top (`st.metric`) showing: portfolio size, % similar found, avg neighbor reserve, predicted reserve delta. Executives anchor on numbers.
- **Custom theme via `.streamlit/config.toml`** — match the prospect's brand colors.

Falls flat:
- **Live LLM calls** during the demo without retry/fallback — kills momentum.
- **Excessive widgets** in the workbench — pick 4 levers max (k, similarity threshold, cohort filter, hop-depth).
- **Default Streamlit aesthetics** — non-technical audiences silently judge. Spend the hour on a clean theme + custom font.
- **Loading the full graph database into memory at app startup**.

---

## 5. Trajectory Similarity Algorithms

### 5.1 Method Comparison for Categorical Event Sequences

Treat each claim's stage progression as a string over an alphabet of MTC codes (~30 symbols).

| Method | Strengths | Weaknesses | Fit for this demo |
|---|---|---|---|
| **Longest Common Subsequence (LCS / LCSS)** | Robust to insertions/deletions; widely used for trajectory similarity (Vlachos 2002 origin); good for prefix/in-progress matching | Ignores temporal spacing; needs threshold for "match" | **Yes — primary algorithm for trajectory shape** |
| **Edit / Levenshtein distance (EDR)** | Symmetric; quantifies "how many edits to align"; intuitive for adjusters | Same unit cost ignores semantic distance between codes | Use as **secondary metric** |
| **Smith-Waterman (local alignment)** | Finds *similar regions* between dissimilar overall sequences (Sha et al., NCBI PMC6921442); used for EHR patient similarity in published literature | Slightly more complex to explain | **Yes** — a great fit for "matching prefix" use case (b); use a substitution matrix (e.g., MMI vs P&S = match; IP vs PY = near-match; 04 vs FN = mismatch) |
| **Needleman-Wunsch (global alignment)** | Optimal global alignment of full trajectories | Less useful when one claim is mid-trajectory | Use only for closed-vs-closed (capability a) |
| **Dynamic Time Warping (DTW)** | Handles stage-duration similarity (warp time); battle-tested in time-series; tslearn & dtaidistance both fast | Requires numeric features (e.g., days at each stage); doesn't satisfy triangle inequality | **Yes — secondary axis ("pacing" component of the similarity score)** |
| **M&M / OTCS** | Designed for categorical multi-attribute trajectories | Less library support in Python; harder to explain | Skip for demo |

**Recommended hybrid score for the demo** (decomposable for explainability):

```
similarity(A, B) = w_demo · demographic_similarity        // Jaccard over BodyPart, Cause, NAICS, Jurisdiction
                + w_shape · normalized_LCS(events_A, events_B)
                + w_pace  · 1 / (1 + DTW(durations_A, durations_B))
                + w_graph · GDS_node_similarity_or_FastRP_cosine
```
Default weights 0.25 each, exposed as Streamlit sliders. Show each component score in a stacked bar — this is how you **decompose for exec audiences** ("they're 80% similar on demographics but only 40% similar on pacing — that's why we predict longer duration").

### 5.2 Python Library Choices

- **DTW**: `dtaidistance.dtw.distance_fast()` (C-backed, fastest) for pacing; `tslearn.metrics.dtw_path` if you want to *visualize* the alignment path (great for the demo).
- **LCS / Smith-Waterman**: roll your own (~30 lines of NumPy DP) or use `python-Levenshtein` for edit distance; `parasail` or `Bio.pairwise2` for SW with custom substitution matrices. Bio.pairwise2 is friendliest for the demo.
- **Jaccard / cosine on attribute sets**: `sklearn.metrics.pairwise`.

### 5.3 Neo4j GDS Path

**Critical caveat (open question / risk)**: Neo4j AuraDB **Free tier does not expose the GDS library**. GDS procedures are only available on **AuraDS** (a separate paid product) or on self-hosted Neo4j with the GDS plugin. This is documented in the Neo4j community forum where users hit `gds.graph.project` errors on Aura free, and is implicit in the AuraDS pricing page (Pro/Enterprise tiers only).

Implications:
- If the demo runs on **AuraDB Free**, GDS-based similarity (k-NN, FastRP, Node2Vec) must be done **client-side in Python**. Pull the relevant projection via Cypher, run the algorithm in `networkx` / `node2vec` / `scikit-learn`, write similarity edges back as `:SIMILAR_TO` relationships.
- Alternative: provision **AuraDS Professional** for the demo (paid; ~$0.14/hour for the small sizes; can pause). This gives you `gds.knn`, `gds.nodeSimilarity`, `gds.fastRP`, and `gds.node2vec` natively.
- **Recommendation**: Build similarity offline in Python at data-load time, persist as `:SIMILAR_TO {score, demo_score, shape_score, pace_score, graph_score}` edges. This is **demo-safe** (no live computation latency) and works on the free tier.

### 5.4 Embeddings (FastRP / Node2Vec / GraphSAGE)

- **For 300–500 claims, embeddings are likely overkill** for the headline algorithm, but they're a fantastic "wow" addition for the data-leader audience: project claims into 64-d FastRP space, run UMAP to 2D, and show that the cohorts cluster naturally with no labels. This is a 10-line scikit-learn snippet — high payoff per LOC.
- **Production-grade**: embeddings shine at >100K claims when raw feature engineering breaks down. For this demo, **show them as a teaser**, not the centerpiece.

### 5.5 Computational Tradeoffs

- **Pre-compute the pairwise similarity matrix at load time** (300×300 = 90K pairs; trivial in Python; <30 seconds even with Smith-Waterman). Persist top-k neighbors per claim as `:SIMILAR_TO` edges with score property.
- **On-demand recomputation** only when the user changes weight sliders in the workbench; recompute in-memory in <2 seconds (pre-computed component scores, just re-weight the linear combination).
- This split is the "demo-safe" pattern: hero scenarios use pre-computed edges; the workbench feels live.

### 5.6 Explaining Similarity to Non-Technical Audiences

Three explanatory layers:

1. **Single number** (the similarity score, 0–100%). Displayed as a colored progress bar.
2. **Decomposed bars**: Demographics / Trajectory shape / Pacing / Network context — each 0–100% with one-line tooltip.
3. **Witness evidence**: the actual aligned trajectory (Smith-Waterman path) and the actual shared entities (subgraph), so the adjuster can verify the claim "really is" similar.

This three-layer disclosure is well-supported by AI explainability literature and matches CLARA's "Risk Notes" framing.

---

## 6. Scenario Walkthrough Narrative Design

### 6.1 Optimal 15–20-Minute Demo Flow for Mixed Audience

A widely-used structure for graph database executive demos (drawn from Neo4j fraud detection demo templates and CLARA presentations):

1. **0:00–2:00 — The Pain (anchor in dollars)**: Open with the iceberg slide and three stats: 7–14% leakage (EY), $44K avg WC settlement (NSC 2024), 5x cost differential when litigated (CLARA). Frame: "Your senior adjuster knows in their gut that this claim looks like the worst one they handled in 2022 — but they can't search for it. We're going to make that searchable."
2. **2:00–4:00 — The Schema Reveal (orient the data audience)**: One slide of the WC KG schema diagram. Voice over: "Person, Provider, Employer, Attorney, Policy — all the entities you already have. The new thing is the event chain on each claim." Show the Cypher schema constraint script briefly; collapse it.
3. **4:00–9:00 — Hero Scenario 1 — Closed-to-Closed Similarity (capability a)**: Pick a closed lumbar strain warehouse claim that ended at $185K. Reveal its subgraph progressively. Run similarity. Show top 5 neighbors. Pull up #1 — same body part, different jurisdiction, $192K. Click into trajectory comparison: "they took the same path." This is the "audience leans forward" moment.
4. **9:00–14:00 — Hero Scenario 2 — In-progress Trajectory (capability b)**: Pick an open shoulder claim, day 45 post-DOI, currently reserved at $25K. Run prefix matching. Show 3 closed claims with the same first-45-days trajectory; their ultimate cost averaged $87K. **The reserve recommendation is to reset to $87K with high confidence.** Then show the proactive intervention angle: "of those 3, the 2 that did NCM enrollment closed for $45K; the 1 that didn't closed for $171K. Recommended action: enroll NCM today."
5. **14:00–17:00 — The Workbench (give them control)**: Brief tour of the exploratory workbench. Let the head of claims pick any claim and play. *Don't* try to script this — let it breathe.
6. **17:00–19:00 — Beyond Similarity (the data-product pitch)**: One slide listing the 8 downstream use cases (§3.4). "Same KG, same data, 7 more solutions." Hint at the GraphRAG adjuster copilot — show one Aura Agent screenshot if you have it.
7. **19:00–20:00 — Close**: 90-day pilot offer with success metrics defined upfront (reserve accuracy lift, time-to-NCM, etc.).

### 6.2 "Aha" Moments to Engineer

- **Aha 1**: The graph zooms out to reveal that 4 of the highest-cost claims share the same orthopedic surgeon. (Network effect)
- **Aha 2**: Two claims look identical for the first 30 days, but one had NCM enrolled and closed at $40K while the other didn't and creep-catastrophic'd to $300K. (Intervention leverage)
- **Aha 3**: The trajectory visualization shows the in-progress claim's events aligning perfectly with a closed claim's first 60 days — the audience can *see* the prediction.

### 6.3 Common Demo Pitfalls (from technical-product demo literature & Neo4j's own guidance)

- **Going too deep too fast** on Cypher syntax. Cypher is shown only inside expanders.
- **Live data dependency**: never rely on a live algorithm or LLM API in front of execs. Pre-cache scenario state. Have a screen-recorded fallback video at the ready.
- **Graph viz that "explodes"** with 1000+ nodes — embarrassing. Always cap visible nodes.
- **No business framing**: showing graphs without dollar amounts loses claims-ops leaders. Every visual must answer "so what."
- **Skipping the "before"** — without contrasting to the SQL/warehouse status quo, the data leader can't quote the value to their CFO.
- **Not having a written runbook** of clicks for the demo operator — fumbling kills credibility.

### 6.4 Documented "Demos That Closed" Patterns

- Neo4j's published whiplash-for-cash fraud demo follows the pattern: *show the fraud ring as a table (boring) → show it as a graph (immediately legible)*. This is the proven framing.
- CLARA's case studies (Foresight, Eastern Alliance, Black Car Fund, RAS) consistently anchor on three numbers: claim cycle time reduction, reserve accuracy lift, and ROI multiple. Build the close around those exact three.

---

## 7. Schema and Data Model Details

### 7.1 Reserve as Node vs. Property (recommended: **node**)

The standard Neo4j time-series guidance (Jeff Tallman's widely-cited "Modeling Longitudinal/Time Series/Sequential Data in Neo4j" and the Neo4j temporal fraud blog) is to model time-varying values as **separate nodes connected by `:NEXT`** when:
- You need to query history (e.g., "show me how this reserve changed over the lifecycle").
- The value has its own metadata (who set it, why, source MTC).
- You need to attach the value to specific events.

**Recommendation**: Model reserve as `(:ReserveSnapshot {indemnity_amt, medical_amt, expense_amt, total_amt, set_at})` connected to the triggering `:ClaimEvent` via `:RESET_BY`, and chained `(:ReserveSnapshot)-[:NEXT_RESERVE]->(:ReserveSnapshot)`. The Claim has `:CURRENT_RESERVE` and `:INITIAL_RESERVE` shortcut pointers (matches the Stage / FIRST_EVENT / CURRENT_EVENT pattern already chosen).

This lets the demo say "the reserve was reset 4 times; here's the moment it jumped from $25K to $80K — it was triggered by the IME finding a herniated disc."

### 7.2 Documents (medical reports, IME reports, demand letters)

Two patterns from KG literature:

- **Property pattern**: store docs as JSON properties on the relevant ClaimEvent (`{document_uri, document_type}`). Simpler; fine for a 300-claim demo.
- **Node pattern**: `(:Document {uri, type, summary, text_embedding})` connected via `:GENERATED_BY` to the ClaimEvent and `:ABOUT` to the Claim. Enables vector search and GraphRAG.

**Recommendation**: For this demo, use the **node pattern** but keep it lightweight — one Document node per material event (FROI, IME, MMI, Demand Letter, Settlement). Add a stub `summary` text property and (optionally) a synthetic `text_embedding` (random vectors are fine for the demo's hero shot of vector + graph hybrid retrieval). This gives you a clean "GraphRAG-ready" schema without the cost of generating real text. The MDPI claim KG paper validates this construction-claims pattern.

### 7.3 FROI/SROI Submission Events vs. Stage Transitions

These are subtly different:
- The **submission** is the regulatory transmission to the jurisdiction (an audit trail).
- The **stage transition** is the business-state change (e.g., the claim went from "in-treatment" to "MMI").

**Recommendation**: Two related but distinct nodes:
- `(:ClaimEvent {event_type:'STAGE_TRANSITION', stage:'MMI', occurred_at})`
- `(:Submission {mtc:'PY', submitted_at, jurisdiction})` linked via `:DOCUMENTS` to the ClaimEvent

Most demos can collapse these into one `ClaimEvent` node with both properties (`stage`, `mtc`, `submitted_at`) for simplicity. Only split them out if the audience asks specifically about regulatory compliance — at which point you can say "yes, our schema separates the regulatory artifact from the business event."

### 7.4 APOC vs. Pure Cypher on AuraDB Free

- **AuraDB Free includes APOC Core (a subset)** — see the official "APOC support — Neo4j Aura" doc for the supported procedures list. Most data-loading helpers (`apoc.load.json`, `apoc.merge.node`, `apoc.create.relationship`, `apoc.periodic.iterate`, `apoc.text.*`, `apoc.coll.*`, `apoc.convert.*`) are available.
- **NOT available on Free**: `apoc.ml.*` (OpenAI embeddings — confirmed in GitHub issue #13324), most `apoc.export.*` to file system, custom procedures, the APOC Extended package.
- **Recommendation**: write the data load as pure Cypher using `UNWIND` over Python-prepared parameter lists (cleanest deployment story). Reserve APOC Core for things that pure Cypher can't do (`apoc.periodic.iterate` for batched merges if the dataset grows beyond ~5K nodes; `apoc.path.expandConfig` for variable-depth traversals if useful in queries).

### 7.5 Indexes and Constraints for AuraDB Free

Critical for performance even at 300-claim scale (and a nice "we did this right" detail for the data leader):

```cypher
// Uniqueness constraints (also create indexes)
CREATE CONSTRAINT claim_id        IF NOT EXISTS FOR (c:Claim)        REQUIRE c.claim_id IS UNIQUE;
CREATE CONSTRAINT person_id       IF NOT EXISTS FOR (p:Person)       REQUIRE p.person_id IS UNIQUE;
CREATE CONSTRAINT provider_id     IF NOT EXISTS FOR (p:Provider)     REQUIRE p.provider_id IS UNIQUE;
CREATE CONSTRAINT employer_id     IF NOT EXISTS FOR (e:Employer)     REQUIRE e.employer_id IS UNIQUE;
CREATE CONSTRAINT attorney_id     IF NOT EXISTS FOR (a:Attorney)     REQUIRE a.attorney_id IS UNIQUE;
CREATE CONSTRAINT policy_id       IF NOT EXISTS FOR (p:Policy)       REQUIRE p.policy_id IS UNIQUE;
CREATE CONSTRAINT insurer_id      IF NOT EXISTS FOR (i:Insurer)      REQUIRE i.insurer_id IS UNIQUE;
CREATE CONSTRAINT jurisdiction_id IF NOT EXISTS FOR (j:Jurisdiction) REQUIRE j.code IS UNIQUE;
CREATE CONSTRAINT bodypart_id     IF NOT EXISTS FOR (b:BodyPart)     REQUIRE b.code IS UNIQUE;
CREATE CONSTRAINT cause_id        IF NOT EXISTS FOR (c:InjuryCause)  REQUIRE c.code IS UNIQUE;
CREATE CONSTRAINT stage_id        IF NOT EXISTS FOR (s:Stage)        REQUIRE s.code IS UNIQUE;
CREATE CONSTRAINT event_id        IF NOT EXISTS FOR (e:ClaimEvent)   REQUIRE e.event_id IS UNIQUE;

// Range indexes for filter/sort
CREATE INDEX claim_status      IF NOT EXISTS FOR (c:Claim)      ON (c.status);
CREATE INDEX claim_doi         IF NOT EXISTS FOR (c:Claim)      ON (c.date_of_injury);
CREATE INDEX claim_total_paid  IF NOT EXISTS FOR (c:Claim)      ON (c.total_paid);
CREATE INDEX event_stage       IF NOT EXISTS FOR (e:ClaimEvent) ON (e.stage);
CREATE INDEX event_occurred_at IF NOT EXISTS FOR (e:ClaimEvent) ON (e.occurred_at);
CREATE INDEX similar_score     IF NOT EXISTS FOR ()-[r:SIMILAR_TO]-() ON (r.score);
```

These uniqueness constraints are essential to make `MERGE` operations idempotent (re-runnable demo loads).

### 7.6 Final Recommended Schema Sketch

```
Catalog (small, static):
  (:Stage {code, label, category})    // FROI_00, SROI_IP, SROI_PY, MMI, IME, RTW, ...
  (:BodyPart {code, label, region})    // WCIO Part of Body codes
  (:InjuryCause {code, label})         // WCIO Cause of Injury codes
  (:Jurisdiction {code, name})         // CA, NY, TX, FL, ...

Master entities:
  (:Person {person_id, role:'CLAIMANT'|'ADJUSTER', dob, gender, tenure_years, ...})
  (:Provider {provider_id, npi, specialty, performance_score})
  (:Employer {employer_id, naics, size_band})
  (:Attorney {attorney_id, firm, plaintiff_or_defense})
  (:Insurer {insurer_id, name})
  (:Policy {policy_id, effective_date, expiration_date})

Claim & event chain:
  (:Claim {claim_id, date_of_injury, status:'OPEN'|'CLOSED', total_paid, current_reserve, jurisdiction_code, ...})
    -[:HAS_CLAIMANT]-> (:Person)
    -[:ASSIGNED_TO]-> (:Person {role:'ADJUSTER'})
    -[:OCCURRED_AT_EMPLOYER]-> (:Employer)
    -[:UNDER_POLICY]-> (:Policy) -[:ISSUED_BY]-> (:Insurer)
    -[:IN_JURISDICTION]-> (:Jurisdiction)
    -[:INVOLVES_BODYPART]-> (:BodyPart)
    -[:CAUSED_BY]-> (:InjuryCause)
    -[:REPRESENTED_BY]-> (:Attorney)        // optional
    -[:FIRST_EVENT]-> (:ClaimEvent)
    -[:CURRENT_EVENT]-> (:ClaimEvent)        // shortcut pointer

  (:ClaimEvent {event_id, occurred_at, mtc, narrative})
    -[:OF_STAGE]-> (:Stage)
    -[:NEXT]-> (:ClaimEvent)
    -[:TREATED_BY]-> (:Provider)             // when applicable
    -[:RESET_RESERVE]-> (:ReserveSnapshot)   // when applicable
    -[:REFERENCES_DOC]-> (:Document)         // when applicable

  (:ReserveSnapshot {indemnity, medical, expense, total, set_at})
    -[:NEXT_RESERVE]-> (:ReserveSnapshot)

  (:Document {doc_id, type, summary, embedding})

Similarity (pre-computed, written back from Python):
  (:Claim)-[:SIMILAR_TO {score, demo_score, shape_score, pace_score, graph_score, computed_at}]->(:Claim)
```

This keeps the schema **legible on a single slide** while having enough structure to support all hero scenarios and downstream use cases.

---

## Cross-Cutting Risks and Open Questions

1. **GDS not available on AuraDB Free** is the single biggest implementation constraint. Either (a) compute similarity client-side in Python (recommended), or (b) provision AuraDS Professional for the demo (paid; pause when not in use). Decide before build kickoff.
2. **300–500 claims is a small N for embeddings** to shine. FastRP/Node2Vec demos will look noisy. Use embeddings as a teaser only; lead with handcrafted decomposable similarity.
3. **Synthetic data fidelity** — adjusters will sniff out unrealistic data within seconds. Use real WCIO Body Part codes, real NCCI severity bands, realistic biweekly indemnity payment cadence, and validated MTC sequences. Have a domain SME pressure-test the synthetic dataset before exec demos.
4. **Vendor benchmark caveats** — most ROI numbers (CLARA 12.8x, Mitchell $6,100/8:1 NCM, Crawford 70% claim cost reduction with RTW) are vendor-published. Frame as "industry benchmarks" and lean more heavily on academic/CAS-published numbers (Hodes/Feldblum on reserves, NCCI cost data, EY 7–14% leakage) for the most quoted figures.
5. **Live LLM/GraphRAG demos are high-risk** for executive sessions. Show GraphRAG as a screenshot-and-talk-through unless network/API reliability is bulletproof. Aura Agent (March 2026 release) is promising but still early; presenting it as a roadmap item is safer than presenting it as live capability.
6. **GraphRAG vs. straight retrieval** — research literature (e.g., "Empowering GraphRAG with Knowledge Filtering and Integration", arXiv 2503.13804) shows that GraphRAG can over-rely on retrieved context vs. LLM intrinsic knowledge. Don't oversell — position as "deterministic, explainable retrieval over your KG."

---

## Quick-Reference: Numbers to Quote in the Pitch (with Source Tier)

| Stat | Value | Source quality |
|---|---|---|
| US P&C claims leakage range | **7–14% of total spend** | Tier-1 (EY 2024 assessment) |
| Industry leakage consensus | **5–10%** | Tier-2 (vendor blogs aggregating EY/Aon/etc.) |
| Avg lost-time WC claim cost (2022–23) | **$47,316** | Tier-1 (NCCI via NSC Injury Facts) |
| Avg WC settlement (2024) | **$44,179** | Tier-1 (NSC) |
| Litigated vs non-litigated WC claim cost | **$77,807 vs $15,936 mean (~5x)** | Tier-1 (CLARA white paper, 50,840 claims, 11 yrs) |
| Litigated CA claims | **>7x non-litigated** | Tier-2 (CA-specific) |
| NCM ROI | **8:1 ROI; ~$6,100 saved/claim** | Tier-2 (Mitchell/Enlyte) |
| NCM late-referral penalty | **+18% cost when referred at week 2** | Tier-2 (Enlyte) |
| RTW program ROI range | **3:1 to 6:1** | Tier-2 (WorkCare); some sources up to 16:1 |
| 10-yr RTW outcome (Crawford/JHU) | **WC costs −54%, lost-time claims −73%** | Tier-2 (industry studies) |
| Iceberg: indirect-to-direct ratio | **$2.12 indirect per $1 direct** | Tier-1 (Liberty Mutual / Harvard) |
| Adverse loss development P&C | **$16B added in 2024 alone; $62B over decade** | Tier-1 (industry data) |
| Top-decile claims share of cost | **5–10% of claims = 70–90% of cost** | Tier-2 (Amaxx, repeated industry consensus) |
| Probability of RTW > 104 wks | **4.9%** | Tier-1 (WA L&I) |
| Psychosocial screening predictive accuracy | **Up to 89% (Örebro/PHQ-4)** | Tier-2 (Amaxx, citing screening tool literature) |
| AuraDB Free limits | **200K nodes / 400K relationships** | Tier-1 (Neo4j docs; some legacy sources cite 50K/175K — current is 200K/400K) |
| Travelers predictive analytics outcome | **−20% cycle time, +18% CSAT** | Tier-3 (vendor blog) |
| Liberty Mutual property AI | **−30% reserve adjustments** | Tier-3 (vendor blog) |
| CLARA WC carrier ROI | **12.8x** | Tier-3 (vendor self-published) |

(Tier-1 = primary regulator/actuarial; Tier-2 = trade press citing primary studies; Tier-3 = vendor self-published.)

---

This brief contains the substantive findings needed to drive the next phase: a detailed execution plan and code build for the Streamlit + Neo4j AuraDB Workers' Compensation similarity demo. The most consequential decisions to make immediately are (1) AuraDB Free vs. AuraDS Pro for the runtime, (2) lock the synthetic dataset cohort design with an SME, and (3) finalize the two hero scenarios (recommend: closed lumbar warehouse 5x severity differential; in-progress shoulder rotator cuff with NCM-vs-no-NCM divergence).