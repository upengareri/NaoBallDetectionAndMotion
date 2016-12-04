#Names: Upendar_Gareri, Jennifer_Victor, Anusha_Karemane_JayaKumar

import cv2
import imutils
from imutils.object_detection import non_max_suppression
from imutils import paths
import numpy as np
from naoqi import ALProxy
from vision_definitions import kQVGA,kBGRColorSpace
import sys
import math
import almath
import time

NAO="nao.local"

if __name__=="__main__":    # this is to check if we are importing

    camera_index=0 # top camera

    # http://colorizer.org/
    # define the lower and upper boundaries of the "yellow"
    # ball in the HSV color space, then initialize the
    #yellowLower = (25, 86, 6)
    #yellowUpper = (35, 255, 255)
    lower_range = np.array([20, 100, 100], dtype = np.uint8) #yellow
    upper_range = np.array([40, 255, 255], dtype = np.uint8) #yellow
    #lower_range = np.array([169, 100, 100], dtype = np.uint8) #red
    #upper_range = np.array([189, 255, 255], dtype = np.uint8) #red

    colorLower = lower_range
    colorUpper = upper_range

    # Create a proxy for ALVideoDevice
    name="nao_opencv"
    video=ALProxy("ALVideoDevice",NAO,9559)
    motionProxy = ALProxy("ALMotion", NAO, 9559)
    motionProxy.setStiffnesses("Head", 0.8) 

    # subscribe to video device on a specific camera # BGR for opencv
    name=video.subscribeCamera(name,camera_index,kQVGA,kBGRColorSpace,30)
    print "subscribed name",name

    useSensors  = True
    names = ["HeadYaw", "HeadPitch"]

    try:
        frame=None
        # keep looping
        while True:
            key=cv2.waitKey(33)&0xFF
            if  key == ord('q') or key==27: #quit when 'q' or 'escape' is pressed
                motionProxy.setStiffnesses("Head", 0.0)
                sensorAngles = motionProxy.getAngles(names, True)
                print "Sensor angles:"
                print str(sensorAngles)
                print "Center of the ball:"
                print str(center_object)
                break

            # obtain image
            alimg=video.getImageRemote(name)

            # extract fields
            width=alimg[0]
            height=alimg[1]
            nchannels=alimg[2]
            imgbuffer=alimg[6]
            center_frame = (width, height)

            # build opencv image (allocate on first pass)
            if frame is None:
                print 'Grabbed image: ',width,'x',height,' nchannels=',nchannels
                frame=np.asarray(bytearray(imgbuffer), dtype=np.uint8)
                frame=frame.reshape((height,width,3))
            else:
                frame.data=bytearray(imgbuffer)

            # Smoothing Images
            # http://docs.opencv.org/master/d4/d13/tutorial_py_filtering.html#gsc.tab=0
            blurred = cv2.GaussianBlur(frame, (11, 11), 0)
            # Converts an image from one color space to another
            #http://docs.opencv.org/master/df/d9d/tutorial_py_colorspaces.html#gsc.tab=0
            hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

            # construct a mask for the color, then perform
            #  a series of dilations and erosions to remove any small
            # blobs left in the mask
            mask = cv2.inRange(hsv,colorLower,colorUpper)
            mask = cv2.erode(mask, None, iterations=2)
            mask = cv2.dilate(mask, None, iterations=2)

            # find contours in the mask and initialize the current
            # (x, y) center of the ball
            cnts = cv2.findContours(mask.copy(), cv2.RETR_EXTERNAL,
                cv2.CHAIN_APPROX_SIMPLE)[-2]
            center = None

            # only proceed if at least one contour was found
            if len(cnts) > 0:
                # find the largest contour in the mask, then use
                # it to compute the minimum enclosing circle and
                # centroid
                c = max(cnts, key=cv2.contourArea)
                ((x_enclosing, y_enclosing), radius) = cv2.minEnclosingCircle(c)
                M = cv2.moments(c) #moment can be used to find coordinate positions, mass etc of the object

                #sensorAngles = motionProxy.getAngles(names, True)
                #print "Sensor angles:"
                #print str(sensorAngles)
                #print ""

                x_object = int(M["m10"] / M["m00"]) #gives x coordinate of the object
                y_object = int(M["m01"] / M["m00"]) #gives y coordinate of the object
                center_object = (x_object,y_object)

                # only proceed if the radius meets a minimum size
                if radius > 10:
                    # draw the circle and centroid on the frame,
                    # then update the list of tracked points
                    diff = np.subtract(center_object, center_frame)
                    #print center_object
                    #print diff
                    cv2.circle(frame, (int(x_enclosing), int(y_enclosing)), int(radius),
                        (0, 255, 255), 2)
                    cv2.circle(frame, center_object, 5, (0, 0, 255), -1)
                    changes = [-(diff[0]*0.001), diff[1]*0.001]
                    #print changes
                    motionProxy.setAngles(names, changes, 0.05)

            # show the frame to our screen
            # Do not run this code if your run your python in the robot
            # NAO has no screen to show
            cv2.imshow("Frame", frame)

    finally: # if anything goes wrong we'll make sure to unsubscribe
        print "unsubscribing",name
        motionProxy.setStiffnesses("Head", 0.0)
        sensorAngles = motionProxy.getAngles(names, True)
     	print "Sensor angles:"
     	print str(sensorAngles)
        print "Center of the ball:"
        print str(center_object)
        video.unsubscribe(name)
