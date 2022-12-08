import cv2 as cv
import numpy as np
import depthai as dai
import logging
import pickle
import time
from bev.transformer import BEVTransformer

# SETUP
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="[ %(levelname)s ] %(message)s")

    # Create pipeline
    pipeline = dai.Pipeline()

    # Define source and output
    camRgb = pipeline.create(dai.node.ColorCamera)
    xoutVideo = pipeline.create(dai.node.XLinkOut)

    xoutVideo.setStreamName("video")

    # Properties
    camRgb.setFps(30)
    camRgb.setBoardSocket(dai.CameraBoardSocket.RGB)
    camRgb.setResolution(dai.ColorCameraProperties.SensorResolution.THE_1080_P)
    camRgb.setVideoSize(1920, 1080)

    xoutVideo.input.setBlocking(False)
    xoutVideo.input.setQueueSize(1)

    # Linking
    camRgb.video.link(xoutVideo.input)

    logging.info("Loading homography matrix")
    with open('homography_mat.pkl', 'rb') as f:
        H = pickle.load(f)


    # Connect to device and start pipeline
    logging.info("Starting video stream")
    with dai.Device(pipeline) as device:

        video = device.getOutputQueue(name="video", maxSize=1, blocking=False)

        while True:
            start = time.time()
            
            videoIn = video.get()
            cv_frame = videoIn.getCvFrame()
            bev_img = birdseye_view(cv_frame, H)

            # Time elapsed
            end = time.time()
            seconds = end - start
            print (f"Frame time: {round(seconds, 4)} seconds")
        
            # Calculate frames per second
            fps  = 1 / seconds
            print(f"Estimated FPS: {fps}")

            # disp_img = np.hstack([cv_frame, bev_img])
            if DEBUG:
                cv.namedWindow("BEV", cv.WINDOW_NORMAL)
                preview_bev = cv.resize(bev_img, (1920//4, 1080//4))
                cv.imshow("BEV", preview_bev)

                if cv.waitKey(1) == ord('q'):
                    break

    