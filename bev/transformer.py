import numpy as np
import cv2 as cv
import logging
from utils.color import bcolors

class BEVTransformer:
    def __init__(self, H, width, height) -> None:
        self.H = H
        self.width = width
        self.height = height

        # downward translation (temporarily)
        self.T = np.array([[1, 0, 100], 
                    [0, 1, 100]], dtype=np.float32)

        count = cv.cuda.getCudaEnabledDeviceCount()
        if count: 
            logging.info(f"{bcolors.OKBLUE}Found {count} CUDA devices{bcolors.ENDC}")
            cv.cuda.setDevice(0)
        else:
            logging.warn(f"{bcolors.WARNING}No CUDA devices found{bcolors.ENDC}")

    
    def birdseye_view(self, img: np.ndarray) -> np.ndarray:
        """apply perspective transformation to obtain bird's eye view using precalculated homography matrix"""
        try: 
            cuda_img = cv.cuda_GpuMat(img) # transfer to GPU
            transformed_frame = cv.cuda.warpPerspective(cuda_img, self.H, (self.width, self.height)) # apply transformation
            translated_frame = cv.cuda.warpAffine(transformed_frame, self.T, (self.width, self.height)) # downward translation
            return translated_frame
        except Exception as e:
            logging.error(bcolors.FAIL + str(e) + bcolors.ENDC)
            return None
