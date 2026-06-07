const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
  HeadingLevel, AlignmentType, BorderStyle, WidthType, ShadingType,
  VerticalAlign, PageNumber, Header, Footer, ExternalHyperlink,
  PageBreak, LevelFormat, ImageRun
} = require('docx');
const fs = require('fs');

const BLUE      = "1E3A8A";
const LIGHT_BLUE = "2563EB";
const ACCENT    = "DBEAFE";
const GREEN     = "166534";
const GREEN_BG  = "DCFCE7";
const RED       = "991B1B";
const RED_BG    = "FEE2E2";
const YELLOW    = "92400E";
const YELLOW_BG = "FEF9C3";
const DARK      = "0F172A";
const GRAY      = "64748B";
const LIGHT_GRAY= "F8FAFC";
const WHITE     = "FFFFFF";
const BORDER_COLOR = "CBD5E1";

const border = { style: BorderStyle.SINGLE, size: 1, color: BORDER_COLOR };
const borders = { top: border, bottom: border, left: border, right: border };
const noBorder = { style: BorderStyle.NONE, size: 0, color: "FFFFFF" };
const noBorders = { top: noBorder, bottom: noBorder, left: noBorder, right: noBorder };

function h1(text) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_1,
    spacing: { before: 360, after: 160 },
    children: [new TextRun({ text, bold: true, size: 36, color: DARK, font: "Arial" })]
  });
}

function h2(text) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_2,
    spacing: { before: 280, after: 120 },
    children: [new TextRun({ text, bold: true, size: 28, color: BLUE, font: "Arial" })]
  });
}

function h3(text) {
  return new Paragraph({
    spacing: { before: 200, after: 80 },
    children: [new TextRun({ text, bold: true, size: 24, color: LIGHT_BLUE, font: "Arial" })]
  });
}

function body(text, options = {}) {
  return new Paragraph({
    spacing: { before: 60, after: 80 },
    children: [new TextRun({ text, size: 22, color: "374151", font: "Arial", ...options })]
  });
}

function bullet(text, bold = false) {
  return new Paragraph({
    numbering: { reference: "bullets", level: 0 },
    spacing: { before: 40, after: 40 },
    children: [new TextRun({ text, size: 22, color: "374151", font: "Arial", bold })]
  });
}

function spacer(lines = 1) {
  return new Paragraph({ spacing: { before: 0, after: lines * 80 }, children: [new TextRun("")] });
}

function pageBreak() {
  return new Paragraph({ children: [new PageBreak()] });
}

function divider() {
  return new Paragraph({
    spacing: { before: 160, after: 160 },
    border: { bottom: { style: BorderStyle.SINGLE, size: 4, color: BORDER_COLOR } },
    children: [new TextRun("")]
  });
}

// Blue highlight box
function infoBox(title, lines) {
  const rows = [];
  const children = [];
  if (title) children.push(new TextRun({ text: title, bold: true, size: 24, color: BLUE, font: "Arial" }));
  const cellChildren = title ? [new Paragraph({ spacing: { before: 0, after: 80 }, children })] : [];
  for (const line of lines) {
    cellChildren.push(new Paragraph({
      spacing: { before: 40, after: 40 },
      children: [new TextRun({ text: line, size: 22, color: "1E3A5F", font: "Arial" })]
    }));
  }
  return new Table({
    width: { size: 9360, type: WidthType.DXA },
    columnWidths: [9360],
    rows: [
      new TableRow({
        children: [
          new TableCell({
            borders,
            width: { size: 9360, type: WidthType.DXA },
            shading: { fill: ACCENT, type: ShadingType.CLEAR },
            margins: { top: 160, bottom: 160, left: 220, right: 220 },
            children: cellChildren
          })
        ]
      })
    ]
  });
}

// Feature table
function featureTable(headers, rows, colWidths) {
  const totalWidth = colWidths.reduce((a, b) => a + b, 0);
  const headerRow = new TableRow({
    children: headers.map((h, i) => new TableCell({
      borders,
      width: { size: colWidths[i], type: WidthType.DXA },
      shading: { fill: BLUE, type: ShadingType.CLEAR },
      margins: { top: 100, bottom: 100, left: 140, right: 140 },
      verticalAlign: VerticalAlign.CENTER,
      children: [new Paragraph({
        children: [new TextRun({ text: h, bold: true, size: 20, color: WHITE, font: "Arial" })]
      })]
    }))
  });

  const dataRows = rows.map((row, ri) => new TableRow({
    children: row.map((cell, ci) => new TableCell({
      borders,
      width: { size: colWidths[ci], type: WidthType.DXA },
      shading: { fill: ri % 2 === 0 ? WHITE : "F8FAFC", type: ShadingType.CLEAR },
      margins: { top: 80, bottom: 80, left: 140, right: 140 },
      children: [new Paragraph({
        children: [new TextRun({ text: cell, size: 20, color: "374151", font: "Arial" })]
      })]
    }))
  }));

  return new Table({
    width: { size: totalWidth, type: WidthType.DXA },
    columnWidths: colWidths,
    rows: [headerRow, ...dataRows]
  });
}

