# 🚀 Build Phases & Roadmap

**← [[00 - Home]]**

---

## Phase 1 — Prototype ✅ COMPLETE

- [x] Full UI prototype in single HTML file (`index.html`)
- [x] All 11 pages built and interactive
- [x] Simulated upload + analysis flow
- [x] Ledger drill-down modal
- [x] Export to Tally modal (XML / Excel / CSV)
- [x] Error explanation panels with accounting rules
- [x] Auto-correction journal entry suggestions
- [x] Fix workflow (status / assign / comment / mark resolved)
- [x] Bank Reconciliation page (upload + match simulation)
- [x] TDS Analysis page (section-wise + interest + 26AS mismatch)
- [x] PT Analysis — Kolkata WB slabs + employee-wise + journal entries
- [x] Contextual AI chat (reads uploaded data)
- [x] Multi-format upload (Excel, XML, Ledger, Bank, GST JSON)
- [x] Data mapping screen + Chart of Accounts mapping
- [x] UX: colour legend, FY filter, sort, download report

---

## Phase 2 — MVP (Build Next)

**Goal:** Working product with real data

- [ ] React 18 frontend (convert prototype to React)
- [ ] FastAPI backend setup
- [ ] File upload endpoint (multipart/form-data)
- [ ] Excel parser (pandas) — Trial Balance
- [ ] Rule-based ledger analysis engine (implement [[11 - Ledger Analysis Rules]])
- [ ] PostgreSQL database + all tables ([[09 - Database Schema]])
- [ ] JWT auth (login / signup / logout)
- [ ] Real analysis report stored in DB
- [ ] Claude API integration for AI chat ([[17 - AI Integration (Claude API)]])
- [ ] Workflow status + assign + comments (real DB)
- [ ] Deploy: Vercel (frontend) + Railway (backend)

**Estimated time:** 6–8 weeks

---

## Phase 2B — CA Feedback Features (Sandeep Bajoria — 12 June 2026)

**Goal:** Build what real CAs actually need

- [ ] TDS Detection upgrade — detect missed TDS from ledger, AI suggests section + action
- [ ] Balance Sheet generator — auto-build from Trial Balance groupings
- [ ] P&L on Shares + MF — read trading/investment ledgers, calculate realized gains
- [ ] Tally vs Broker Statement reconciliation — match trades both sides
- [ ] Document availability checker — show what vouchers/bills exist per entry
- [ ] GST Return file generator — raw Tally data → GSTR-1/3B ready format
- [ ] Fund Flow + Cash Flow statements — from Tally bank/cash book data
- [ ] Budget creation — from bank/cash book historical patterns

**Note:** Bank Reconciliation DROPPED (Tally handles it). Party-wise Ledger Rec to be improved instead.

---

## Phase 3 — Growth

**Goal:** Full-featured product, paying customers

- [ ] Tally XML export (real format matching Tally import spec)
- [ ] PDF report generation (WeasyPrint or Puppeteer)
- [ ] Compliance calendar with email reminders (Resend)
- [ ] Multi-client support for CA firms
- [ ] Razorpay payment integration
- [ ] Real bank reconciliation algorithm
- [ ] Real TDS section detection from ledger names
- [ ] PT auto-calculation from payroll ledgers
- [ ] Form 26AS import + reconciliation
- [ ] Tally XML import (upload .xml exported from Tally)

**Estimated time:** 8–12 weeks after Phase 2

---

## Phase 4 — Scale

**Goal:** Market leader, automation

- [ ] Tally direct integration (Tally XML API / TDL scripts)
- [ ] WhatsApp bot (Twilio or WATI) for compliance reminders
- [ ] GSTR-2A/2B vs books reconciliation
- [ ] Bank statement auto-import (HDFC/ICICI API)
- [ ] P&L + Balance Sheet validation
- [ ] Multi-branch support
- [ ] Mobile app (React Native)
- [ ] Custom rule builder for CA firms
- [ ] White-label for large CA firms

**Estimated time:** 3–6 months after Phase 3

---

## Priority Order for Phase 2

1. Auth + File upload + Excel parser
2. Analysis engine (core value)
3. Results page (show errors with explanations)
4. DB storage + history
5. AI chat (Claude API)
6. Export to Tally
7. Compliance calendar
8. TDS + PT analysis
9. Bank reconciliation
10. Payments (Razorpay)

---

## Related Notes
- [[08 - Tech Stack]]
- [[17 - AI Integration (Claude API)]]
- [[18 - Change Log]]
