# CLAUDE.md — VirtualCA Project Briefing
> Read this first. Every session. No exceptions.

---

## 🧠 What Is This Project?
**VirtualCA** — AI-powered Tally accounting audit SaaS for Indian SMBs and CA firms.
**Owner:** Sagar Pathak, Kolkata
**Started:** 14 March 2026

### One Line
> Upload your Tally file → get full audit + error fixes + compliance alerts in 30 seconds.

---

## 📁 Project Folder
```
C:\Users\sagar\Downloads\tally_saas\
```

### Files In This Folder
```
index.html          → Complete UI prototype (all 11 pages, fully interactive)
analyzer.py         → Python analysis logic (reference only)
CLAUDE.md           → THIS FILE — read every session
LOG.md              → Full technical build diary
CONTEXT.md          → (same as this file, backup)

Obsidian Vault Notes:
00 - Home.md                        → Master index
01 - What We Are Building.md
02 - Target Users.md
03 - Features Overview.md
04 - Pricing Plans.md
05 - All Pages & Screens.md
06 - Fix Workflow & Team Collaboration.md
07 - Export to Tally.md
08 - Tech Stack.md
09 - Database Schema.md
10 - API Endpoints.md
11 - Ledger Analysis Rules.md
12 - TDS Analysis.md
13 - PT Analysis Kolkata.md
14 - Bank Reconciliation.md
15 - Compliance Calendar.md
16 - Build Phases & Roadmap.md
17 - AI Integration (Claude API).md
18 - Change Log.md
```

---

## ⚙️ Tech Stack (Decided)
| Layer | Technology |
|---|---|
| Frontend + Backend | Next.js 14 (App Router) |
| Styling | Tailwind CSS |
| Database + Auth | Supabase (PostgreSQL) |
| File Storage | Supabase Storage |
| AI Chat | Anthropic Claude API (claude-sonnet) |
| Payments | Razorpay |
| Deploy Frontend | Vercel |
| Version Control | GitHub |

---

## 🗄️ Database (Supabase)
Tables to build:
- `companies` — multi-tenant
- `users` — linked to company, roles: admin/accountant/viewer
- `uploads` — every file upload
- `ledger_results` — analysis results per ledger
- `workflow_comments` — comments on errors
- `transactions` — voucher drill-down data
- `compliance_items` — due dates + status
- `tds_records` — section-wise TDS
- `pt_records` — employee-wise PT (WB slabs)
- `bank_recon_sessions` — reconciliation sessions
- `bank_recon_entries` — individual matched/unmatched entries
- `chat_messages` — AI chat history

Full schema → see `09 - Database Schema.md`

---

## 🖥️ All 11 Pages (Prototype Complete)
1. Login
2. Dashboard (4 stat cards + recent analyses + compliance alerts)
3. Upload & Analyze (5 file types + data mapping screen)
4. Analysis Results (error cards + ledger drill-down + fix workflow)
5. History
6. Bank Reconciliation
7. Ask Your CA (AI chat — reads uploaded data)
8. Journal Entry Guide
9. Compliance Calendar
10. TDS Analysis
11. Admin Panel

---

## ⚡ Key Features (All Built in Prototype)
1. Smart Upload — Excel, Tally XML, Ledger Dump, Bank Statement, GST JSON
2. Data Mapping Screen + Chart of Accounts mapping
3. Analysis Results — colour coded (Critical/Review/OK/Ignored)
4. Error Explanation Panel — why error, rule violated, fix
5. Ledger Drill-Down — transaction history, voucher details
6. Auto-Correction Journal Entry on every error
7. Fix Workflow — Open/InProgress/Resolved/Ignored + Assign + Comment
8. Export to Tally — XML / Excel / CSV
9. Bank Reconciliation — auto-match, Matched/Unmatched/TallyOnly/Duplicates
10. TDS Analysis — section-wise, late interest, 26AS mismatch
11. PT Analysis — Kolkata/WB slabs (₹110/₹130/₹150/₹200), Grips portal
12. AI Chat — contextual, reads actual uploaded data
13. Compliance Calendar — TDS 7th, GSTR-1 11th, GSTR-3B 20th, PT 21st

