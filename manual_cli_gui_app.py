from __future__ import annotations

import queue
import threading
import time
from pathlib import Path
import tkinter as tk
from tkinter import ttk, messagebox

import pyautogui

import manual_cli_human_automation as runner


class ManualCliGuiApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Manual CLI Runner")
        self.root.geometry("560x430")
        self.root.resizable(False, False)

        self.log_queue: queue.Queue[str] = queue.Queue()
        self.worker: threading.Thread | None = None

        self.run_id_var = tk.StringVar(value="1")
        self.base_dir_var = tk.StringVar(value=str(runner.DEFAULT_BASE_DIR))
        self.type_delay_var = tk.StringVar(value="0.03")
        self.countdown_var = tk.StringVar(value="5")
        self.clean_var = tk.BooleanVar(value=True)

        self._build_ui()
        self.root.after(100, self._drain_log_queue)

    def _build_ui(self) -> None:
        frame = ttk.Frame(self.root, padding=12)
        frame.pack(fill="both", expand=True)

        ttk.Label(frame, text="Run ID").grid(row=0, column=0, sticky="w")
        run_box = ttk.Frame(frame)
        run_box.grid(row=0, column=1, sticky="w", pady=(0, 8))
        for run_id in ("1", "2", "3"):
            ttk.Radiobutton(run_box, text=run_id, variable=self.run_id_var, value=run_id).pack(
                side="left", padx=(0, 12)
            )

        ttk.Label(frame, text="Base directory").grid(row=1, column=0, sticky="w")
        ttk.Entry(frame, textvariable=self.base_dir_var, width=54).grid(row=1, column=1, sticky="w", pady=(0, 8))

        ttk.Label(frame, text="Typing delay (sec)").grid(row=2, column=0, sticky="w")
        ttk.Entry(frame, textvariable=self.type_delay_var, width=12).grid(row=2, column=1, sticky="w", pady=(0, 8))

        ttk.Label(frame, text="Countdown (sec)").grid(row=3, column=0, sticky="w")
        ttk.Entry(frame, textvariable=self.countdown_var, width=12).grid(row=3, column=1, sticky="w", pady=(0, 8))

        ttk.Checkbutton(frame, text="Clean selected case folder before run", variable=self.clean_var).grid(
            row=4, column=1, sticky="w", pady=(0, 10)
        )

        self.start_btn = ttk.Button(frame, text="Start Run", command=self.on_start)
        self.start_btn.grid(row=5, column=1, sticky="w")

        ttk.Label(
            frame,
            text="Safety: move mouse to top-left corner to abort pyautogui actions.",
            foreground="#333333",
        ).grid(row=6, column=0, columnspan=2, sticky="w", pady=(10, 6))

        self.log_text = tk.Text(frame, height=12, width=68, state="disabled")
        self.log_text.grid(row=7, column=0, columnspan=2, sticky="nsew")

        frame.columnconfigure(1, weight=1)
        frame.rowconfigure(7, weight=1)

    def on_start(self) -> None:
        if self.worker and self.worker.is_alive():
            messagebox.showinfo("Manual CLI Runner", "A run is already in progress.")
            return

        run_id = self.run_id_var.get().strip()
        base_dir = self.base_dir_var.get().strip()

        try:
            type_delay = float(self.type_delay_var.get().strip())
            countdown = int(self.countdown_var.get().strip())
        except ValueError:
            messagebox.showerror("Invalid input", "Typing delay must be a number and countdown must be an integer.")
            return

        if type_delay < 0:
            messagebox.showerror("Invalid input", "Typing delay must be >= 0.")
            return
        if countdown < 0:
            messagebox.showerror("Invalid input", "Countdown must be >= 0.")
            return
        if not base_dir:
            messagebox.showerror("Invalid input", "Base directory is required.")
            return

        self.start_btn.config(state="disabled")
        self._log("Starting run...")

        self.worker = threading.Thread(
            target=self._run_worker,
            args=(run_id, Path(base_dir), type_delay, countdown, self.clean_var.get()),
            daemon=True,
        )
        self.worker.start()

    def _run_worker(self, run_id: str, base_dir: Path, type_delay: float, countdown: int, clean: bool) -> None:
        try:
            self._log(f"Selected run ID: {run_id}")
            self._log(f"Base directory: {base_dir}")

            if clean:
                runner.clean_case_folders(base_dir, run_id)
                self._log("Cleaned selected case folder.")

            runner.open_cmd(base_dir)
            self._log("CMD opened.")

            for sec in range(countdown, 0, -1):
                self._log(f"Starting in {sec}...")
                time.sleep(1)

            self._log("Automation started. Please don't use keyboard/mouse.")

            if run_id == "1":
                runner.run_case_1(type_delay)
            elif run_id == "2":
                runner.run_case_2(type_delay)
            elif run_id == "3":
                runner.run_case_3(base_dir, type_delay)

            self._log(f"Done. Case {run_id} completed.")
        except pyautogui.FailSafeException:
            self._log("Aborted by fail-safe (mouse moved to top-left).")
        except Exception as exc:
            self._log(f"Run failed: {exc}")
        finally:
            self.root.after(0, lambda: self.start_btn.config(state="normal"))

    def _log(self, text: str) -> None:
        self.log_queue.put(text)

    def _drain_log_queue(self) -> None:
        while not self.log_queue.empty():
            message = self.log_queue.get_nowait()
            self.log_text.config(state="normal")
            self.log_text.insert("end", message + "\n")
            self.log_text.see("end")
            self.log_text.config(state="disabled")
        self.root.after(100, self._drain_log_queue)


def main() -> int:
    root = tk.Tk()
    ManualCliGuiApp(root)
    root.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
