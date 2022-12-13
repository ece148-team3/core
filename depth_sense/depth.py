import cv2
import depthai as dai
import numpy as np

class DaiDepth:
    def __init__(self, extended_disparity, subpixel, lr_check, show_frame, pipeline):
        # Closer-in minimum depth, disparity range is doubled (from 95 to 190):
        self.extended_disparity = extended_disparity
        # Better accuracy for longer distance, fractional disparity 32-levels:
        self.subpixel = subpixel
        # Better handling for occlusions:
        self.lr_check = lr_check
        # Pipeline
        self.pipeline = pipeline
        # Show camera view with frame labels
        self.show_frame = show_frame

        # Define sources and outputs
        self.monoLeft = self.pipeline.create(dai.node.MonoCamera)
        self.monoRight = self.pipeline.create(dai.node.MonoCamera)
        self.depth = self.pipeline.create(dai.node.StereoDepth)
        self.xout = self.pipeline.create(dai.node.XLinkOut)
        self.xout.setStreamName("disparity")
        # Properties
        self.monoLeft.setResolution(dai.MonoCameraProperties.SensorResolution.THE_400_P)
        self.monoLeft.setBoardSocket(dai.CameraBoardSocket.LEFT)
        self.monoRight.setResolution(dai.MonoCameraProperties.SensorResolution.THE_400_P)
        self.monoRight.setBoardSocket(dai.CameraBoardSocket.RIGHT)

        # Create a node that will produce the depth map (using disparity output as it's easier to visualize depth this way)
        self.depth.setDefaultProfilePreset(dai.node.StereoDepth.PresetMode.HIGH_DENSITY)
        # Options: MEDIAN_OFF, KERNEL_3x3, KERNEL_5x5, KERNEL_7x7 (default)
        self.depth.initialConfig.setMedianFilter(dai.MedianFilter.KERNEL_7x7)
        self.depth.setLeftRightCheck(self.lr_check)
        self.depth.setExtendedDisparity(self.extended_disparity)
        self.depth.setSubpixel(self.subpixel)

        config = self.depth.initialConfig.get()
        config.postProcessing.speckleFilter.enable = False
        config.postProcessing.speckleFilter.speckleRange = 50
        config.postProcessing.temporalFilter.enable = True
        config.postProcessing.spatialFilter.enable = True
        config.postProcessing.spatialFilter.holeFillingRadius = 2
        config.postProcessing.spatialFilter.numIterations = 1
        config.postProcessing.thresholdFilter.minRange = 400
        config.postProcessing.thresholdFilter.maxRange = 15000
        config.postProcessing.decimationFilter.decimationFactor = 1
        self.depth.initialConfig.set(config)
        self.max_disparity_val = self.depth.initialConfig.getMaxDisparity()

        # Linking
        self.monoLeft.out.link(self.depth.left)
        self.monoRight.out.link(self.depth.right)
        self.depth.disparity.link(self.xout.input)

        self.focal_length = dai.Device(self.pipeline).readCalibration().getCameraIntrinsics(dai.CameraBoardSocket.RIGHT)[0][0]


    def get_frame(self, disparity_stream, visualize=False):
        """Get raw disparity stream from the pipeline, apply normalization to make range into [0, 255]"""
        inDisparity = disparity_stream.get()  # blocking call, will wait until a new data has arrived
        frame = inDisparity.getFrame()
        normalized_frame = (frame * (255 / self.max_disparity_val)).astype(np.float32) # normalize and return
        return normalized_frame

    def get_grid_disparity(self, frame, show_frame=False):
        # calculate the corners of the square frames
        num_box = 4 * 6
        num_pts = 5 * 7
        pts = z = np.empty((4, num_box), dtype=np.uint16)
        vis_frame = None
        # fill the pts array column-wise
        for i in range(6):
            for j in range(4):
                pts[0][4*i+j] = 1 + 106 * i # x1
                pts[1][4*i+j] = 1 + 106 * (i+1) # x2
                pts[2][4*i+j] = 1 + 99 * j # y1
                pts[3][4*i+j] = 1 + 99 * (j+1) # y2
        # print(pts)
        scaling  = 190 / 255 if self.extended_disparity else 95 / 255

        if show_frame:
            print(frame.shape)
            vis_frame = cv2.applyColorMap(frame.astype(np.uint8), cv2.COLORMAP_JET)

        disparities, depths, middle_pts = np.empty(num_box, dtype=np.uint16), np.empty(num_box, dtype=np.float64), []  
        for i in range(num_box):
            subframe = frame[pts[2][i]:pts[3][i], pts[0][i]:pts[1][i]]
            subframe = subframe[subframe>0] # we don't want extreme values
            subframe = subframe[subframe<190]
            disparities[i] = frame[(pts[2][i]+pts[3][i])//2][(pts[0][i]+pts[1][i])//2] * scaling

            if show_frame:
                middle_pts.append(((pts[0][i]+pts[1][i])//2, (pts[2][i]+pts[3][i])//2))
                vis_frame = cv2.rectangle(vis_frame, (pts[0][i],pts[2][i]), (pts[1][i],pts[3][i]), (0,255,0), 1)
                vis_frame = cv2.putText(vis_frame, str(disparities[i]), middle_pts[i], cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0,255,0), 1, cv2.LINE_AA)
        
        if show_frame:
            cv2.imshow("disparity_color_map", vis_frame)
            
        return disparities

         



                