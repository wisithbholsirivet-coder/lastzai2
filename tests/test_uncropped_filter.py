"""Test Stage 2 _fixOCRText — uncropped image noise filtering."""
from py_mini_racer import MiniRacer
import json

ctx = MiniRacer()

# Load InciCleaner first — it attaches to global `self`
# In V8, global is `this` at top level. inci-cleaner.js uses
# `typeof self !== 'undefined' ? self : this` which in V8 = globalThis
with open(r'C:\Users\Wisithbhol S\.gemini\antigravity\scratch\chaecheck\js\inci-cleaner.js', 'r', encoding='utf-8') as f:
    inci_src = f.read()
ctx.eval(inci_src)

# Verify it loaded
assert ctx.eval('typeof InciCleaner') == 'object', 'InciCleaner not loaded!'
print('InciCleaner loaded OK')

# Now load scanner with stubs — but need to provide stubs BEFORE scanner runs
stubs = '''
var window = { showToast: function(){} };
var document = {
  getElementById: function(){return null},
  querySelectorAll: function(){return {forEach:function(){}}},
  addEventListener: function(){}
};
var I18n = { t: function(k,d){return d||k}, getLang: function(){return 'en'} };
var DB = { isLoaded: function(){return true}, search: function(){return []},
           fuzzyCorrect: function(s){return s}, getById: function(){return null} };
var HistoryManager = { add: function(){} };
var Worker = function(){};
var URL = { createObjectURL: function(){return ''} };
var fetch = function(){return {then:function(){return {catch:function(){}}}}};
var createImageBitmap = function(){return {then:function(){}}};
var OffscreenCanvas = function(){this.getContext=function(){return {drawImage:function(){},getImageData:function(){return {data:{buffer:{}}}}}};this.convertToBlob=function(){return {then:function(){}}}};
var FileReader = function(){};
var Blob = function(){};
var AbortController = function(){this.signal={};this.abort=function(){}};
var setTimeout = function(f,t){return 0};
var clearTimeout = function(){};
'''
ctx.eval(stubs)

with open(r'C:\Users\Wisithbhol S\.gemini\antigravity\scratch\chaecheck\js\scanner.js', 'r', encoding='utf-8') as f:
    scanner_src = f.read()

# Expose _fixOCRText
scanner_src = scanner_src.replace(
    'return { init, scan, showResults, restoreResults, openModal, closeModal, getOCRAudit };',
    'return { init, scan, showResults, restoreResults, openModal, closeModal, getOCRAudit, _fixOCRText: _fixOCRText };'
)
ctx.eval(scanner_src)

# Verify
assert ctx.eval('typeof Scanner._fixOCRText') == 'function', '_fixOCRText not exposed!'
print('Scanner._fixOCRText exposed OK')

passed = 0
failed = 0

def test(name, raw_input, must_have, must_not_have):
    global passed, failed
    # Pass input as JSON string to avoid escaping hell
    ctx.eval(f'var __test_input = {json.dumps(raw_input)}')
    result = ctx.eval('Scanner._fixOCRText(__test_input)')
    result_lower = result.lower()
    ok = True
    for item in must_have:
        if item.lower() not in result_lower:
            print(f"  FAIL {name}: missing '{item}'")
            ok = False
    for item in must_not_have:
        if item.lower() in result_lower:
            print(f"  FAIL {name}: unwanted '{item}' found")
            ok = False
    if ok:
        print(f"PASS {name}")
        passed += 1
    else:
        print(f"  -> got: {result[:300]}")
        failed += 1

# ── Tests ──

test("uncropped_with_directions",
     "SunShield Pro SPF 50+ PA++++\n"
     "Ingredients: Aqua, Homosalate, Octocrylene, Glycerin, Niacinamide, Tocopherol.\n"
     "Directions for use: Apply liberally 15 minutes before sun exposure.",
     must_have=["Aqua", "Homosalate", "Octocrylene", "Glycerin", "Niacinamide", "Tocopherol"],
     must_not_have=["SunShield", "liberally"])

test("manufacturer_noise",
     "Ingredients: Water, Cetyl Alcohol, Dimethicone, Phenoxyethanol.\n"
     "Manufactured by ABC Cosmetics Co., Ltd. Tel: 02-123-4567",
     must_have=["Water", "Cetyl Alcohol", "Dimethicone", "Phenoxyethanol"],
     must_not_have=["ABC Cosmetics"])

