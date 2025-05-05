import sys
import subprocess
import signal
from PyQt6.QtWidgets import QApplication, QWidget, QPushButton, QVBoxLayout, QMessageBox

# 配置Chrome路径（根据实际路径修改）
chrome_path = "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe"
chrome_process = None  # 用于存储Chrome进程对象

def start_chrome():
    global chrome_process
    if chrome_process is None:
        try:
            chrome_process = subprocess.Popen(
                [
                    chrome_path,
                    '--remote-debugging-port=9222',
                    '--new-window'
                ],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
            )
            print("Chrome started.")
        except Exception as e:
            print(f"启动Chrome失败: {e}")
    else:
        print("Chrome 已经在运行。")


def stop_chrome():
    global chrome_process
    if chrome_process is not None:
        try:
            chrome_process.send_signal(signal.CTRL_BREAK_EVENT)
            chrome_process.wait(timeout=5)
            print("Chrome 已关闭。")
        except subprocess.TimeoutExpired:
            chrome_process.kill()
            print("Chrome 强制关闭。")
        except Exception as e:
            print(f"关闭Chrome时出错: {e}")
        finally:
            chrome_process = None
    else:
        print("没有可关闭的Chrome进程。")


class ChromeControlApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Chrome 控制器")
        self.setGeometry(300, 300, 300, 100)
        layout = QVBoxLayout()

        self.start_button = QPushButton("Start Chrome")
        self.start_button.clicked.connect(start_chrome)

        self.stop_button = QPushButton("Stop Chrome")
        self.stop_button.clicked.connect(stop_chrome)

        layout.addWidget(self.start_button)
        layout.addWidget(self.stop_button)

        self.setLayout(layout)

    def closeEvent(self, event):
        if chrome_process is not None:
            stop_chrome()
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ChromeControlApp()
    window.show()
    sys.exit(app.exec())
