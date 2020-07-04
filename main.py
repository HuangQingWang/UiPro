import sys
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from untitled import Ui_MainWindow
from takepic import Ui_Form
import cv2
import numpy as np
from client_socket import send
from videoShow import showVideo, getoneFrame
from pykinect2 import PyKinectV2
from pykinect2.PyKinectV2 import *
from pykinect2 import PyKinectRuntime
import os
import socket
import time
import re

# 定义两个全局变量用来主线程和socket线程通信
localPicPath = ''
realSendPicName = ''
#
picResultPath  = ''  #处理好的图片的存放路径的名字
picResultNmae = ''   #处理好的图片的名字        比如:   people20

class waitPicThread(QThread):
    findPicSignal  = pyqtSignal()
    def __init__(self, address,Obj, parent=None):
        QThread.__init__(self, parent)
        self.address = address
        self.textLines = Obj
    def run(self):
        TimeCount = 0
        while True:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect(self.address)
            sock.send('$|$'.encode())  # 默认编码 utf-8,发送文件长度和文件名
            reply = sock.recv(1024)
            if reply.decode() == 'startconImagetoMyPC_OK':
                #获得接收图片的名字和大小
                #开始接收图片
                global picResultPath,picResultNmae
                sock.send('ok'.encode())
                reply = sock.recv(1024)
                length, file_name = reply.decode().split('|')
                sock.send('ok_ok'.encode())
                desk = os.path.join(os.path.expanduser("~"), 'Desktop') + '\\'
                tempnameList = file_name.split('&')
                picResultNmae = tempnameList[1] + tempnameList[2]
                picResultPath = desk + tempnameList[1] + tempnameList[2]
                newfile = open(picResultPath, 'wb')
                file = b''
                total = int(length)
                get = 0
                while get < total:  # 接收文件
                    data = sock.recv(1024)
                    file += data
                    get = get + len(data)
                print('应该接收{},实际接收{}'.format(length, len(file)))
                # 开始接收图片
                if file:
                    print('acturally length:{}'.format(len(file)))
                    newfile.write(file[:])
                    newfile.close()
                    sock.send(b'copy')  # 告诉完整的收到文件了
                    self.textLines.append("Succeed in receiving Image")
                    self.findPicSignal.emit()
                break

            else:
                time.sleep(2)
                TimeCount =TimeCount  +1
                print("Waiting Image From Yun")
                self.textLines.append("Waiting Image From Yun")
                if TimeCount == 15:
                    break
            sock.close()



class picUploadThread(QThread):
    startWaitRePicFla= pyqtSignal()
    def generatePicName(self):
        temp = time.strftime("%Y-%m-%d-%H:%M:%S", time.localtime())
        sendFileName = temp + '&' + realSendPicName + '&' + '000'
        return sendFileName

    def run(self):
        send(localPicPath, self.generatePicName())
        # 图片发送成功之后就要开始开始等待新的图片了到来了,这里要开启一个定时器，因为定时向服务器请求图片是否处理成功
        self.startWaitRePicFla.emit()

class showVideoThread(QThread):
    def __init__(self, uiobj, kinectobj, parent=None):
        QThread.__init__(self, parent)
        self.ui = uiobj
        self.kinect = kinectobj

    def run(self):
        showVideo(self.ui, self.kinect)


