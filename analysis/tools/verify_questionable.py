import cv2
import glob
import numpy as np
import json

f1 = glob.glob('reference/*5.88sec clip*')[0]
f2 = glob.glob('reference/*05.888sec-18.10seconds*')[0]
f3 = glob.glob('reference/*full video*')[0]

c1 = cv2.VideoCapture(f1)
c2 = cv2.VideoCapture(f2)
c3 = cv2.VideoCapture(f3)

fps = 23.976023976023978

def get_frame(global_idx):
    if global_idx < 141:
        c1.set(cv2.CAP_PROP_POS_FRAMES, global_idx)
        ret, fr = c1.read()
        return fr
    elif global_idx < 380:
        c2.set(cv2.CAP_PROP_POS_FRAMES, global_idx - 141)
        ret, fr = c2.read()
        return fr
    elif global_idx < 1955:
        c3.set(cv2.CAP_PROP_POS_FRAMES, global_idx - 380)
        ret, fr = c3.read()
        return fr
    return None

# Let's inspect questionable peaks to confirm whether they are cuts or in-shot action:
questionable = [
    # (frame, description/question)
    (540, "Between 514 and 588 - missile explosion cut?"),
    (675, "Inside shot 180 - ram impact vs cut?"),
    (734, "Inside shot 200 - Tony shock face vs cut?"),
    (762, "Inside shot 213 - nanotech mask reform?"),
    (775, "Inside shot 216 - Tony skidding?"),
    (886, "Inside shot 240 - purple stone firing blast?"),
    (912, "Inside shot 255 - beam hitting shield?"),
    (1004, "Inside shot 270 - Iron Man flight?"),
    (1040, "Inside shot 290 - boot clamp?"),
    (1076, "Inside shot 300 - arm weapon spin?"),
    (1082, "Inside shot 310 - punch?"),
    (1262, "Inside shot 360 - face-off?"),
    (1269, "Inside shot 370 - leg sweep?"),
    (1293, "Inside shot 375 - flip?"),
    (1339, "Inside shot 400 - block?"),
    (1346, "Inside shot 405 - punch 1?"),
    (1357, "Inside shot 410 - ground?"),
    (1375, "Inside shot 410 - recovery?"),
    (1402, "Inside shot 420 - dirt?"),
    (1409, "Inside shot 425 - overhead punch?"),
    (1423, "Inside shot 430 - broken helmet?"),
    (1478, "Inside shot 435 - point-blank blast?"),
    (1569, "Inside shot 450/455 - repulsor beam?"),
    (1646, "Inside shot 470 - flame stream?"),
    (1764, "Inside shot 490 - punch 1?"),
    (1768, "Inside shot 490 - punch 1 landing?"),
    (1783, "Inside shot 505 - punch 2 windup?"),
    (1788, "Inside shot 505 - punch 2 block?"),
    (1793, "Inside shot 505 - struggle?"),
    (1840, "Inside shot 530 - landscape struggle?"),
    (1865, "Inside shot 535/540 - sword reveal?")
]

print("Verifying questionable peaks:")
for f_idx, desc in questionable:
    fa = get_frame(f_idx - 1)
    fb = get_frame(f_idx)
    diff = np.mean(np.abs(fa[100:910].astype(float) - fb[100:910].astype(float)))
    # Save a small diagnostic image
    ca = cv2.resize(fa[100:910], (320, 150))
    cb = cv2.resize(fb[100:910], (320, 150))
    pair = np.hstack([ca, cb])
    cv2.putText(pair, f"f{f_idx-1}", (10, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)
    cv2.putText(pair, f"f{f_idx} ({f_idx/fps:.2f}s)", (330, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)
    cv2.imwrite(f"analysis/diagnostic_f{f_idx}.jpg", pair)
    print(f"Frame {f_idx:4d} ({f_idx/fps:6.3f}s): diff={diff:5.2f} | {desc}")