---

## 📏 Analysis Engine — 20 Ledger Rules
Key rules:
- TDS Receivable → must be Current Assets (not Duties & Taxes)
- TDS Payable → must be Duties & Taxes
- GST ITC → must be Current Assets
- Bank Interest Received → must be Indirect Incomes (not Expenses)
- Capital/Drawings → must be Capital Account
- Prepaid Expenses → must be Current Assets
- PT Payable → must be Duties & Taxes
- Suspense Account non-zero → Critical
- Debtor with credit balance → Review
- Creditor with debit balance → Review

Full rules → see `11 - Ledger Analysis Rules.md`

---

## 🏙️ PT Rules (Kolkata — West Bengal)
| Gross Salary | PT Amount |
|---|---|
| Up to ₹10,000 | Nil |
| ₹10,001 – ₹15,000 | ₹110/month |
| ₹15,001 – ₹25,000 | ₹130/month |
| ₹25,001 – ₹40,000 | ₹150/month |
| Above ₹40,000 | ₹200/month |

Deposit by: **21st every month** via **Grips portal (wbifms.gov.in)**

---

## 💰 Pricing
| Plan | Price |
|---|---|
| Free | ₹0 |
| Starter | ₹499/month |
| Pro | ₹1,499/month |
| CA Firm | ₹3,999/month |

---

## 🚀 Build Status

### ✅ Phase 1 — COMPLETE
- Full prototype in `index.html` — all 11 pages interactive
- All features working in prototype (simulated data)
- Full documentation in Obsidian vault (18 notes)
- CLAUDE.md created

### 🔲 Phase 2 — NOT STARTED (Next Step)
Build real working app:
- [ ] Step 1: Next.js project setup + Tailwind
- [ ] Step 2: Supabase project setup (DB tables + auth)
- [ ] Step 3: Login page (real Supabase auth)
- [ ] Step 4: Dashboard (real data from DB)
- [ ] Step 5: File upload + Excel parser
- [ ] Step 6: Analysis engine (20 rules)
- [ ] Step 7: Results page
- [ ] Step 8: Claude API chat integration
- [ ] Step 9: TDS + PT analysis
- [ ] Step 10: Bank reconciliation
- [ ] Step 11: Compliance calendar
- [ ] Step 12: Export to Tally (XML/Excel/CSV)
- [ ] Step 13: Payments (Razorpay)
- [ ] Step 14: Deploy (GitHub → Vercel)

---

## 🔑 Environment Variables Needed (.env.local)
```
NEXT_PUBLIC_SUPABASE_URL=
NEXT_PUBLIC_SUPABASE_ANON_KEY=
SUPABASE_SERVICE_ROLE_KEY=
ANTHROPIC_API_KEY=
RAZORPAY_KEY_ID=
RAZORPAY_KEY_SECRET=
```

---

## 👤 Team Model
| Role | Person | Cost |
|---|---|---|
| Product Owner + AI Director | Sagar Pathak | — |
| Code Writer | Claude (me) | Claude subscription |
| Tech Monitor / Ops | 1 fresher/intern (BCA/MCA) | ₹5,000–₹10,000/month |

---

## 📋 How To Continue Each Session
1. Open new Claude conversation
2. Paste this CLAUDE.md file
3. Say "continue from [step number]" or describe the problem
4. I will know everything and continue immediately

---

## 🖥️ How To Run Locally (Once Built)
```bash
cd C:\Users\sagar\Downloads\tally_saas
npm run dev
```
Open browser → `localhost:3000`

## 🌐 How To Deploy
```bash
git add .
git commit -m "update"
git push
```
Vercel auto-deploys in 2 minutes → live at `https://virtualca.vercel.app`

---

*Last updated: 15 March 2026 | Owner: Sagar Pathak | Built with Claude*