test("end_marker_batch",
     "Aqua, Glycerin, Butylene Glycol, Sodium Hyaluronate END_OF_LIST Batch No: BN2024X789",
     must_have=["Aqua", "Glycerin", "Butylene Glycol", "Sodium Hyaluronate"],
     must_not_have=["BN2024X789"])

test("barcode_stripped",
     "8850007123456 Ingredients: PEG-100 Stearate, Polysorbate 60, CI 77891 END_OF_LIST",
     must_have=["PEG-100 Stearate", "Polysorbate 60", "CI 77891"],
     must_not_have=["8850007123456"])

test("marketing_claims",
     "Ingredients: Aqua, Niacinamide, Panthenol. Dermatologically tested. Hypoallergenic.",
     must_have=["Aqua", "Niacinamide", "Panthenol"],
     must_not_have=["Dermatologically", "Hypoallergenic"])

test("thai_mixed",
     "\u0e2a\u0e48\u0e27\u0e19\u0e1b\u0e23\u0e30\u0e01\u0e2d\u0e1a (Ingredients): Aqua, Cetearyl Alcohol, Dimethicone, Fragrance.\n"
     "\u0e44\u0e21\u0e48\u0e21\u0e35 mineral oil",
     must_have=["Aqua", "Cetearyl Alcohol", "Dimethicone", "Fragrance"],
     must_not_have=["mineral oil"])

test("long_inci_with_chem_indicator",
     "Ingredients: Caprylic Capric Triglyceride, Disodium Ethylene Dicocamide PEG-15 Disulfate END_OF_LIST",
     must_have=["Caprylic Capric Triglyceride"],
     must_not_have=[])

test("loop_killer",
     "Ingredients: Aqua, Glycerin, Niacinamide, Tocopherol, Aqua, Glycerin, Niacinamide",
     must_have=["Aqua", "Glycerin", "Niacinamide", "Tocopherol"],
     must_not_have=[])

test("expiry_date",
     "Ingredients: Water, Butylene Glycol, Panthenol.\nExp: 12/2027 Lot: ABC123",
     must_have=["Water", "Butylene Glycol", "Panthenol"],
     must_not_have=["2027"])

test("how_to_use_section",
     "Ingredients: Retinol, Squalane, Jojoba Oil, Tocopherol.\n"
     "How to use: Apply a small amount to face at night. Avoid contact with eyes.",
     must_have=["Retinol", "Squalane", "Jojoba Oil", "Tocopherol"],
     must_not_have=["small amount", "Avoid contact"])

test("legit_mineral_oil_kept",
     "Ingredients: Paraffinum Liquidum, Mineral Oil, Petrolatum, C12-15 Alkyl Benzoate END_OF_LIST",
     must_have=["Mineral Oil", "Petrolatum", "C12-15 Alkyl Benzoate"],
     must_not_have=[])

test("thai_paraben_free_claim",
     "Ingredients: Aqua, Glycerin, Phenoxyethanol.\n\u0e1b\u0e23\u0e32\u0e28\u0e08\u0e32\u0e01 paraben alcohol",
     must_have=["Aqua", "Glycerin", "Phenoxyethanol"],
     must_not_have=["paraben", "alcohol"])

test("markdown_and_floating_letters",
     "```markdown\nAqua, U, Glycerin, o, Niacinamide\n```",
     must_have=["Aqua", "Glycerin", "Niacinamide"],
     must_not_have=["markdown", "```"])

test("ui_chatter_wait",
     "Wait, Aqua, Glycerin, Wait, let me check, Silica",
     must_have=["Aqua", "Glycerin", "Silica"],
     must_not_have=["Wait", "let me", "check"])

test("mangled_fragment_dropped",
     "Aqua, Isohexadecane, U vegetable o, Fragrance",
     must_have=["Aqua", "Isohexadecane", "Fragrance"],
     must_not_have=["vegetable", "U "])

test("legit_single_letters_kept",
     "Tocopherol (Vitamin E), D Panthenol, Retinyl Palmitate (Vitamin A), Mineral Oil",
     must_have=["Vitamin E", "D Panthenol", "Vitamin A", "Mineral Oil"],
     must_not_have=[])

print(f"\n{passed}/{passed+failed} tests passed")
if failed:
    exit(1)
