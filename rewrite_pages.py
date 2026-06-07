with open('index.html', 'r', encoding='utf-8') as f:
    content = f.read()

# ══════════════════════════════════════════════════════════════════════════════
# 1. UPLOAD & ANALYZE — replace fake simulateUpload with real API call
#    Find the step-1 drop zone section and replace the Choose File input
#    so it actually triggers a real upload to /api/audit
# ══════════════════════════════════════════════════════════════════════════════

old_upload_step1_inner = '''          <!-- Other formats link -->
          <div class="text-center">
            <button onclick="toggleOtherFormats()" class="text-xs text-gray-400 hover:text-gray-600 transition">
              <i class="fas fa-plus-circle mr-1"></i>Using Tally XML, Ledger Dump, or GST JSON instead?
            </button>
          </div>'''

# We leave the upload page as-is but wire the Choose File button to real upload
# The existing simulateUpload() will be replaced in JS section below

# ══════════════════════════════════════════════════════════════════════════════
# 2. HISTORY PAGE — replace hardcoded table rows with dynamic rendering
# ══════════════════════════════════════════════════════════════════════════════
old_history_table = '''        <table class="w-full text-sm">
          <thead><tr class="text-left text-gray-400 border-b border-gray-100 text-xs uppercase">
            <th class="pb-3 font-medium">File Name</th><th class="pb-3 font-medium">Uploaded By</th>
            <th class="pb-3 font-medium">Date</th><th class="pb-3 font-medium">Period</th>
            <th class="pb-3 font-medium">Result</th><th class="pb-3 font-medium">Action</th>
          </tr></thead>
          <tbody class="divide-y divide-gray-50">
            <tr class="hover:bg-gray-50 cursor-pointer" onclick="showPage('results')">
              <td class="py-3.5"><div class="flex items-center gap-2"><i class="fas fa-file-excel text-green-500"></i><span class="font-medium text-gray-800">AJKL Traial balance.xlsx</span></div></td>
              <td class="py-3.5 text-gray-500">Sagar Pathak</td>
              <td class="py-3.5 text-gray-500">14 Mar 2026</td>
              <td class="py-3.5 text-gray-500">FY 2025-26</td>
              <td class="py-3.5"><div class="flex gap-1"><span class="tag-critical text-xs px-2 py-0.5 rounded-full">7 Critical</span><span class="tag-review text-xs px-2 py-0.5 rounded-full">12 Review</span></div></td>
              <td class="py-3.5"><button class="text-blue-600 text-xs hover:underline">View Report</button></td>
            </tr>
            <tr class="hover:bg-gray-50 cursor-pointer">
              <td class="py-3.5"><div class="flex items-center gap-2"><i class="fas fa-file-excel text-green-500"></i><span class="font-medium text-gray-800">AJKL Trial Balance March.xlsx</span></div></td>
              <td class="py-3.5 text-gray-500">Rahul Sharma</td>
              <td class="py-3.5 text-gray-500">11 Mar 2026</td>
              <td class="py-3.5 text-gray-500">FY 2024-25</td>
              <td class="py-3.5"><span class="tag-ok text-xs px-2 py-0.5 rounded-full">✅ All OK</span></td>
              <td class="py-3.5"><button class="text-blue-600 text-xs hover:underline">View Report</button></td>
            </tr>
            <tr class="hover:bg-gray-50 cursor-pointer">
              <td class="py-3.5"><div class="flex items-center gap-2"><i class="fas fa-file-excel text-green-500"></i><span class="font-medium text-gray-800">TB_Feb2026.xlsx</span></div></td>
              <td class="py-3.5 text-gray-500">Sagar Pathak</td>
              <td class="py-3.5 text-gray-500">07 Mar 2026</td>
              <td class="py-3.5 text-gray-500">FY 2025-26</td>
              <td class="py-3.5"><span class="tag-review text-xs px-2 py-0.5 rounded-full">5 Review</span></td>
              <td class="py-3.5"><button class="text-blue-600 text-xs hover:underline">View Report</button></td>
            </tr>
          </tbody>
        </table>'''

new_history_table = '''        <div id="history-body">
          <div class="flex flex-col items-center py-12 text-center">
            <i class="fas fa-folder-open text-gray-200 text-4xl mb-3"></i>
            <div class="text-sm text-gray-400">No audit history yet</div>
            <button onclick="showPage('fullaudit')" class="mt-4 bg-orange-500 text-white text-xs px-4 py-2 rounded-xl font-semibold">Run First Audit</button>
          </div>
        </div>'''

content = content.replace(old_history_table, new_history_table)

# ══════════════════════════════════════════════════════════════════════════════
# 3. ADMIN PAGE — remove fake users and fake upload list
# ══════════════════════════════════════════════════════════════════════════════
old_admin_stats = '''      <div class="grid grid-cols-3 gap-6 mb-6">
        <div class="stat-card card-shadow"><div class="text-sm text-gray-500 mb-1">Total Users</div><div class="text-3xl font-bold text-gray-800">4</div></div>
        <div class="stat-card card-shadow"><div class="text-sm text-gray-500 mb-1">Total Uploads</div><div class="text-3xl font-bold text-gray-800">24</div></div>
        <div class="stat-card card-shadow"><div class="text-sm text-gray-500 mb-1">Errors Fixed</div><div class="text-3xl font-bold text-green-600">47</div></div>
      </div>'''