class MyUi_Form(QWidget):
    def __init__(self, parent=None):
        super(MyUi_Form, self).__init__(parent)
        self.ui = Ui_Form()
        self.ui.setupUi(self)
        self.ke = PyKinectRuntime.PyKinectRuntime(PyKinectV2.FrameSourceTypes_Color)
        self.ui.picButton.clicked.connect(self.takepic)
        self.ui.picButton_2.clicked.connect(self.savepic)
        self.showVideoThread = showVideoThread(uiobj=self.ui, kinectobj=self.ke)
        self.saveFrame = None

    def takepic(self):
        self.saveFrame = getoneFrame()
        self.ke.close()
        self.showVideoThread.quit()

    def savepic(self):
        self.showVideoThread.quit()
        desk = os.path.join(os.path.expanduser("~"), 'Desktop') + '\\'
        filename = QFileDialog.getSaveFileName(self, '选择保存路径', desk, 'jpg(*.jpg)')
        cv2.imwrite(filename[0], self.saveFrame)
        #self.showVideoThread.start()

    def open(self):
        self.show()
        self.ke = PyKinectRuntime.PyKinectRuntime(PyKinectV2.FrameSourceTypes_Color)
        self.showVideoThread.start()

    def closeEvent(self, event):
        reply = QMessageBox.question(self,
                                     '本程序',
                                     "是否要退出程序？",
                                     QMessageBox.Yes | QMessageBox.No,
                                     QMessageBox.No)
        if reply == QMessageBox.Yes:

            event.accept()
        else:
            event.ignore()


