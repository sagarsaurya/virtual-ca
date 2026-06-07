# 🤖 AI Integration — Claude API

**← [[00 - Home]]**

---

## Overview

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
