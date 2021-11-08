import sys

import cv2
import numpy as np
import os

from PIL import Image 

from PyQt5 import uic, QtGui, QtCore, QtWidgets
from PyQt5.QtWidgets import QApplication, QWidget, QMainWindow, QLabel, QFileDialog, QDialog

PIXEL_WIDTH=32
PIXEL_HEIGHT=32
SCALE = 19
BORDER = 1


class GenerateAnimatedGifDialog(QDialog):
    def __init__(self, app):
        super(GenerateAnimatedGifDialog, self).__init__()
        self.image = app.rawImage.copy()
        self.offsetX = app.offsetX
        self.offsetY = app.offsetY
        uic.loadUi('Dialog-NumberFrames.ui', self)

        # Set some good defaults for our text boxes
        self.strideXWidget.setText(str(PIXEL_WIDTH))
        self.strideYWidget.setText(str(PIXEL_HEIGHT))
        self.frameDelayWidget.setText(str(75))

        # Number of frames until the edge of the image.
        imageFramesUntilEnd = int((self.image.shape[0] - self.offsetX) / PIXEL_WIDTH )
        self.numberFramesWidget.setText(str(imageFramesUntilEnd))

        proposedFilename = ""
        proposedFileIndex = 1
        while True:
            proposedFilename = "{base}-{proposedFileIndex}.gif".format(base=app.filename[0:-4], proposedFileIndex=proposedFileIndex)
            print(f"proposedFilename: {proposedFilename}")
            if not os.path.isfile(proposedFilename):
                break
            proposedFileIndex += 1
        self.filenameWidget.setText(proposedFilename)


    def _getNextLocation(self):
        resultX = self.offsetX
        resultY = self.offsetY

        self.offsetX += self.strideX
        if self.offsetX + PIXEL_WIDTH - 1 >= self.image.shape[1]:
            self.offsetX = 0
            self.offsetY += self.strideY

            # Make sure that I haven't gone too far and wrap around if I have.
            if self.offsetY + PIXEL_HEIGHT - 1 >= self.image.shape[0]:
                self.offsetX = 0
                self.offsetY = 0

        return (resultX, resultY)

    def _getNextFrame(self):
        (x,y) = self._getNextLocation()
        roi = self.image[y:y+PIXEL_HEIGHT,x:x+PIXEL_WIDTH]
        pilImage = Image.fromarray(roi)
        return pilImage

    def accept(self):
        numberFrames = int(self.numberFramesWidget.text())
        frameDelayMs = int(self.frameDelayWidget.text())
        self.strideX = int(self.strideXWidget.text())
        self.strideY = int(self.strideYWidget.text())
        print( f"accept - generating frames;  numberFrames: {numberFrames}")
        frames = []
        for i in range(numberFrames):
            frames.append(self._getNextFrame())

        firstFrame = frames[0]
        firstFrame.save(self.filenameWidget.text(), format="GIF", append_images=frames,
               save_all=True, duration=frameDelayMs, loop=0)

        self.close()