new_admin_stats = '''      <div class="grid grid-cols-3 gap-6 mb-6">
        <div class="stat-card card-shadow"><div class="text-sm text-gray-500 mb-1">Total Audits Run</div><div class="text-3xl font-bold text-gray-800" id="admin-total">—</div></div>
        <div class="stat-card card-shadow"><div class="text-sm text-gray-500 mb-1">Last Score</div><div class="text-3xl font-bold text-gray-800" id="admin-score">—</div></div>
        <div class="stat-card card-shadow"><div class="text-sm text-gray-500 mb-1">Critical Issues (last)</div><div class="text-3xl font-bold text-red-600" id="admin-critical">—</div></div>
      </div>'''

content = content.replace(old_admin_stats, new_admin_stats)

# remove fake users list
old_users = '''      <div class="grid grid-cols-2 gap-6">
        <div class="bg-white rounded-2xl card-shadow p-6">
          <div class="flex items-center justify-between mb-5">
            <h3 class="font-semibold text-gray-800">Users</h3>
            <button class="bg-blue-600 text-white px-3 py-2 rounded-xl text-xs hover:bg-blue-700 transition">
              <i class="fas fa-plus mr-1"></i>Add User
            </button>
          </div>
          <div class="space-y-3">
            <div class="flex items-center gap-3 p-3 rounded-xl bg-gray-50">
              <div class="w-9 h-9 rounded-full bg-blue-600 flex items-center justify-center text-white font-bold text-sm">S</div>
              <div class="flex-1"><div class="text-sm font-medium text-gray-800">Sagar Pathak</div><div class="text-xs text-gray-400">admin@company.com</div></div>
              <span class="bg-blue-100 text-blue-600 text-xs px-2 py-0.5 rounded-full">Admin</span>
            </div>
            <div class="flex items-center gap-3 p-3 rounded-xl hover:bg-gray-50">
              <div class="w-9 h-9 rounded-full bg-purple-500 flex items-center justify-center text-white font-bold text-sm">R</div>
              <div class="flex-1"><div class="text-sm font-medium text-gray-800">Rahul Sharma</div><div class="text-xs text-gray-400">rahul@company.com</div></div>
              <span class="bg-gray-100 text-gray-600 text-xs px-2 py-0.5 rounded-full">User</span>
              <button class="text-red-400 hover:text-red-500 text-xs ml-2"><i class="fas fa-trash"></i></button>
            </div>
            <div class="flex items-center gap-3 p-3 rounded-xl hover:bg-gray-50">
              <div class="w-9 h-9 rounded-full bg-green-500 flex items-center justify-center text-white font-bold text-sm">P</div>
              <div class="flex-1"><div class="text-sm font-medium text-gray-800">Priya Mehta</div><div class="text-xs text-gray-400">priya@company.com</div></div>
              <span class="bg-gray-100 text-gray-600 text-xs px-2 py-0.5 rounded-full">User</span>
              <button class="text-red-400 hover:text-red-500 text-xs ml-2"><i class="fas fa-trash"></i></button>
            </div>
          </div>
        </div>

        <div class="bg-white rounded-2xl card-shadow p-6">
          <h3 class="font-semibold text-gray-800 mb-5">All Uploads — Overview</h3>
          <div class="space-y-3">
            <div class="flex items-center gap-3 p-3 rounded-xl border border-gray-100">
              <i class="fas fa-file-excel text-green-500"></i>
              <div class="flex-1"><div class="text-sm font-medium text-gray-700">AJKL Traial balance.xlsx</div><div class="text-xs text-gray-400">Sagar Pathak • 14 Mar 2026</div></div>
              <span class="tag-critical text-xs px-2 py-0.5 rounded-full">7 Critical</span>
            </div>
            <div class="flex items-center gap-3 p-3 rounded-xl border border-gray-100">
              <i class="fas fa-file-excel text-green-500"></i>
              <div class="flex-1"><div class="text-sm font-medium text-gray-700">AJKL Trial Balance March.xlsx</div><div class="text-xs text-gray-400">Rahul Sharma • 11 Mar 2026</div></div>
              <span class="tag-ok text-xs px-2 py-0.5 rounded-full">✅ All OK</span>
            </div>
            <div class="flex items-center gap-3 p-3 rounded-xl border border-gray-100">
              <i class="fas fa-file-excel text-green-500"></i>
              <div class="flex-1"><div class="text-sm font-medium text-gray-700">TB_Feb2026.xlsx</div><div class="text-xs text-gray-400">Sagar Pathak • 07 Mar 2026</div></div>
              <span class="tag-review text-xs px-2 py-0.5 rounded-full">5 Review</span>
            </div>
          </div>
        </div>
      </div>'''

new_admin_section = '''      <div class="bg-white rounded-2xl card-shadow p-6">
        <h3 class="font-semibold text-gray-800 mb-4">Audit History</h3>
        <div id="admin-history-list">
          <div class="text-sm text-gray-400 py-6 text-center">No audits run yet</div>
        </div>
      </div>'''

content = content.replace(old_users, new_admin_section)

with open('index.html', 'w', encoding='utf-8') as f:
    f.write(content)
print('Pages rewritten. len=', len(content))
