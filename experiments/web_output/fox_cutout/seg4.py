import cv2, numpy as np, sys
E = lambda r: cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(r,r))
def fill_holes(m):
    H, W = m.shape; ff = m.copy(); mk = np.zeros((H+2,W+2),np.uint8)
    for x,y in [(0,0),(W-1,0),(0,H-1),(W-1,H-1)]:
        if ff[y,x]==0: cv2.floodFill(ff, mk, (x,y), 128)
    return np.where(ff==128,0,255).astype(np.uint8)
def seg(im, thr=12, ck=15):
    H, W = im.shape[:2]
    g = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)
    lines = ((cv2.GaussianBlur(g,(0,0),5).astype(int) - g.astype(int)) > thr).astype(np.uint8)*255
    # 작은 점(깃털 결, 구름 결) 제거: 길쭉한 선만
    n, lab, st, _ = cv2.connectedComponentsWithStats(lines)
    keep = np.zeros_like(lines)
    for i in range(1, n):
        if st[i,4] >= 25: keep[lab==i] = 255
    sealed = cv2.morphologyEx(keep, cv2.MORPH_CLOSE, E(ck))
    free = cv2.bitwise_not(sealed); ff = free.copy(); mk = np.zeros((H+2,W+2),np.uint8)
    for x in range(0, W, 20):
        for y in (0, H-1):
            if ff[y,x]==255: cv2.floodFill(ff, mk, (x,y), 128)
    for y in range(0, H, 20):
        for x in (0, W-1):
            if ff[y,x]==255: cv2.floodFill(ff, mk, (x,y), 128)
    inside = np.where(ff==128,0,255).astype(np.uint8)
    blob = fill_holes(cv2.morphologyEx(inside, cv2.MORPH_CLOSE, E(25)))
    blob = cv2.morphologyEx(blob, cv2.MORPH_OPEN, E(11))
    n, lab, st, _ = cv2.connectedComponentsWithStats(blob)
    if n < 2: return blob
    big = 1 + np.argmax(st[1:,4]); fg = np.where(lab==big,255,0).astype(np.uint8)
    # 닫기로 바깥쪽에 생긴 군살 조금 깎기
    return cv2.erode(fg, E(3))
if __name__ == '__main__':
    thr, ck = int(sys.argv[1]), int(sys.argv[2]); out=[]
    for i in [1,5,40,80,84,88,90,109,60,20,70,100]:
        im = cv2.imread(f'fv/frames/{i+1:04d}.png'); m = seg(im, thr, ck)
        o = im.copy(); o[m<128] = (o[m<128]*0.25 + np.array([60,200,60])*0.75).astype(np.uint8); out.append(cv2.resize(o,None,fx=.25,fy=.25))
    cv2.imwrite(f'fv/seg4_{thr}_{ck}.png', np.vstack([np.hstack(out[k:k+4]) for k in range(0,12,4)]))
