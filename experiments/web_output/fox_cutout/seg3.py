import cv2, numpy as np, sys
sys.path.insert(0, 'fv'); from seg2 import seg as lineseg
E = lambda r: cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(r,r))
def seg3(im, s=.5):
    core_full = lineseg(im)
    sm = cv2.resize(im, None, fx=s, fy=s, interpolation=cv2.INTER_AREA); H, W = sm.shape[:2]
    core = cv2.resize(core_full, (W, H), interpolation=cv2.INTER_NEAREST)
    b, g, r = [sm[:,:,i].astype(int) for i in range(3)]
    mask = np.full((H,W), cv2.GC_BGD, np.uint8)
    near = cv2.dilate(core, E(int(140*s)))                      # 몸통 주변(꼬리가 있을 만한 곳)
    mask[near > 0] = cv2.GC_PR_BGD
    mask[(near > 0) & (r - b > 22)] = cv2.GC_PR_FGD            # 따뜻한 금빛·크림색은 여우일 가능성
    mask[cv2.erode(core, E(int(10*s))) > 0] = cv2.GC_FGD
    mask[(b - r > 6) & (mask != cv2.GC_FGD)] = cv2.GC_BGD       # 푸른 하늘
    bg = np.zeros((1,65)); fg = np.zeros((1,65))
    try: cv2.grabCut(sm, mask, None, bg, fg, 4, cv2.GC_INIT_WITH_MASK)
    except cv2.error: pass
    m = np.where((mask==1)|(mask==3),255,0).astype(np.uint8)
    m = cv2.morphologyEx(m, cv2.MORPH_OPEN, E(5))
    n, lab, st, _ = cv2.connectedComponentsWithStats(m)
    if n > 1:
        keep = np.zeros_like(m)
        big = 1 + np.argmax(st[1:,4])
        for i in range(1, n):                                    # 큰 덩어리 + 그 근처 큰 조각
            if i == big or st[i,4] > 0.15 * st[big,4]: keep[lab==i] = 255
        m = keep
    m = cv2.resize(m, (im.shape[1], im.shape[0]), interpolation=cv2.INTER_LINEAR)
    m = np.maximum(m, core_full)
    return m
if __name__ == '__main__':
    import glob
    out=[]
    for i in [int(v) for v in sys.argv[1:]]:
        im = cv2.imread(f'fv/frames/{i+1:04d}.png'); m = seg3(im)
        o = im.copy(); o[m<128] = (o[m<128]*0.25 + np.array([60,200,60])*0.75).astype(np.uint8); out.append(cv2.resize(o,None,fx=.25,fy=.25))
    rows=[np.hstack(out[k:k+4]) for k in range(0,len(out),4)]
    cv2.imwrite('fv/seg3.png', np.vstack(rows))
