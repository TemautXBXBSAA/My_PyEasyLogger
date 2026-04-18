import cv2
import numpy as np
import threading
from typing import Callable, Optional
import ctypes
import time
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Cv2Window:
    """
    A thread-safe OpenCV window display class.
    Supports multi-threaded image updates, custom mouse/keyboard event handling, 
    automatic scaling, and centered display.
    """
    def __init__(self, pic: np.ndarray, name: str, fps: int = 24, auto_scale: float = 0.8):
        """
        Initialize Cv2Window.
        
        :param pic: Initial image to display (numpy array).
        :param name: Window name.
        :param fps: Refresh frame rate.
        :param auto_scale: Maximum ratio of screen occupied by the window (0.0 - 1.0). 
                           If 0, automatic scaling is disabled.
        """
        self._pic = pic.copy()
        self.name = name
        self.fps = max(1, fps)
        self.auto_scale = max(0, min(1.0, auto_scale))
        
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._pic_lock = threading.Lock()
        self._close_event = threading.Event()
        
        self._mouse_actions = {
            cv2.EVENT_LBUTTONUP: self._on_l_up,
            cv2.EVENT_LBUTTONDOWN: self._on_l_down,
            cv2.EVENT_RBUTTONUP: self._on_r_up,
            cv2.EVENT_RBUTTONDOWN: self._on_r_down,
            cv2.EVENT_MBUTTONDOWN: self._on_m_down,
            cv2.EVENT_MBUTTONUP: self._on_m_up,
            cv2.EVENT_MOUSEWHEEL: self._on_scroll,
            cv2.EVENT_LBUTTONDBLCLK: self._on_double_l_click,
            cv2.EVENT_RBUTTONDBLCLK: self._on_double_r_click,
            cv2.EVENT_MOUSEMOVE: self._on_drag,
        }
        
        self._board_event_handler: Callable[[int], None] = self._default_board_event

    def show(self):
        """
        Start window display in a background thread. Ignored if already running.
        """
        if self._running:
            logger.warning(f"Window '{self.name}' is already running.")
            return

        self._close_event.clear()
        self._running = True
        self._thread = threading.Thread(target=self._display_loop, daemon=False, name=f"Cv2Window-{self.name}")
        self._thread.start()
        logger.info(f"Window '{self.name}' started.")

    def close(self):
        """
        Close the window and stop the background thread.
        """
        if not self._running:
            return
            
        self._running = False
        self._close_event.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2.0)
            if self._thread.is_alive():
                logger.warning(f"Thread for window '{self.name}' did not terminate gracefully.")
        try:
            cv2.destroyWindow(self.name)
        except cv2.error as e:
            if e.code != -27:
                logger.error(f"Error destroying window: {e}")

        
        self._thread = None
        logger.info(f"Window '{self.name}' closed.")

    def update(self, pic: np.ndarray):
        """
        Thread-safely update the image displayed in the window.
        
        :param pic: New image data.
        """
        if pic is None or not isinstance(pic, np.ndarray):
            logger.warning("Invalid image provided to update().")
            return
            
        with self._pic_lock:
            self._pic = pic.copy()

    def change_mouse_event(self, event: int, function: Callable[[int, int, int, int, any], None]):
        """
        Change the callback function for a specific mouse event.
        
        :param event: OpenCV mouse event constant (e.g., cv2.EVENT_LBUTTONDOWN).
        :param function: Callback function with signature func(event, x, y, flags, param).
        """
        if event in self._mouse_actions:
            self._mouse_actions[event] = function
        else:
            logger.warning(f"Event {event} is not supported or recognized.")

    def change_board_event(self, function: Callable[[int], None]):
        """
        Set custom keyboard event handling logic.
        Note: This function is called in every loop iteration with the current key value (int).
        Do not call cv2.waitKey inside this function, as it is handled by the underlying loop.
        
        :param function: Callback function receiving the key value (int), defaults: `lambda key: logger.debug(f"Key pressed: {key}")`
        """
        self._board_event_handler = function
    def _display_loop(self):
        """
        Main loop of the background thread, responsible for creating the window, 
        handling events, and refreshing the image.
        """
        try:
            cv2.namedWindow(self.name, cv2.WINDOW_NORMAL | cv2.WINDOW_KEEPRATIO)
            cv2.setMouseCallback(self.name, self._mouse_callback)
            self._adjust_window_initial_state()
            wait_time = 1000 // self.fps
            time.sleep(0.1)
            
            while self._running and not self._close_event.is_set():
                if cv2.getWindowProperty(self.name, cv2.WND_PROP_VISIBLE) < 1:
                    break
                key = cv2.waitKey(wait_time) & 0xFF
                self._board_event_handler(key)

                # Display
                with self._pic_lock:
                    current_pic = self._pic.copy()
                
                if current_pic is not None and current_pic.size > 0:
                    cv2.imshow(self.name, current_pic)
                    
        except Exception as e:
            logger.error(f"Error in display loop for window '{self.name}': {e}", exc_info=True)
        finally:
            self.close()

    def _adjust_window_initial_state(self):
        """
        Adjust the initial size and position of the window based on screen dimensions 
        and auto_scale setting.
        """
        try:
            # Use ctypes to get screen width and height via Windows API
            user32 = ctypes.windll.user32
            screen_width = user32.GetSystemMetrics(0)  # SM_CXSCREEN
            screen_height = user32.GetSystemMetrics(1) # SM_CYSCREEN
            
            h, w = self._pic.shape[:2]
            scale_w = (screen_width * self.auto_scale) / w
            scale_h = (screen_height * self.auto_scale) / h
            scale = min(scale_w, scale_h, 1.0)

            display_w = int(w * scale) if self.auto_scale > 0 else w
            display_h = int(h * scale) if self.auto_scale > 0 else h

            pos_x = max(0, (screen_width - display_w) // 2)
            pos_y = max(0, (screen_height - display_h) // 2)
            
            cv2.resizeWindow(self.name, display_w, display_h)
            cv2.moveWindow(self.name, pos_x, pos_y)
            
        except Exception as e:
            logger.warning(f"Could not adjust window position/size automatically: {e}")

    def _mouse_callback(self, event: int, x: int, y: int, flags: int, param: any):
        """
        Unified entry point for OpenCV mouse events.
        """
        if event in self._mouse_actions:
            try:
                self._mouse_actions[event](event, x, y, flags, param)
            except Exception as e:
                logger.error(f"Error in mouse event handler for event {event}: {e}")
    def _default_board_event(self, key: int):
        """Default keyboard event handler"""
        if key == 27: # ESC
            logger.debug("ESC pressed, closing window.")
            self.close()
        elif key == 255:
            pass
        else:
            logger.debug(f"Key pressed: {key}")

    def _on_l_up(self, event, x, y, flags, param):
        logger.debug(f"Left Button Up: ({x}, {y})")

    def _on_l_down(self, event, x, y, flags, param):
        logger.debug(f"Left Button Down: ({x}, {y})")

    def _on_r_up(self, event, x, y, flags, param):
        logger.debug(f"Right Button Up: ({x}, {y})")

    def _on_r_down(self, event, x, y, flags, param):
        logger.debug(f"Right Button Down: ({x}, {y})")

    def _on_m_down(self, event, x, y, flags, param):
        logger.debug(f"Middle Button Down: ({x}, {y})")

    def _on_m_up(self, event, x, y, flags, param):
        logger.debug(f"Middle Button Up: ({x}, {y})")

    def _on_scroll(self, event, x, y, flags, param):
        direction = "Up" if flags > 0 else "Down"
        logger.debug(f"Scroll {direction}: ({x}, {y})")

    def _on_double_l_click(self, event, x, y, flags, param):
        logger.debug(f"Left Double Click: ({x}, {y})")

    def _on_double_r_click(self, event, x, y, flags, param):
        logger.debug(f"Right Double Click: ({x}, {y})")

    def _on_drag(self, event, x, y, flags, param):
        if flags & cv2.EVENT_FLAG_LBUTTON:
            logger.debug(f"Left Drag: ({x}, {y})")
        elif flags & cv2.EVENT_FLAG_RBUTTON:
            logger.debug(f"Right Drag: ({x}, {y})")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        return False


if __name__ == "__main__":
    pic = np.zeros((480, 640, 3), dtype=np.uint8)
    cv2.putText(pic, "Image 1", (50, 240), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
    pic_2 = np.zeros((480, 640, 3), dtype=np.uint8)
    cv2.putText(pic_2, "Image 2", (50, 240), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)

    def new_board_event(key):
        if key == ord(' '):
            print("Space bar pressed!")
        elif key == 27:
            print("ESC pressed via custom handler!")

    with Cv2Window(pic, "Test Window", fps=30, auto_scale=0.5) as cv2_window:
        cv2_window.change_board_event(new_board_event)
        cv2_window.show()
        for i in range(10):
            time.sleep(0.1)
            if i % 2 == 0:
                cv2_window.update(pic_2)
            else:
                cv2_window.update(pic)
    print("Application finished.")
