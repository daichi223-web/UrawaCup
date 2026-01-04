# UrawaCup Consolidated Issues & Report

**Last Updated:** 2026-01-04
**Source Files:** `ISSUES.md`, `Issue/Issue.md`, `Issue/TechnicalDebtReport.md`, `Issue/ErrorAnalysis.md`

---

## 🚀 Active Issues (Open)

### Critical / Spec Gaps
- **[CRITICAL] Match API Schema Gap (Affected: Final Day)**
    - **Status**: ✅ Fixed (2026-01-04)
    - **Gap**: `Match` DB model has `referee_main`, `referee_assistant`, `venue_manager`, BUT `MatchResponse` and `MatchUpdate` Pydantic schemas do not.
    - **Fix**: Added `referee_main`, `referee_assistant`, `venue_manager` to both `MatchResponse` and `MatchUpdate` schemas.
- **[Issue #008] Result Approval Flow (Missing Phase: MIDDLE)**
    - **Status**: Open
    - **Gap**: Workflow for Venue Input -> HQ Approval does not exist.
    - **Action Plan**: Add `approval_status`, `approved_by` to Match model. Implement API.
- **[Issue #015] Service Worker / PWA Offline Support (Missing Phase: MAX)**
    - **Status**: Open (Manifest exists, SW missing)
    - **Action Plan**: Implement `sw.js`, offline cache strategy.
- **[Gap] Public View API**
    - **Status**: Open (Detected by Simulation)
    - **Gap**: Simulation showed `/public/*` endpoints are missing or return 404.
    - **Impact**: Public users cannot view standings/matches without login.
- **[T004] Venue Update Bug**
    - **Status**: Likely Fixed (Code Review)
    - **Analysis**: Backend uses `exclude_unset=True` and Frontend explicitly sends `false`. Logic appears correct.
- **[T011] Frontend Interaction**
    - **Status**: ✅ Fixed (2026-01-04)
    - **Symptom**: Match Schedule generation button lacks debounce/disable on submit (Double-click prevention).
    - **Fix**: Added `disabled={isGenerating}` to all schedule generation buttons.

### Technical Debt & Architecture
- **[Issue #009] Authentication & Security**
    - **A. Secret Key**: Currently using default "your-secret-key..." (Critical). Needs `.env`.
    - **B. Naming Convention**: Backend `access_token` vs Frontend `accessToken`. Recommendation: Use Pydantic alias generator.
- **API Client Proliferation**
    - **Status**: ✅ Resolved (Verified 2026-01-04)
    - **Problem**: Previously 3 different axios instances existed.
    - **Resolution**: Already consolidated to single client at `core/http/client.ts`.
- **Naming Convention Mismatch (Snake vs Camel)**
    - **Status**: High Priority Debt
    - **Problem**: Types in `shared/types` are snake_case, but API returns camelCase.
    - **Action**: Rename all shared types to camelCase.

---

## ✅ Recently Resolved / Verified

- **[System Verification] Core Data Linkage**
    - **Status**: Verified (2026-01-04 User Simulation)
    - **Coverage**: Auth (Login), Teams (CRUD), Matches (Schedule/Score), Standings (View), Venues (View).
    - **Result**: All core flows working correctly on port 8100.
    - **Note**: Auth script required `password_hash` column, while User model uses `password_hash`. `reset_admin` script initially used `hashed_password` which caused failure. Codebase uses `password_hash` consistently.
- **[System Verification] Player Data Linkage**
    - **Status**: Verified Logic (2026-01-04)
    - **Finding**: Goal model uses `player_name` snapshot for Ranking. `player_id` is stored but not used for aggregation.
    - **Implication**: Renaming a player will NOT update historical goal records/rankings. This is a design choice (history preservation) but may confuse users if they correct a typo.
- **[Issue #022] Match Input HTTP Method**
    - **Status**: Verified Consistent
    - **Finding**: Backend expects `PUT` at `/matches/{id}/score`, and Frontend sends `PUT`. No mismatch found.
- **[T015] Frontend Excel Import**
    - **Status**: Verified existing
    - **Finding**: Feature is implemented in `PlayerManagement` page using `features/players/hooks` -> `features/players/api`. It is fully accessible.
- **[Issue #024] Group Table Composite Key**
    - **Status**: Fixed
    - **Fix**: Implemented composite primary key `(tournament_id, id)` for Groups.
- **[Issue #019] Admin User Missing**
    - **Status**: Fixed
    - **Fix**: Verified DB access and reset password mechanism.


---

## 🔍 Deep Dive: Error Analysis Summary

### 1. Team Edit Not Saving
- **Cause**: `editForm` state initialization missing `teamType`. API snake_case vs camelCase mismatch.
- **Fix**: Updated `TeamManagement.tsx` to include all fields and match API casing.

### 2. Schedule Generation 400 Error
- **Cause**: Exclusion pairs not set (variant league requires 3 exclusions for 6 teams).
- **Fix**: Must create exclusion pairs before schedule generation.

### 3. Match Score 401 Error
- **Cause**: `api/client.ts` was missing Auth Interceptor.
- **Fix**: Added interceptor to attach Bearer token.

---

## 🛠 Usage Guide
- **For Spec Gaps**: Refer to "Active Issues".
- **For Coding Standards**: Refer to "Technical Debt" (CamelCase everywhere).
- **For Debugging**: Refer to `Issue/ErrorAnalysis.md` (original file) for full verification steps.
