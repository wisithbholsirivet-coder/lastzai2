"""Repro: push problem OCR output through real Stage 2 (_fixOCRText) + Stage 3 (DB.fuzzyCorrect)."""
import json, os, sys
from py_mini_racer import MiniRacer
sys.stdout.reconfigure(encoding='utf-8')
ROOT = r'C:\Users\Wisithbhol S\.gemini\antigravity\scratch\chaecheck'

def make_ctx():
    ctx = MiniRacer()
    data = {f: json.load(open(os.path.join(ROOT, 'data', f), encoding='utf-8'))
            for f in os.listdir(os.path.join(ROOT, 'data')) if f.endswith('.json')}
    ctx.eval('var self = this; var window = {}; var document = { getElementById: () => null, querySelectorAll: () => [], addEventListener(){} };'
             'var I18n = { t: (k, f) => f, getLang: () => "en" }; var HistoryManager = {}; var setTimeout = () => 0; var clearTimeout = () => {};')
    ctx.eval('var __DATA = ' + json.dumps(data, ensure_ascii=False) + ';')
    ctx.eval('var fetch = (url) => { const f = url.split("/").pop().split("?")[0];'
             ' return Promise.resolve({ ok: !!__DATA[f], json: () => Promise.resolve(__DATA[f] || {}) }); };')
    ctx.eval(open(os.path.join(ROOT, 'js', 'inci-cleaner.js'), encoding='utf-8').read())
    ctx.eval(open(os.path.join(ROOT, 'js', 'db.js'), encoding='utf-8').read().replace('const DB =', 'var DB ='))
    src = open(os.path.join(ROOT, 'js', 'scanner.js'), encoding='utf-8').read()
    src = src.replace('const Scanner =', 'var Scanner =').replace(
        'getOCRAudit };', 'getOCRAudit, _fixOCRText };')
    ctx.eval(src)
    ctx.eval('var __ok = false; DB.load().then(() => { __ok = true; });'); ctx.eval('1')
    assert ctx.eval('__ok'), 'DB failed to load'
    return ctx

def pipeline(ctx, raw):
    s2 = ctx.eval(f'Scanner._fixOCRText({json.dumps(raw)})')
    s3 = ctx.eval(f'DB.fuzzyCorrect({json.dumps(s2)})')
    return s2, s3

if __name__ == '__main__':
    ctx = make_ctx()
    raw = 'Wait, Aqua (Water), lisohexdacne, SilICA, Octocryrene, U vegetable o, Fragrance. Wait'
    s2, s3 = pipeline(ctx, raw)
    print('RAW  :', raw); print('STG2 :', s2); print('STG3 :', s3)
