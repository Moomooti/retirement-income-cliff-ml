import cv2, numpy as np, sys
def seg(im, prev=None):
    H, W = im.shape[:2]
    g = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(g, (0,0), 6)
    lines = ((blur.astype(int) - g.astype(int)) > 18).astype(np.uint8) * 255   # 주변보다 어두운 가는 선
    lines = cv2.morphologyEx(lines, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(5,5)))
    free = cv2.bitwise_not(lines)
    ff = free.copy(); m2 = np.zeros((H+2,W+2),np.uint8)
    for (x,y) in [(0,0),(W-1,0),(0,H-1),(W-1,H-1),(W//2,0),(0,H//2),(W-1,H//2)]:
        if ff[y,x]==255: cv2.floodFill(ff, m2, (x,y), 128)
    inside = np.where(ff==128, 0, 255).astype(np.uint8)
    inside = cv2.morphologyEx(inside, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(7,7)))
    n, lab, st, _ = cv2.connectedComponentsWithStats(inside)
    if n < 2: return inside, lines
    k = 1 + np.argmax(st[1:,4]); fg = np.where(lab==k,255,0).astype(np.uint8)
    return fg, lines
if __name__ == '__main__':
    for t in sys.argv[1:]:
        im = cv2.imread(f'fv/f_{t}.png'); fg, lines = seg(im)
        out = im.copy(); out[fg==0] = (out[fg==0]*0.25 + np.array([60,200,60])*0.75).astype(np.uint8)
        cv2.imwrite(f'fv/seg_{t}.png', cv2.resize(np.hstack([out, cv2.cvtColor(lines,cv2.COLOR_GRAY2BGR)]), None, fx=.4, fy=.4))
        print(t, round(fg.mean()/255,3))
