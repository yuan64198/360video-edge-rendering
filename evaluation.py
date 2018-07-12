from libs import VPsnrCalc

import cv2
import cPickle

seg_id = 1
VIDEO = "drive"
user_id = "01"
mode = "TR"
bitrate = "1Mbps"

expe = cv2.VideoCapture("./output_drive_user01_1_1Mbps_VPR/output_drive_user01_1_1Mbps_VPR.mp4")
cont = cv2.VideoCapture("../360videos_60s/drive_equir.mp4")

frame_no = (seg_id - 1)*64 + 1

for i in range(frame_no-1):
    ret, imgC = cont.read()

while(True):
    ret, imgE = expe.read()
    if(imgE is None):
        print("next clip...")
        break
    ret, imgC = cont.read()
    if(imgC is None):
        print("Error!!!!!!!!!!!!!!!!!!")
        break
    tmp = frame_no%64 if frame_no%64!=0 else 64
    pickle_path = "./pickles/fov_drive_user01_1_16Mbps_VPR_1.pkl"
    viewed_fov = cPickle.load(open(pickle_path,"rb"))
    psnr = VPsnrCalc.VPsnrCalc(imgE, imgC, viewed_fov)
    print(str(frame_no)+" viewport_psnr:        "+str(psnr))
