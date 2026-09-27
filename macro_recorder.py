import json
import time
import random
import threading
import pyautogui
from pynput import mouse, keyboard
import customtkinter as ctk

class MacroRecorderGUI(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Humanized Macro Recorder")
        self.geometry("400x350")
        self.configure(fg_color="#2c2214")
        
        self.events = []
        self.recording = False
        self.playing = False
        
        self.mouse_listener = None
        self.start_time = None

        # UI Elements
        self.lbl = ctk.CTkLabel(self, text="Macro Recorder", font=ctk.CTkFont(size=20, weight="bold"), text_color="#d6a940")
        self.lbl.pack(pady=(15, 10))

        self.status_lbl = ctk.CTkLabel(self, text="Status: IDLE", text_color="white")
        self.status_lbl.pack(pady=5)
        
        self.btn_record = ctk.CTkButton(self, text="Record (Press 'F8' to Stop)", fg_color="#852c2c", hover_color="#5e1f1f", command=self.start_recording)
        self.btn_record.pack(pady=10)
        
        self.btn_play = ctk.CTkButton(self, text="Play (Humanized)", fg_color="#366b2a", hover_color="#274a1f", command=self.play_macro)
        self.btn_play.pack(pady=10)
        
        self.btn_save = ctk.CTkButton(self, text="Save to File", command=self.save_macro)
        self.btn_save.pack(pady=10)
        
    def on_click(self, x, y, button, pressed):
        if pressed and self.recording:
            # We only record the click down event
            t = time.time() - self.start_time
            self.events.append({
                "time": t,
                "x": x,
                "y": y,
                "button": str(button)
            })

    def start_recording(self):
        if self.recording:
            return
            
        self.events = []
        self.recording = True
        self.status_lbl.configure(text="Status: RECORDING (Press F8 to Stop)", text_color="#ff5555")
        self.start_time = time.time()
        
        self.mouse_listener = mouse.Listener(on_click=self.on_click)
        self.mouse_listener.start()
        
        # Start a keyboard listener just for the stop hotkey
        def on_press(key):
            if key == keyboard.Key.f8:
                self.stop_recording()
                return False
                
        self.kb_listener = keyboard.Listener(on_press=on_press)
        self.kb_listener.start()

    def stop_recording(self):
        self.recording = False
        if self.mouse_listener:
            self.mouse_listener.stop()
        self.status_lbl.configure(text=f"Status: Recorded {len(self.events)} clicks.", text_color="#55ff55")

    def save_macro(self):
        if not self.events:
            return
        with open("saved_macro.json", "w") as f:
            json.dump(self.events, f, indent=4)
        self.status_lbl.configure(text="Status: Saved to saved_macro.json")

    def play_macro(self):
        if not self.events or self.playing:
            return
        self.playing = True
        self.status_lbl.configure(text="Status: PLAYING MACRO", text_color="#55ff55")
        threading.Thread(target=self._playback_thread, daemon=True).start()

    def _playback_thread(self):
        # We simulate the exact delays, but add a bit of gaussian noise
        last_t = 0
        for ev in self.events:
            wait_time = ev["time"] - last_t
            
            # Humanize the wait time (add ±10% to 20% noise, gaussian)
            human_wait = max(0.1, wait_time * random.gauss(1.0, 0.15))
            time.sleep(human_wait)
            
            # Humanize coordinates (offset by a few pixels)
            hx = ev["x"] + int(random.gauss(0, 3))
            hy = ev["y"] + int(random.gauss(0, 3))
            
            # Move mouse smoothly to the new coordinate
            dur = max(0.1, random.gauss(0.2, 0.05))
            pyautogui.moveTo(hx, hy, duration=dur, tween=pyautogui.easeOutQuad)
            
            btn = 'left' if 'left' in ev["button"] else 'right'
            pyautogui.click(button=btn)
            
            last_t = ev["time"]
            
        self.playing = False
        self.status_lbl.configure(text="Status: PLAYBACK COMPLETE", text_color="white")

if __name__ == "__main__":
    app = ctk.CTk()
    MacroRecorderGUI(app)
    app.mainloop()
