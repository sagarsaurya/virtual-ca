# 📝 Change Log

**← [[00 - Home]]**

---

## 15 March 2026

### Prototype Updates — Major
- ✅ Added **Fix Workflow** to Results page
  - Status: Open / In Progress / Resolved / Ignored
  - Assign to team member
  - Add comment thread
  - Mark Resolved with timestamp
- ✅ Added **Fix Workflow Status Bar** (Open / InProgress / Resolved / Ignored counts)
- ✅ Added **UX toolbar** — colour legend, FY filter, sort by, download report (PDF/Excel/CSV)

### Upload System
- ✅ **5 file type tabs**: Excel Trial Balance, Tally XML, Ledger Dump, Bank Statement, GST JSON
- ✅ **Data Mapping Screen** after upload
- ✅ **Chart of Accounts Mapping** — custom group → standard Tally group

### New Modules
- ✅ **Bank Reconciliation Module** — upload 2 files, auto-match, Unmatched/Tally Only/Duplicates/Matched tabs
- ✅ **TDS Analysis Page** — section-wise (194C/194J/194I/192), late interest calculator, 26AS mismatch table
- ✅ **PT Analysis Section (Kolkata/WB)** — WB slabs, employee-wise PT, journal entries, Grips steps

### AI Chat
- ✅ **Contextual AI banner** — "Data Connected" with file name + error count
- ✅ **Pre-loaded contextual Q&A** — Why is profit low? → data-specific answer
- ✅ **5 quick-ask chips** — context-aware, pre-filled and auto-send

### Error Cards
- ✅ **Ledger Drill-Down modal** — transaction history + voucher details
- ✅ **Export to Tally modal** — XML / Excel / CSV with import instructions
- ✅ **Error Explanation Panel** — why error occurred + accounting rule violated
- ✅ **Auto-Correction Journal Entry** on each error card

### Documentation
- ✅ Created full `LOG.md` — complete technical build log
- ✅ Created `VirtualCA_Product_Overview.docx` — client-facing Word document
- ✅ Created Obsidian vault — 18 structured notes with wikilinks

---

## 14 March 2026

### Initial Build
- ✅ Created full UI prototype (`prototype.html` → renamed `index.html`)
- ✅ 8 pages: Login, Dashboard, Upload, Results, History, Ask CA, Journal Guide, Compliance
- ✅ Created `LOG.md` with initial product documentation
- ✅ Created `analyzer.py` — Python script for Excel analysis logic

---

## Upcoming (Phase 2)

- [ ] Convert prototype to React 18 app
- [ ] FastAPI backend with all endpoints
- [ ] Real Excel parser with pandas
- [ ] PostgreSQL database setup
- [ ] JWT auth
- [ ] Claude API live integration
- [ ] Deploy to Vercel + Railway

See [[16 - Build Phases & Roadmap]]