class PixelApp(QMainWindow):
    def __init__(self):
        super(PixelApp, self).__init__()
        uic.loadUi('PixelArt.ui', self)

        self.leftButton.clicked.connect(lambda: self.moveViewport(-1,0))
        self.rightButton.clicked.connect(lambda: self.moveViewport(1,0))
        self.upButton.clicked.connect(lambda: self.moveViewport(0,-1))
        self.downButton.clicked.connect(lambda: self.moveViewport(0,1))
        self.actionLoad.triggered.connect(self.loadClicked)
        self.actionGenerate.triggered.connect(self.generateClicked)

        self.offsetX = 0
        self.offsetY = 0

        self.w = PIXEL_WIDTH        # w is the pixel width
        self.h = PIXEL_HEIGHT       # h is the pixel height
        self.b = BORDER             # b is the border size
        self.s = SCALE              # s is the scale to blow up each pixel in the viewport window

        # The viewport window is a view into the image where each pixel is increased
        # in size in a uniform way based on the scale.
        self.viewportWidth = (self.w * self.s) + (self.b * self.w)
        self.viewportHeight = (self.h * self.s) + (self.b * self.h)

        self.overviewWidth = self.overviewImageFrame.width()
        self.overviewHeight = self.overviewImageFrame.height()

        self.rawImage = None
        self.filename = None

    def generateClicked(self):
        dlg = GenerateAnimatedGifDialog(self)
        dlg.exec()

    def moveViewport(self, deltaX, deltaY):
        self.offsetX += deltaX
        self.offsetY += deltaY
        self.enforceOffsetBoundaries()
        self.buildDisplay()

    def enforceOffsetBoundaries(self):
        self.offsetX = max(0, min(self.rawImage.shape[1]-self.w, self.offsetX))
        self.offsetY = max(0, min(self.rawImage.shape[0]-self.h, self.offsetY))

    def keyPressEvent(self, event):
        print(f"got keystroke: {event.key()}")
        modifiers = QtWidgets.QApplication.keyboardModifiers()
        deltaMovementX = 1
        deltaMovementY = 1
        if (modifiers & QtCore.Qt.ShiftModifier) == QtCore.Qt.ShiftModifier:
            deltaMovementX = self.w
            deltaMovementY = self.h
        if event.key() == QtCore.Qt.Key_Q:
            self.deleteLater()
        elif event.key() == QtCore.Qt.Key_H:
            self.moveViewport(-deltaMovementX,0)
        elif event.key() == QtCore.Qt.Key_J:
            self.moveViewport(0,deltaMovementY)
        elif event.key() == QtCore.Qt.Key_K:
            self.moveViewport(0,-deltaMovementY)
        elif event.key() == QtCore.Qt.Key_L:
            self.moveViewport(deltaMovementX,0)
        elif event.key() == QtCore.Qt.Key_S:
            self.rescaleImage(0.5)
        elif event.key() == QtCore.Qt.Key_B:
            self.rescaleImage(2)
        event.accept()

    def rescaleImage(self, amount):
        if self.rawImage.shape[1]*amount < self.w or self.rawImage.shape[0]*amount < self.h:
            print("This would make it too small.")
        else:
            self.rawImage = cv2.resize(self.rawImage, (0,0), fx=amount, fy=amount)
            self.offsetX = int(self.offsetX*amount)
            self.offsetY = int(self.offsetY*amount)
            self.enforceOffsetBoundaries()
            self.buildDisplay()

    def loadClicked(self):
        fname, filter=QFileDialog.getOpenFileName(self,'Open File','imgs/',"Image Files(*.jpg *.png *.gif)")
        if fname:
            self.loadImage(fname)
        else:
            print('No image selected')

    def loadImage(self, filename):
        self.filename = filename
        self.offsetX = 0
        self.offsetY = 0
        self.rawImage = cv2.imread(filename)
        assert len(self.rawImage.shape)==3

        if self.rawImage.shape[2] ==4:
            self.qformat=QtGui.QImage.Format_RGBA8888
        else:
            self.qformat=QtGui.QImage.Format_RGB888

        self.buildDisplay()

    def buildDisplay(self):
        # First show the grid version of the pixels
        self.displayImage = np.zeros((self.viewportHeight, self.viewportWidth,3), np.uint8)
        for y in range(self.h):
            for x in range(self.w):
                color = self.rawImage[self.offsetY + y, self.offsetX+x]
                cv2.rectangle(self.displayImage, 
                         ((x * (self.s + self.b)), (y * (self.s + self.b))), 
                          (((x+1) * (self.s + self.b)) - 1, ((y+1) * (self.s + self.b) - 1)),
                        (int(color[0]),int(color[1]),int(color[2])),
                        -1)

        image = QtGui.QImage(
                self.displayImage.data, 
                self.displayImage.shape[1], 
                self.displayImage.shape[0], 
                self.displayImage.strides[0],
                self.qformat)
        image.rgbSwapped()
        self.imageFrame.setPixmap(QtGui.QPixmap.fromImage(image))

        # Next draw the holistic view of the entire image along with what we
        # are currently seeing within the viewport.
        self.overviewImage = np.zeros((self.overviewHeight, self.overviewWidth,3), np.uint8)
        
        # determine how much to scale the rawImage so that it fits within the
        # overviewHeight and overviewWidth but without distorting the ratio.
        ratio = min(self.overviewHeight / self.rawImage.shape[0], self.overviewWidth / self.rawImage.shape[1] )
        print(f"overviewSize: {self.overviewWidth}, {self.overviewHeight}, rawImageSize: {self.rawImage.shape[1]},{self.rawImage.shape[0]}, ratio: {ratio}")

        rawImageResized = cv2.resize(self.rawImage, (0,0), fx=ratio, fy=ratio)

        # Draw the red box around the area that I'm viewing now.
        x0 = int(self.offsetX * ratio)
        y0 = int(self.offsetY * ratio) 

        x1 = int((self.offsetX+self.w) * ratio)
        y1 = int((self.offsetY+self.h) * ratio)

        print(f"region: ({x0},{y0}) -> ({x1},{y1}) for offsetX: {self.offsetX}, offsetY: {self.offsetY}")

        cv2.rectangle(rawImageResized, 
                (x0, y0),
                (x1, y1),
                (255,0,0),
                2)

        image = QtGui.QImage(
                rawImageResized.data, 
                rawImageResized.shape[1], 
                rawImageResized.shape[0], 
                rawImageResized.strides[0],
                QtGui.QImage.Format_RGB888)
        image.rgbSwapped()
        self.overviewImageFrame.setPixmap(QtGui.QPixmap.fromImage(image))


if __name__ == "__main__":
    app = QApplication(sys.argv)

    pixelApp = PixelApp()
    pixelApp.loadImage("imgs/SpriteSheet3.png")
    pixelApp.show()

    sys.exit(app.exec_())
