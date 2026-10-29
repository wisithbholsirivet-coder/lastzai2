"""End-to-end: load real js/inci-cleaner.js + js/db.js + data/*.json in V8,
run DB.search / DB.fuzzyCorrect on OCR-style inputs."""
import json, os, sys
from py_mini_racer import MiniRacer
sys.stdout.reconfigure(encoding='utf-8')
ROOT = r'C:\Users\Wisithbhol S\.gemini\antigravity\scratch\chaecheck'

ctx = MiniRacer()
data = {f: json.load(open(os.path.join(ROOT, 'data', f), encoding='utf-8'))
        for f in os.listdir(os.path.join(ROOT, 'data')) if f.endswith('.json')}
ctx.eval('var self = this; var document = { getElementById: () => null };'
         'var I18n = { t: (k, f) => f };')
ctx.eval('var __DATA = ' + json.dumps(data, ensure_ascii=False) + ';')
ctx.eval('var fetch = (url) => { const f = url.split("/").pop().split("?")[0];'
         ' return Promise.resolve({ ok: true, json: () => Promise.resolve(__DATA[f]) }); };')
ctx.eval(open(os.path.join(ROOT, 'js', 'inci-cleaner.js'), encoding='utf-8').read())
ctx.eval(open(os.path.join(ROOT, 'js', 'db.js'), encoding='utf-8').read().replace('const DB =', 'var DB ='))
ctx.eval('var __ok = false; DB.load().then(() => { __ok = true; });')
ctx.eval('1')  # flush microtasks
assert ctx.eval('__ok'), 'DB failed to load'
print('loaded', ctx.eval('DB.getCount()'))

def search(text):
    return json.loads(ctx.eval(f'JSON.stringify(DB.search({json.dumps(text)}).map(r => [r.inputName, r.id, r._matchType]))'))

CASES = [
  # (input, expected matched ids in order — None means "must be Unknown")
  ("PHENYLBENZIMIDAZOLE SULFONIC ACID,SodiumHYDROXIDETitaniumDIOXIDES ,sodium HyALuronates", 4),
  ("PEG-100 Stearate, Polysorbate 60, 1,2-Hexanediol, CI 77891", 4),
  ("Aqua (Water), Butyrospermum Parkii (Shea) Butter, Niacinamide (5%)", 3),
  ("Aqua/Water/Eau, Caprylic/Capric Triglyceride. Glycerin.", 3),
  ("PhenoxyEthanol, Iso hexadecane, C12-15 Alkyl Benzoate", 3),
  ("WATERGLYCERINDIMETHICONE", 3),
]
fails = 0
for text, n_expected in CASES:
    res = search(text)
    matched = [r for r in res if r[1]]
    ok = len(matched) == n_expected and len(res) == n_expected
    fails += not ok
    print('PASS' if ok else 'FAIL', '|', text)
    for r in res: print('      ', r)

FUZZY = [
  # (OCR typo, expected exact DB name — case-insensitive; None = must stay unchanged)
  ("Dimethylicone",        "Dimethicone"),
  ("Octocryrene",          "Octocrylene"),
  ("Gliceryll Stearate",   "Glyceryl Stearate"),
  ("DIPROPILEGlycol",      "Dipropylene Glycol"),
  ("Phenylbenzmidiazole Sulfonic Acid", "Phenylbenzimidazole Sulfonic Acid"),
  ("Niacinamid",           "Niacinamide"),
  ("Tocopheryl Acetat",    "Tocopheryl Acetate"),
  ("1,2-Hexanediol",       "1,2-Hexanediol"),   # already correct — keep
  ("PEG-100 Stearate",     "PEG-100 Stearate"), # numbers must survive
  ("Xyzzyplonk",           None),               # gibberish — must NOT be forced to a DB name
]
for typo, want in FUZZY:
    got = ctx.eval(f'DB.fuzzyCorrect({json.dumps(typo)})').strip()
    ok = (got.lower() == want.lower()) if want else (got.lower() == typo.lower())
    fails += not ok
    print('PASS' if ok else 'FAIL', f'| fuzzy {typo!r} -> {got!r}', '' if ok else f'(want {want!r})')

# Exact-case output: UI must render DB spelling, not OCR casing/scramble
EXACT_CASE = [("lisohexdacne", "Isohexadecane"), ("SilICA", "Silica"), ("Octocryrene", "Octocrylene"),
              ("Dimethylicone", "Dimethicone")]
for typo, want in EXACT_CASE:
    got = ctx.eval(f'DB.fuzzyCorrect({json.dumps(typo)})').strip()
    ok = got == want
    fails += not ok
    print('PASS' if ok else 'FAIL', f'| case  {typo!r} -> {got!r}', '' if ok else f'(want {want!r})')

# DB.search must NOT map marketing words / non-DB chemicals onto a different entry
SEARCH_NEG = ["Waterproof", "Hydrating", "Moisturizing", "Brightening", "Sodium Polyaspartate", "Wait"]
for t in SEARCH_NEG:
    rid = ctx.eval(f'(DB.search({json.dumps(t)})[0] || {{}}).id || null')
    ok = rid is None
    fails += not ok
    print('PASS' if ok else 'FAIL', f'| search-neg {t!r} -> {rid!r}')

total = len(CASES) + len(FUZZY) + len(EXACT_CASE) + len(SEARCH_NEG)
print(f'{total-fails}/{total} passed')
sys.exit(1 if fails else 0)
