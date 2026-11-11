import numpy as np
def label(D, base):
    f = {k: D[f'{base}_f{k}'] for k in [2, 3, 4]}
    obs = sum(f[k].notna().astype(int) for k in f); below = sum((f[k] < 1).astype(int) for k in f)
    ok = f[2].notna() & f[4].notna()
    y = np.where(f[3].notna(), below >= 2, (f[2] < 1) & (f[4] < 1))   # 3번 중 2번, 격년 조사는 2번 중 2번
    return ok, y.astype(int)


