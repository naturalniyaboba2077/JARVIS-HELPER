# -*- coding: utf-8 -*-
"""Static deep-audit of jarvis.py"""
import ast
import sys

with open('jarvis.py', encoding='utf-8') as f:
    src = f.read()
    lines = src.splitlines()

results = {}

# 1. asyncio is top-level import
asyncio_line = next((i+1 for i,l in enumerate(lines)
                     if 'import asyncio' in l and not l.strip().startswith('#')), None)
results['asyncio top-level (line<=11)'] = asyncio_line is not None and asyncio_line <= 11

# 2. No asyncio.run()
results['No asyncio.run()'] = 'asyncio.run(' not in src

# 3. asyncio.new_event_loop used in TTS
results['new_event_loop in _run_edge_tts_sync'] = 'asyncio.new_event_loop()' in src

# 4. Wake-word: fuzzy matcher + collision blocklist
results['Wake-word fuzzy matcher'] = (
    'WAKE_FUZZY_THRESHOLD = 0.72' in src
    and 'SequenceMatcher' in src
    and 'WAKE_BLOCKLIST' in src
)

# 5. Background listener started exactly once
results['listen_in_background called exactly once'] = src.count('listen_in_background') == 1

# 6. LLM temperature 0.3
results['LLM temperature=0.3'] = 'temperature=0.3' in src

# 7. System prompt has all tag examples
results['Prompt: [OPEN:browser] example'] = '[OPEN:browser]' in src
results['Prompt: [MUSIC:PLAY: example'] = '[MUSIC:PLAY:' in src
results['Prompt: [OPEN:notepad] example'] = '[OPEN:notepad]' in src
results['Prompt: [OPEN:calc] example'] = '[OPEN:calc]' in src
results['Prompt: [MUSIC:OPEN] example'] = '[MUSIC:OPEN]' in src
results['Prompt: EXECUTE_PYTHON example'] = '[EXECUTE_PYTHON]' in src

# 8. Intent fallback
results['detect_intent_from_text() defined'] = 'def detect_intent_from_text' in src
results['INTENT_PATTERNS list defined'] = 'INTENT_PATTERNS' in src
results['Fallback called in parse_and_execute_tags'] = 'detect_intent_from_text(original_user_text)' in src

# 9. Obsidian cache
results['OBSIDIAN_CACHE_TTL defined'] = 'OBSIDIAN_CACHE_TTL' in src
results['Cache time checked'] = '_obsidian_cache_time' in src

# 10. Singleton OpenAI client
results['_openrouter_client singleton'] = '_openrouter_client = None' in src
results['get_openrouter_client() used in LLM'] = 'client = get_openrouter_client()' in src

# 11. Anti-wipe policy: block system/project wipe, not arbitrary code APIs
results['Anti-wipe enforced for Python'] = 'ok, reason = is_code_safe(code)' in src
results['Anti-wipe enforced for shell'] = 'ok, reason = is_code_safe(cmd)' in src
results['Anti-wipe protects project roots'] = 'def _protected_roots()' in src

# 12. No legacy g4f
results['No g4f import'] = 'g4f' not in src

# 13. Daemon threads
daemon_count = src.count('daemon=True')
results['daemon=True threads (>=2)'] = daemon_count >= 2

# 14. Consolidated tag parsing
results['parse_and_execute_tags() single function'] = 'def parse_and_execute_tags' in src

# 15. Voice confirmation was deliberately removed
results['No dangerous-code confirmation state'] = 'pending_dangerous_code =' not in src

# 16. XTTS path preserved
results['XTTS _load_xtts_if_needed intact'] = 'def _load_xtts_if_needed' in src

# 17. No syntax errors
try:
    ast.parse(src)
    results['No syntax errors (AST parse OK)'] = True
except SyntaxError as e:
    results[f'SYNTAX ERROR: {e}'] = False

# ---- Report ----
all_ok = True
for name, ok in results.items():
    status = 'OK  ' if ok else 'FAIL'
    if not ok:
        all_ok = False
    print(f'  [{status}] {name}')

passed = sum(1 for v in results.values() if v)
total = len(results)
print()
print(f'Static audit: {passed}/{total}')
print('ALL CHECKS PASSED' if all_ok else 'SOME CHECKS FAILED')
sys.exit(0 if all_ok else 1)
