import customtkinter as ctk
import subprocess
import threading
import sys
import time
import os
import glob
from PIL import Image
import os
from macro_recorder import MacroRecorderGUI

# --- GUI Config ---
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

# RuneScape-esque colors
BG_BROWN = "#2c2214"
FG_TAN = "#e8c991"
ACCENT_GOLD = "#d6a940"
PANEL_BROWN = "#1f170d"
TEXT_COLOR = "#ffffff"

class OSRSBotGUI(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("OSRS Smart Bot Framework")
        self.geometry("1350x650")
        self.configure(fg_color=BG_BROWN)
        
        # Grid layout
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        # --- Sidebar (Controls) ---
        self.sidebar = ctk.CTkScrollableFrame(self, width=280, corner_radius=0, fg_color=PANEL_BROWN)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        
        self.logo = ctk.CTkLabel(self.sidebar, text="OSRS Smart Bot", font=ctk.CTkFont(size=22, weight="bold"), text_color=ACCENT_GOLD)
        self.logo.grid(row=0, column=0, padx=20, pady=(5, 5))
        
        # Setup Guide and Macro Buttons
        btn_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        btn_frame.grid(row=1, column=0, padx=20, pady=5, sticky="ew")
        btn_frame.grid_columnconfigure(0, weight=1)
        btn_frame.grid_columnconfigure(1, weight=1)
        
        self.guide_btn = ctk.CTkButton(btn_frame, text="Setup Guide", fg_color="#443322", hover_color="#554433", text_color=FG_TAN, command=self.open_setup_guide)
        self.guide_btn.grid(row=0, column=0, padx=(0,2), sticky="ew")
        
        self.macro_btn = ctk.CTkButton(btn_frame, text="Macro", fg_color="#332211", hover_color="#443322", text_color="#d6a940", command=self.open_macro)
        self.macro_btn.grid(row=0, column=1, padx=(2,0), sticky="ew")


        # Script Selection
        self.script_label = ctk.CTkLabel(self.sidebar, text="Select Script:", text_color=FG_TAN)
        self.script_label.grid(row=2, column=0, padx=20, pady=(10, 0), sticky="w")
        
        script_files = [f for f in glob.glob("*bot.py")]
        if not script_files:
            script_files = ["smart_sand_crab_bot.py"]
            
        self.script_var = ctk.StringVar(value=script_files[0])
        self.script_menu = ctk.CTkOptionMenu(self.sidebar, variable=self.script_var, values=script_files, fg_color="#443322", button_color=ACCENT_GOLD, button_hover_color="#b58d33")
        self.script_menu.grid(row=3, column=0, padx=20, pady=(5, 5), sticky="ew")

        # Switches
        self.food_var = ctk.BooleanVar(value=True)
        self.food_switch = ctk.CTkSwitch(self.sidebar, text="Auto-Eat (Green Tags)", variable=self.food_var, text_color=FG_TAN, progress_color=ACCENT_GOLD)
        self.food_switch.grid(row=4, column=0, padx=20, pady=5, sticky="w")
        
        self.pot_var = ctk.BooleanVar(value=True)
        self.pot_switch = ctk.CTkSwitch(self.sidebar, text="Combat Potions", variable=self.pot_var, text_color=FG_TAN, progress_color=ACCENT_GOLD)
        self.pot_switch.grid(row=5, column=0, padx=20, pady=5, sticky="w")
        
        self.relogin_var = ctk.BooleanVar(value=True)
        self.relogin_switch = ctk.CTkSwitch(self.sidebar, text="Auto Re-Login / OCR", variable=self.relogin_var, text_color=FG_TAN, progress_color=ACCENT_GOLD)
        self.relogin_switch.grid(row=6, column=0, padx=20, pady=5, sticky="w")

        self.debug_var = ctk.BooleanVar(value=False)
        self.debug_switch = ctk.CTkSwitch(self.sidebar, text="Debug Logging", variable=self.debug_var, text_color=FG_TAN, progress_color=ACCENT_GOLD)
        self.debug_switch.grid(row=7, column=0, padx=20, pady=5, sticky="w")
        
        # Runtime Slider
        self.runtime_label = ctk.CTkLabel(self.sidebar, text="Max Runtime: 6.0 Hours", text_color=FG_TAN)
        self.runtime_label.grid(row=8, column=0, padx=20, pady=(5, 0), sticky="w")
        
        self.runtime_slider = ctk.CTkSlider(self.sidebar, from_=1, to=12, number_of_steps=11, button_color=ACCENT_GOLD, progress_color=ACCENT_GOLD, command=self.update_runtime_label)
        self.runtime_slider.grid(row=9, column=0, padx=20, pady=(5, 5), sticky="ew")
        self.runtime_slider.set(6)
        
        # Hotkeys
        self.hotkey_label = ctk.CTkLabel(self.sidebar, text="Hotkeys:", text_color=ACCENT_GOLD, font=ctk.CTkFont(weight="bold"))
        self.hotkey_label.grid(row=10, column=0, padx=20, pady=(5, 0), sticky="w")
        
        hotkeys_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        hotkeys_frame.grid(row=11, column=0, padx=20, pady=5, sticky="ew")
        
        ctk.CTkLabel(hotkeys_frame, text="Stop:", text_color=FG_TAN).grid(row=0, column=0, padx=5, pady=2, sticky="w")
        self.hk_stop = ctk.CTkEntry(hotkeys_frame, width=40, justify="center")
        self.hk_stop.grid(row=0, column=1, padx=5, pady=2)
        self.hk_stop.insert(0, "q")
        
        ctk.CTkLabel(hotkeys_frame, text="Pause:", text_color=FG_TAN).grid(row=1, column=0, padx=5, pady=2, sticky="w")
        self.hk_pause = ctk.CTkEntry(hotkeys_frame, width=40, justify="center")
        self.hk_pause.grid(row=1, column=1, padx=5, pady=2)
        self.hk_pause.insert(0, "p")
        
        ctk.CTkLabel(hotkeys_frame, text="Force Home:", text_color=FG_TAN).grid(row=2, column=0, padx=5, pady=2, sticky="w")
        self.hk_force = ctk.CTkEntry(hotkeys_frame, width=40, justify="center")
        self.hk_force.grid(row=2, column=1, padx=5, pady=2)
        self.hk_force.insert(0, "w")

        # Timer
        self.timer_label = ctk.CTkLabel(self.sidebar, text="Active Runtime: 00:00:00", text_color="#70ff70", font=ctk.CTkFont(weight="bold"))
        self.timer_label.grid(row=12, column=0, padx=20, pady=(5, 0))

        # Buttons
        self.start_btn = ctk.CTkButton(self.sidebar, text="[>] START BOT", fg_color="#366b2a", hover_color="#274a1f", text_color="white", font=ctk.CTkFont(weight="bold"), command=self.start_bot)
        self.start_btn.grid(row=13, column=0, padx=20, pady=(5, 5), sticky="ew")
        
        self.stop_btn = ctk.CTkButton(self.sidebar, text="[X] STOP BOT", fg_color="#852c2c", hover_color="#5e1f1f", text_color="white", font=ctk.CTkFont(weight="bold"), state="disabled", command=self.stop_bot)
        self.stop_btn.grid(row=14, column=0, padx=20, pady=(0, 5), sticky="ew")
        
        # --- Main Console Area ---
        self.console_frame = ctk.CTkFrame(self, fg_color=BG_BROWN)
        self.console_frame.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")
        self.console_frame.grid_columnconfigure(0, weight=1)
        self.console_frame.grid_rowconfigure(0, weight=1)
        
        self.textbox = ctk.CTkTextbox(self.console_frame, font=ctk.CTkFont(family="Consolas", size=13), fg_color="#120d07", text_color="#d6a940")
        self.textbox.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")
        self.textbox.insert("0.0", "Welcome to the OSRS Smart Bot Framework.\nConfigure your settings on the left and click START.\n\n")
        self.textbox.configure(state="disabled")
        
        # --- Screenshot Area ---
        self.screen_frame = ctk.CTkFrame(self, fg_color=BG_BROWN)
        self.screen_frame.grid(row=0, column=2, padx=(0, 10), pady=10, sticky="nsew")
        
        self.screen_label = ctk.CTkLabel(self.screen_frame, text="Live Feed (Stopped)", text_color=FG_TAN)
        self.screen_label.pack(expand=True, fill="both", padx=10, pady=10)
        
        # Start screenshot loop
        self.after(2000, self.update_screenshot)

        
        self.bot_process = None
        self.bot_start_time = None
        self.timer_running = False
        
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    def on_closing(self):
        if self.bot_process:
            try:
                self.bot_process.terminate()
            except Exception:
                pass
        self.destroy()


    def open_macro(self):
        MacroRecorderGUI(self)

    def update_screenshot(self):
        is_running = self.bot_process is not None and self.bot_process.poll() is None
        if is_running and os.path.exists("latest_frame.jpg"):
            try:
                with Image.open("latest_frame.jpg") as img:
                    img_copy = img.copy()
                ctk_img = ctk.CTkImage(light_image=img_copy, dark_image=img_copy, size=(400, 263))
                self.screen_label.configure(image=ctk_img, text="")
            except Exception:
                pass
        elif is_running:
            self.screen_label.configure(image="", text="Live Feed (Connecting...)")
        else:
            self.screen_label.configure(image="", text="Live Feed (Stopped)")
            
        self.after(1000, self.update_screenshot)

    def open_setup_guide(self):
        guide_window = ctk.CTkToplevel(self)
        guide_window.title("Setup Guide")
        guide_window.geometry("600x500")
        guide_window.configure(fg_color=PANEL_BROWN)
        
        guide_text = ctk.CTkTextbox(guide_window, font=ctk.CTkFont(size=14), fg_color=BG_BROWN, text_color=FG_TAN)
        guide_text.pack(expand=True, fill="both", padx=10, pady=10)
        
        text = """=== OSRS Smart Bot Setup Guide ===

1. RUNELITE SETTINGS
- Game Layout must be 'Fixed - Classic Layout'
- Camera Zoom must be completely zoomed out
- Set camera pitch all the way UP (looking down)
- Compass must face NORTH (click the compass icon)

2. MARKERS & COLORS
We use OpenCV to navigate. You must mark ground tiles exactly with these colors:
- MAGENTA (#FF00FF): Your "Home" tile where you stand to fight.
- CYAN (#00FFFF): Your "Mid-way" route tiles. Place these to lead to aggro boundary.
- BLUE (#0000FF): Your "Far" turnaround point. 
- BLACK (#000000): "Breadcrumb" tiles. Only used as a fallback if the bot gets lost.

3. INVENTORY TAGS
- FOOD: Tag your food GREEN in the inventory using 'Inventory Tags' plugin.
- POTIONS: Combat potions aren't auto-detected yet by tag, keep them visible.

4. FAILSAFES
- The bot relies on the HP Orb turning RED. If you accidentally drag your window, the bot will notice the HP orb isn't red anymore and auto-calibrate itself!
- If the world map opens by accident, it will press ESC to clear it.
- If you hit a login screen, EasyOCR will read the text.
"""
        guide_text.insert("0.0", text)
        guide_text.configure(state="disabled")

    def update_runtime_label(self, value):
        self.runtime_label.configure(text=f"Max Runtime: {value:.1f} Hours")

    def log(self, message):
        self.textbox.configure(state="normal")
        self.textbox.insert("end", message + "\n")
        self.textbox.see("end")
        self.textbox.configure(state="disabled")

    def start_bot(self):
        if self.bot_process is not None:
            return
            
        self.start_btn.configure(state="disabled")
        self.stop_btn.configure(state="normal")
        
        # Lock controls
        self.food_switch.configure(state="disabled")
        self.pot_switch.configure(state="disabled")
        self.runtime_slider.configure(state="disabled")
        self.script_menu.configure(state="disabled")
        self.relogin_switch.configure(state="disabled")
        self.hk_stop.configure(state="disabled")
        self.hk_pause.configure(state="disabled")
        self.hk_force.configure(state="disabled")
        
        self.textbox.configure(state="normal")
        self.textbox.delete("0.0", "end")
        self.textbox.configure(state="disabled")
        
        script_file = self.script_var.get()
        self.log(f"[*] Initializing {script_file}...")
        self.bot_start_time = time.time()
        self.timer_running = True
        self.update_timer()
        
        # Determine python executable (handles PyInstaller compilation)
        python_exe = sys.executable
        if getattr(sys, 'frozen', False):
            python_exe = "python"  # Fallback to system python if GUI is compiled
            
        # Build command args
        cmd = [python_exe, "-u", script_file, "--fast"]
        if not self.food_var.get():
            cmd.append("--no-food")
        if not self.pot_var.get():
            cmd.append("--no-pots")
        if not self.relogin_var.get():
            cmd.append("--no-relogin")
        if self.debug_var.get():
            cmd.append("--debug")
            
        cmd.extend(["--max-time", str(int(self.runtime_slider.get()))])
        
        # Add hotkeys
        cmd.extend(["--hotkey-stop", self.hk_stop.get()])
        cmd.extend(["--hotkey-pause", self.hk_pause.get()])
        cmd.extend(["--hotkey-force", self.hk_force.get()])
        
        try:
            self.bot_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            )
            
            # Start thread to read output
            threading.Thread(target=self.read_output, daemon=True).start()
        except Exception as e:
            self.log(f"[!] Error starting bot: {e}")
            self.bot_finished()


    def update_timer(self):
        if self.timer_running and self.bot_start_time:
            elapsed = int(time.time() - self.bot_start_time)
            hours = elapsed // 3600
            minutes = (elapsed % 3600) // 60
            seconds = elapsed % 60
            self.timer_label.configure(text=f"Active Runtime: {hours:02d}:{minutes:02d}:{seconds:02d}")
            self.after(1000, self.update_timer)

    def read_output(self):
        try:
            for line in iter(self.bot_process.stdout.readline, ''):
                if line:
                    self.after(0, self.log, line.strip('\\n'))
            self.bot_process.stdout.close()
            self.bot_process.wait()
        except Exception as e:
            self.after(0, self.log, f"[!] Process read error: {e}")
        finally:
            self.after(0, self.bot_finished)

    def stop_bot(self):
        if self.bot_process:
            self.log("[!] User pressed STOP. Terminating bot...")
            self.bot_process.terminate()
            
    def bot_finished(self):
        if self.bot_process:
            self.log("\n[!] Bot process has terminated.")
        self.bot_process = None
        self.timer_running = False
        self.timer_label.configure(text="Active Runtime: 00:00:00")
        self.bot_start_time = None
        self.timer_running = False
        self.start_btn.configure(state="normal")
        self.stop_btn.configure(state="disabled")
        
        # Unlock controls
        self.food_switch.configure(state="normal")
        self.pot_switch.configure(state="normal")
        self.runtime_slider.configure(state="normal")
        self.script_menu.configure(state="normal")
        self.relogin_switch.configure(state="normal")
        self.hk_stop.configure(state="normal")
        self.hk_pause.configure(state="normal")
        self.hk_force.configure(state="normal")

if __name__ == "__main__":
    app = OSRSBotGUI()
    app.mainloop()
