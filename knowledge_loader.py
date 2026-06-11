"""
knowledge_loader.py — Loads all knowledge base .md files for injection into AI prompts.
Call load_knowledge() once at startup; it caches the result.
"""
import os

_cache = {}

KNOWLEDGE_DIR = os.path.join(os.path.dirname(__file__), 'knowledge')

# Which files to load for which feature
FEATURE_MAP = {
    'ask_ca':    ['gst', 'income_tax', 'audit', 'accounting', 'tally'],
    'full_audit':['audit', 'accounting', 'tally', 'income_tax'],
    'quick_audit':['audit', 'accounting', 'tally'],
    'bank_recon':['tally', 'accounting'],
    'tds':       ['income_tax'],
    'all':       ['gst', 'income_tax', 'audit', 'accounting', 'tally'],
}

def load_knowledge(feature: str = 'all') -> str:
    """Return combined knowledge base text for the given feature."""
    if feature in _cache:
        return _cache[feature]

    folders = FEATURE_MAP.get(feature, FEATURE_MAP['all'])
    sections = []

    for folder in folders:
        folder_path = os.path.join(KNOWLEDGE_DIR, folder)
        if not os.path.exists(folder_path):
            continue
        for fname in sorted(os.listdir(folder_path)):
            if not fname.endswith('.md'):
                continue
            fpath = os.path.join(folder_path, fname)
            try:
                with open(fpath, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                # Add section header so AI knows which file it's from
                sections.append(f"=== {folder.upper()} / {fname.replace('.md','')} ===\n{content}")
            except Exception:
                continue

    result = '\n\n'.join(sections)
    _cache[feature] = result
    return result


def get_summary() -> str:
    """Return a short summary of what's loaded — for debugging."""
    lines = []
    for folder in ['gst', 'income_tax', 'audit', 'accounting', 'tally']:
        folder_path = os.path.join(KNOWLEDGE_DIR, folder)
        if os.path.exists(folder_path):
            files = [f for f in os.listdir(folder_path) if f.endswith('.md')]
            lines.append(f"  {folder}/: {len(files)} files")
    return "Knowledge base loaded:\n" + '\n'.join(lines)