// Pricing card table
function pricingTable() {
  const plans = [
    { name: "Free",     price: "₹0/month",       color: GRAY,        bg: "F8FAFC", features: "2 uploads/month · Basic error detection · No AI chat" },
    { name: "Starter",  price: "₹499/month",      color: LIGHT_BLUE,  bg: ACCENT,   features: "10 uploads/month · AI chat (50 msgs) · Compliance alerts" },
    { name: "Pro",      price: "₹1,499/month",    color: "7C3AED",    bg: "F5F3FF", features: "Unlimited uploads · Unlimited AI chat · Full compliance suite · TDS + PT analysis" },
    { name: "CA Firm",  price: "₹3,999/month",    color: BLUE,        bg: "EFF6FF", features: "Multiple clients · Team access · Bank reconciliation · Priority support · Export all formats" },
  ];

  return new Table({
    width: { size: 9360, type: WidthType.DXA },
    columnWidths: [1800, 2200, 5360],
    rows: [
      new TableRow({
        children: [
          new TableCell({ borders, width: { size: 1800, type: WidthType.DXA }, shading: { fill: BLUE, type: ShadingType.CLEAR }, margins: { top: 80, bottom: 80, left: 140, right: 140 }, children: [new Paragraph({ children: [new TextRun({ text: "Plan", bold: true, size: 20, color: WHITE, font: "Arial" })] })] }),
          new TableCell({ borders, width: { size: 2200, type: WidthType.DXA }, shading: { fill: BLUE, type: ShadingType.CLEAR }, margins: { top: 80, bottom: 80, left: 140, right: 140 }, children: [new Paragraph({ children: [new TextRun({ text: "Price", bold: true, size: 20, color: WHITE, font: "Arial" })] })] }),
          new TableCell({ borders, width: { size: 5360, type: WidthType.DXA }, shading: { fill: BLUE, type: ShadingType.CLEAR }, margins: { top: 80, bottom: 80, left: 140, right: 140 }, children: [new Paragraph({ children: [new TextRun({ text: "What You Get", bold: true, size: 20, color: WHITE, font: "Arial" })] })] }),
        ]
      }),
      ...plans.map(p => new TableRow({
        children: [
          new TableCell({ borders, width: { size: 1800, type: WidthType.DXA }, shading: { fill: p.bg, type: ShadingType.CLEAR }, margins: { top: 80, bottom: 80, left: 140, right: 140 }, children: [new Paragraph({ children: [new TextRun({ text: p.name, bold: true, size: 20, color: p.color, font: "Arial" })] })] }),
          new TableCell({ borders, width: { size: 2200, type: WidthType.DXA }, shading: { fill: p.bg, type: ShadingType.CLEAR }, margins: { top: 80, bottom: 80, left: 140, right: 140 }, children: [new Paragraph({ children: [new TextRun({ text: p.price, bold: true, size: 20, color: "374151", font: "Arial" })] })] }),
          new TableCell({ borders, width: { size: 5360, type: WidthType.DXA }, shading: { fill: p.bg, type: ShadingType.CLEAR }, margins: { top: 80, bottom: 80, left: 140, right: 140 }, children: [new Paragraph({ children: [new TextRun({ text: p.features, size: 20, color: "374151", font: "Arial" })] })] }),
        ]
      }))
    ]
  });
}

