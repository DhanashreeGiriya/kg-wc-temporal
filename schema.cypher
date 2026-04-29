// ============================================================================
// WC Knowledge Graph — Schema Constraints & Indexes
// Run once on a fresh AuraDB instance before data generation.
// ============================================================================

// ----- Uniqueness constraints (also create indexes) -----
CREATE CONSTRAINT claim_id        IF NOT EXISTS FOR (c:Claim)            REQUIRE c.claim_id IS UNIQUE;
CREATE CONSTRAINT person_id       IF NOT EXISTS FOR (p:Person)           REQUIRE p.person_id IS UNIQUE;
CREATE CONSTRAINT provider_id     IF NOT EXISTS FOR (p:Provider)         REQUIRE p.provider_id IS UNIQUE;
CREATE CONSTRAINT employer_id     IF NOT EXISTS FOR (e:Employer)         REQUIRE e.employer_id IS UNIQUE;
CREATE CONSTRAINT attorney_id     IF NOT EXISTS FOR (a:Attorney)         REQUIRE a.attorney_id IS UNIQUE;
CREATE CONSTRAINT policy_id       IF NOT EXISTS FOR (p:Policy)           REQUIRE p.policy_id IS UNIQUE;
CREATE CONSTRAINT insurer_id      IF NOT EXISTS FOR (i:Insurer)          REQUIRE i.insurer_id IS UNIQUE;
CREATE CONSTRAINT stage_id        IF NOT EXISTS FOR (s:Stage)            REQUIRE s.code IS UNIQUE;
CREATE CONSTRAINT bodypart_id     IF NOT EXISTS FOR (b:BodyPart)         REQUIRE b.code IS UNIQUE;
CREATE CONSTRAINT cause_id        IF NOT EXISTS FOR (c:InjuryCause)      REQUIRE c.code IS UNIQUE;
CREATE CONSTRAINT event_id        IF NOT EXISTS FOR (e:ClaimEvent)       REQUIRE e.event_id IS UNIQUE;

// ----- Range indexes for filter/sort -----
CREATE INDEX claim_status      IF NOT EXISTS FOR (c:Claim)      ON (c.status);
CREATE INDEX claim_doi         IF NOT EXISTS FOR (c:Claim)      ON (c.date_of_injury);
CREATE INDEX claim_total_paid  IF NOT EXISTS FOR (c:Claim)      ON (c.total_paid);
CREATE INDEX event_stage       IF NOT EXISTS FOR (e:ClaimEvent) ON (e.stage);
CREATE INDEX event_occurred_at IF NOT EXISTS FOR (e:ClaimEvent) ON (e.occurred_at);
CREATE INDEX similar_score     IF NOT EXISTS FOR ()-[r:SIMILAR_TO]-() ON (r.score);
