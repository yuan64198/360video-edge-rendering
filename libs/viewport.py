#!/usr/bin/env python
#   Program:
#       To render the viewport of a viewer.
#   Author:
#       Wen-Chih, MosQuito, Lo
#   Date:
#       2017.4.22

import os 
import sys 
import math 
import subprocess 
import cv2 
import time 
import numpy
from libs import cal_prob
from libs import filemanager
from PIL import Image, ImageDraw

# Path
bitrate_path = "./bitrate/"
qp_path = "./qp/"
auto_path = "/auto/"
output_path = "./output/"
tmp_path = "./tmp/"
frame_path = "./frame/"

# Constants
FPS = 30
ENCODING_SERVER_ADDR = "140.114.77.170"

# ================================================================= #

def download_video_from_server(seg_length, seg_id, video):
    panorama = ENCODING_SERVER_ADDR + bitrate_path[1:] + str(seg_length) + "s" + "/" + str(video) + "/" + str(video) + "_equir_" + str(seg_id) + ".mp4"
    start_recv_ts = time.time()
    subprocess.call("wget %s -P %s" % (panorama, tmp_path), shell=True)
    return start_recv_ts


def ori_2_viewport(yaw, pitch, fov_degreew, fov_degreeh, tile_w, tile_h):
    return cal_prob.gen_fov(yaw, pitch, fov_degreew, fov_degreeh, tile_w, tile_h)

def count_tiles(prob):
    num = 0
    for i in range(0, len(prob), 1):
        if prob[i] == 1:
            num += 1
    return num

def video_2_image(seg_length, user_id, seg_id, video, bitrate):

    global tmp_path
    tmp_path = "./tmp_"+ video + '_user' + user_id + '_' + str(seg_id) + '_' + bitrate + '_VPR/'
    global output_path
    output_path = "./output_" + video + '_user' + user_id + '_' + str(seg_id) + '_' + bitrate + '_VPR/'
    global frame
    frame_path = "./frame_" + video + '_user' + user_id + '_' + str(seg_id) + '_' + bitrate + '_VPR/'
    # Check path and files existed or not
    filemanager.make_sure_path_exists(tmp_path)
    filemanager.make_sure_path_exists(output_path)
    filemanager.make_sure_path_exists(frame_path)


    # clip video into frames
    mp4_path = tmp_path + str(video) + "_equir_" + str(seg_id) + ".mp4"
    yuv_path = tmp_path + str(video) + "_equir_" + str(seg_id) + ".yuv"
    the_file = "output_" + video + '_user'+ user_id + '_' + str(seg_id) + '_' + bitrate + "_VPR.mp4"
    subprocess.call('mv %s %s' % (output_path + the_file, mp4_path), shell=True)
    conv2yuv = "ffmpeg -y -i " + mp4_path + " -c:v rawvideo -pix_fmt yuv420p " + yuv_path
    subprocess.call(conv2yuv, shell=True)
    vidcap = cv2.VideoCapture(mp4_path)
    if vidcap.isOpened():
        width = int(vidcap.get(cv2.CAP_PROP_FRAME_WIDTH))    # get width 
        height = int(vidcap.get(cv2.CAP_PROP_FRAME_HEIGHT))  # get height
        fps = int(vidcap.get(cv2.CAP_PROP_FPS))              # get fps
        length = int(vidcap.get(cv2.CAP_PROP_FRAME_COUNT))   # get length
    
    depth = 3
    ratio = 2 # YUV420: (4Y+1Cb+1Cr) = 12 bits per pixel
    frame_size = int(width * height * depth / ratio ) # bytes per frame
    
    # clip each frame form yuv video
    with open(yuv_path, 'rb') as vid_in:
        for i in range(1, int(length) + 1):
            # read data from yuv file
            frame_data = vid_in.read(frame_size)
            # output it as 1-frame long yuv file
            filename = frame_path + "frame" + str(i) + ".yuv"
            output_frame = open(filename, "w")
            output_frame.write(frame_data)
            print >> sys.stderr, "Clip a new frame:", filename


