"""Run js/inci-cleaner.js in V8 (py_mini_racer) against INCI edge cases."""
import json, sys
from py_mini_racer import MiniRacer
sys.stdout.reconfigure(encoding='utf-8')
ROOT = r'C:\Users\Wisithbhol S\.gemini\antigravity\scratch\chaecheck'
ctx = MiniRacer()
ctx.eval('var self = this;')
ctx.eval(open(ROOT + r'\js\inci-cleaner.js', encoding='utf-8').read())

CASES = [
  # (input label, expected tokens)
  ("PEG-100 Stearate, Polysorbate 60, Glycerin.", ["PEG-100 Stearate", "Polysorbate 60", "Glycerin"]),
  ("Water (Aqua), 1,2-Hexanediol, C12-15 Alkyl Benzoate", ["Water (Aqua)", "1,2-Hexanediol", "C12-15 Alkyl Benzoate"]),
  ("Niacinamide (5%), Zinc PCA 1 %, Panthenol", ["Niacinamide", "Zinc PCA", "Panthenol"]),
  ("Titanium Dioxide (CI 77891), CI 77491; Mica", ["Titanium Dioxide (CI 77891)", "CI 77491", "Mica"]),
  ("Aloe Barbadensis Leaf Juice*, Fragrance (and) Linalool", ["Aloe Barbadensis Leaf Juice", "Fragrance Linalool"]),
  ("PEG - 40 Hydrogenated Castor Oil. Ceteareth-20. Steareth-2", ["PEG-40 Hydrogenated Castor Oil", "Ceteareth-20", "Steareth-2"]),
  ("Caprylic/Capric Triglyceride，Dimethicone、Tocopherol", ["Caprylic/Capric Triglyceride", "Dimethicone", "Tocopherol"]),
  ("Butyrospermum Parkii (Shea) Butter, 2,4-Diaminophenoxyethanol HCl", ["Butyrospermum Parkii (Shea) Butter", "2,4-Diaminophenoxyethanol HCl"]),
  ("C.I. 77891, Red 7 Lake, Ceramide NP", ["C.I. 77891", "Red 7 Lake", "Ceramide NP"]),
  ("Acrylates/C10-30 Alkyl Acrylate Crosspolymer, Polyquaternium-10, Nylon-12", ["Acrylates/C10-30 Alkyl Acrylate Crosspolymer", "Polyquaternium-10", "Nylon-12"]),
  ("Glycerin (organic), Retinol (0.3%), Zinc Oxide [nano]", ["Glycerin", "Retinol", "Zinc Oxide [nano]"]),
  ("Sodium Chloride, 123, %, Citric Acid", ["Sodium Chloride", "Citric Acid"]),
]
fails = 0
for text, exp in CASES:
    got = ctx.eval(f'JSON.stringify(InciCleaner.splitIngredients({json.dumps(text)}))')
    got = json.loads(got)
    ok = got == exp
    fails += not ok
    print('PASS' if ok else 'FAIL', '|', text, '\n     ', got if not ok else '')
print(ctx.eval('JSON.stringify(InciCleaner.matchCandidates("Butyrospermum Parkii (Shea) Butter"))'))
print(ctx.eval('JSON.stringify(InciCleaner.matchCandidates("Aqua/Water/Eau"))'))
print(f'{len(CASES)-fails}/{len(CASES)} passed')
