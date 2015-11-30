
import sys
import math

from PyQt5.QtWidgets import QWidget, QApplication
from PyQt5.QtGui import QPainter, QColor, QPen, QBrush
from PyQt5.QtCore import (Qt, QPointF, QTimer, QElapsedTimer,
    pyqtSignal, QDateTime)


class CalibrationWidget(QWidget):

    cursorPos = pyqtSignal(float, float, 'qint64')

    def __init__(self, parent=None):
        super().__init__(parent)

        self._margin_x = 0.0
        self._margin_y = 0.0
        self._offset_x = 1.0
        self._offset_y = 1.0
        self._ampl_x = 1.0
        self._ampl_y = 1.0
        self._coeff_x = 5.0
        self._coeff_y = 4.0
        self._coeff_delta = 0.0
        self._t = 0.0
        self._circle_size = 20

        self._pen = QPen()
        self._pen.setWidth(2)
        self._pen.setColor(Qt.black)
        self._brush = QBrush(Qt.yellow)

        self._elapsed_timer = QElapsedTimer()
        self._timer = QTimer()
        self._timer.setInterval(1000 / 60)
        self._timer.timeout.connect(self.update)

        self.resize(800, 600)
        self.setWindowTitle('Eyetracker calibration')

        self._elapsed_timer.start()
        self._timer.start()

    def resizeEvent(self, event):
        w, h = self.width(), self.height()
        self._margin_x = 0.05 * w
        self._margin_y = 0.08 * h
        self._offset_x = 0.5 * w
        self._offset_y = 0.5 * h
        self._ampl_x = 0.5 * (w - 2.0 * self._margin_x)
        self._ampl_y = 0.5 * (h - 2.0 * self._margin_y)
        self._circle_size = 0.05 * h
        self._pen.setWidth(0.005 * h)

    def paintEvent(self, event):
        qp = QPainter()
        qp.begin(self)

        qp.setRenderHint(QPainter.Antialiasing)

        elapsed = self._elapsed_timer.restart()
        if elapsed > 100:
            elapsed = 100
        self._t += 0.0002 * elapsed

        x = self._offset_x + \
            self._ampl_x * math.sin(self._coeff_x * self._t + self._coeff_delta)

        y = self._offset_y + \
            self._ampl_y * math.sin(self._coeff_y * self._t)

        qp.setPen(self._pen)
        qp.setBrush(self._brush)
        qp.drawEllipse(QPointF(x, y), self._circle_size, self._circle_size)

        qp.end()

        self.cursorPos.emit(x, y, QDateTime.currentMSecsSinceEpoch())


if __name__ == '__main__':
    app = QApplication(sys.argv)
    wnd = CalibrationWidget()
    wnd.show()
    sys.exit(app.exec_())
