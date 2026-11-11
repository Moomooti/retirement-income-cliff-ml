import cv2, numpy as np, sys
E = lambda r: cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(r,r))
def fill_holes(m):
    H, W = m.shape; ff = m.copy(); mk = np.zeros((H+2,W+2),np.uint8)
    for x,y in [(0,0),(W-1,0),(0,H-1),(W-1,H-1)]:
        if ff[y,x]==0: cv2.floodFill(ff, mk, (x,y), 128)
    return np.where(ff==128,0,255).astype(np.uint8)
def flood_border(img):
    H, W = img.shape; ff = img.copy(); mk = np.zeros((H+2,W+2),np.uint8)
    for x in range(0, W, 8):
        for y in (0, H-1):
            if ff[y,x]==255: cv2.floodFill(ff, mk, (x,y), 128)
    for y in range(0, H, 8):
        for x in (0, W-1):
            if ff[y,x]==255: cv2.floodFill(ff, mk, (x,y), 128)
    return (ff==128).astype(np.uint8)*255
def seg(im, thr=12, d=9):
    H, W = im.shape[:2]
    g = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)
    lines = ((cv2.GaussianBlur(g,(0,0),5).astype(int) - g.astype(int)) > thr).astype(np.uint8)*255
    n, lab, st, _ = cv2.connectedComponentsWithStats(lines)
    small = np.isin(lab, np.where(st[:,4] < 25)[0]); lines[small] = 0
    lines = cv2.morphologyEx(lines, cv2.MORPH_CLOSE, E(5))
    free = cv2.bitwise_not(lines)
    core_bg = flood_border(cv2.erode(free, E(2*d+1)))            # 좁은 틈(2d px 미만)으로는 못 들어가는 배경
    bg = cv2.bitwise_and(cv2.dilate(core_bg, E(2*d+1)), free)
    bg = cv2.bitwise_and(flood_border(np.where(bg>0,255,0).astype(np.uint8)), bg)   # 바깥과 이어진 배경만
    inside = cv2.bitwise_not(bg)
    blob = fill_holes(cv2.morphologyEx(inside, cv2.MORPH_OPEN, E(7)))
    n, lab, st, _ = cv2.connectedComponentsWithStats(blob)
    if n < 2: return blob
    big = 1 + np.argmax(st[1:,4]); return np.where(lab==big,255,0).astype(np.uint8)
if __name__ == '__main__':
    thr, d = int(sys.argv[1]), int(sys.argv[2]); out=[]
    for i in [1,5,40,80,84,88,90,109,60,20,70,100]:
        im = cv2.imread(f'fv/frames/{i+1:04d}.png'); m = seg(im, thr, d)
        o = im.copy(); o[m<128] = (o[m<128]*0.25 + np.array([60,200,60])*0.75).astype(np.uint8); out.append(cv2.resize(o,None,fx=.25,fy=.25))
    cv2.imwrite(f'fv/seg5_{thr}_{d}.png', np.vstack([np.hstack(out[k:k+4]) for k in range(0,12,4)]))
