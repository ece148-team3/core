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

# custom libraries
from vesc.vesc_control import VESC
from bev.transformer import BEVTransformer
from depth_sense.depth import DaiDepth


if __name__ == "__main__":
    
    DEBUG = True # global debug flag
    RGB_WIDTH = 1920
    RGB_HEIGHT = 1080
    
    logging.basicConfig(level=logging.INFO, format="[ %(levelname)s ] %(module)s -> %(funcName)s: %(message)s")
    try: 
        myvesc = VESC('/dev/ttyACM0', steering_offset=0.05)
    except Exception as e:
        logging.error(e)

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
    # depth = DaiDepth(True, False, True, True, dai.Pipeline())


    with dai.Device(pipeline) as device:

        logging.info('Connected cameras: ', device.getConnectedCameras())
        logging.info('Usb speed: ', device.getUsbSpeed().name)

        # Output queue will be used to get the rgb frames from the output defined above
        rbg_stream = device.getOutputQueue(name="rgb", maxSize=4, blocking=False)

        # disparity_stream = device.getOutputQueue(name="disparity", maxSize=1, blocking=False)
        while True:
            videoIn = rbg_stream.get()
            cv_frame = videoIn.getCvFrame()
            bev_img = bev_transformer.birdseye_view(cv_frame)
            bev_img = bev_img.download()

            if DEBUG:  
                cv.namedWindow("bev", cv.WINDOW_NORMAL)
                preview_bev = cv.resize(bev_img, (1920//4, 1080//4)) # downsizing for preview
                cv.imshow("bev", preview_bev)
                if cv.waitKey(1) == ord('q'):
                    continue




    






    
