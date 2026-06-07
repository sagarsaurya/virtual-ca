with open('index.html', 'r', encoding='utf-8') as f:
    content = f.read()

old = content[content.find('        <div id="brtab-content-unmatched"'):content.find('      <!-- Empty state before upload -->')]

new = '''        <div id="brtab-content-unmatched" class="space-y-3">
          <div id="br-bank-only-list"><div class="text-sm text-gray-400 p-4 text-center">Run reconciliation to see results</div></div>
        </div>
        <div id="brtab-content-tally" class="space-y-3 hidden">
          <div id="br-tally-only-list"><div class="text-sm text-gray-400 p-4 text-center">Run reconciliation to see results</div></div>
        </div>
        <div id="brtab-content-duplicate" class="space-y-3 hidden">
          <div id="br-duplicates-list"><div class="text-sm text-gray-400 p-4 text-center">Run reconciliation to see results</div></div>
        </div>
        <div id="brtab-content-matched" class="hidden">
          <div id="br-matched-list"><div class="text-sm text-gray-400 p-4 text-center">Run reconciliation to see results</div></div>
        </div>
      </div>

      '''

start = content.find('        <div id="brtab-content-unmatched"')
end   = content.find('      <!-- Empty state before upload -->')
content = content[:start] + new + content[end:]

with open('index.html', 'w', encoding='utf-8') as f:
    f.write(content)
print('done', len(content))
