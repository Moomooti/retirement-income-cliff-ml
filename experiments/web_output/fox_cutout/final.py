import cv2, numpy as np, glob, sys
sys.path.insert(0, 'fv')
import seg2, seg4, seg5
E = lambda r: cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(r,r))
fs = sorted(glob.glob('fv/frames/0*.png')); ims = [cv2.imread(f) for f in fs]
ms = []
for im in ims:
    m = np.maximum.reduce([seg2.seg(im), seg4.seg(im, 12, 15), seg5.seg(im, 12, 9)])
    m = seg4.fill_holes(m)
    n, lab, st, _ = cv2.connectedComponentsWithStats(m)
    if n > 1: m = np.where(lab == 1 + np.argmax(st[1:,4]), 255, 0).astype(np.uint8)
    ms.append(m)
area = np.array([m.mean() for m in ms])
med = np.array([np.median(area[max(0,i-4):i+5]) for i in range(len(area))])
good = area >= 0.88 * med
# 몸이 크게 빠진 프레임은 가장 가까운 멀쩡한 프레임으로
idx = []
for i in range(len(ms)):
    if good[i]: idx.append(i); continue
    cand = [j for j in range(len(ms)) if good[j]]; idx.append(min(cand, key=lambda j: abs(j-i)))
print('바꾼 프레임', [i for i in range(len(ms)) if not good[i]])
H, W = ims[0].shape[:2]
fade = np.ones((H,1),np.float32); n = int(H*.06); fade[H-n:,0] = np.linspace(1,0,n)
union = np.zeros((H,W),np.uint8)
for i in idx: union |= (ms[i] > 0).astype(np.uint8)
ys, xs = np.where(union); y0,y1,x0,x1 = max(0,ys.min()-6), min(H,ys.max()+6), max(0,xs.min()-6), min(W,xs.max()+6)
print('bbox', x0, y0, x1, y1)
for k, i in enumerate(idx):
    im, m = ims[i], ms[i]
    m = cv2.erode(m, E(3))                                     # 하늘빛 테두리 1~2px 깎기
    a = cv2.GaussianBlur(m.astype(np.float32), (0,0), 1.2)
    # 가장자리 색 보정: 테두리 픽셀 색을 안쪽 털 색으로 끌어오기
    core = cv2.erode(m, E(9)).astype(np.float32) / 255
    num = cv2.GaussianBlur(im.astype(np.float32) * core[...,None], (0,0), 4); den = cv2.GaussianBlur(core, (0,0), 4)[...,None]
    inner = num / np.maximum(den, 1e-3)
    edge = ((a > 2) & (a < 250) | ((m > 0) & (core == 0)))[...,None]
    col = np.where(edge & (den > .02), .5 * im + .5 * inner, im).astype(np.uint8)
    rgba = cv2.cvtColor(col, cv2.COLOR_BGR2BGRA); rgba[:,:,3] = np.clip(a * fade, 0, 255).astype(np.uint8)
    rgba[rgba[:,:,3] < 3] = 0
    cv2.imwrite(f'fv/frames/b_{k:04d}.png', rgba[y0:y1, x0:x1])