def render_fov_local( video, user_id, seg_id, index, bitrate, viewed_fov=[]):
    # open the image which can be many different formats
    global frame_path
    frame_path = "./frame_" + video + '_user'+user_id+'_'+ str(seg_id) + '_' + bitrate + '_VPR/'
    mp4_path = tmp_path + str(video) + "_equir_" + str(seg_id) + ".mp4"

    vidcap = cv2.VideoCapture(mp4_path)
    if vidcap.isOpened():
        width = int(vidcap.get(cv2.CAP_PROP_FRAME_WIDTH))    # get width 
        height = int(vidcap.get(cv2.CAP_PROP_FRAME_HEIGHT))  # get height
        fps = int(vidcap.get(cv2.CAP_PROP_FPS))              # get fps
        length = int(vidcap.get(cv2.CAP_PROP_FRAME_COUNT))   # get length
    
    depth = 3
    ratio = 2 # YUV420: (4Y+1Cb+1Cr) = 12 bits per pixel
    frame_size = int(width * height * depth / ratio ) # bytes per frame


    #open the image which can be many different formats
    ori_path= frame_path + "frame" + str(index) + ".yuv"
    (Y, U, V) = video2YCbCr(ori_path, width, height)
    # initialize the YUV map
    ret_Y = numpy.zeros([height, width], numpy.uint8, 'C')    
    ret_U = numpy.zeros([height // 2, width // 2], numpy.uint8, 'C')    
    ret_V = numpy.zeros([height // 2, width // 2], numpy.uint8, 'C')
    # get the pixel in viewport
    size = len(viewed_fov)
    for i in range(0, size):
        w = int(viewed_fov[i][0])
        h = int(viewed_fov[i][1])
        ret_Y[h, w] = Y[h, w]
        ret_U[h // 2, w // 2] = U[h // 2, w // 2]
        ret_V[h // 2, w // 2] = V[h // 2, w // 2]

    tmp = numpy.concatenate( (ret_Y.reshape(-1), ret_U.reshape(-1)) )
    ret = numpy.concatenate( (tmp, ret_V.reshape(-1)) )

    new_path = tmp_path + "fov_temp" + str(index) + ".yuv" 
    ret.tofile(new_path, "")
    print >> sys.stderr, frame_path + "frame" + str(index) + ".yuv" + " --> " + tmp_path + "fov_temp" + str(index) + ".yuv"


def video2YCbCr(filename, width, height):    
    fp = open(filename, "rb")    
    print >> sys.stderr, "Read YUV frame:", filename
    #print >> sys.stderr, "width =", width, ", height =", height

    d00 = height // 2
    d01 = width // 2

    Y = numpy.zeros([height, width], numpy.uint8, 'C')    
    U = numpy.zeros([d00, d01], numpy.uint8, 'C')    
    V = numpy.zeros([d00, d01], numpy.uint8, 'C')

    for m in range(height):    
        for n in range(width):    
            Y[m, n] = ord(fp.read(1))    
    for m in range(d00):    
        for n in range(d01):    
            U[m, n] = ord(fp.read(1))    
    for m in range(d00):    
        for n in range(d01):    
            V[m, n] = ord(fp.read(1))    
    fp.close()    
    return (Y, U, V)

def concat_image_2_video( video, user_id, seg_id, bitrate):
    mp4_path = tmp_path + str(video) + "_equir_" + str(seg_id) + ".mp4"
    vidcap = cv2.VideoCapture(mp4_path)
    if vidcap.isOpened():
        width = int(vidcap.get(cv2.CAP_PROP_FRAME_WIDTH))    # get width 
        height = int(vidcap.get(cv2.CAP_PROP_FRAME_HEIGHT))  # get height
        fps = int(vidcap.get(cv2.CAP_PROP_FPS))              # get fps
        length = int(vidcap.get(cv2.CAP_PROP_FRAME_COUNT))   # get length
    # merge yuv frames into one yuv
    frame_list = []
    for i in range(1, length + 1):
        frame_name = tmp_path + "fov_temp" + str(i) + ".yuv" 
        frame_list.append(frame_name)
    for i in range(0, len(frame_list)):
        subprocess.call('cat %s >> %s' % (frame_list[i], tmp_path) + 'concat_frame.yuv', shell=True)
    # compress the yuv file
        kvazaar = "kvazaar -i " + tmp_path + "concat_frame.yuv" + " --input-res=3840x1920 --input-fps 30.0 --bitrate " + str(int(int(bitrate[:-4]) * math.pow(10, 6))) + " -o " + tmp_path + "concat_frame.hvc" + " 2>&1 | tee " + tmp_path + "psnr_" + video + '_' + str(seg_id) + '_' + str(bitrate) + "_VPR.csv"
        subprocess.call(kvazaar, shell=True)

    # encapsulate hvc bitstream into mp4 container
    #mp4box = "MP4Box -add " + tmp_path + "concat_frame.hvc:fps=" + str(FPS) + " -new " + output_path + "output_%s.mp4" % seg_id
    the_file = "output_" + video + '_user'+ user_id + '_' + str(seg_id) + '_' + bitrate + "_VPR.mp4"
    mp4box = "MP4Box -add " + tmp_path + "concat_frame.hvc:fps=" + str(FPS) + " -new " + output_path + the_file
    subprocess.call(mp4box, shell=True)

def create_image(i, j):
    # Create a new image with the given size
    image = Image.new("RGB", (i, j))
    return image


def get_pixel(image, i, j):
    # inside image bounds or not 
    width, height = image.size 
    if i > width or j > height:
        return None
    # get pixel
    pixel = image.getpixel( (i, j) )
    return pixel
