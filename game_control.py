import os
import time
import ctypes
import pydirectinput
import win32api
import win32con
import pygetwindow as gw

user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32

ROBLOX_LINK = "roblox://experiences/start?placeId=1537690962"
LOAD_COLOR = 0x00A85722  # #2257a8 in COLORREF (BGR) format
LOAD_PIXEL = (800, 800)

_log_callback = None

def set_log_callback(callback):
    global _log_callback
    _log_callback = callback

def _log(msg):
    if _log_callback:
        _log_callback(msg)
    else:
        print(msg)

gdi32 = ctypes.windll.gdi32

def _get_pixel_color(x, y):
    hdc = user32.GetDC(0)
    color = gdi32.GetPixel(hdc, x, y)
    user32.ReleaseDC(0, hdc)
    return color

def join_game():
    _log("launching game...")
    os.startfile(ROBLOX_LINK)
    _log("waiting for loading screen...")
    while _get_pixel_color(*LOAD_PIXEL) != LOAD_COLOR:
        time.sleep(0.5)
    _log("loading screen detected. waiting for game to load...")
    while _get_pixel_color(*LOAD_PIXEL) == LOAD_COLOR:
        time.sleep(0.5)
    _log("game loaded.")

def _attach_thread_input(hwnd):
    try:
        foreground_tid = user32.GetWindowThreadProcessId(hwnd, None)
        current_tid = kernel32.GetCurrentThreadId()
        if foreground_tid != current_tid:
            user32.AttachThreadInput(current_tid, foreground_tid, True)
    except Exception as e:
        _log(f"Note: AttachThreadInput failed (ignoring): {e}")

def activate_roblox_window():
    try:
        rblx_window = gw.getWindowsWithTitle("Roblox")[0]
        if not rblx_window.isActive:
            try:
                rblx_window.activate()
            except Exception as e:
                _log(f"Note: Error during window activation (ignoring): {e}")
            time.sleep(1)
            _log("roblox window focused.")
        _attach_thread_input(rblx_window._hWnd)
        return rblx_window
    except IndexError:
        _log("roblox window not found. retrying...")
        time.sleep(1)
        os.startfile(ROBLOX_LINK)
        time.sleep(15)
        try:
            rblx_window = gw.getWindowsWithTitle("Roblox")[0]
            try:
                rblx_window.activate()
            except Exception as e:
                _log(f"Note: Error during window activation (ignoring): {e}")
            time.sleep(1)
            _attach_thread_input(rblx_window._hWnd)
            return rblx_window
        except IndexError:
            _log("roblox window still not found after retry.")
            return None

def leave_game():
    _log("closing roblox")
    window = activate_roblox_window()
    if not window:
        return
    time.sleep(0.2)
    pydirectinput.keyDown('esc')
    time.sleep(0.05)
    pydirectinput.press('l')
    time.sleep(0.05)
    pydirectinput.keyUp('enter')
    _log("roblox closed")

def reset_character():
    _log("resetting character...")
    window = activate_roblox_window()
    if not window:
        return
    time.sleep(0.2)
    pydirectinput.press('esc')
    time.sleep(0.1)
    pydirectinput.press('r')
    time.sleep(0.1)
    pydirectinput.press('enter')
    time.sleep(6)

def align_camera():
    _log("aligning camera...")
    window = activate_roblox_window()
    if not window:
        return

    center_x = window.left + (window.width // 2)
    center_y = window.top + (window.height // 2)

    pydirectinput.click(center_x, center_y)
    time.sleep(0.2)

    for _ in range(4):
        pydirectinput.press('o')
        time.sleep(0.02)

    _log("dragging camera down")
    win32api.mouse_event(win32con.MOUSEEVENTF_RIGHTDOWN, 0, 0, 0, 0)
    time.sleep(0.1)

    for _ in range(20):
        win32api.mouse_event(win32con.MOUSEEVENTF_MOVE, 0, -20, 0, 0)
        time.sleep(0.01)
    win32api.mouse_event(win32con.MOUSEEVENTF_RIGHTUP, 0, 0, 0, 0)
    time.sleep(0.2)
    pydirectinput.click(center_x, center_y)

    _log("moving camera left")
    for _ in range(2):
        pydirectinput.press('.')
    _log("camera aligned")
    

def align_camera2():
    _log("aligning camera...")
    window = activate_roblox_window()
    if not window:
        return

    center_x = window.left + (window.width // 2)
    center_y = window.top + (window.height // 2)

    pydirectinput.click(center_x, center_y)
    time.sleep(0.2)

    for _ in range(4):
        pydirectinput.press('o')
        time.sleep(0.02)

    _log("dragging camera down")
    win32api.mouse_event(win32con.MOUSEEVENTF_RIGHTDOWN, 0, 0, 0, 0)
    time.sleep(0.1)

    for _ in range(20):
        win32api.mouse_event(win32con.MOUSEEVENTF_MOVE, 0, -20, 0, 0)
        time.sleep(0.01)
    win32api.mouse_event(win32con.MOUSEEVENTF_RIGHTUP, 0, 0, 0, 0)
    time.sleep(0.2)
    pydirectinput.click(center_x, center_y)
    _log("dragging camera down (again)")
    win32api.mouse_event(win32con.MOUSEEVENTF_RIGHTDOWN, 0, 0, 0, 0)
    time.sleep(0.1)

    for _ in range(20):
        win32api.mouse_event(win32con.MOUSEEVENTF_MOVE, 0, -20, 0, 0)
        time.sleep(0.01)
    win32api.mouse_event(win32con.MOUSEEVENTF_RIGHTUP, 0, 0, 0, 0)
    time.sleep(0.2)

    _log("moving camera left")
    for _ in range(2):
        pydirectinput.press('.')
    _log("camera aligned")
    