class MainWindow(QMainWindow):
    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.ui.pushButton_2.clicked.connect(self.openPic)
        self.ui.pushButton_6.clicked.connect(self.esLink)
        self.ui.pushButton_4.clicked.connect(self.showslectedPic)
        self.ui.pushButton_5.clicked.connect(self.showPicresult)

        self.ui.checkBox.clicked.connect(self.checkBoxSlection)
        self.ui.checkBox_2.clicked.connect(self.checkBoxSlection)
        self.ui.checkBox_3.clicked.connect(self.checkBoxSlection)
        self.ui.checkBox_4.clicked.connect(self.checkBoxSlection)
        self.ui.checkBox_5.clicked.connect(self.checkBoxSlection)
        self.ui.checkBox_6.clicked.connect(self.checkBoxSlection)
        self.ui.pushButton_3.clicked.connect(self.uploadPic)

        self.tempList = [self.ui.checkBox, self.ui.checkBox_2, self.ui.checkBox_3, self.ui.checkBox_4,
                         self.ui.checkBox_5, self.ui.checkBox_6]
        self.checkSlectedFlage = 0
        self.detectObjection = ''
        self.picName = ''
        self.address = ['', 8000]
        self.address[0] = self.ui.lineEdit.text()

        self.picUploadThread = picUploadThread()
        self.picUploadThread.startWaitRePicFla.connect(self.openWaitTimer)
        self.waitPicThread = waitPicThread(address=tuple(self.address),Obj=self.ui.textBrowser)
        self.waitPicThread.findPicSignal.connect(self.FindPicture)



    #  self.showVideoThread = showVideoThread(uiobj = self.ui)
    #每当上传完图片会发送一个信号，这是接受槽
    def openWaitTimer(self):
        self.waitPicThread.start()

    def FindPicture(self):
        #得到图片之后就把图片显示在界面上面
        QMessageBox.about(self, '通知', '图片已经处理完毕')
        number= re.findall(r'\d+', picResultNmae)
        self.ui.label_4.setText("<html><head/><body><p><span style=\" font-size:72pt; color:#5500ff;\">"+str(number[0])+"</span></p></body></html>")

    #显示被选中的图片的槽函数
    def showslectedPic(self):
        global localPicPath
        fname = localPicPath
        if fname:
            img = cv2.imdecode(np.fromfile(fname, dtype=np.uint8), -1)  # 当使用中文路径的时候只能这样读
            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            self.zoomscale = 1
            height, width, depth = img.shape
            frame = QImage(img.data, width, height, width * depth, QImage.Format_RGB888)
            pix = QPixmap.fromImage(frame)
            self.item = QGraphicsPixmapItem(pix)
            scene = QGraphicsScene()
            scene.addItem(self.item)
            self.ui.graphicsView.setScene(scene)
        else:
            pass

    #显示选中图片处理之后的槽函数
    def showPicresult(self):
        global picResultPath
        fname = picResultPath
        if fname:
            img = cv2.imdecode(np.fromfile(fname, dtype=np.uint8), -1)  # 当使用中文路径的时候只能这样读
            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            self.zoomscale = 1
            height, width, depth = img.shape
            frame = QImage(img.data, width, height, width * depth, QImage.Format_RGB888)
            pix = QPixmap.fromImage(frame)
            self.item = QGraphicsPixmapItem(pix)
            scene = QGraphicsScene()
            scene.addItem(self.item)
            self.ui.graphicsView.setScene(scene)
        else:
            pass

    # 定义建立连接的槽
    def esLink(self):
        addressTuple = tuple(self.address)
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect(addressTuple)
        sock.send('&|&'.encode())  # 默认编码 utf-8,发送文件长度和文件名
        reply = sock.recv(1024)
        if reply.decode() == 'link_ok':
            self.ui.textBrowser.append("成功连接服务器！！！")
        else:
            self.ui.textBrowser.append("连接服务器失败！！！")
        sock.close()

    # 以下定义的是打开图片按钮的槽
    def openPic(self):
        global localPicPath
        print("打开图片被按下")
        self.ui.textBrowser.append("打开图片按钮 被按下")
        fname, _ = QFileDialog.getOpenFileName(self, '打开文件', '.', '图像文件(*.jpg *.png)')
        if fname:
            localPicPath = fname
            img = cv2.imdecode(np.fromfile(fname, dtype=np.uint8), -1)  # 当使用中文路径的时候只能这样读
            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            self.zoomscale = 1
            height, width, depth = img.shape
            frame = QImage(img.data, width, height, width * depth, QImage.Format_RGB888)
            pix = QPixmap.fromImage(frame)
            self.item = QGraphicsPixmapItem(pix)
            scene = QGraphicsScene()
            scene.addItem(self.item)
            self.ui.graphicsView.setScene(scene)
        else:
            pass


    # 以下是定义checkbox的槽函数
    def checkBoxSlection(self):
        global realSendPicName
        if self.checkSlectedFlage == 0:
            for index, i in enumerate(self.tempList):
                if i.isChecked():
                    for index_j, j in enumerate(self.tempList):
                        if index_j != index:
                            j.setEnabled(False)
                        self.checkSlectedFlage = 1
                        if index == 0:
                            self.detectObjection = 'person'
                        elif index == 1:
                            self.detectObjection = 'desk'
                        elif index == 2:
                            self.detectObjection = 'car'
                        elif index == 3:
                            self.detectObjection = 'chair'
                        elif index == 4:
                            self.detectObjection = 'lightcar'
                        elif index == 5:
                            self.detectObjection = 'tv'

                        self.picName = self.detectObjection
                        realSendPicName = self.picName
        elif self.checkSlectedFlage == 1:
            for i in self.tempList:
                i.setEnabled(True)
                self.checkSlectedFlage = 0

    # 以下是定义上传图片的槽
    def uploadPic(self):
        global localPicPath
        if localPicPath == '':
            QMessageBox.warning(self, '警告', '请打开一张图片')
        elif self.checkSlectedFlage == 0:
            QMessageBox.warning(self, '警告', '请选择一个需要检测的物体')
        else:
            self.picUploadThread.start()

    def keyPressEvent(self, e):
        if e.key() == Qt.Key_Q:
            self.ui.textBrowser.append("Q被按下 图片被缩小")
            self.zoomscale = self.zoomscale - 0.05
            if self.zoomscale <= 0:
                self.zoomscale = 0.2
            self.item.setScale(self.zoomscale)
        if e.key() == Qt.Key_W:
            self.ui.textBrowser.append("W被按下 图片被放大")
            self.zoomscale = self.zoomscale + 0.05
            if self.zoomscale >= 1.2:
                self.zoomscale = 1.2
            self.item.setScale(self.zoomscale)

    def openVideo(self):
        self.showVideoThread.start(self.ui)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    main = MainWindow()
    w1 = MyUi_Form()
    main.show()
    main.ui.pushButton_7.clicked.connect(w1.open)
    sys.exit(app.exec_())