// ── ROI savings box
function roiBox() {
  const items = [
    ["CA Audit Fees Saved",       "₹15,000 – ₹40,000/year", "Catch errors before CA review"],
    ["Accountant Error Rework",   "8–12 hrs/month",          "Auto-detect wrong ledger groupings"],
    ["TDS Late Interest Avoided", "₹1,000 – ₹10,000/year",  "Alerts before 7th of every month"],
    ["PT Penalty Avoided",        "₹200–₹1,000/year",        "21st deadline never missed"],
    ["Bank Recon Time",           "4–6 hrs/month saved",     "Auto-match 90%+ transactions"],
    ["Compliance Penalties",      "Up to ₹50,000/year",      "Calendar with overdue alerts"],
  ];

  return new Table({
    width: { size: 9360, type: WidthType.DXA },
    columnWidths: [3200, 2400, 3760],
    rows: [
      new TableRow({
        children: [
          new TableCell({ borders, width:{size:3200,type:WidthType.DXA}, shading:{fill:GREEN,type:ShadingType.CLEAR}, margins:{top:80,bottom:80,left:140,right:140}, children:[new Paragraph({children:[new TextRun({text:"What You Save",bold:true,size:20,color:WHITE,font:"Arial"})]})] }),
          new TableCell({ borders, width:{size:2400,type:WidthType.DXA}, shading:{fill:GREEN,type:ShadingType.CLEAR}, margins:{top:80,bottom:80,left:140,right:140}, children:[new Paragraph({children:[new TextRun({text:"Amount / Time",bold:true,size:20,color:WHITE,font:"Arial"})]})] }),
          new TableCell({ borders, width:{size:3760,type:WidthType.DXA}, shading:{fill:GREEN,type:ShadingType.CLEAR}, margins:{top:80,bottom:80,left:140,right:140}, children:[new Paragraph({children:[new TextRun({text:"How",bold:true,size:20,color:WHITE,font:"Arial"})]})] }),
        ]
      }),
      ...items.map((row, i) => new TableRow({
        children: [
          new TableCell({ borders, width:{size:3200,type:WidthType.DXA}, shading:{fill: i%2===0 ? WHITE : GREEN_BG, type:ShadingType.CLEAR}, margins:{top:80,bottom:80,left:140,right:140}, children:[new Paragraph({children:[new TextRun({text:row[0],bold:true,size:20,color:"166534",font:"Arial"})]})] }),
          new TableCell({ borders, width:{size:2400,type:WidthType.DXA}, shading:{fill: i%2===0 ? WHITE : GREEN_BG, type:ShadingType.CLEAR}, margins:{top:80,bottom:80,left:140,right:140}, children:[new Paragraph({children:[new TextRun({text:row[1],bold:true,size:20,color:"374151",font:"Arial"})]})] }),
          new TableCell({ borders, width:{size:3760,type:WidthType.DXA}, shading:{fill: i%2===0 ? WHITE : GREEN_BG, type:ShadingType.CLEAR}, margins:{top:80,bottom:80,left:140,right:140}, children:[new Paragraph({children:[new TextRun({text:row[2],size:20,color:"374151",font:"Arial"})]})] }),
        ]
      }))
    ]
  });
}

