import customtkinter as ctk
import threading
import time
import winsound
from tkinter import messagebox
from game_control import join_game, align_camera, leave_game, reset_character, set_log_callback, align_camera2
from detector import ChimeDetector

AMBER = "#F5A623"
AMBER_HOVER = "#D4891E"
GREEN = "#4CAF50"

class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("BSS Wind Chime Detector")
        self.geometry("500x550")
        self.resizable(False, False)

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("dark-blue")

        self._stop_event = threading.Event()
        self._running = False
        self._server_count = 0
        self._calibrated_this_session = False

        set_log_callback(self._log_from_thread)
        self._detector = ChimeDetector(log_callback=self._log_from_thread)

        self._build_ui()
        self._append_log("Ready. Click Start to begin.")

    def _build_ui(self):
        self._tabview = ctk.CTkTabview(self, width=470, height=520)
        self._tabview.pack(padx=15, pady=15)

        self._tabview.add("Quick Start")
        self._tabview.add("Advanced")

        self._build_quick_start(self._tabview.tab("Quick Start"))
        self._build_advanced(self._tabview.tab("Advanced"))

    def _build_quick_start(self, parent):
        self._start_btn = ctk.CTkButton(
            parent, text="START AUTO DETECT", height=50, font=("", 16, "bold"),
            fg_color=AMBER, hover_color=AMBER_HOVER, text_color="black",
            command=self._on_start
        )
        self._start_btn.pack(pady=(10, 5), fill="x", padx=10)

        self._stop_btn = ctk.CTkButton(
            parent, text="STOP", height=40, font=("", 14),
            fg_color="#555", hover_color="#777",
            command=self._on_stop, state="disabled"
        )
        self._stop_btn.pack(pady=(0, 10), fill="x", padx=10)

        info_frame = ctk.CTkFrame(parent, fg_color="transparent")
        info_frame.pack(fill="x", padx=10, pady=(0, 5))

        self._status_label = ctk.CTkLabel(info_frame, text="Status: Idle", anchor="w")
        self._status_label.pack(fill="x")
        self._step_label = ctk.CTkLabel(info_frame, text="Step:   --", anchor="w")
        self._step_label.pack(fill="x")
        self._server_label = ctk.CTkLabel(info_frame, text="Server: #0", anchor="w")
        self._server_label.pack(fill="x")

        self._log_box = ctk.CTkTextbox(parent, height=200, state="disabled")
        self._log_box.pack(fill="both", expand=True, padx=10, pady=(5, 5))

    def _build_advanced(self, parent):
        grid = ctk.CTkFrame(parent, fg_color="transparent")
        grid.pack(fill="x", padx=10, pady=10)

        buttons = [
            ("Join Game", self._adv_join),
            ("Leave Game", self._adv_leave),
            ("Align Cam", self._adv_align),
            ("Reset Character", self._adv_reset),
            ("Calibrate", self._adv_calibrate),
            ("Detect Once", self._adv_detect),
        ]
        self._adv_buttons = []
        for i, (label, cmd) in enumerate(buttons):
            btn = ctk.CTkButton(
                grid, text=label, height=40,
                fg_color=AMBER, hover_color=AMBER_HOVER, text_color="black",
                command=cmd
            )
            btn.grid(row=i // 2, column=i % 2, padx=5, pady=5, sticky="ew")
            self._adv_buttons.append(btn)

        grid.columnconfigure(0, weight=1)
        grid.columnconfigure(1, weight=1)

        self._adv_log_box = ctk.CTkTextbox(parent, height=200, state="disabled")
        self._adv_log_box.pack(fill="both", expand=True, padx=10, pady=(5, 5))

    # --- Logging ---

    def _log_from_thread(self, msg):
        self.after(0, self._append_log, msg)

    def _append_log(self, msg):
        for box in (self._log_box, self._adv_log_box):
            box.configure(state="normal")
            box.insert("end", msg + "\n")
            box.see("end")
            box.configure(state="disabled")

    # --- Status helpers ---

    def _set_status(self, status, color=None):
        self.after(0, lambda: self._status_label.configure(
            text=f"Status: {status}",
            text_color=color or "white"
        ))

    def _set_step(self, step):
        self.after(0, lambda: self._step_label.configure(text=f"Step:   {step}"))

    def _set_server(self, n):
        self.after(0, lambda: self._server_label.configure(text=f"Server: #{n}"))

    def _set_buttons_running(self, running):
        self._running = running
        state_start = "disabled" if running else "normal"
        state_stop = "normal" if running else "disabled"
        self.after(0, lambda: self._start_btn.configure(state=state_start))
        self.after(0, lambda: self._stop_btn.configure(state=state_stop))
        for btn in self._adv_buttons:
            self.after(0, lambda b=btn: b.configure(state=state_start))

    # --- Quick Start ---

    def _on_start(self):
        self._stop_event.clear()
        self._server_count = 0
        self._set_buttons_running(True)
        self._set_status("Running", AMBER)
        threading.Thread(target=self._auto_loop, daemon=True).start()

    def _on_stop(self):
        self._stop_event.set()
        self._log_from_thread("Stop requested. Finishing current step...")
        self._set_status("Stopping...")

    def _auto_loop(self):
        try:
            while not self._stop_event.is_set():
                self._server_count += 1
                self._set_server(self._server_count)

                self._set_step("Joining game...")
                join_game()
                if self._stop_event.is_set():
                    break

                max_retries = 3
                found_movement = False

                for attempt in range(max_retries):
                    if self._stop_event.is_set():
                        break

                    self._set_step("Aligning camera...")
                    # align_camera()
                    if self._stop_event.is_set():
                        break

                    if not self._calibrated_this_session:
                        self._set_step("Calibrating...")
                        align_camera2()
                        self._log_from_thread("Camera aligned. Draw ROI around the chimes.")
                        if not self._detector.calibrate():
                            self._log_from_thread("Calibration cancelled. Stopping.")
                            self._stop_event.set()
                            break
                        self._calibrated_this_session = True
                        if self._stop_event.is_set():
                            break
                    else :
                        align_camera()

                    self._set_step("Detecting...")
                    result = self._detector.detect_movement(duration=3)

                    if result is True:
                        found_movement = True
                        break
                    elif result == "obstructed":
                        self._log_from_thread("Obstruction detected. Rejoining...")
                        break
                    elif result == "missing":
                        self._log_from_thread(
                            f"Chimes missing (Attempt {attempt+1}/{max_retries}). Resetting..."
                        )
                        if attempt < max_retries - 1:
                            self._set_step("Resetting character...")
                            reset_character()
                        else:
                            self._log_from_thread("Max retries reached for this server.")
                    else:
                        self._log_from_thread("Chimes are static.")
                        break

                if found_movement:
                    self._alert_found()
                    break

                if self._stop_event.is_set():
                    break

                self._log_from_thread("Rejoining a new server...")

        except Exception as e:
            self._log_from_thread(f"Error: {e}")
        finally:
            self._finish_auto()

    def _alert_found(self):
        self._set_status("CHIMES MOVING!", GREEN)
        self._set_step("Done!")
        self._log_from_thread("something's alive in the ocean")
        self.after(0, self._flash_window)
        try:
            winsound.MessageBeep(winsound.MB_ICONEXCLAMATION)
        except Exception:
            pass
        self.after(0, lambda: messagebox.showwarning(
            "Movement Detected",
            "Movement detected! Check the chimes.\n\n\nPlayers using the red cannon or balloons may trigger false alarms."
        ))

    def _flash_window(self):
        self.attributes("-topmost", True)
        self.after(100, lambda: self.attributes("-topmost", False))
        self.focus_force()

    def _finish_auto(self):
        if not self._stop_event.is_set():
            pass  # finished naturally (chimes found)
        else:
            self._set_status("Idle")
            self._set_step("--")
        self._set_buttons_running(False)

    # --- Advanced ---

    def _run_in_thread(self, fn, step_name):
        if self._running:
            return
        self._set_buttons_running(True)
        self._set_status("Running", AMBER)
        self._set_step(step_name)

        def wrapper():
            try:
                fn()
            except Exception as e:
                self._log_from_thread(f"Error: {e}")
            finally:
                self._set_status("Idle")
                self._set_step("--")
                self._set_buttons_running(False)

        threading.Thread(target=wrapper, daemon=True).start()

    def _adv_join(self):
        self._run_in_thread(join_game, "Joining game...")

    def _adv_leave(self):
        self._run_in_thread(leave_game, "Leaving game...")

    def _adv_align(self):
        self._run_in_thread(align_camera, "Aligning camera...")

    def _adv_reset(self):
        self._run_in_thread(reset_character, "Resetting character...")

    def _adv_calibrate(self):
        def calibrate_and_mark():
            if self._detector.calibrate():
                self._calibrated_this_session = True
        self._run_in_thread(calibrate_and_mark, "Calibrating...")

    def _adv_detect(self):
        self._run_in_thread(lambda: self._detector.detect_movement(duration=3), "Detecting...")


if __name__ == "__main__":
    app = App()
    app.mainloop()
