import os
import sys

import cv2
import numpy as np
from PyQt5.QtCore import Qt, QSize, pyqtSignal
from PyQt5.QtGui import QPixmap, QImage, QIcon
from PyQt5.QtWidgets import QApplication, QMainWindow, QAction, QVBoxLayout, QHBoxLayout, QWidget, QLabel, QScrollArea, \
    QFileDialog, QSizePolicy, QPushButton, QMessageBox, QTextEdit

from lsfInfo import LSFFile
from synthesis_util import synthesis


class BottomBarComponent(QWidget):
    index_changed = pyqtSignal(object)

    def __init__(self, type_str, cv2_image, data_list, index, sid=0):
        super().__init__()
        self.type = type_str
        self.sid = sid
        self.data_list = data_list
        self.index = index

        layout = QVBoxLayout()
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(0)

        text_label = QLabel(type_str)
        text_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(text_label)

        if cv2_image is not None:
            if cv2_image.shape[2] == 4:
                height, width, channel = cv2_image.shape
                bytes_per_line = 4 * width
                q_image = QImage(cv2_image.data, width, height, bytes_per_line, QImage.Format_ARGB32)
            else:
                height, width, channel = cv2_image.shape
                bytes_per_line = 3 * width
                q_image = QImage(cv2_image.data, width, height, bytes_per_line, QImage.Format_RGB888).rgbSwapped()
            pixmap = QPixmap.fromImage(q_image)
            scaled_pixmap = pixmap.scaledToHeight(100, Qt.SmoothTransformation)
            self.image_label = QLabel()
            self.image_label.setPixmap(scaled_pixmap)
            self.image_label.setAlignment(Qt.AlignCenter)
            self.image_label.setMargin(0)
            layout.addWidget(self.image_label)

        bottom_layout = QHBoxLayout()

        left_button = QPushButton()
        left_button.setIcon(QIcon("static/BxLeftArrow.svg"))
        left_button.setIconSize(QSize(20, 20))
        left_button.setFlat(True)
        left_button.setStyleSheet("background-color: transparent;")
        left_button.clicked.connect(self.decrement_index)
        bottom_layout.addWidget(left_button)

        self.bottom_text_label = QLabel(f"{self.index + 1}/{len(self.data_list)}")
        self.bottom_text_label.setAlignment(Qt.AlignCenter)
        bottom_layout.addWidget(self.bottom_text_label)

        right_button = QPushButton()
        right_button.setIcon(QIcon("static/BxRightArrow.svg"))
        right_button.setIconSize(QSize(20, 20))
        right_button.setFlat(True)
        right_button.setStyleSheet("background-color: transparent;")
        right_button.clicked.connect(self.increment_index)
        bottom_layout.addWidget(right_button)

        # 将底部布局添加到主布局中
        layout.addLayout(bottom_layout)

        self.setLayout(layout)
        self.setStyleSheet("border: 1px solid #808080; padding: 5px;")
        size_policy = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        self.setSizePolicy(size_policy)

    def decrement_index(self):
        self.index -= 1
        self.index %= len(self.data_list)
        self.bottom_text_label.setText(f"{self.index + 1}/{len(self.data_list)}")
        self.index_changed.emit(self)

    def increment_index(self):
        self.index += 1
        self.index %= len(self.data_list)
        self.bottom_text_label.setText(f"{self.index + 1}/{len(self.data_list)}")
        self.index_changed.emit(self)

    def reset_image(self, cv2_image):
        # 重新设置图片
        if cv2_image is not None:
            if cv2_image.shape[2] == 4:
                height, width, channel = cv2_image.shape
                bytes_per_line = 4 * width
                q_image = QImage(cv2_image.data, width, height, bytes_per_line, QImage.Format_ARGB32)
            else:
                height, width, channel = cv2_image.shape
                bytes_per_line = 3 * width
                q_image = QImage(cv2_image.data, width, height, bytes_per_line, QImage.Format_RGB888).rgbSwapped()
            pixmap = QPixmap.fromImage(q_image)
            # 按比例缩放图片
            scaled_pixmap = pixmap.scaledToHeight(100, Qt.SmoothTransformation)
            self.image_label.setPixmap(scaled_pixmap)


class SynthesisGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.directory = None
        self.main_layout = None
        self.sidebar_layout = QVBoxLayout()
        self.sidebar_widget = QWidget()
        self.sidebar_widget.setLayout(self.sidebar_layout)
        self.setWindowTitle('ESCUDE-CG-Composer')
        self.setGeometry(100, 100, 800, 600)

        self.menubar = self.menuBar()
        file_menu = self.menubar.addMenu('导入目录')
        extract_menu = self.menubar.addMenu('提取')
        help_menu = self.menubar.addMenu('帮助')
        exit_menu = self.menubar.addMenu('退出')

        exit_action = QAction('退出', self)
        exit_action.triggered.connect(self.close)
        exit_menu.addAction(exit_action)

        import_action = QAction('导入目录', self)
        import_action.triggered.connect(self.open_directory_dialog)
        file_menu.addAction(import_action)

        extract_action = QAction('提取图片', self)
        extract_action.triggered.connect(self.extract_image)
        extract_menu.addAction(extract_action)

        help_action = QAction('操作说明', self)
        help_action.triggered.connect(self.show_help_document)
        help_menu.addAction(help_action)

        self.main_layout = QVBoxLayout()

        self.sidebar = QScrollArea()
        self.sidebar.setFixedWidth(200)
        self.sidebar.setWidgetResizable(True)
        self.sidebar_layout.setSpacing(5)
        self.sidebar_layout.setContentsMargins(5, 5, 5, 5)
        self.sidebar.setWidget(self.sidebar_widget)

        self.image_display = QScrollArea()
        self.image_display.setWidgetResizable(True)
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.display_cv2_image()
        self.image_display.setWidget(self.image_label)

        self.top_layout = QHBoxLayout()
        self.top_layout.addWidget(self.sidebar)
        self.top_layout.addWidget(self.image_display)

        self.bottom_bar = QScrollArea()
        self.bottom_bar.setFixedHeight(200)
        self.bottom_bar.setWidgetResizable(True)
        bottom_bar_widget = QWidget()
        self.bottom_bar_layout = QHBoxLayout(bottom_bar_widget)
        self.bottom_bar_layout.setContentsMargins(5, 5, 5, 5)  # 调整外边距
        self.bottom_bar_layout.setSpacing(5)  # 调整间距
        self.bottom_bar.setWidget(bottom_bar_widget)

        self.main_layout.addLayout(self.top_layout)
        self.main_layout.addWidget(self.bottom_bar)

        self.central_widget = QWidget()
        self.central_widget.setLayout(self.main_layout)
        self.setCentralWidget(self.central_widget)

        self.selected_label = None
        self.lsfData = None

        self.bi_key = 1
        self.fd_key = {}
        self.fe_key = {}
        self.hl_key = 0
        self.image_counter = 1

    def open_directory_dialog(self):
        self.directory = QFileDialog.getExistingDirectory(self, "选择文件夹")
        self.display_cv2_image()
        self.clear_bottom_bar_components()
        if self.directory:
            self.update_sidebar(self.directory)

    def update_sidebar(self, folder_path):
        self.selected_label = None
        for i in reversed(range(self.sidebar_layout.count())):
            widget = self.sidebar_layout.itemAt(i).widget()
            if widget is not None:
                widget.deleteLater()

        for filename in os.listdir(folder_path):
            if filename.endswith('.lsf'):
                label = QLabel(os.path.splitext(filename)[0])
                label.setAlignment(Qt.AlignLeft)
                label.setFixedHeight(30)
                label.setStyleSheet("border: 1px solid #D3D3D3;")
                label.mousePressEvent = lambda event, lbl=label: self.on_label_clicked(lbl)
                self.sidebar_layout.addWidget(label)

        self.sidebar_layout.setAlignment(Qt.AlignTop)
        self.sidebar_layout.setSpacing(5)

    def on_label_clicked(self, label):
        if self.selected_label:
            self.selected_label.setStyleSheet("border: 1px solid #D3D3D3;")
        label.setStyleSheet("border: 2px solid #4CAF50; background-color: #E0F7FA;")  # 选中颜色
        self.selected_label = label
        file_path = os.path.join(self.directory, label.text() + '.lsf')
        self.lsfData = LSFFile(file_path)
        self.bi_key = self.lsfData.get_base_images_keys()[0]
        image = self.synthesis_image()
        self.display_cv2_image(image)

        self.clear_bottom_bar_components()  # 清空底边栏子构件

        operator_blocks = self.lsfData.base_images[self.bi_key]
        image_bi = synthesis(self.lsfData.x, self.lsfData.y, operator_blocks, self.directory)
        data_list = self.lsfData.get_base_images_keys()
        index = 0
        self.add_bottom_bar_component("图片", image_bi, data_list, index)

        for fd_key in self.lsfData.get_face_differences_keys():
            data_list = self.lsfData.get_face_differences_keys()[fd_key]
            index = 0
            fd_image_path = os.path.join(self.directory,
                                         self.lsfData.face_differences[fd_key][data_list[index]].name + '.png')
            fd_image = cv2.imread(fd_image_path, cv2.IMREAD_UNCHANGED)
            self.add_bottom_bar_component(f"人脸{fd_key}", fd_image, data_list, index, fd_key)

        for fe_key in self.lsfData.get_face_effects_keys():
            data_list = self.lsfData.get_face_effects_keys()[fe_key]
            data_list.insert(0, 0)
            index = 0
            fe_image = np.zeros((100, 100, 4))
            self.add_bottom_bar_component(f"特效{fe_key}", fe_image, data_list, index, fe_key)

        data_list = self.lsfData.get_holy_light_keys()
        if len(data_list) == 0:
            return
        data_list.insert(0, 0)
        index = 0
        hl_image = np.zeros((100, 100, 4))
        self.add_bottom_bar_component("圣光", hl_image, data_list, index, 0)

    def extract_image(self):
        image = self.synthesis_image()
        if image is None:
            QMessageBox.warning(self, "警告", "合成图片为空，无法提取。")
        else:
            default_file_name = f"synthesized_image_{self.image_counter}.png"
            file_path, _ = QFileDialog.getSaveFileName(self, "保存图片", default_file_name,
                                                       "PNG Files (*.png);;All Files (*)")
            if file_path:
                while os.path.exists(file_path):
                    self.image_counter += 1
                    default_file_name = f"synthesized_image_{self.image_counter}.png"
                    file_path, _ = QFileDialog.getSaveFileName(self, "保存图片", default_file_name,
                                                               "PNG Files (*.png);;All Files (*)")
                    if not file_path:
                        return  # 用户取消保存
                cv2.imwrite(file_path, image)
                QMessageBox.information(self, "成功", f"图片已保存到 {file_path}")
                self.image_counter += 1  # 保存成功后增加计数器

    def display_cv2_image(self, cv2_image=None):
        if cv2_image is not None:
            if cv2_image.shape[2] == 4:  # 检查是否为4通道图
                height, width, channel = cv2_image.shape
                bytes_per_line = 4 * width
                q_image = QImage(cv2_image.data, width, height, bytes_per_line, QImage.Format_ARGB32)
            else:
                height, width, channel = cv2_image.shape
                bytes_per_line = 3 * width
                q_image = QImage(cv2_image.data, width, height, bytes_per_line, QImage.Format_RGB888).rgbSwapped()
            pixmap = QPixmap.fromImage(q_image)
            self.image_label.setPixmap(pixmap)
        else:
            self.image_label.clear()

    def synthesis_image(self):
        if self.lsfData is not None:
            operation_blocks = self.lsfData.get_operation_blocks(self.bi_key, self.fd_key, self.fe_key, self.hl_key)

            return synthesis(self.lsfData.x, self.lsfData.y, operation_blocks, self.directory)

    def add_bottom_bar_component(self, type_str, cv2_image, data_list, index, sid=0):
        component = BottomBarComponent(type_str, cv2_image, data_list, index, sid)
        component.index_changed.connect(self.handle_index_change)  # 连接信号到槽函数
        component.setMaximumSize(150, 150)
        component.setMinimumSize(150, 150)
        self.bottom_bar_layout.addWidget(component)
        self.bottom_bar_layout.setAlignment(Qt.AlignLeft)  # 子控件靠左分布

    def clear_bottom_bar_components(self):
        for i in reversed(range(self.bottom_bar_layout.count())):
            widget = self.bottom_bar_layout.itemAt(i).widget()
            if widget is not None:
                widget.deleteLater()

    def handle_index_change(self, widget):
        if widget.type == "图片":
            self.bi_key = widget.data_list[widget.index]
            operator_blocks = self.lsfData.base_images[self.bi_key]
            image_bi = synthesis(self.lsfData.x, self.lsfData.y, operator_blocks, self.directory)
            widget.reset_image(image_bi)
        elif widget.type.startswith("人脸"):
            fd_key = widget.data_list[widget.index]
            fd_image_path = os.path.join(self.directory,
                                         self.lsfData.face_differences[widget.sid][fd_key].name + '.png')
            fd_image = cv2.imread(fd_image_path, cv2.IMREAD_UNCHANGED)
            widget.reset_image(fd_image)
            self.fd_key[widget.sid] = fd_key
        elif widget.type.startswith("特效"):
            fe_key = widget.data_list[widget.index]
            if fe_key != 0:
                fe_image_path = os.path.join(self.directory,
                                             self.lsfData.face_effects[widget.sid][fe_key].name + '.png')
                fe_image = cv2.imread(fe_image_path, cv2.IMREAD_UNCHANGED)
            else:
                fe_image = np.zeros((100, 100, 4))
            widget.reset_image(fe_image)
            self.fe_key[widget.sid] = fe_key
        elif widget.type == "圣光":
            hl_key = widget.data_list[widget.index]
            if hl_key != 0:
                hl_image_path = os.path.join(self.directory, self.lsfData.holy_light[hl_key].name + '.png')
                hl_image = cv2.imread(hl_image_path, cv2.IMREAD_UNCHANGED)
            else:
                hl_image = np.zeros((100, 100, 4))
            widget.reset_image(hl_image)
            self.hl_key = hl_key

        image = self.synthesis_image()
        self.display_cv2_image(image)

    def show_help_document(self):
        try:
            with open('static/help_document.txt', 'r', encoding='utf-8') as file:
                help_text = file.read()
            dialog = QMessageBox(self)
            dialog.setWindowTitle("操作说明")
            dialog.setText(help_text)
            dialog.setStandardButtons(QMessageBox.Ok)
            dialog.setIcon(QMessageBox.Information)

            dialog.setFixedSize(600, 400)

            text_edit = QTextEdit()
            text_edit.setReadOnly(True)
            text_edit.setLineWrapMode(QTextEdit.WidgetWidth)
            text_edit.setPlainText(help_text)

            layout = dialog.layout()
            layout.addWidget(text_edit, 0, 0, 1, dialog.layout().columnCount())

            dialog.exec_()
        except FileNotFoundError:
            QMessageBox.warning(self, "警告", "操作说明文档未找到。")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"读取操作说明文档时发生错误: {str(e)}")



