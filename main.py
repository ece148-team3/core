"""
This script is the main script to run the entire system. It will run the following:
- OAK-D lite RGB pipeline
- OAK-D lite depth pipeline
- BEV transformer
- VESC motor controller
- Socket client to send data to the server for image stitching
"""

# python built-in libraries
import logging
import pickle

# 3rd party libraries
import depthai as dai
import cv2 as cv
import numpy as np

# custom libraries
from vesc.vesc_control import VESC
from bev.transformer import BEVTransformer
from depth_sense.depth import DaiDepth

if __name__ == "__main__":
    
    DEBUG = True # global debug flag
    RGB_WIDTH = 1920
    RGB_HEIGHT = 1080
    
    logging.basicConfig(level=logging.INFO, format="[ %(levelname)s ] %(module)s -> %(funcName)s: %(message)s")
    
    # open VESC device
    try: 
        myvesc = VESC('/dev/ttyACM0', steering_offset=0.05)
    except Exception as e:
        logging.error(e)

    # load homography matrix for BEV
    logging.info("Loading homography matrix")
    with open('bev/homography_mat.pkl', 'rb') as f:
        H = pickle.load(f)

    bev_transformer = BEVTransformer(H, RGB_WIDTH, RGB_HEIGHT)

    # create pipeline
    pipeline = dai.Pipeline()

    # define source and output
    camRgb = pipeline.create(dai.node.ColorCamera)
    xoutRgb = pipeline.create(dai.node.XLinkOut)
    xoutRgb.setStreamName("rgb")

    # properties
    camRgb.setResolution(dai.ColorCameraProperties.SensorResolution.THE_1080_P)
    camRgb.setPreviewSize(RGB_WIDTH, RGB_HEIGHT)
    camRgb.setInterleaved(False)
    camRgb.setColorOrder(dai.ColorCameraProperties.ColorOrder.RGB)

    # linking
    camRgb.video.link(xoutRgb.input)

    # depth pipeline
    depth = DaiDepth(True, False, True, True, pipeline)

    with dai.Device(pipeline) as device:

        # Output queue will be used to get the rgb frames from the output defined above
        rbg_stream = device.getOutputQueue(name="rgb", maxSize=4, blocking=False)
        disparity_stream = device.getOutputQueue(name="disparity", maxSize=4, blocking=False)

        # disparity_stream = device.getOutputQueue(name="disparity", maxSize=1, blocking=False)
        while True:
            videoIn = rbg_stream.get()
            cv_frame = videoIn.getCvFrame()
            bev_img = bev_transformer.birdseye_view(cv_frame)
            bev_img = bev_img.download() # move back to CPU

            if DEBUG:
                cv.namedWindow("bev", cv.WINDOW_NORMAL)
                preview_bev = cv.resize(bev_img, (1920//4, 1080//4)) # downsizing for preview
                cv.imshow("bev", bev_img)

            # depth pipeline
            disparity_frame = depth.get_frame(disparity_stream)
            disparity_grid = depth.get_grid_disparity(disparity_frame, DEBUG)

            if cv.waitKey(1) == ord('q'):
                break
                
            # determine how the car should react if there is an obstacle
            turn_left = (np.sum(disparity_grid[0:3]) + np.sum(disparity_grid[6:9] == 0)) > 0
            turn_right = (np.sum(disparity_grid[12:15]) + np.sum(disparity_grid[18:21] == 0)) > 0

            print(disparity_grid)
            myvesc.set_angle(0.5)
            myvesc.set_throttle(0.1)

            # basic obstacle avoidance
            # if (turn_left and turn_right):
            #     logging.info("Reversing")
            #     myvesc.set_throttle(-0.1)
            # elif (turn_left):
            #     logging.info("Turning left")
            #     myvesc.set_angle(-1)
            # elif(turn_right):
            #     logging.info("Turning right")
            #     myvesc.set_angle(1)
            #     myvesc.set_throttle(0.1)
            # else:
            #     logging.info("Going straight")
            #     myvesc.set_angle(0)
            #     myvesc.set_throttle(0.1)
            


    






    
