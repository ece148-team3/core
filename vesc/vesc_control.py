"""The VESC class in this file is slightly modified to fit the needs of this ECE 148 project."""

import time
import logging
from utils.color import bcolors

class VESC:
    ''' 
    VESC Motor controler using pyvesc
    This is used for most electric scateboards.
    
    inputs: serial_port---- port used communicate with vesc. for linux should be something like /dev/ttyACM1
    has_sensor=False------- default value from pyvesc
    start_heartbeat=True----default value from pyvesc (I believe this sets up a heartbeat and kills speed if lost)
    baudrate=115200--------- baudrate used for communication with VESC
    timeout=0.05-------------time it will try before giving up on establishing connection
    
    percent=.2--------------max percentage of the dutycycle that the motor will be set to
    outputs: none
    
    uses the pyvesc library to open communication with the VESC and sets the servo to the angle (0-1) and the duty_cycle(speed of the car) to the throttle (mapped so that percentage will be max/min speed)
    
    Note that this depends on pyvesc, but using pip install pyvesc will create a pyvesc file that
    can only set the speed, but not set the servo angle. 
    
    Instead please use:
    pip install git+https://github.com/LiamBindle/PyVESC.git@master
    to install the pyvesc library
    '''
    def __init__(self, serial_port: str, percent: float=.2, has_sensor: bool=False, 
                 start_heartbeat: bool=True, baudrate: int=115200, timeout :float=0.05, 
                 steering_scale: float=1.0, steering_offset: float=0.0):
        
        try:
            import pyvesc
        except Exception as err:
            logging.error(bcolors.FAIL + str(err) + bcolors.ENDC)
            print("please use the following command to import pyvesc so that you can also set the servo position:")
            print("pip install git+https://github.com/LiamBindle/PyVESC.git@master")
            time.sleep(1)
            raise
        
        assert percent <= 1 and percent >= -1,'\n\nOnly percentages are allowed for MAX_VESC_SPEED (we recommend a value of about .2) (negative values flip direction of motor)'
        self.steering_scale = steering_scale
        self.steering_offset = steering_offset
        self.percent = percent
        
        try:
            self.v = pyvesc.VESC(serial_port, has_sensor, start_heartbeat, baudrate, timeout)
        except Exception as err:
            logging.error(bcolors.FAIL + str(err) + bcolors.ENDC)
            print("To fix permission denied errors, try running the following command:")
            print("sudo chmod a+rw {}".format(serial_port), "\n\n\n\n")
            time.sleep(1)
            raise

        logging.info(f"{bcolors.OKBLUE}VESC connected successfully{bcolors.ENDC}")
        logging.info("Testing VESC...")
        self._vesc_test()

        
    def run(self, angle: float, throttle: float):
        self.v.set_servo((angle * self.steering_scale) + self.steering_offset)
        self.v.set_duty_cycle(throttle*self.percent)

    def set_angle(self, angle: float):
        assert angle <= 1 and angle >= -1, '\n\nAngle values must be between -1 and 1'
        self.v.set_servo((angle * self.steering_scale) + self.steering_offset)

    def set_throttle(self, throttle: float):
        assert throttle <= 1 and throttle >= 0, '\n\nThrottle values must be between 0 and 1'
        self.v.set_duty_cycle(throttle*self.percent)

    def _vesc_test(self):
        """Test the VESC motor controller. """
        pause_timer = 0.2
        logging.info("Testing throttle...")
        myvesc.set_throttle(0.2)
        time.sleep(pause_timer)

        logging.info("Testing angle...")
        logging.info("Setting angle to 0.5")
        myvesc.set_angle(0.5)
        logging.info("Setting angle to 1")
        time.sleep(pause_timer)
        myvesc.set_angle(1)
        logging.info("Setting angle to -1")
        time.sleep(pause_timer)
        myvesc.set_angle(-1)
        time.sleep(pause_timer)

        logging.info("Testing completed.")
        myvesc.set_throttle(0)



# Test code
if __name__ == '__main__':
    myvesc = VESC('/dev/ttyACM0')
    myvesc.run(0, 0)  # angle is from -1 to 1, throttle is from 0 to 1 (0.2 is 20% of max speed)