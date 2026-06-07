with open('index.html', 'r', encoding='utf-8') as f:
    content = f.read()

# ── DASHBOARD: stats ──────────────────────────────────────────────────────────
content = content.replace(
    '<div class="text-3xl font-bold text-gray-800">24</div>\n          <div class="text-xs text-green-500 mt-1"><i class="fas fa-arrow-up"></i> 8 this month</div>',
    '<div class="text-3xl font-bold text-gray-800" id="dash-total">0</div>\n          <div class="text-xs text-gray-400 mt-1">Run your first audit</div>'
)
content = content.replace(
    '<div class="text-3xl font-bold text-red-600">7</div>\n          <div class="text-xs text-red-400 mt-1">In last upload</div>',
    '<div class="text-3xl font-bold text-red-600" id="dash-critical">—</div>\n          <div class="text-xs text-gray-400 mt-1">No audit yet</div>'
)
content = content.replace(
    '<div class="text-3xl font-bold text-yellow-600">12</div>\n          <div class="text-xs text-yellow-400 mt-1">In last upload</div>',
    '<div class="text-3xl font-bold text-yellow-600" id="dash-warnings">—</div>\n          <div class="text-xs text-gray-400 mt-1">No audit yet</div>'
)
content = content.replace(
    '<div class="text-3xl font-bold text-gray-800">72%</div>\n          <div class="progress-bar mt-2"><div class="progress-fill" style="width:72%"></div></div>',
    '<div class="text-3xl font-bold text-gray-800" id="dash-score">—</div>\n          <div class="progress-bar mt-2"><div class="progress-fill" id="dash-score-bar" style="width:0%"></div></div>'
)

# ── DASHBOARD: recent analyses — replace with empty state ─────────────────────
old_recent = '''          <div class="space-y-3">
            <div onclick="showPage('results')" class="flex items-center gap-4 p-4 rounded-xl border border-gray-100 hover:border-blue-200 hover:bg-blue-50/30 cursor-pointer transition">
              <div class="w-10 h-10 rounded-xl bg-red-50 flex items-center justify-center flex-shrink-0">
                <i class="fas fa-file-excel text-red-500"></i>
              </div>
              <div class="flex-1">
                <div class="font-medium text-gray-800 text-sm">AJKL Trial Balance</div>
                <div class="text-xs text-gray-400 mt-0.5">Uploaded today • FY 2025-26</div>
              </div>
              <div class="flex items-center gap-2">
                <span class="tag-critical text-xs px-2.5 py-1 rounded-full font-medium">7 Critical</span>
                <span class="tag-review text-xs px-2.5 py-1 rounded-full font-medium">12 Review</span>
              </div>
              <i class="fas fa-chevron-right text-gray-400 text-sm"></i>
            </div>
            <div class="flex items-center gap-4 p-4 rounded-xl border border-gray-100 hover:border-blue-200 hover:bg-blue-50/30 cursor-pointer transition">
              <div class="w-10 h-10 rounded-xl bg-green-50 flex items-center justify-center flex-shrink-0">
                <i class="fas fa-file-excel text-green-500"></i>
              </div>
              <div class="flex-1">
                <div class="font-medium text-gray-800 text-sm">AJKL Trial Balance</div>
                <div class="text-xs text-gray-400 mt-0.5">3 days ago • FY 2024-25</div>
              </div>
              <div class="flex items-center gap-2">
                <span class="tag-ok text-xs px-2.5 py-1 rounded-full font-medium">All Clear</span>
              </div>
              <i class="fas fa-chevron-right text-gray-400 text-sm"></i>
            </div>
            <div class="flex items-center gap-4 p-4 rounded-xl border border-gray-100 hover:border-blue-200 hover:bg-blue-50/30 cursor-pointer transition">
              <div class="w-10 h-10 rounded-xl bg-yellow-50 flex items-center justify-center flex-shrink-0">
                <i class="fas fa-file-excel text-yellow-500"></i>
              </div>
              <div class="flex-1">
                <div class="font-medium text-gray-800 text-sm">AJKL Trial Balance</div>
                <div class="text-xs text-gray-400 mt-0.5">1 week ago • FY 2024-25</div>
              </div>
              <div class="flex items-center gap-2">
                <span class="tag-review text-xs px-2.5 py-1 rounded-full font-medium">5 Review</span>
              </div>
              <i class="fas fa-chevron-right text-gray-400 text-sm"></i>
            </div>
          </div>'''

