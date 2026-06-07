# 🔧 Fix Workflow & Team Collaboration

**← [[00 - Home]]**

---

## Why This Exists

VirtualCA doesn't just detect errors — it tracks the **entire fix process** from discovery to resolution, with team collaboration built in.

---

## Status System

Every error card has a status that can be changed:

| Status | Meaning | Colour |
|---|---|---|
| **Open** | Error detected, not yet actioned | 🔴 Red |
| **In Progress** | Accountant has started working on it | 🟡 Yellow |
| **Resolved** | Fix has been applied in Tally | 🟢 Green |
| **Ignored** | Acknowledged, decided to skip (with reason) | ⚫ Grey |

---

## Fix Workflow Status Bar (top of Results page)

```
Open: 7  |  In Progress: 2  |  Resolved: 3  |  Ignored: 1
Last updated by Sagar Pathak at 2:30 PM
```

---

## Actions on Each Error Card

### 1. Change Status
- Dropdown: Open / In Progress / Resolved / Ignored
- Change is saved immediately with timestamp + user name

### 2. Assign to Accountant
- Dropdown shows all team members
- Assigned person gets notified (Phase 3: email/WhatsApp)
- Error shows assignee badge

### 3. Add Comment
- Text input at bottom of error card
- Send button (or Enter key)
- Comments thread visible to whole team
- Each comment shows: name, time, message

### 4. Mark Resolved
- Green "Mark Resolved" button
- Saves: resolved_by, resolved_at, status = 'resolved'
- Error moves to Resolved tab

---

## Team Roles

| Role | Can Do |
|---|---|
| **Admin** | See all errors, assign, resolve, manage users |
| **Accountant** | See assigned errors, update status, add comments |
| **Viewer** | Read-only — can see report but not change anything |

---

## To Build (Backend)

```sql
-- Status update
PATCH /api/uploads/:id/results/:ledger_id
{ status: 'inprogress', assigned_to: user_id }

-- Comment
POST /api/uploads/:id/results/:ledger_id/comments
{ comment: 'Working on this, will update Tally by EOD' }
```

Tables needed: `ledger_results` (workflow_status, assigned_to), `workflow_comments`

See [[09 - Database Schema]]

---

## Related Notes
- [[05 - All Pages & Screens]]
- [[07 - Export to Tally]]
- [[09 - Database Schema]]
