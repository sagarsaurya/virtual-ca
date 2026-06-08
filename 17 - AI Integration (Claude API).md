# 🤖 AI Integration

**← [[00 - Home]]**

---

## ⚡ CURRENT STATUS (as of 8 June 2026)

**Live on production** — using Groq API (free tier). See section below.

---

## CURRENT IMPLEMENTATION — Groq API (Live ✅)

### Provider
- **Groq API** (free) — `console.groq.com`
- Model: `llama-3.3-70b-versatile`
- Key stored in: Render Environment Variable `GROQ_API_KEY`

### Files
| File | Purpose |
|---|---|
| `ca_agent.py` | Core AI logic — builds context from audit data, calls Groq, returns response |
| `app.py` → `/api/ca-chat` | Flask endpoint — loads last audit result, calls ca_agent, returns JSON |
| `.env` | Local dev key storage (not committed to git) |

### How It Works
1. User uploads Trial Balance / Daybook → audit runs → result saved to `data/audit_result.json`
2. User opens "Ask Your CA" tab
3. Page loads → calls `/api/audit/last` → builds numbered queries from audit data → shows greeting
4. User sends message → JS calls `/api/ca-chat` with `{message, history[]}`
5. Backend loads `audit_result.json` as context → sends to Groq with CA system prompt
6. Response returned as JSON `{reply: "..."}` → rendered in chat panel

### Context Built for AI
```
Company: AJKL
Period: 1-Apr-25 to 31-Mar-26
Score: 82/100
Issues: 2 Critical | 8 Important

LEDGER CLASSIFICATION ISSUES (2):
  [Critical] Credit Card Membership Fee — rule text | Balance: ₹X

CASH VIOLATIONS (Sec 40A3):
  date  party  ₹amount

OUTSTANDING BALANCES:
  [Critical] Difference in Opening Balances — question text

LARGE EXPENSES — TDS threshold:
  date  party  ₹amount  [voucher_type]

LOANS:
  ledger — ₹balance | question text
```

### Query Auto-Generation (Left Panel)
Queries are built in JS from `auditData` using `buildCAQueries()`:
- `ledger_classification` → LEDGER category queries (uses: `rule`, `current_group`, `correct_group`, `balance`, `fix`)
- `cash_violations` → SEC 40A(3) queries (uses: `party`, `amount`, `date`, `issue`, `impact`, `section`)
- `outstanding` → BALANCE queries (uses: `ledger`, `amount`, `question`, `severity`)
- `large_expenses` → TDS·BILL queries (uses: `party`, `amount`, `date`, `question`)
- `loans` → LOAN queries (uses: `ledger`, `balance`, `question`)

### Conversation History
- Client-side array `caChatHistory` — last 20 turns
- Sent with every request so AI remembers context
- Cleared on "Clear chat" button or page reload

---

## PREVIOUS DESIGN — Claude API (Planned, not yet live)

> The below was the original plan. Now superseded by Groq implementation above.
> Will be revisited if Claude API is preferred in future.

### Overview

VirtualCA uses Anthropic's Claude API to power the "Ask Your CA" chat feature. The AI reads the actual uploaded data and gives specific, data-driven answers — not generic accounting advice.

---

## Models Used

| Use Case | Model |
|---|---|
| AI Chat (full answers) | `claude-sonnet-4-6` |
| Quick suggestions | `claude-haiku-4-5-20251001` |

---

## How It Works

1. User uploads Tally file → analysis runs → results stored in DB
2. User opens "Ask Your CA" page
3. AI is loaded with a **system prompt** containing the actual uploaded data
4. User asks a question → Claude answers using the specific ledger data
5. Response is streamed back (typing effect)

---

## System Prompt Structure

```python
system_prompt = f"""
You are VirtualCA, an expert Indian Chartered Accountant assistant.
You are analyzing the following uploaded trial balance:

Company: {company.name}
Financial Year: {upload.fy_period}
Total Ledgers: {upload.total_ledgers}

CRITICAL ERRORS FOUND:
{format_errors(critical_errors)}

REVIEW ITEMS:
{format_errors(review_items)}

TDS Status:
- Deducted: ₹{tds.deducted} | Deposited: ₹{tds.deposited} | Pending: ₹{tds.pending}
- Interest accrued: ₹{tds.interest}

PT Status (Kolkata/WB):
- PT Deducted: ₹{pt.deducted} | Deposited: ₹{pt.deposited} | Due: 21st

Answer questions based on this specific data.
Always mention ledger names and amounts from the data.
Provide journal entries using Tally format (Dr/Cr).
Include Tally navigation paths in your answers.
Respond in clear English. Keep answers concise but complete.
"""
```

---

## Example Contextual Q&A

**User asks:** "Why is my profit low this month?"

**VirtualCA answers:**
> Based on your uploaded data, here are the reasons:
>
> 1. **Purchases increased 28%** — ₹4.2L this month vs ₹3.3L last month
> 2. **Outstanding debtors increased ₹3.2L** — Raj Traders (₹1.8L), ABC Ltd (₹1.4L)
> 3. **4 GST mismatches detected** — ₹18,400 in Input Credit is blocked
> 4. **Bank Interest ₹25,000 booked as Expense** — reduces profit incorrectly
>    Fix: Gateway → Accounts Info → Ledgers → Alter → Bank Interest → Change group to Indirect Incomes

---

## Quick-Ask Chips (pre-loaded in UI)

1. "Top 3 errors to fix first?"
2. "TDS pending amount and interest?"
3. "Debtors with credit balance?"
4. "Journal entries to fix all errors?"
5. "How to improve my compliance score?"

Each chip pre-fills the input and auto-sends.

---

## API Call (Backend)

```python
from anthropic import Anthropic

client = Anthropic()

@app.post("/api/chat")
async def chat(request: ChatRequest):
    # Build context from DB
    upload = get_upload(request.upload_id)
    errors = get_errors(request.upload_id)
    tds = get_tds(request.upload_id)
    pt = get_pt(request.upload_id)

    system = build_system_prompt(upload, errors, tds, pt)

    # Stream response
    with client.messages.stream(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        system=system,
        messages=[{"role": "user", "content": request.message}]
    ) as stream:
        for text in stream.text_stream:
            yield text
```

---

## UI Features

- **"Data Connected" banner** — shows file name, ledger count, error count
- **Green pulsing badge** — "Data Connected"
- **Typing indicator** — animated 3 dots while AI is thinking
- **Chat history** — stored per session (optional: per upload)
- **Footer note** — "AI answers are based on your uploaded data"

---

## Related Notes
- [[03 - Features Overview]]
- [[08 - Tech Stack]]
- [[16 - Build Phases & Roadmap]]
