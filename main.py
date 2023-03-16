import os
import cv2
import nuke
from PySide2.QtWidgets import (QApplication, QWidget, QVBoxLayout, QGridLayout, QLabel, QPushButton,
                               QFileDialog, QScrollArea, QFrame, QCheckBox, QHBoxLayout)
from PySide2.QtGui import QImage, QPixmap
from PySide2.QtCore import Qt, QTimer, QSize


class VideoPreview(QWidget):
    def __init__(self):
        super(VideoPreview, self).__init__()

        self.setWindowTitle('MOV Previews and Import')
        self.setGeometry(100, 100, 800, 450)

        self.layout = QVBoxLayout()
        self.scroll_area = QScrollArea()
        self.scroll_widget = QFrame()
        self.grid_layout = QGridLayout()
        self.open_button = QPushButton('Open MOV')
        self.import_button = QPushButton('Import Selected into Nuke')

        self.scroll_widget.setLayout(self.grid_layout)
        self.scroll_area.setWidget(self.scroll_widget)
        self.scroll_area.setWidgetResizable(True)

        self.layout.addWidget(self.scroll_area)
        self.layout.addWidget(self.open_button)
        self.layout.addWidget(self.import_button)

        self.setLayout(self.layout)

        self.open_button.clicked.connect(self.open_mov)
        self.import_button.clicked.connect(self.import_mov)

        self.timer = QTimer()
        self.timer.timeout.connect(self.playback)

        self.videos = {}

    def open_mov(self):
        file_paths, _ = QFileDialog.getOpenFileNames(self, 'Open MOV', '', 'MOV Files (*.mov)')
        for idx, file_path in enumerate(file_paths):
            title = os.path.basename(file_path)
            checkbox = QCheckBox(title)
            capture = cv2.VideoCapture(file_path)
            play_button = QPushButton('Play')
            stop_button = QPushButton('Stop')
            hbox = QHBoxLayout()

            # Thay đổi kích thước của nút
            play_button.setFixedSize(QSize(60, 25))
            stop_button.setFixedSize(QSize(60, 25))

            hbox.addWidget(play_button)
            hbox.addWidget(stop_button)

            self.videos[idx] = {
                'path': file_path,
                'capture': capture,
                'label': QLabel(),
                'checkbox': checkbox,
                'first_frame': int(capture.get(cv2.CAP_PROP_POS_FRAMES)),
                'last_frame': int(capture.get(cv2.CAP_PROP_FRAME_COUNT)) - 1,
                'play_button': play_button,
                'stop_button': stop_button
            }

            self.grid_layout.addWidget(checkbox, idx, 0)
            self.grid_layout.addWidget(self.videos[idx]['label'], idx, 1)
            self.grid_layout.addLayout(hbox, idx, 2)

            play_button.clicked.connect(self.create_play_callback(idx))
            stop_button.clicked.connect(self.create_stop_callback(idx))

            # Hiển thị frame đầu tiên của mỗi video
            self.videos[idx]['playing'] = True
            self.playback()
            self.videos[idx]['playing'] = False

    def create_play_callback(self, idx):
        def play_callback():
            if not self.timer.isActive():
                self.timer.start(1000 / 30)
            self.videos[idx]['playing'] = True

        return play_callback

    def create_stop_callback(self, idx):
        def stop_callback():
            self.videos[idx]['playing'] = False

        return stop_callback

    def playback(self):
        for idx, video in self.videos.items():
            if not video.get('playing'):
                continue
            capture = video['capture']
            ret, frame = capture.read()
            if not ret:
                capture.set(cv2.CAP_PROP_POS_FRAMES, 0)
                continue

            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frame = cv2.resize(frame, (200, 150))
            h, w, c = frame.shape
            qimg = QImage(frame.data, w, h, c * w, QImage.Format_RGB888)
            pixmap = QPixmap.fromImage(qimg)
            video['label'].setPixmap(pixmap.scaled(200, 150, Qt.KeepAspectRatio))

    def import_mov(self):
        for idx, video in self.videos.items():
            if video['checkbox'].isChecked():
                file_path = video['path']
                read_node = nuke.createNode('Read')
                read_node['file'].setValue(file_path)
                read_node['first'].setValue(video['first_frame'])
                read_node['last'].setValue(video['last_frame'])
app = QApplication.instance()
if not app:
    app = QApplication([])

video_preview = VideoPreview()
video_preview.show()

app.exec_()


