"""Calibrate Stage 3 fuzzy tiers: correct-map rate on synthetic OCR typos,
and false-map rate on names NOT in the DB (must stay unchanged)."""
import json, random, sys
from pipeline_harness import make_ctx
sys.stdout.reconfigure(encoding='utf-8')
random.seed(7)
ctx = make_ctx()

def fc(s): return ctx.eval(f'DB.fuzzyCorrect({json.dumps(s)})').strip()
def in_db_id(s):
    return ctx.eval(f'(DB.search({json.dumps(s)})[0] || {{}}).id || null')

# ── Positives: random DB names with OCR-style damage ──
names = json.loads(ctx.eval('JSON.stringify((() => { const out = []; const seen = new Set();'
    ' for (const n of __ALLNAMES) { const k = n.toLowerCase().replace(/[^a-z0-9]/g, ""); '
    ' if (k.length >= 8 && /^[A-Za-z][A-Za-z ]+$/.test(n) && !seen.has(k)) { seen.add(k); out.push(n); } } return out; })())')) \
    if ctx.eval('typeof __ALLNAMES') != 'undefined' else None
if names is None:
    ctx.eval('var __ALLNAMES = Object.values(__DATA).filter(Array.isArray).flat().map(r => r.names[0]);')
    names = json.loads(ctx.eval('JSON.stringify(__ALLNAMES.filter(n => n && /^[A-Za-z][A-Za-z ]+$/.test(n) && n.replace(/ /g,"").length >= 8))'))

def damage(n):
    s = list(n)
    for _ in range(2):
        i = random.randrange(1, len(s) - 1)
        op = random.choice(['swap', 'del', 'dup', 'sub'])
        if op == 'swap' and s[i] != ' ' and s[i+1] != ' ': s[i], s[i+1] = s[i+1], s[i]
        elif op == 'del' and s[i] != ' ': del s[i]
        elif op == 'dup': s.insert(i, s[i])
        elif op == 'sub' and s[i].isalpha(): s[i] = random.choice('ilrnaeo')
    if random.random() < 0.3: s.insert(0, 'l')                    # stray leading glyph
    out = ''.join(s)
    return ''.join(c.upper() if random.random() < 0.2 else c for c in out)  # random caps

sample = random.sample(names, 300)
ok = wrong = miss = 0; wrong_ex = []
for n in sample:
    want = in_db_id(n)
    t = damage(n)
    got = fc(t)
    gid = in_db_id(got)
    if gid == want: ok += 1
    elif got.lower() == t.lower(): miss += 1
    else: wrong += 1; wrong_ex.append((n, t, got))
print(f'POSITIVES  correct {ok}/300  unchanged {miss}  WRONG {wrong}')
for e in wrong_ex[:15]: print('   wrong:', e)

# ── Negatives: must NOT be forced onto a DB entry ──
NEG = ['Ectoin', 'Bakuchiol', 'Hydroxypinacolone Retinoate', 'Sodium Polyaspartate',
       'Tetrahexyldecyl Ascorbate', 'Polyhydroxystearic Acid', 'Diisostearyl Malate',
       'Trimethylsiloxysilicate', 'Hydrogenated Polydecene', 'Methylpropanediol',
       'Caprylhydroxamic Acid', 'Isononyl Isononanoate', 'Diethylhexyl Syringylidenemalonate',
       'Tromethamine', 'Dipotassium Glycyrrhizate', 'Hydroxyacetophenone', 'Sodium Stearoyl Glutamate',
       'Polyglyceryl Diisostearate', 'Ethylhexyl Palmitate', 'Bis Ethylhexyloxyphenol Methoxyphenyl Triazine',
       'Instructions', 'Dermatologist', 'Moisturizing', 'Hydrating', 'Lightweight', 'Waterproof',
       'Brightening', 'Refreshing', 'Sensitive', 'Everyday', 'Nourishing', 'Soothing', 'Recommended']
neg_total = forced = 0
for n in NEG:
    if in_db_id(n): continue                 # actually in DB → not a negative
    neg_total += 1
    got = fc(n)
    if got.lower() != n.lower():
        forced += 1; print(f'   FORCED: {n!r} -> {got!r}')
print(f'NEGATIVES  forced {forced}/{neg_total}')
