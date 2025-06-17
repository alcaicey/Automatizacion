# Minimal stub for pyautogui used in tests
import logging

def hotkey(*args, **kwargs):
    logging.info("pyautogui.hotkey called with %s", args)

def press(key):
    logging.info("pyautogui.press called with %s", key)
