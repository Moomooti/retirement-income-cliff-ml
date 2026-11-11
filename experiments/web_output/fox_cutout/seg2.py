import cv2, numpy as np, sys
E = lambda r: cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(r,r))
def fill_holes(m):
    H, W = m.shape; ff = m.copy(); mk = np.zeros((H+2,W+2),np.uint8)
    for x,y in [(0,0),(W-1,0),(0,H-1),(W-1,H-1)]:
        if ff[y,x]==0: cv2.floodFill(ff, mk, (x,y), 128)
    return np.where(ff==128,0,255).astype(np.uint8)
def seg(im):
    H, W = im.shape[:2]
    g = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)
    lines = ((cv2.GaussianBlur(g,(0,0),6).astype(int) - g.astype(int)) > 16).astype(np.uint8)*255
    lines = cv2.morphologyEx(lines, cv2.MORPH_CLOSE, E(9))
    free = cv2.bitwise_not(lines); ff = free.copy(); mk = np.zeros((H+2,W+2),np.uint8)
    for x in range(0, W, 40):
        for y in (0, H-1):
            if ff[y,x]==255: cv2.floodFill(ff, mk, (x,y), 128)
    for y in range(0, H, 40):
        for x in (0, W-1):
            if ff[y,x]==255: cv2.floodFill(ff, mk, (x,y), 128)
    inside = np.where(ff==128,0,255).astype(np.uint8)          # 선 + 선으로 닫힌 영역
    blob = cv2.morphologyEx(inside, cv2.MORPH_CLOSE, E(21))      # 몸 안쪽 조각들 합치기
    blob = fill_holes(blob)
    blob = cv2.morphologyEx(blob, cv2.MORPH_OPEN, E(9))          # 가는 잔선 제거
    n, lab, st, _ = cv2.connectedComponentsWithStats(blob)
    if n < 2: return blob
    k = 1 + np.argmax(st[1:,4]); fg = np.where(lab==k,255,0).astype(np.uint8)
    return fg
if __name__ == '__main__':
    outs=[]
    for t in sys.argv[1:]:
        im = cv2.imread(f'fv/f_{t}.png'); fg = seg(im)
        o = im.copy(); o[fg==0] = (o[fg==0]*0.25 + np.array([60,200,60])*0.75).astype(np.uint8); outs.append(cv2.resize(o,None,fx=.4,fy=.4))
    cv2.imwrite('fv/seg2_all.png', np.vstack([np.hstack(outs[:2]), np.hstack(outs[2:4])]))
