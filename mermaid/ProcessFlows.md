
# Process Flows

## 1. Match Approval Workflow
This diagram illustrates the newly implemented approval process for match results.

```mermaid
sequenceDiagram
    participant Staff as Venue Staff
    participant UI as Frontend
    participant API as Backend API
    participant DB as Database
    participant Admin as Administrator
    participant Public as Public View

    Note over Staff, Public: === 1. Input & Review ===
    Staff->>UI: Input Score (2-1)
    UI->>API: POST /matches/101/score
    API->>DB: Update score, status='completed', approval='pending'
    API-->>UI: 200 OK
    
    par Real-time Notification
        API->>Admin: WebSocket: { type: "match_updated", id: 101, status: "pending" }
    end

    Note over Staff, Public: === 2. Admin Approval ===
    Admin->>UI: View /approval page
    UI->>API: GET /matches?approval_status=pending
    API-->>UI: Match List [101]

    Admin->>UI: Click "Approve"
    UI->>API: POST /matches/101/approve
    API->>DB: Update approval='approved'
    API->>DB: Recalculate Standings (if Preliminary)
    
    par Broadcast Updates
        API->>Staff: WS: Approved
        API->>Public: WS: Match Result & Standings Update
    end
```

## 2. PWA Offline Score Input
Flow for handling score inputs when network is unavailable.

```mermaid
sequenceDiagram
    participant Staff
    participant SW as Service Worker
    participant IDB as IndexedDB
    participant React as React App
    participant Sync as Background Sync

    Note over Staff, Sync: === Offline Mode ===
    Staff->>React: Input Score & Click Save
    React->>React: Check Network Status (Offline)
    React->>IDB: Save to 'offline-queue'
    React-->>Staff: Show "Saved Offline" Notification
    
    Note over Staff, Sync: === Online Recovery ===
    SW->>SW: Detect Network Recovery
    SW->>Sync: Trigger 'sync' event
    Sync->>IDB: Read queued items
    
    loop For each item
        Sync->>API: POST /matches/id/score
        API-->>Sync: 200 OK
        Sync->>IDB: Remove from queue
    end
    
    Sync->>React: Broadcast "Sync Complete"
    React-->>Staff: Show "Sync Completed" Notification
```
