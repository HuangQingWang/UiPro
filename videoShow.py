from pykinect2 import PyKinectV2
from pykinect2.PyKinectV2 import *
from pykinect2 import PyKinectRuntime
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
import cv2
import numpy as np

def cvimg_to_qtimg(cvimg):
    height, width, depth = cvimg.shape
    cvimg = cv2.cvtColor(cvimg, cv2.COLOR_BGR2RGB)
    cvimg = QImage(cvimg.data, width, height, width * depth, QImage.Format_RGB888)
    return cvimg

_kinect = None

def getoneFrame():
    frame = _kinect.get_last_color_frame()
    colourframe = np.reshape(frame, (2073600, 4))
    colourframe = colourframe[:, 0:3]

    # extract then combine the RBG data
    colourframeR = colourframe[:, 0]
    colourframeR = np.reshape(colourframeR, (1080, 1920))
    colourframeG = colourframe[:, 1]
    colourframeG = np.reshape(colourframeG, (1080, 1920))
    colourframeB = colourframe[:, 2]
    colourframeB = np.reshape(colourframeB, (1080, 1920))
    frame = cv2.merge([colourframeR, colourframeG, colourframeB])
    return frame

def showVideo(uiobj,kinect):
    global _kinect
    _kinect = kinect
    h, w = 840, 1536

    while True:
        if _kinect.has_new_color_frame():
            frame = _kinect.get_last_color_frame()
            colourframe = np.reshape(frame, (2073600, 4))
            colourframe = colourframe[:, 0:3]

            # extract then combine the RBG data
            colourframeR = colourframe[:, 0]
            colourframeR = np.reshape(colourframeR, (1080, 1920))
            colourframeG = colourframe[:, 1]
            colourframeG = np.reshape(colourframeG, (1080, 1920))
            colourframeB = colourframe[:, 2]
            colourframeB = np.reshape(colourframeB, (1080, 1920))

            frame = cv2.merge([colourframeR, colourframeG, colourframeB])
            frame = cv2.resize(frame,(w ,h), 0, 0)
            image = cvimg_to_qtimg(frame)
            uiobj.label.setPixmap(QPixmap(image).scaled(uiobj.label.width(), uiobj.label.height()))
            cv2.waitKey(2)
        else:
            continue