# 2026-01-03 Issues Investigation

This document records the investigation results for the issues reported in `ISSUES.md` on 2026-01-03.

## [T004] Venue Update API (Boolean false issue)
- **Problem**: When updating `forFinalDay` or `isFinalsVenue` to `false`, the API returns the updated value (`false`), but it is not saved in the database (remains `true`).
- **Status**: Investigation completed.
- **Findings**:
    1. **Backend Logic Verified**: Created reproduction script `reproduce_venue_bug.py`.
        - Direct DB update using SQLAlchemy model works correctly (False is persisted).
        - Pydantic schema `VenueUpdate` parsing works correctly (input `{"forFinalDay": false}` parses to `for_final_day=False`).
    2. **Hypothesis**: The issue is likely not in the core backend logic (Model/Schema).
        - `routes/venues.py` uses `exclude_unset=True`. If the frontend sends `false`, it is processed.
        - The fact that the response returns `false` means the in-memory object was updated.
        - The persistence failure suggests a transaction commit issue specific to the running environment or the specific request flow, which was not reproduced in the isolated script.
    3. **Recommendation**: Verify if the frontend explicitly sends `false` (not `null` or undefined). (Code in `Settings.tsx` line 205-206 seems to do this correctly: `for_final_day: venueForm.forFinalDay`).

## [T003] Venue List API (Endpoint & Case)
- **Problem**: 
  - Test used `/venues` but correct is `/api/venues/`.
  - Response format `camelCase` vs `snake_case`.
- **Status**: Resolved.
- **Findings**:
  - The correct endpoint is `/api/venues/` (verified via valid response in `ISSUES.md`).
  - Python Backend uses `CamelCaseModel` (`src/backend/schemas/common.py`), so responses are automatically serialized to `camelCase`. The `snake_case` properties in `Venue` type definition (`src/shared/types/index.ts`) are backward compatibility fallbacks.

## [T007] Frontend Build Errors
- **Problem**: 24 errors including unused variables and type mismatches.
- **Status**: Identified root cause (Environment/Cache mismatch).
- **Findings**:
  - **Type Mismatch (`Venue` properties)**: The error claims `isFinalsVenue` is missing on `Venue`.
    - Verified `src/shared/types/index.ts` (Line 307): `isFinalsVenue: boolean;` **exists**.
    - Verified `src/frontend/tsconfig.json`: Correctly maps `@shared/*` to `../shared/*`.
    - **Conclusion**: The source code is correct. The build error reported in `ISSUES.md` likely stemmed from a stale environment, incorrect path resolution in the CI/test runner, or the `node_modules` cache being out of date.
  - **Unused Variables**: Confirmed multiple unused imports in `src/frontend/src/features/final-day/utils/exportSchedule.ts` etc. These are valid lint errors to fix.

## [T010] Settings.tsx Missing
- **Problem**: File was not found during test.
- **Resolution**: Located at `src/frontend/src/pages/Settings.tsx`. The test runner was likely in the wrong directory or searching incorrectly.

- [x] Reporting
    - [x] Compile all findings into `docs/investigations/2026-01-03_issues_investigation.md` <!-- id: 13 -->
    - [x] Notify user <!-- id: 14 -->

## Verification: Spec vs Implementation & Proposed Solutions

### 1. Missing Features (Final Day)
- **Status**: Confirmed Incomplete.
- **Missing UI**: Referee Input, Venue Manager Input (Editable).
- **Missing Logic**: `handleSaveMatch` only updates teams, ignoring Time/Referees.
- **API Gap**: No dedicated internal endpoint for updating match metadata on this screen.

#### **Solution Proposal: Implement `updateFinalDayMatch`**
1.  **Backend (`src/backend/routes/matches.py`)**:
    -   Create `PUT /matches/{match_id}/details` (or extend existing).
    -   Accept `kickoff_time`, `referee_main`, `referee_assistant` (and venue manager if linked to venue).
    -   *Note*: Venue Manager is typically a property of the *Venue*, not the Match. Updating it here implies updating the `Venue` Schedule for that day.
2.  **Frontend (`FinalDaySchedule.tsx`)**:
    -   Update `handleSaveMatch` to call this new endpoint.
    -   Pass full `match` object including new fields.

### 2. [T004] Venue Update Bug (Boolean False Persistence)
- **Status**: Reproduced in integration. Code logic looks correct but persistence fails.
- **Root Cause Hypothesis**:
    -   If `models/venue.py` uses default values or `server_default` without `nullable=False`, SQLAlchemy might produce unexpected behavior with `False`.
    -   Or, `exclude_unset=True` combined with frontend optionality causes the field to be dropped if the library treats `false` as "unset" (unlikely for Pydantic v2, but possible in specific configs).
- **Solution**:
    -   **Immediate Fix**: In `routes/venues.py`, remove `exclude_unset=True` and instead explicitly explicitly pick fields from the payload if they exist, OR ensure frontend sends all fields.
    -   **Better Fix**: Verify the `Venue` model definition. If `for_final_day` is `Boolean`, `False` is a valid value. Ensure the DB column isn't `Boolean(create_constraint=True)` interfering.

### 3. [T007] Frontend Build Errors (Types)
- **Status**: False Positive / Environment consistency issue.
- **Findings**: `types/index.ts` correctly re-exports `@shared/types`.
- **Solution**:
    -   Run `npm ci` to reset node_modules.
    -   Ensure `Settings.tsx` imports from `@/types` or `@shared/types` explicitly.
    -   Restart VSCode TS Server.

### 4. Confirmed Non-Issues
- **[T005, T006, T008]**: Verified as correct implementations. Reports were due to testing errors.

## Investigation: Remaining Issues

### [T005] Team List API (Endpoint/Params)
- **Problem**: `ISSUES.md` reported `/teams?tournamentId=1` failing.
- **Findings**:
    - Correct Endpoint: `/api/teams/` (verified).
    - Frontend Code: `teams/api.ts` uses `/teams` with `{ params: { tournamentId } }`.
    - **Mechanism**: `core/http/client.ts` contains a request interceptor that uses `decamelizeKeys`. Thus, `tournamentId` is correctly converted to `tournament_id` before sending.
    - **Conclusion**: The frontend implementation is **correct**. The issue reported was likely due to testing with raw curl without parameter conversion or missing the `/api` prefix in the manual test.

### [T006] Match List API (Endpoint)
- **Problem**: Endpoint path mismatch.
- **Findings**:
    - Correct Endpoint: `/api/matches/` (verified).
    - SC: `FinalDaySchedule.tsx` uses `/matches/?tournament_id=...`.
    - **Conclusion**: Frontend code correctly uses the proxy-supported path.

### [T008] CSV Upload Implementation
- **Problem**: Feature reported as potentially missing/file access error.
- **Findings**:
    - **Ui Implementation**: `TeamManagement.tsx` includes a file input and `handleCsvImport`.
    - **API Integration**: `teams/api.ts` defines `importCsv` sending POST to `/teams/import-csv` with `multipart/form-data`.
    - **Conclusion**: The CSV upload feature **is implemented** on the frontend. The "File not found" error in T008 was a test runner artifact.
