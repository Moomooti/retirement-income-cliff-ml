import cv2, numpy as np, glob, sys
sys.path.insert(0, 'fv'); from seg2 import seg
fs = sorted(glob.glob('fv/frames/*.png')); ims = [cv2.imread(f) for f in fs]
ms = [seg(im).astype(np.float32) for im in ims]
ms = [cv2.GaussianBlur(m, (0,0), 1.6) for m in ms]
sm = []
for i in range(len(ms)):                       # 깜빡임 줄이기: 앞뒤 프레임과 살짝 평균
    a = ms[max(0,i-1)]; c = ms[min(len(ms)-1,i+1)]; sm.append(.2*a + .6*ms[i] + .2*c)
H, W = ims[0].shape[:2]
fade = np.ones((H,1),np.float32); n = int(H*.06); fade[H-n:,0] = np.linspace(1,0,n)   # 영상 아래로 잘린 부분 부드럽게
union = np.zeros((H,W),np.uint8)
for m in sm: union |= (m > 40).astype(np.uint8)
ys, xs = np.where(union); y0,y1,x0,x1 = max(0,ys.min()-6), min(H,ys.max()+6), max(0,xs.min()-6), min(W,xs.max()+6)
print('bbox', x0,y0,x1,y1)
for i,(im,m) in enumerate(zip(ims,sm)):
    a = np.clip(m * fade, 0, 255).astype(np.uint8)
    rgba = cv2.cvtColor(im, cv2.COLOR_BGR2BGRA); rgba[:,:,3] = a
    rgba[a < 3] = 0
    cv2.imwrite(f'fv/frames/a_{i:04d}.png', rgba[y0:y1, x0:x1])
