import subprocess
import time
import signal
import sys
import os

# 获取当前项目路径并创建 ChromeUserData 文件夹
base_dir = os.path.abspath(os.path.dirname(__file__))
user_data_dir = os.path.join(base_dir, "ChromeUserData")
os.makedirs(user_data_dir, exist_ok=True)

# 配置 Chrome 路径（确保正确）
chrome_path = r"C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe"

def start_chrome():
    """启动 Chrome 并返回进程对象"""
    process = subprocess.Popen(
        [
            chrome_path,
            f'--remote-debugging-port=9222',
            f'--user-data-dir={user_data_dir}',
            '--new-window'
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        creationflags=subprocess.CREATE_NEW_PROCESS_GROUP  # Windows 专用
    )
    return process

def stop_chrome(process):
    """关闭 Chrome 进程"""
    try:
        process.send_signal(signal.CTRL_BREAK_EVENT)
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()
    except Exception as e:
        print(f"关闭 Chrome 时出错: {e}")

if __name__ == "__main__":
    print(f"正在启动 Chrome，用户数据目录：{user_data_dir}")
    chrome_process = start_chrome()

    try:
        while True:
            cmd = input("输入 'exit' 退出: ")
            if cmd.lower() == 'exit':
                break
            time.sleep(1)
    finally:
        print("正在关闭 Chrome...")
        stop_chrome(chrome_process)
