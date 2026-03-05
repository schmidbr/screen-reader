from __future__ import annotations

import tkinter as tk
from pathlib import Path
from tkinter import messagebox, ttk

from screen_reader.config import AppConfig, init_config, load_config, save_config


class SettingsUI:
    def __init__(self, config_path: Path) -> None:
        self.config_path = config_path
        if not self.config_path.exists():
            init_config(self.config_path, force=True)
        self.cfg = load_config(self.config_path)
        self.root = tk.Tk()
        self.root.title("Screen Reader Settings")
        self.root.geometry("760x620")
        self.root.minsize(700, 560)
        self.root.protocol("WM_DELETE_WINDOW", self._close)

        self.vars: dict[str, tk.Variable] = {}
        self._build()

    def _build(self) -> None:
        frame = ttk.Frame(self.root, padding=12)
        frame.pack(fill=tk.BOTH, expand=True)

        row = 0
        ttk.Label(frame, text="OpenAI", font=("Segoe UI", 11, "bold")).grid(row=row, column=0, sticky="w", pady=(0, 4))
        row += 1
        self._add_entry(frame, row, "OpenAI API Key", "openai.api_key", self.cfg.openai.api_key, show="*")
        row += 1
        self._add_entry(frame, row, "OpenAI Model", "openai.model", self.cfg.openai.model)
        row += 1

        ttk.Separator(frame).grid(row=row, column=0, columnspan=2, sticky="ew", pady=8)
        row += 1
        ttk.Label(frame, text="ElevenLabs", font=("Segoe UI", 11, "bold")).grid(row=row, column=0, sticky="w", pady=(0, 4))
        row += 1
        self._add_entry(frame, row, "ElevenLabs API Key", "elevenlabs.api_key", self.cfg.elevenlabs.api_key, show="*")
        row += 1
        self._add_entry(frame, row, "Voice ID", "elevenlabs.voice_id", self.cfg.elevenlabs.voice_id)
        row += 1
        self._add_entry(frame, row, "Model ID", "elevenlabs.model_id", self.cfg.elevenlabs.model_id)
        row += 1
        self._add_entry(frame, row, "Output Format", "elevenlabs.output_format", self.cfg.elevenlabs.output_format)
        row += 1

        ttk.Separator(frame).grid(row=row, column=0, columnspan=2, sticky="ew", pady=8)
        row += 1
        ttk.Label(frame, text="Hotkeys & Capture", font=("Segoe UI", 11, "bold")).grid(row=row, column=0, sticky="w", pady=(0, 4))
        row += 1
        self._add_entry(frame, row, "Capture Hotkey", "capture.hotkey", self.cfg.capture.hotkey)
        row += 1
        self._add_entry(frame, row, "Stop Hotkey", "capture.stop_hotkey", self.cfg.capture.stop_hotkey)
        row += 1
        self._add_entry(frame, row, "Capture Cooldown (ms)", "capture.cooldown_ms", str(self.cfg.capture.cooldown_ms))
        row += 1

        ttk.Separator(frame).grid(row=row, column=0, columnspan=2, sticky="ew", pady=8)
        row += 1
        ttk.Label(frame, text="Filtering / Dedup / Playback", font=("Segoe UI", 11, "bold")).grid(row=row, column=0, sticky="w", pady=(0, 4))
        row += 1
        self._add_entry(frame, row, "Min Block Chars", "filter.min_block_chars", str(self.cfg.filter.min_block_chars))
        row += 1
        self._add_entry(frame, row, "Ignore Short Lines (< words)", "filter.ignore_short_lines", str(self.cfg.filter.ignore_short_lines))
        row += 1
        self._add_checkbox(frame, row, "Dedup Enabled", "dedup.enabled", self.cfg.dedup.enabled)
        row += 1
        self._add_entry(frame, row, "Dedup Similarity Threshold", "dedup.similarity_threshold", str(self.cfg.dedup.similarity_threshold))
        row += 1
        self._add_entry(frame, row, "Retry Count", "playback.retry_count", str(self.cfg.playback.retry_count))
        row += 1
        self._add_entry(frame, row, "Retry Backoff (ms)", "playback.retry_backoff_ms", str(self.cfg.playback.retry_backoff_ms))
        row += 1

        ttk.Separator(frame).grid(row=row, column=0, columnspan=2, sticky="ew", pady=8)
        row += 1
        ttk.Label(frame, text="Debug / Logs", font=("Segoe UI", 11, "bold")).grid(row=row, column=0, sticky="w", pady=(0, 4))
        row += 1
        self._add_checkbox(frame, row, "Save Debug Screenshots", "debug.save_screenshots", self.cfg.debug.save_screenshots)
        row += 1
        self._add_entry(frame, row, "Debug Screenshot Directory", "debug.screenshot_dir", self.cfg.debug.screenshot_dir)
        row += 1
        self._add_entry(frame, row, "Log File", "log_file", self.cfg.log_file)
        row += 1

        button_row = ttk.Frame(frame)
        button_row.grid(row=row, column=0, columnspan=2, sticky="e", pady=(10, 0))
        ttk.Button(button_row, text="Save", command=self._save).pack(side=tk.RIGHT, padx=(8, 0))
        ttk.Button(button_row, text="Save & Close", command=self._save_and_close).pack(side=tk.RIGHT)
        ttk.Button(button_row, text="Close", command=self._close).pack(side=tk.RIGHT, padx=(0, 8))

        frame.columnconfigure(1, weight=1)

    def _add_entry(self, parent: ttk.Frame, row: int, label: str, key: str, value: str, show: str | None = None) -> None:
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky="w", pady=4, padx=(0, 10))
        var = tk.StringVar(value=value)
        self.vars[key] = var
        entry = ttk.Entry(parent, textvariable=var, show=show or "")
        entry.grid(row=row, column=1, sticky="ew", pady=4)

    def _add_checkbox(self, parent: ttk.Frame, row: int, label: str, key: str, value: bool) -> None:
        var = tk.BooleanVar(value=value)
        self.vars[key] = var
        ttk.Checkbutton(parent, text=label, variable=var).grid(row=row, column=0, columnspan=2, sticky="w", pady=4)

    def _to_int(self, key: str) -> int:
        return int(str(self.vars[key].get()).strip())

    def _to_float(self, key: str) -> float:
        return float(str(self.vars[key].get()).strip())

    def _apply_form(self, cfg: AppConfig) -> AppConfig:
        cfg.openai.api_key = str(self.vars["openai.api_key"].get()).strip()
        cfg.openai.model = str(self.vars["openai.model"].get()).strip()

        cfg.elevenlabs.api_key = str(self.vars["elevenlabs.api_key"].get()).strip()
        cfg.elevenlabs.voice_id = str(self.vars["elevenlabs.voice_id"].get()).strip()
        cfg.elevenlabs.model_id = str(self.vars["elevenlabs.model_id"].get()).strip()
        cfg.elevenlabs.output_format = str(self.vars["elevenlabs.output_format"].get()).strip()

        cfg.capture.hotkey = str(self.vars["capture.hotkey"].get()).strip()
        cfg.capture.stop_hotkey = str(self.vars["capture.stop_hotkey"].get()).strip()
        cfg.capture.cooldown_ms = self._to_int("capture.cooldown_ms")

        cfg.filter.min_block_chars = self._to_int("filter.min_block_chars")
        cfg.filter.ignore_short_lines = self._to_int("filter.ignore_short_lines")

        cfg.dedup.enabled = bool(self.vars["dedup.enabled"].get())
        cfg.dedup.similarity_threshold = self._to_float("dedup.similarity_threshold")

        cfg.playback.retry_count = self._to_int("playback.retry_count")
        cfg.playback.retry_backoff_ms = self._to_int("playback.retry_backoff_ms")

        cfg.debug.save_screenshots = bool(self.vars["debug.save_screenshots"].get())
        cfg.debug.screenshot_dir = str(self.vars["debug.screenshot_dir"].get()).strip()
        cfg.log_file = str(self.vars["log_file"].get()).strip()
        return cfg

    def _save(self) -> bool:
        try:
            updated = self._apply_form(load_config(self.config_path))
            save_config(self.config_path, updated)
            messagebox.showinfo("Saved", f"Settings saved to {self.config_path}")
            return True
        except Exception as exc:  # noqa: BLE001
            messagebox.showerror("Save Failed", str(exc))
            return False

    def _save_and_close(self) -> None:
        if self._save():
            self._close()

    def _close(self) -> None:
        try:
            self.root.quit()
        finally:
            self.root.destroy()

    def run(self) -> int:
        self.root.mainloop()
        return 0


def launch_settings_ui(config_path: Path) -> int:
    ui = SettingsUI(config_path)
    return ui.run()
