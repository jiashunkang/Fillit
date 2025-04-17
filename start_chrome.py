import subprocess
import time
import signal
import sys

# 配置Chrome路径（根据实际路径修改）
chrome_path = "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe"

def start_chrome():
    """启动Chrome并返回进程对象"""
    process = subprocess.Popen(
        [
            chrome_path,
            '--remote-debugging-port=9222',
            '--new-window'  # 确保在新窗口打开
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        creationflags=subprocess.CREATE_NEW_PROCESS_GROUP  # Windows需要这个flag才能正确发送信号
    )
    return process

def stop_chrome(process):
    """关闭Chrome进程"""
    try:
        # Windows使用CTRL_BREAK_EVENT信号
        process.send_signal(signal.CTRL_BREAK_EVENT)
        process.wait(timeout=5)  # 等待5秒让进程退出
    except subprocess.TimeoutExpired:
        process.kill()  # 强制终止
    except Exception as e:
        print(f"关闭Chrome时出错: {e}")

if __name__ == "__main__":
    print("正在启动Chrome...")
    chrome_process = start_chrome()
    
    try:
        # 模拟程序运行（实际使用时替换为你的业务逻辑）
        while True:
            cmd = input("输入 'exit' 退出: ")
            if cmd.lower() == 'exit':
                break
            time.sleep(1)
    finally:
        print("正在关闭Chrome...")
        stop_chrome(chrome_process)