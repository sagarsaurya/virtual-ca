# 🗄️ Database Schema

**← [[00 - Home]]**
**Database:** PostgreSQL

---

## Tables Overview

| Table | Purpose |
|---|---|
| `companies` | Multi-tenant — one row per company |
| `users` | All users, linked to company |
| `uploads` | Every file upload |
| `ledger_results` | Analysis results per ledger per upload |
| `workflow_comments` | Comments on errors |
| `transactions` | Voucher-level data for drill-down |
| `compliance_items` | Compliance calendar items |
| `tds_records` | TDS section-wise data |
| `pt_records` | Employee-wise PT data |
| `bank_recon_sessions` | Bank reconciliation sessions |
| `bank_recon_entries` | Individual recon entries |
| `chat_messages` | AI chat history |

---

## companies
```sql
companies (
  id          UUID PRIMARY KEY,
  name        TEXT,
  gstin       TEXT,
  city        TEXT,
  state       TEXT,
  plan        TEXT,  -- free/starter/pro/ca_firm
  created_at  TIMESTAMP
)
```

---

## users
```sql
users (
  id            UUID PRIMARY KEY,
  company_id    UUID REFERENCES companies(id),
  name          TEXT,
  email         TEXT UNIQUE,
  password_hash TEXT,
  role          TEXT,  -- admin/accountant/viewer
  created_at    TIMESTAMP
)
```

---

## uploads
```sql
uploads (
  id             UUID PRIMARY KEY,
  company_id     UUID REFERENCES companies(id),
  uploaded_by    UUID REFERENCES users(id),
  file_name      TEXT,
  file_type      TEXT,  -- excel/xml/ledger/bank/gst
  fy_period      TEXT,  -- '2025-26'
  status         TEXT,  -- processing/complete/failed
  total_ledgers  INT,
  critical_count INT,
  review_count   INT,
  ok_count       INT,
  created_at     TIMESTAMP
)
```

---

## ledger_results
```sql
ledger_results (
  id               UUID PRIMARY KEY,
  upload_id        UUID REFERENCES uploads(id),
  ledger_name      TEXT,
  ledger_number    INT,
  current_group    TEXT,
  correct_group    TEXT,
  closing_balance  NUMERIC,
  dr_cr            TEXT,  -- Dr/Cr
  severity         TEXT,  -- critical/review/ok
  error_type       TEXT,  -- wrong_group/credit_balance/dormant/ob_diff
  rule_violated    TEXT,
  tally_fix_path   TEXT,
  workflow_status  TEXT,  -- open/inprogress/resolved/ignored
  assigned_to      UUID REFERENCES users(id),
  created_at       TIMESTAMP
)
```

---

## workflow_comments
```sql
workflow_comments (
  id               UUID PRIMARY KEY,
  ledger_result_id UUID REFERENCES ledger_results(id),
  user_id          UUID REFERENCES users(id),
  comment          TEXT,
  created_at       TIMESTAMP
)
```

---

## transactions (drill-down)
```sql
transactions (
  id           UUID PRIMARY KEY,
  upload_id    UUID REFERENCES uploads(id),
  ledger_name  TEXT,
  date         DATE,
  voucher_no   TEXT,
  voucher_type TEXT,
  narration    TEXT,
  debit        NUMERIC,
  credit       NUMERIC,
  party        TEXT
)
```

---

## compliance_items
```sql
compliance_items (
  id              UUID PRIMARY KEY,
  company_id      UUID REFERENCES companies(id),
  title           TEXT,
  description     TEXT,
  due_date        DATE,
  recurrence      TEXT,  -- monthly/quarterly/annual
  status          TEXT,  -- pending/done/overdue
  marked_done_by  UUID REFERENCES users(id),
  marked_done_at  TIMESTAMP,
  penalty_note    TEXT
)
```

---

## tds_records
```sql
tds_records (
  id              UUID PRIMARY KEY,
  upload_id       UUID REFERENCES uploads(id),
  section         TEXT,  -- 194C/194J/194I/192
  nature          TEXT,
  deducted        NUMERIC,
  deposited       NUMERIC,
  pending         NUMERIC,
  interest_amount NUMERIC,
  status          TEXT
)
```

---

## pt_records
```sql
pt_records (
  id            UUID PRIMARY KEY,
  upload_id     UUID REFERENCES uploads(id),
  employee_name TEXT,
  gross_salary  NUMERIC,
  pt_slab       TEXT,
  pt_amount     NUMERIC,
  month         TEXT,
  deposited     BOOLEAN,
  deposit_date  DATE
)
```

---

## bank_recon_sessions
```sql
bank_recon_sessions (
  id              UUID PRIMARY KEY,
  company_id      UUID REFERENCES companies(id),
  upload_id       UUID REFERENCES uploads(id),
  bank_file_name  TEXT,
  tally_file_name TEXT,
  matched         INT,
  unmatched       INT,
  tally_only      INT,
  duplicates      INT,
  created_at      TIMESTAMP
)
```

---

## bank_recon_entries
```sql
bank_recon_entries (
  id          UUID PRIMARY KEY,
  session_id  UUID REFERENCES bank_recon_sessions(id),
  entry_type  TEXT,  -- matched/unmatched/tally_only/duplicate
  date        DATE,
  narration   TEXT,
  bank_amount NUMERIC,
  tally_amount NUMERIC,
  bank_ref    TEXT,
  voucher_no  TEXT,
  party       TEXT
)
```

---

## chat_messages
```sql
chat_messages (
  id          UUID PRIMARY KEY,
  company_id  UUID REFERENCES companies(id),
  upload_id   UUID REFERENCES uploads(id),
  user_id     UUID REFERENCES users(id),
  role        TEXT,  -- user/assistant
  content     TEXT,
  created_at  TIMESTAMP
)
```

---

## Related Notes
- [[08 - Tech Stack]]
- [[10 - API Endpoints]]