const doc = new Document({
  numbering: {
    config: [
      {
        reference: "bullets",
        levels: [{
          level: 0, format: LevelFormat.BULLET, text: "\u2022", alignment: AlignmentType.LEFT,
          style: { paragraph: { indent: { left: 560, hanging: 280 } } }
        }]
      },
      {
        reference: "bullets2",
        levels: [{
          level: 0, format: LevelFormat.BULLET, text: "\u2713", alignment: AlignmentType.LEFT,
          style: { paragraph: { indent: { left: 560, hanging: 280 } } }
        }]
      }
    ]
  },
  styles: {
    default: {
      document: { run: { font: "Arial", size: 22 } }
    },
    paragraphStyles: [
      { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 36, bold: true, font: "Arial", color: DARK },
        paragraph: { spacing: { before: 360, after: 160 }, outlineLevel: 0 } },
      { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 28, bold: true, font: "Arial", color: BLUE },
        paragraph: { spacing: { before: 280, after: 120 }, outlineLevel: 1 } },
    ]
  },
  sections: [{
    properties: {
      page: {
        size: { width: 12240, height: 15840 },
        margin: { top: 1440, right: 1260, bottom: 1440, left: 1260 }
      }
    },
    headers: {
      default: new Header({
        children: [
          new Paragraph({
            border: { bottom: { style: BorderStyle.SINGLE, size: 4, color: BORDER_COLOR } },
            spacing: { before: 0, after: 120 },
            children: [
              new TextRun({ text: "VirtualCA", bold: true, size: 20, color: LIGHT_BLUE, font: "Arial" }),
              new TextRun({ text: "   |   Your AI-Powered Accounting Assistant", size: 20, color: GRAY, font: "Arial" }),
            ]
          })
        ]
      })
    },
    footers: {
      default: new Footer({
        children: [
          new Paragraph({
            border: { top: { style: BorderStyle.SINGLE, size: 4, color: BORDER_COLOR } },
            spacing: { before: 120, after: 0 },
            alignment: AlignmentType.CENTER,
            children: [
              new TextRun({ text: "Confidential   |   VirtualCA Product Overview   |   Page ", size: 18, color: GRAY, font: "Arial" }),
              new TextRun({ children: [PageNumber.CURRENT], size: 18, color: GRAY, font: "Arial" }),
            ]
          })
        ]
      })
    },
    children: [

      // ══════════════════════════════════════════
      // COVER
      // ══════════════════════════════════════════
      spacer(3),
      new Paragraph({
        alignment: AlignmentType.CENTER,
        spacing: { before: 0, after: 80 },
        children: [new TextRun({ text: "VirtualCA", bold: true, size: 72, color: BLUE, font: "Arial" })]
      }),
      new Paragraph({
        alignment: AlignmentType.CENTER,
        spacing: { before: 0, after: 160 },
        children: [new TextRun({ text: "Your AI-Powered Accounting Assistant", size: 32, color: GRAY, font: "Arial" })]
      }),
      new Paragraph({
        alignment: AlignmentType.CENTER,
        spacing: { before: 0, after: 80 },
        border: { top: { style: BorderStyle.SINGLE, size: 8, color: LIGHT_BLUE }, bottom: { style: BorderStyle.SINGLE, size: 8, color: LIGHT_BLUE } },
        children: [new TextRun({ text: '  "Upload your Tally file. Get a full audit in 30 seconds."  ', size: 28, color: LIGHT_BLUE, italics: true, font: "Arial" })]
      }),
      spacer(2),
      new Paragraph({
        alignment: AlignmentType.CENTER,
        spacing: { before: 0, after: 80 },
        children: [new TextRun({ text: "Product Overview & Feature Guide", bold: true, size: 26, color: DARK, font: "Arial" })]
      }),
      new Paragraph({
        alignment: AlignmentType.CENTER,
        spacing: { before: 0, after: 80 },
        children: [new TextRun({ text: "March 2026  |  Prepared for: Clients & Partners", size: 22, color: GRAY, font: "Arial" })]
      }),
      spacer(4),

      pageBreak(),

      // ══════════════════════════════════════════
      // 1. WHAT IS VIRTUALCA
      // ══════════════════════════════════════════
      h1("1. What is VirtualCA?"),
      body("VirtualCA is an AI-powered SaaS platform built specifically for Indian small and medium businesses (SMBs) and Chartered Accountant (CA) firms that use Tally for accounting."),
      spacer(),
      body("Most businesses using Tally make accounting errors they never know about — wrong ledger groupings, missed TDS deposits, unreconciled bank entries, and PT defaults. These small mistakes compound over months and result in incorrect P&L reports, GST mismatches, and costly penalties."),
      spacer(),
      body("VirtualCA solves this by acting as a 24/7 AI accountant that reads your Tally data, instantly identifies every error, explains exactly what went wrong, and tells you step-by-step how to fix it inside Tally — in under 30 seconds."),
      spacer(),
      infoBox("One-Line Summary", [
        "Upload your Tally file \u2192 AI scans every ledger \u2192 Flags all errors with fix instructions \u2192 Export corrections back to Tally."
      ]),
      spacer(),

      divider(),

      // ══════════════════════════════════════════
      // 2. WHO IS IT FOR
      // ══════════════════════════════════════════
      h1("2. Who is VirtualCA For?"),
      spacer(),
      featureTable(
        ["User Type", "Their Problem", "How VirtualCA Helps"],
        [
          ["SMB Owner / Director",   "Does not know if books are correct",         "Gets a full audit report in 30 seconds"],
          ["In-house Accountant",    "Makes ledger grouping errors regularly",      "Error list with exact Tally fix navigation"],
          ["CA Firm",                "Reviews 10–20 clients manually every month",  "Multi-client dashboard, team assign workflow"],
          ["Startup Finance Team",   "Misses compliance deadlines (TDS, PT, GST)",  "Compliance calendar with auto-alerts"],
          ["Business Owner Kolkata", "PT deductions & Grips deposit always missed", "Auto PT slab calculation + Grips guide"],
        ],
        [2520, 3240, 3600]
      ),
      spacer(),

      pageBreak(),

      // ══════════════════════════════════════════
      // 3. FEATURES
      // ══════════════════════════════════════════
      h1("3. Complete Feature List"),

      // 3.1 Upload
      h2("3.1  Smart Upload & Data Mapping"),
      body("VirtualCA accepts data in all formats that Tally can export — no special setup required."),
      spacer(),
      featureTable(
        ["File Type", "How to Export from Tally", "What We Analyze"],
        [
          ["Excel Trial Balance (.xlsx/.csv)", "Alt+E from Trial Balance screen",         "All ledgers, groups, balances"],
          ["Tally XML (.xml)",                 "Gateway \u2192 Export Data \u2192 Masters", "Full voucher + ledger data"],
          ["Ledger Dump (.xlsx)",              "Account Books \u2192 Ledger \u2192 Alt+E",  "Transaction-level detail"],
          ["Bank Statement (.csv/.xlsx)",      "Download from net banking portal",         "Bank reconciliation"],
          ["GST JSON (.json)",                 "Download GSTR-2A/2B from GST portal",      "GST mismatch detection"],
        ],
        [2800, 3200, 3360]
      ),
      spacer(),
      body("After upload, VirtualCA shows a Data Mapping Screen where you confirm column headings and map custom ledger group names to standard Tally groups. The system remembers your preferences for future uploads."),
      spacer(),

      // 3.2 Analysis Results
      h2("3.2  Instant Analysis Results"),
      body("Every ledger in your file is checked against a comprehensive rule library. Results are displayed in a clean, colour-coded report:"),
      spacer(),
      featureTable(
        ["Colour", "Status",   "Meaning"],
        [
          ["Red",    "Critical", "Wrong ledger group, balance error, or compliance violation — must fix immediately"],
          ["Yellow", "Review",   "Needs attention — possible misclassification or anomaly"],
          ["Green",  "OK",       "Ledger is correctly grouped and balanced"],
          ["Grey",   "Ignored",  "User has acknowledged and chosen to skip"],
        ],
        [1200, 1800, 6360]
      ),
      spacer(),
      body("Common errors detected include:"),
      bullet("TDS Receivable booked under Duties & Taxes instead of Current Assets"),
      bullet("GST Input Credit (ITC) placed in wrong group"),
      bullet("Bank Interest Received booked as Expense instead of Indirect Income"),
      bullet("Capital / Partner Capital placed under Loans"),
      bullet("Drawings booked as Indirect Expenses"),
      bullet("Prepaid Expenses not under Current Assets"),
      bullet("Suspense Account with non-zero balance"),
      bullet("Debtor with credit balance / Creditor with debit balance"),
      bullet("Difference in Opening Balance (Dr total \u2260 Cr total)"),
      bullet("PT Payable placed under wrong group"),
      bullet("Sales Returns greater than Sales"),
      spacer(),

      // 3.3 Error Explanation
      h2("3.3  Error Explanation Panel"),
      body("When you click on any error, VirtualCA shows a full explanation panel — not just a flag, but a complete breakdown:"),
      spacer(),
      featureTable(
        ["Section",              "What it Shows"],
        [
          ["Why This Error Occurred",       "Plain-English explanation of what went wrong and why it matters"],
          ["Accounting Rule Violated",      "The specific standard breached (e.g. AS-2, Matching Principle, Double Entry)"],
          ["Current vs Correct Group",      "Visual side-by-side: wrong group (red) \u2192 correct group (green)"],
          ["Auto-Correction Journal Entry", "Ready-made journal entry — Dr and Cr lines with amounts"],
          ["How to Fix in Tally",           "Exact Tally navigation path, step by step"],
        ],
        [3200, 6160]
      ),
      spacer(),
      infoBox("Example — Wrong Ledger Grouping", [
        "Problem:  Bank Interest Received is booked under Indirect Expenses",
        "Rule:     Income must be classified as Indirect Income, not Expense (Matching Principle)",
        "Fix:      Dr Bank Interest Received A/c   Cr Indirect Income (re-group in Tally)",
        "Tally:    Gateway of Tally \u2192 Accounts Info \u2192 Ledgers \u2192 Alter \u2192 Change Group"
      ]),
      spacer(),

      // 3.4 Ledger Drill-Down
      h2("3.4  Ledger Drill-Down"),
      body("Click any ledger to instantly open its full transaction history — without going back to Tally:"),
      bullet("Opening Balance, Total Debits, Total Credits, Closing Balance"),
      bullet("Full transaction history table: Date, Voucher No, Narration, Dr/Cr Amount"),
      bullet("Related vouchers list: Voucher type, Party name, Amount"),
      spacer(),

      // 3.5 Fix Workflow
      h2("3.5  Fix Workflow & Team Collaboration"),
      body("VirtualCA is not just a detector — it is a full fix management system. Every error has a workflow status:"),
      spacer(),
      featureTable(
        ["Status",      "Meaning"],
        [
          ["Open",        "Error detected, not yet actioned"],
          ["In Progress", "Accountant has started working on this fix"],
          ["Resolved",    "Fix has been applied in Tally"],
          ["Ignored",     "Acknowledged, decided not to fix (with reason)"],
        ],
        [2400, 6960]
      ),
      spacer(),
      body("For each error, you can also:"),
      bullet("Assign to Accountant — send the error to a specific team member"),
      bullet("Add Comment — write notes, attach instructions, have a conversation thread"),
      bullet("Mark Resolved — close the error with a timestamp and your name"),
      spacer(),

      pageBreak(),

      // 3.6 Export to Tally
      h2("3.6  Export Back to Tally"),
      body("Once corrections are reviewed, export them directly back into Tally. Three formats supported:"),
      spacer(),
      featureTable(
        ["Export Format",             "Use For",                                   "How to Import"],
        [
          ["Tally XML (.xml)",         "Direct Tally import — full voucher data",   "Gateway \u2192 Import Data \u2192 Vouchers"],
          ["Excel Correction Sheet",   "Share with accountant for manual entry",    "Open in Excel, reference while fixing"],
          ["Tally Import CSV",         "Simplified import for basic corrections",   "Gateway \u2192 Import Data \u2192 Masters"],
        ],
        [2800, 3400, 3160]
      ),
      spacer(),

      // 3.7 Bank Reconciliation
      h2("3.7  Bank Reconciliation Module"),
      body("Upload your bank statement and Tally bank ledger — VirtualCA automatically matches every transaction:"),
      spacer(),
      featureTable(
        ["Category",           "What It Means",                                         "Action Required"],
        [
          ["Matched (91.6%)",   "Transaction found in both bank statement and Tally",    "None — all clean"],
          ["Unmatched",         "Entry in bank statement but missing in Tally",          "Pass journal entry in Tally"],
          ["Tally Only",        "Entry in Tally but not in bank — possible error",       "Verify if cheque is outstanding or wrong entry"],
          ["Duplicate",         "Same amount + same date appears twice in Tally",        "Delete the duplicate voucher"],
        ],
        [2200, 4200, 2960]
      ),
      spacer(),
      body("For each unmatched entry, VirtualCA suggests the journal entry you need to pass in Tally to reconcile it."),
      spacer(),

      // 3.8 TDS Analysis
      h2("3.8  TDS Analysis"),
      body("VirtualCA provides a complete TDS health check across all sections:"),
      bullet("Section-wise breakdown: 194C (Contractor), 194J (Professional), 194I (Rent), 192 (Salary), 194H, 194D, 194A"),
      bullet("Deducted vs Deposited vs Pending — at a glance"),
      bullet("Late Payment Interest calculator — 1.5% per month on pending TDS (Section 201(1A))"),
      bullet("TDS Return Mismatch — compares Form 26AS against your books, shows differences"),
      bullet("Due date alert — TDS must be deposited by 7th of every month"),
      spacer(),
      infoBox("Why This Matters", [
        "Late TDS deposit attracts interest at 1.5% per month plus penalty of \u20b9200/day under Section 234E.",
        "VirtualCA calculates your exact interest liability so you know before the CA finds it."
      ]),
      spacer(),

      // 3.9 PT Analysis
      h2("3.9  Professional Tax (PT) Analysis — Kolkata / West Bengal"),
      body("Professional Tax is a state-level tax deducted from employee salaries. VirtualCA handles the full PT workflow for West Bengal:"),
      spacer(),
      featureTable(
        ["Gross Monthly Salary",        "PT Deduction (WB)"],
        [
          ["Up to \u20b910,000",          "Nil"],
          ["\u20b910,001 \u2013 \u20b915,000", "\u20b9110 per month"],
          ["\u20b915,001 \u2013 \u20b925,000", "\u20b9130 per month"],
          ["\u20b925,001 \u2013 \u20b940,000", "\u20b9150 per month"],
          ["Above \u20b940,000",           "\u20b9200 per month"],
        ],
        [4680, 4680]
      ),
      spacer(),
      body("VirtualCA provides:"),
      bullet("Employee-wise PT calculation based on salary slabs"),
      bullet("PT Deducted vs PT Deposited tracking"),
      bullet("Due date reminder: 21st of every month via Grips portal (wbifms.gov.in)"),
      bullet("Ready-made Tally journal entries for PT deduction and PT deposit"),
      bullet("Step-by-step Grips WB payment instructions"),
      spacer(),

      pageBreak(),

      // 3.10 AI Chat
      h2("3.10  Ask Your CA — AI Chat"),
      body("Every analysis is connected to an intelligent AI assistant that reads your actual uploaded data. You can ask any accounting question and get a specific, data-driven answer based on your books."),
      spacer(),
      infoBox("Real Example — Contextual AI Answer", [
        "You ask:  \"Why is my profit low this month?\"",
        "",
        "VirtualCA answers:",
        "  1. Purchases increased 28% vs last month (\u20b94.2L vs \u20b93.3L)",
        "  2. Outstanding debtors increased by \u20b93.2L (Raj Traders, ABC Ltd)",
        "  3. 4 GST mismatches detected in Input Credit (\u20b918,400 blocked)",
        "  4. Bank Interest \u20b925,000 booked as Expense (reduces profit incorrectly)",
        "",
        "All answers are based on your specific uploaded file."
      ]),
      spacer(),
      body("Quick-ask chips pre-loaded in the chat:"),
      bullet("Top 3 errors to fix first?"),
      bullet("TDS pending amount and interest?"),
      bullet("Debtors with credit balance?"),
      bullet("Journal entries to fix all errors?"),
      bullet("How to improve compliance score?"),
      spacer(),

      // 3.11 Compliance Calendar
      h2("3.11  Compliance Calendar"),
      body("Never miss a statutory deadline again. VirtualCA tracks all Indian compliance due dates and shows live status:"),
      spacer(),
      featureTable(
        ["Due Date",                  "Compliance Item",          "Penalty if Missed"],
        [
          ["7th every month",          "TDS Deposit",              "\u20b9200/day + 1.5%/month interest"],
          ["11th every month",         "GSTR-1 Filing",            "\u20b9200/day (CGST + SGST)"],
          ["20th every month",         "GSTR-3B Filing",           "\u20b9200/day + late fee"],
          ["21st every month",         "PT Deposit (Kolkata/WB)",  "Penalty + interest from WB Govt"],
          ["Last day of month",        "Salary Payment",           "Labour law violation"],
          ["15 Jun/Sep/Dec/Mar",       "Advance Tax",              "Interest under Sec 234B & 234C"],
          ["31 Jul / 31 Oct",          "TDS Quarterly Returns",    "\u20b9200/day under Section 234E"],
          ["31st July",                "ITR Filing (non-audit)",   "Penalty up to \u20b95,000"],
          ["31st October",             "ITR Filing (audit cases)", "Penalty up to \u20b910,000"],
        ],
        [2400, 3400, 3560]
      ),
      spacer(),
      body("Each item shows: days remaining (or OVERDUE in red), a Mark Done button, and penalty details. Dashboard shows a live Compliance Health Score (0–100%)."),
      spacer(),

      // 3.12 Journal Entry Guide
      h2("3.12  Journal Entry Guide"),
      body("Built-in library of all standard Tally journal entries — searchable, with Dr/Cr format and Tally navigation path:"),
      bullet("Sales Invoice, Purchase Invoice, Bank Receipt, Payment"),
      bullet("TDS Deduction entries (all sections)"),
      bullet("Depreciation, Salary with PT, Advance payment"),
      bullet("GST entries — IGST, CGST, SGST"),
      spacer(),

      pageBreak(),

      // ══════════════════════════════════════════
      // 4. TIME & MONEY SAVINGS
      // ══════════════════════════════════════════
      h1("4. How Much Time & Money Does VirtualCA Save?"),
      spacer(),
      roiBox(),
      spacer(2),
      infoBox("Total Annual Savings Estimate for a Typical SMB", [
        "Time saved:   25\u201340 hours per year (accountant + owner combined)",
        "Money saved:  \u20b930,000 \u2013 \u20b91,00,000 per year (penalties + CA fees + rework)",
        "VirtualCA Pro costs:  \u20b91,499/month = \u20b917,988/year",
        "",
        "Net benefit:  \u20b912,000 \u2013 \u20b982,000 in Year 1 alone."
      ]),
      spacer(),

      pageBreak(),

      // ══════════════════════════════════════════
      // 5. PRICING
      // ══════════════════════════════════════════
      h1("5. Pricing Plans"),
      spacer(),
      pricingTable(),
      spacer(2),
      body("All plans include: Secure cloud storage, SSL encryption, Indian data residency, and free onboarding support."),
      spacer(),
      body("CA Firm plan includes multi-client management — handle all your clients from one dashboard, assign work to team members, and generate separate reports per client."),
      spacer(),

      divider(),

      // ══════════════════════════════════════════
      // 6. HOW IT WORKS (STEP BY STEP)
      // ══════════════════════════════════════════
      h1("6. How It Works — Step by Step"),
      spacer(),
      featureTable(
        ["Step", "What You Do",                     "What VirtualCA Does"],
        [
          ["1", "Export your file from Tally",       "Accepts Excel, XML, Ledger, Bank Statement, GST JSON"],
          ["2", "Upload to VirtualCA",               "Parses and maps all columns automatically"],
          ["3", "Confirm data mapping",              "You approve the column mapping (takes 30 seconds)"],
          ["4", "Click Run Analysis",                "AI scans all ledgers against 20+ accounting rules"],
          ["5", "Review the report",                 "Colour-coded errors with explanations and journal entries"],
          ["6", "Fix errors in Tally",               "Follow the exact Tally navigation steps shown"],
          ["7", "Export corrections",                "Download XML or Excel to import back into Tally"],
          ["8", "Mark items resolved",               "Track progress with your team, add comments"],
          ["9", "Ask the AI questions",              "Get data-specific answers from the AI CA assistant"],
          ["10","Monitor compliance",                "Calendar shows next due dates, mark done when filed"],
        ],
        [600, 3400, 5360]
      ),
      spacer(),

      pageBreak(),

      // ══════════════════════════════════════════
      // 7. SECURITY & DATA PRIVACY
      // ══════════════════════════════════════════
      h1("7. Security & Data Privacy"),
      bullet("All data is encrypted in transit (SSL/TLS) and at rest (AES-256)"),
      bullet("Indian data residency — your data does not leave India"),
      bullet("Each company's data is completely isolated — no cross-access"),
      bullet("Role-based access: Admin, Accountant, Viewer — you control who sees what"),
      bullet("Files are processed and stored securely on AWS / Cloudflare infrastructure"),
      bullet("No data is ever used to train AI models"),
      spacer(),

      divider(),

      // ══════════════════════════════════════════
      // 8. SUPPORTED BANKS & FORMATS
      // ══════════════════════════════════════════
      h1("8. Supported Banks & File Formats"),
      h2("Bank Statement Import"),
      body("Supports CSV and Excel exports from all major Indian banks:"),
      bullet("HDFC Bank"),
      bullet("ICICI Bank"),
      bullet("State Bank of India (SBI)"),
      bullet("Axis Bank"),
      bullet("Kotak Mahindra Bank"),
      bullet("Yes Bank, Punjab National Bank, Bank of Baroda, and more"),
      spacer(),
      h2("Tally Compatibility"),
      bullet("Tally ERP 9 (all versions)"),
      bullet("TallyPrime 1.x, 2.x, 3.x, 4.x"),
      bullet("Supports all standard Tally export formats"),
      spacer(),

      pageBreak(),

      // ══════════════════════════════════════════
      // 9. ROADMAP
      // ══════════════════════════════════════════
      h1("9. What Is Coming Next"),
      spacer(),
      featureTable(
        ["Phase", "Features"],
        [
          ["Now Available",   "Analysis, Error Explanation, Drill-Down, Fix Workflow, TDS, PT, Bank Recon, AI Chat, Compliance Calendar, Export to Tally"],
          ["Q2 2026",         "PDF audit report generation, Email & WhatsApp compliance reminders, Multi-client CA dashboard, Razorpay payment integration"],
          ["Q3 2026",         "Direct Tally integration (no export needed), GSTR-2A/2B reconciliation, P&L and Balance Sheet validation, Mobile app"],
          ["Q4 2026",         "Multi-branch support, WhatsApp bot for quick queries, Bank auto-import (HDFC/ICICI API), Custom rule builder for CA firms"],
        ],
        [2000, 7360]
      ),
      spacer(),

      divider(),

      // ══════════════════════════════════════════
      // 10. CONTACT
      // ══════════════════════════════════════════
      h1("10. Get Started Today"),
      spacer(),
      infoBox("Contact & Demo", [
        "To schedule a live demo or start your free trial, contact:",
        "",
        "Name:     Sagar Pathak",
        "Product:  VirtualCA",
        "Email:    admin@company.com",
        "",
        "Free plan available — no credit card required.",
        "Pro plan starts at \u20b91,499/month. CA Firm plan at \u20b93,999/month."
      ]),
      spacer(2),
      new Paragraph({
        alignment: AlignmentType.CENTER,
        spacing: { before: 160, after: 80 },
        children: [new TextRun({ text: "VirtualCA — Upload your Tally file. Get a full audit in 30 seconds.", italics: true, size: 24, color: LIGHT_BLUE, font: "Arial" })]
      }),
      new Paragraph({
        alignment: AlignmentType.CENTER,
        spacing: { before: 0, after: 0 },
        children: [new TextRun({ text: "Confidential — For Client Use Only", size: 18, color: GRAY, font: "Arial" })]
      }),

    ]
  }]
});

Packer.toBuffer(doc).then(buffer => {
  fs.writeFileSync('C:\\Users\\sagar\\Downloads\\tally_saas\\VirtualCA_Product_Overview.docx', buffer);
  console.log('Done! File saved: VirtualCA_Product_Overview.docx');
});
