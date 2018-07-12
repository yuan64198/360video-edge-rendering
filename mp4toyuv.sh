#!/bin/bash 
PATH=/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin:~/bin:/ssd/bin
export PATH

#videos=(coaster coaster2 diving drive game landscape pacman panel ride sport)

allmp4=($PWD/output*/*.mp4)

for mp4 in ${allmp4[@]}; do 
    echo $mp4
    yuv_name=`basename "$mp4"`
    ffmpeg -i $mp4 -f rawvideo -vcodec rawvideo -pix_fmt yuv420p ${yuv_name%.*}.yuv
done