new_recent = '''          <div id="dash-recent-list">
            <div class="flex flex-col items-center justify-center py-12 text-center">
              <div class="w-14 h-14 rounded-2xl bg-gray-50 flex items-center justify-center mb-3">
                <i class="fas fa-folder-open text-gray-300 text-2xl"></i>
              </div>
              <div class="text-sm font-medium text-gray-400">No audits yet</div>
              <div class="text-xs text-gray-300 mt-1">Run Full Audit to see results here</div>
              <button onclick="showPage('fullaudit')" class="mt-4 bg-orange-500 text-white text-xs px-4 py-2 rounded-xl font-semibold hover:bg-orange-600 transition">Run Full Audit</button>
            </div>
          </div>'''

content = content.replace(old_recent, new_recent)

# ── DASHBOARD: compliance alerts — replace with empty state ───────────────────
old_compliance = '''          <div class="space-y-3">
            <div class="compliance-card overdue rounded-xl p-3">
              <div class="flex items-center gap-2 mb-1">
                <i class="fas fa-exclamation-circle text-red-500 text-sm"></i>
                <span class="text-sm font-semibold text-red-700">TDS Deposit</span>
              </div>
              <div class="text-xs text-red-600">Due: 7th March 2026</div>
              <div class="text-xs text-red-500 mt-1 pulse">⚠ Overdue by 7 days</div>
            </div>
            <div class="compliance-card upcoming rounded-xl p-3">
              <div class="flex items-center gap-2 mb-1">
                <i class="fas fa-clock text-yellow-500 text-sm"></i>
                <span class="text-sm font-semibold text-yellow-700">PT (Kolkata)</span>
              </div>
              <div class="text-xs text-yellow-600">Due: 21st March 2026</div>
              <div class="text-xs text-yellow-500 mt-1">7 days remaining</div>
            </div>
            <div class="compliance-card done rounded-xl p-3">
              <div class="flex items-center gap-2 mb-1">
                <i class="fas fa-check-circle text-green-500 text-sm"></i>
                <span class="text-sm font-semibold text-green-700">Salary — Feb</span>
              </div>
              <div class="text-xs text-green-600">Paid: 28th Feb 2026</div>
              <div class="text-xs text-green-500 mt-1">✓ Completed</div>
            </div>
          </div>
          <button onclick="showPage('compliance')" class="w-full mt-4 text-blue-600 text-sm border border-blue-200 rounded-xl py-2 hover:bg-blue-50 transition">
            View Full Calendar
          </button>'''

new_compliance = '''          <div class="flex flex-col items-center justify-center py-8 text-center">
            <i class="fas fa-calendar-check text-gray-200 text-3xl mb-2"></i>
            <div class="text-xs text-gray-400">No compliance items yet</div>
          </div>
          <button onclick="showPage('compliance')" class="w-full mt-4 text-blue-600 text-sm border border-blue-200 rounded-xl py-2 hover:bg-blue-50 transition">
            View Full Calendar
          </button>'''

content = content.replace(old_compliance, new_compliance)

# ── DASHBOARD: "2 Due" badge ──────────────────────────────────────────────────
content = content.replace(
    '<span class="bg-red-100 text-red-600 text-xs px-2 py-1 rounded-full">2 Due</span>',
    '<span class="bg-gray-100 text-gray-400 text-xs px-2 py-1 rounded-full">0 Due</span>'
)

with open('index.html', 'w', encoding='utf-8') as f:
    f.write(content)
print('Done. Cleaned all demo data.')
