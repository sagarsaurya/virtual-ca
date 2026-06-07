# 🔌 API Endpoints

**← [[00 - Home]]**
**Backend:** FastAPI (Python)

---

## Auth

```
POST   /api/auth/login        → { email, password } → JWT token
POST   /api/auth/signup       → { name, email, password, company } → JWT token
POST   /api/auth/logout       → invalidate token
```

---

## Dashboard

```
GET    /api/dashboard         → stats, recent uploads, compliance alerts
```

---

## Uploads & Analysis

```
POST   /api/uploads                           → upload file (multipart/form-data)
GET    /api/uploads/history                   → paginated list of uploads
GET    /api/uploads/:id/results               → full analysis results
GET    /api/uploads/:id/results/:ledger_id    → drill-down detail (transactions)
PATCH  /api/uploads/:id/results/:ledger_id    → update workflow status / assignee
POST   /api/uploads/:id/results/:ledger_id/comments  → add comment
GET    /api/uploads/:id/export/:format        → format: xml / excel / csv
```

---

## AI Chat

```
POST   /api/chat              → { upload_id, message } → streaming AI response
GET    /api/chat/:upload_id   → chat history for this upload
```

---

## Compliance

```
GET    /api/compliance                → all items for this company
PATCH  /api/compliance/:id/done      → mark item as done
```

---

## TDS & PT

```
GET    /api/tds/:upload_id           → TDS section-wise analysis
GET    /api/pt/:upload_id            → PT employee-wise analysis
```

---

## Bank Reconciliation

```
POST   /api/bankrec                  → start reconciliation (upload 2 files)
GET    /api/bankrec/:session_id      → reconciliation results
```

---

## Admin

```
GET    /api/admin/users              → list all users in company
POST   /api/admin/users              → invite new user (send email)
DELETE /api/admin/users/:id          → remove user
```

---

## Request/Response Examples

### Upload file
```json
POST /api/uploads
Content-Type: multipart/form-data
{
  "file": <binary>,
  "file_type": "excel",
  "fy_period": "2025-26"
}

Response:
{
  "upload_id": "abc-123",
  "status": "processing",
  "message": "File uploaded, analysis started"
}
```

### Get results
```json
GET /api/uploads/abc-123/results

Response:
{
  "upload_id": "abc-123",
  "file_name": "TrialBalance_Mar2026.xlsx",
  "total_ledgers": 120,
  "critical_count": 7,
  "review_count": 12,
  "ok_count": 101,
  "results": [
    {
      "id": "led-001",
      "ledger_name": "Bank Interest Received",
      "current_group": "Indirect Expenses",
      "correct_group": "Indirect Incomes",
      "severity": "critical",
      "error_type": "wrong_group",
      "rule_violated": "Income must be classified under Indirect Incomes",
      "workflow_status": "open"
    }
  ]
}
```

---

## Related Notes
- [[08 - Tech Stack]]
- [[09 - Database Schema]]
- [[17 - AI Integration (Claude API)]]
