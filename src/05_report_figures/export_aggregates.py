"""결과 pkl에서 집계 수치만 JSON으로 꺼낸다 (모델 객체·사람 ID(te_keys)·개인 단위 값은 제외)."""
import pandas as pd, numpy as np, json, sys, os
OUT = sys.argv[1]; os.makedirs(OUT, exist_ok=True)
def cv(v):
    if isinstance(v, pd.DataFrame): return v.to_dict('records')
    if isinstance(v, pd.Series): return v.to_dict()
    if isinstance(v, np.ndarray):
        return v.tolist() if v.size <= 2000 else f'<array {v.shape} 생략>'
    if isinstance(v, (np.floating, np.integer, np.bool_)): return v.item()
    if isinstance(v, dict) or hasattr(v, 'keys'): return {str(k): cv(v[k]) for k in v.keys()}
    if isinstance(v, (list, tuple)): return [cv(x) for x in v]
    if isinstance(v, (str, int, float, bool)) or v is None: return v
    return f'<{type(v).__name__} 생략>'
def dump(name, obj):
    json.dump(obj, open(f'{OUT}/{name}', 'w', encoding='utf-8'), ensure_ascii=False, indent=1, default=str); print(name)
v3 = pd.read_pickle('v3_out.pkl'); dump('v3_results.json', cv(v3))
s = pd.read_pickle('s_out.pkl')
dump('service_model_results.json', {('/'.join(k) if isinstance(k, tuple) else k): (cv(v['res']) if isinstance(v, dict) and 'res' in v else cv(v)) for k, v in s.items()})
b = pd.read_pickle('b_out.pkl'); dump('b20_results.json', {'res': cv(b['res']), 'params': cv(b['M'].get('params')), 'cols': cv(b['M'].get('cols'))})
