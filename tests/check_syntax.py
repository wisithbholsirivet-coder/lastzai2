"""Parse-check every js/*.js in V8 without executing (new Function)."""
import glob, json, os
from py_mini_racer import MiniRacer
os.chdir(r'C:\Users\Wisithbhol S\.gemini\antigravity\scratch\chaecheck')
c = MiniRacer()
bad = 0
for f in sorted(glob.glob('js/*.js')):
    src = json.dumps(open(f, encoding='utf-8').read())
    r = c.eval('(() => { try { new Function(' + src + '); return "OK"; } catch (e) { return "ERR " + e.message; } })()')
    bad += r != 'OK'
    print(f'{r:4} {f}')
print('all OK' if not bad else f'{bad} file(s) with syntax errors')
