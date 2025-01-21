import sys

import cv2
import numpy as np  # 添加numpy库导入
import os  # 添加os库导入，用于文件操作

from PyQt5.QtWidgets import QApplication

from lsfInfo import LSFFile
from synthesisGUI import SynthesisGUI

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = SynthesisGUI()
    ex.show()
    sys.exit(app.exec_())

# 注释说明：main.py 是项目的启动文件