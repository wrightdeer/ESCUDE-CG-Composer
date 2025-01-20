import os
import sys

import cv2
import numpy as np
from PyQt5.QtCore import Qt, QSize, pyqtSignal
from PyQt5.QtGui import QPixmap, QImage, QIcon
from PyQt5.QtWidgets import QApplication, QMainWindow, QAction, QVBoxLayout, QHBoxLayout, QWidget, QLabel, QScrollArea, \
    QFileDialog, QSizePolicy, QPushButton, QMessageBox, QTextEdit  # 添加 QMessageBox 导入

from lsfInfo import LSFFile
from synthesis_util import synthesis


class BottomBarComponent(QWidget):
    index_changed = pyqtSignal(object)  # 修改信号定义，传递type, sid, index 和自身引用

    def __init__(self, type_str, cv2_image, data_list, index, sid=0):
        super().__init__()
        self.type = type_str
        self.sid = sid
        self.data_list = data_list
        self.index = index  # 添加 index 属性

        layout = QVBoxLayout()
        layout.setContentsMargins(5, 5, 5, 5)  # 调整外边距
        layout.setSpacing(0)  # 调整间距

        # 上方文本
        text_label = QLabel(type_str)
        text_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(text_label)

        # 中间图片
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
            scaled_pixmap = pixmap.scaledToHeight(100, Qt.SmoothTransformation)  # 假设最大高度为100
            self.image_label = QLabel()
            self.image_label.setPixmap(scaled_pixmap)
            self.image_label.setAlignment(Qt.AlignCenter)
            self.image_label.setMargin(0)
            layout.addWidget(self.image_label)

        # 创建一个新的水平布局容器
        bottom_layout = QHBoxLayout()

        # 左右图标按键
        left_button = QPushButton()
        left_button.setIcon(QIcon("static/BxLeftArrow.svg"))  # 假设左图标路径
        left_button.setIconSize(QSize(20, 20))  # 设置固定大小，使其保持正方形
        left_button.setFlat(True)  # 使按钮无边框
        left_button.setStyleSheet("background-color: transparent;")  # 使按钮无背景
        left_button.clicked.connect(self.decrement_index)  # 添加点击事件处理函数
        bottom_layout.addWidget(left_button)

        # 下方文本
        self.bottom_text_label = QLabel(f"{self.index + 1}/{len(self.data_list)}")  # 将 bottom_text_label 设置为实例变量
        self.bottom_text_label.setAlignment(Qt.AlignCenter)
        bottom_layout.addWidget(self.bottom_text_label)

        right_button = QPushButton()
        right_button.setIcon(QIcon("static/BxRightArrow.svg"))  # 假设右图标路径
        right_button.setIconSize(QSize(20, 20))  # 设置固定大小，使其保持正方形
        right_button.setFlat(True)  # 使按钮无边框
        right_button.setStyleSheet("background-color: transparent;")  # 使按钮无背景
        right_button.clicked.connect(self.increment_index)  # 添加点击事件处理函数
        bottom_layout.addWidget(right_button)

        # 将底部布局添加到主布局中
        layout.addLayout(bottom_layout)

        self.setLayout(layout)
        self.setStyleSheet("border: 1px solid #808080; padding: 5px;")  # 添加淡灰色细边框和内边距
        # 淡灰背景色
        # self.setStyleSheet("background-color: #000000;")
        size_policy = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)  # 设置高度策略
        self.setSizePolicy(size_policy)

    def decrement_index(self):
        self.index -= 1
        self.index %= len(self.data_list)
        self.bottom_text_label.setText(f"{self.index + 1}/{len(self.data_list)}")
        self.index_changed.emit(self)  # 发射信号，传递自身引用

    def increment_index(self):
        self.index += 1
        self.index %= len(self.data_list)
        self.bottom_text_label.setText(f"{self.index + 1}/{len(self.data_list)}")
        self.index_changed.emit(self)  # 发射信号，传递自身引用

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
            scaled_pixmap = pixmap.scaledToHeight(100, Qt.SmoothTransformation)  # 假设最大高度为100
            self.image_label.setPixmap(scaled_pixmap)


class SynthesisGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.directory = None
        self.main_layout = None
        self.sidebar_layout = QVBoxLayout()  # 初始化侧边栏布局
        self.sidebar_widget = QWidget()
        self.sidebar_widget.setLayout(self.sidebar_layout)  # 设置 sidebar_widget 的布局为 self.sidebar_layout
        self.setWindowTitle('ESCUDE-CG-Composer')
        self.setGeometry(100, 100, 800, 600)

        # 创建菜单栏
        self.menubar = self.menuBar()
        file_menu = self.menubar.addMenu('导入目录')
        extract_menu = self.menubar.addMenu('提取')  # 添加提取菜单
        help_menu = self.menubar.addMenu('帮助')
        exit_menu = self.menubar.addMenu('退出')

        # 添加菜单项
        exit_action = QAction('退出', self)
        exit_action.triggered.connect(self.close)
        exit_menu.addAction(exit_action)

        # 添加导入目录菜单项
        import_action = QAction('导入目录', self)
        import_action.triggered.connect(self.open_directory_dialog)
        file_menu.addAction(import_action)

        # 添加提取菜单项
        extract_action = QAction('提取图片', self)
        extract_action.triggered.connect(self.extract_image)  # 连接到 extract_image 方法
        extract_menu.addAction(extract_action)

        # 添加帮助菜单项
        help_action = QAction('操作说明', self)
        help_action.triggered.connect(self.show_help_document)
        help_menu.addAction(help_action)

        # 创建主布局
        self.main_layout = QVBoxLayout()

        # 创建侧边栏
        self.sidebar = QScrollArea()
        self.sidebar.setFixedWidth(200)
        self.sidebar.setWidgetResizable(True)
        self.sidebar_layout.setSpacing(5)  # 设置上下构件之间的间距
        self.sidebar_layout.setContentsMargins(5, 5, 5, 5)  # 设置侧边栏外边距
        self.sidebar.setWidget(self.sidebar_widget)

        # 创建图片展示区域
        self.image_display = QScrollArea()
        self.image_display.setWidgetResizable(True)
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.display_cv2_image()  # 调用新方法显示图片
        self.image_display.setWidget(self.image_label)

        # 创建顶部布局（侧边栏和图片展示区域）

        self.top_layout = QHBoxLayout()
        self.top_layout.addWidget(self.sidebar)
        self.top_layout.addWidget(self.image_display)

        # 创建底部栏
        self.bottom_bar = QScrollArea()
        self.bottom_bar.setFixedHeight(200)
        self.bottom_bar.setWidgetResizable(True)
        bottom_bar_widget = QWidget()
        self.bottom_bar_layout = QHBoxLayout(bottom_bar_widget)
        self.bottom_bar_layout.setContentsMargins(5, 5, 5, 5)  # 调整外边距
        self.bottom_bar_layout.setSpacing(5)  # 调整间距
        self.bottom_bar.setWidget(bottom_bar_widget)

        # 将顶部布局和底部栏添加到主布局
        self.main_layout.addLayout(self.top_layout)
        self.main_layout.addWidget(self.bottom_bar)

        # 设置主窗口的中心部件
        self.central_widget = QWidget()
        self.central_widget.setLayout(self.main_layout)
        self.setCentralWidget(self.central_widget)

        self.selected_label = None  # 添加变量来跟踪当前选中的子构件
        self.lsfData = None

        self.bi_key = 1
        self.fd_key = {}
        self.fe_key = {}
        self.hl_key = 0
        self.image_counter = 1  # 添加图片计数器

    def open_directory_dialog(self):
        # 打开文件夹选择对话框
        self.directory = QFileDialog.getExistingDirectory(self, "选择文件夹")
        self.display_cv2_image()
        self.clear_bottom_bar_components()
        if self.directory:
            print(f"选择的文件夹路径: {self.directory}")
            self.update_sidebar(self.directory)  # 调用更新侧边栏的方法

    def update_sidebar(self, folder_path):
        self.selected_label = None
        print(f"count:{self.sidebar_layout.count()}")
        # 清空侧边栏
        for i in reversed(range(self.sidebar_layout.count())):
            widget = self.sidebar_layout.itemAt(i).widget()
            if widget is not None:
                widget.deleteLater()

        # 遍历目录，获取所有的lsf文件
        for filename in os.listdir(folder_path):
            if filename.endswith('.lsf'):
                label = QLabel(os.path.splitext(filename)[0])  # 创建子构件，展示文件名（不包括扩展名）
                label.setAlignment(Qt.AlignLeft)  # 设置子构件文字靠左布局
                label.setFixedHeight(30)  # 设置子构件高度
                label.setStyleSheet("border: 1px solid #D3D3D3;")  # 添加淡灰色边框
                label.mousePressEvent = lambda event, lbl=label: self.on_label_clicked(lbl)  # 添加点击事件处理
                self.sidebar_layout.addWidget(label)
                print(f"添加了子构件：{os.path.splitext(filename)[0]}")

        # 设置侧边栏布局的对齐方式为顶部对齐，并设置间距
        self.sidebar_layout.setAlignment(Qt.AlignTop)
        self.sidebar_layout.setSpacing(5)  # 设置子构件之间的间距

    def on_label_clicked(self, label):
        # 如果之前有选中的子构件，恢复其背景颜色
        if self.selected_label:
            self.selected_label.setStyleSheet("border: 1px solid #D3D3D3;")
        # 设置当前子构件为选中状态，并改变其背景颜色
        label.setStyleSheet("border: 2px solid #4CAF50; background-color: #E0F7FA;")  # 选中颜色
        self.selected_label = label
        file_path = os.path.join(self.directory, label.text() + '.lsf')
        self.lsfData = LSFFile(file_path)
        self.bi_key = self.lsfData.get_base_images_keys()[0]
        # print(f"点击了子构件：{file_path}")
        # image_name = self.lsfData.base_images[1][0].name
        # image_path = os.path.join(self.directory, image_name + '.png')
        # image = cv2.imread(image_path)
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
            fd_image_path =  os.path.join(self.directory, self.lsfData.face_differences[fd_key][data_list[index]].name + '.png')
            fd_image = cv2.imread(fd_image_path, cv2.IMREAD_UNCHANGED)
            self.add_bottom_bar_component(f"人脸{fd_key}",fd_image, data_list, index,fd_key)

        for fe_key in self.lsfData.get_face_effects_keys():
            data_list = self.lsfData.get_face_effects_keys()[fe_key]
            data_list.insert(0,0)
            index = 0
            fe_image = np.zeros((100,100,4))
            self.add_bottom_bar_component(f"特效{fe_key}",fe_image, data_list, index,fe_key)

        data_list = self.lsfData.get_holy_light_keys()
        if len(data_list) == 0:
            return
        data_list.insert(0,0)
        index = 0
        hl_image = np.zeros((100,100,4))
        self.add_bottom_bar_component("圣光",hl_image, data_list, index,0)

    def extract_image(self):
        image = self.synthesis_image()
        if image is None:
            QMessageBox.warning(self, "警告", "合成图片为空，无法提取。")
        else:
            # 生成默认文件名
            default_file_name = f"synthesized_image_{self.image_counter}.png"
            file_path, _ = QFileDialog.getSaveFileName(self, "保存图片", default_file_name, "PNG Files (*.png);;All Files (*)")
            if file_path:
                # 检查文件名是否重复
                while os.path.exists(file_path):
                    self.image_counter += 1
                    default_file_name = f"synthesized_image_{self.image_counter}.png"
                    file_path, _ = QFileDialog.getSaveFileName(self, "保存图片", default_file_name, "PNG Files (*.png);;All Files (*)")
                    if not file_path:
                        return # 用户取消保存
                cv2.imwrite(file_path, image)
                QMessageBox.information(self, "成功", f"图片已保存到 {file_path}")
                self.image_counter += 1  # 保存成功后增加计数器

    def display_cv2_image(self, cv2_image=None):
        if cv2_image is not None:
            # 将cv2图片转换为QPixmap
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
            # 如果传入的图片为空，清除图片
            self.image_label.clear()

    def synthesis_image(self):
        if self.lsfData is not None:
            operation_blocks = self.lsfData.get_operation_blocks(self.bi_key, self.fd_key, self.fe_key, self.hl_key)

            return synthesis(self.lsfData.x, self.lsfData.y, operation_blocks, self.directory)

    def add_bottom_bar_component(self, type_str, cv2_image, data_list, index, sid=0):
        component = BottomBarComponent(type_str, cv2_image, data_list, index, sid)
        component.index_changed.connect(self.handle_index_change)  # 连接信号到槽函数
        # 控制子控件的高度，不超出底边栏范围
        component.setMaximumSize(150,150)
        component.setMinimumSize(150,150)
        self.bottom_bar_layout.addWidget(component)
        self.bottom_bar_layout.setAlignment(Qt.AlignLeft)  # 子控件靠左分布

    def clear_bottom_bar_components(self):
        # 清空底边栏子构件
        for i in reversed(range(self.bottom_bar_layout.count())):
            widget = self.bottom_bar_layout.itemAt(i).widget()
            if widget is not None:
                widget.deleteLater()

    def handle_index_change(self, widget):
        print(f"Component ID: {widget.sid}, Type: {widget.type}, Index: {widget.index}")
        if widget.type == "图片":
            self.bi_key = widget.data_list[widget.index]
            operator_blocks = self.lsfData.base_images[self.bi_key]
            image_bi = synthesis(self.lsfData.x, self.lsfData.y, operator_blocks, self.directory)
            widget.reset_image(image_bi)
        elif widget.type.startswith("人脸"):
            fd_key = widget.data_list[widget.index]
            fd_image_path = os.path.join(self.directory, self.lsfData.face_differences[widget.sid][fd_key].name + '.png')
            fd_image = cv2.imread(fd_image_path, cv2.IMREAD_UNCHANGED)
            widget.reset_image(fd_image)
            self.fd_key[widget.sid] = fd_key
        elif widget.type.startswith("特效"):
            fe_key = widget.data_list[widget.index]
            if fe_key != 0:
                fe_image_path = os.path.join(self.directory, self.lsfData.face_effects[widget.sid][fe_key].name + '.png')
                fe_image = cv2.imread(fe_image_path, cv2.IMREAD_UNCHANGED)
            else:
                fe_image = np.zeros((100,100,4))
            widget.reset_image(fe_image)
            self.fe_key[widget.sid] = fe_key
        elif widget.type == "圣光":
            hl_key = widget.data_list[widget.index]
            if hl_key != 0:
                hl_image_path = os.path.join(self.directory, self.lsfData.holy_light[hl_key].name + '.png')
                hl_image = cv2.imread(hl_image_path, cv2.IMREAD_UNCHANGED)
            else:
                hl_image = np.zeros((100,100,4))
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
            
            # 设置固定宽度和高度
            dialog.setFixedSize(600, 400)
            
            # 使用 QTextEdit 来支持滚动条和自动换行
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


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = SynthesisGUI()
    ex.show()
    sys.exit(app.exec_())
