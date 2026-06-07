with open('index.html', 'r', encoding='utf-8') as f:
    content = f.read()

start_marker = '          <!-- Module Results -->'
end_marker   = '          <!-- Download Report -->'

modules_html = """\
          <!-- Module Results (populated dynamically) -->

          <!-- 1. Ledger Classification -->
          <div class="bg-white rounded-2xl card-shadow mb-4 overflow-hidden">
            <div class="flex items-center justify-between p-5 cursor-pointer" onclick="toggleAuditSection('audit-ledger')">
              <div class="flex items-center gap-3">
                <div class="w-9 h-9 rounded-xl bg-red-50 flex items-center justify-center"><i class="fas fa-layer-group text-red-500"></i></div>
                <div><div class="font-semibold text-gray-800">Ledger Classification</div><div class="text-xs text-gray-400">Wrong groups, misclassified accounts</div></div>
              </div>
              <div class="flex items-center gap-3"><span class="tag-critical text-xs px-3 py-1 rounded-full font-medium" id="audit-ledger-badge"></span><i class="fas fa-chevron-down text-gray-400 text-xs"></i></div>
            </div>
            <div id="audit-ledger" class="border-t border-gray-100"><div id="audit-ledger-real"><div class="p-5 text-sm text-gray-400">Run audit to see results</div></div></div>
          </div>

          <!-- 2. Cash Violations -->
          <div class="bg-white rounded-2xl card-shadow mb-4 overflow-hidden">
            <div class="flex items-center justify-between p-5 cursor-pointer" onclick="toggleAuditSection('audit-cash')">
              <div class="flex items-center gap-3">
                <div class="w-9 h-9 rounded-xl bg-red-50 flex items-center justify-center"><i class="fas fa-money-bill-wave text-red-500"></i></div>
                <div><div class="font-semibold text-gray-800">Cash Violations</div><div class="text-xs text-gray-400">Sec 40A(3) &gt;Rs.10k &bull; Sec 269ST &gt;Rs.2L</div></div>
              </div>
              <div class="flex items-center gap-3"><span class="tag-critical text-xs px-3 py-1 rounded-full font-medium" id="audit-cash-badge"></span><i class="fas fa-chevron-down text-gray-400 text-xs"></i></div>
            </div>
            <div id="audit-cash" class="border-t border-gray-100"><div id="audit-cash-real"><div class="p-5 text-sm text-gray-400">Run audit to see results</div></div></div>
          </div>

          <!-- 3. Outstanding Amounts -->
          <div class="bg-white rounded-2xl card-shadow mb-4 overflow-hidden">
            <div class="flex items-center justify-between p-5 cursor-pointer" onclick="toggleAuditSection('audit-outstanding')">
              <div class="flex items-center gap-3">
                <div class="w-9 h-9 rounded-xl bg-yellow-50 flex items-center justify-center"><i class="fas fa-hourglass-half text-yellow-500"></i></div>
                <div><div class="font-semibold text-gray-800">Outstanding Amounts</div><div class="text-xs text-gray-400">Unsettled debtors, creditors, suspense, advances</div></div>
              </div>
              <div class="flex items-center gap-3"><span class="bg-blue-100 text-blue-700 text-xs px-3 py-1 rounded-full font-medium" id="audit-outstanding-badge"></span><i class="fas fa-chevron-down text-gray-400 text-xs"></i></div>
            </div>
            <div id="audit-outstanding" class="border-t border-gray-100"><div id="audit-outstanding-real"><div class="p-5 text-sm text-gray-400">Run audit to see results</div></div></div>
          </div>

          <!-- 4. Loan Audit -->
          <div class="bg-white rounded-2xl card-shadow mb-4 overflow-hidden">
            <div class="flex items-center justify-between p-5 cursor-pointer" onclick="toggleAuditSection('audit-loan')">
              <div class="flex items-center gap-3">
                <div class="w-9 h-9 rounded-xl bg-indigo-50 flex items-center justify-center"><i class="fas fa-university text-indigo-500"></i></div>
                <div><div class="font-semibold text-gray-800">Loan Audit</div><div class="text-xs text-gray-400">Bank statements required &bull; 269SS/269T compliance</div></div>
              </div>
              <div class="flex items-center gap-3"><span class="bg-indigo-100 text-indigo-700 text-xs px-3 py-1 rounded-full font-medium" id="audit-loan-badge"></span><i class="fas fa-chevron-down text-gray-400 text-xs"></i></div>
            </div>
            <div id="audit-loan" class="border-t border-gray-100"><div id="audit-loan-real"><div class="p-5 text-sm text-gray-400">Run audit to see results</div></div></div>
          </div>

          <!-- 5. Large Expenses -->
          <div class="bg-white rounded-2xl card-shadow mb-4 overflow-hidden">
            <div class="flex items-center justify-between p-5 cursor-pointer" onclick="toggleAuditSection('audit-large')">
              <div class="flex items-center gap-3">
                <div class="w-9 h-9 rounded-xl bg-orange-50 flex items-center justify-center"><i class="fas fa-receipt text-orange-500"></i></div>
                <div><div class="font-semibold text-gray-800">Large Expenses</div><div class="text-xs text-gray-400">Single payments above Rs.1L - bill verification</div></div>
              </div>
              <div class="flex items-center gap-3"><span class="bg-orange-100 text-orange-700 text-xs px-3 py-1 rounded-full font-medium" id="audit-large-badge"></span><i class="fas fa-chevron-down text-gray-400 text-xs"></i></div>
            </div>
            <div id="audit-large" class="border-t border-gray-100"><div id="audit-large-real"><div class="p-5 text-sm text-gray-400">Run audit to see results</div></div></div>
          </div>

          <!-- 6. ITR / Tax Audit -->
          <div class="bg-white rounded-2xl card-shadow mb-4 overflow-hidden">
            <div class="flex items-center justify-between p-5 cursor-pointer" onclick="toggleAuditSection('audit-itr')">
              <div class="flex items-center gap-3">
                <div class="w-9 h-9 rounded-xl bg-green-50 flex items-center justify-center"><i class="fas fa-file-invoice text-green-500"></i></div>
                <div><div class="font-semibold text-gray-800">ITR / Tax Audit</div><div class="text-xs text-gray-400">Disallowable expenses, personal expenses in books</div></div>
              </div>
              <div class="flex items-center gap-3"><i class="fas fa-chevron-down text-gray-400 text-xs"></i></div>
            </div>
            <div id="audit-itr" class="border-t border-gray-100"><div id="audit-itr-real"><div class="p-5 text-sm text-gray-400">Run audit to see results</div></div></div>
          </div>

          """

start_idx = content.find(start_marker)
end_idx   = content.find(end_marker)
print(f'start={start_idx} end={end_idx}')

new_content = content[:start_idx] + modules_html + content[end_idx:]
with open('index.html', 'w', encoding='utf-8') as f:
    f.write(new_content)
print('done, len=', len(new_content))
