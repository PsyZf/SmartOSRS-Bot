import sys

def build_advanced_gui():
    filepath = 'C:/Users/psy/Documents/antigravity/amazing-einstein/osrs-smart-bot/gui_app.py'
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
        
    # 1. Replace start/stop text
    content = content.replace('text="â–¶ START BOT"', 'text="[>] START BOT"')
    content = content.replace('text="â–  STOP BOT"', 'text="[X] STOP BOT"')
    
    # 2. Add imports
    if "from PIL import Image" not in content:
        content = content.replace('import glob', 'import glob\nfrom PIL import Image\nimport os\nfrom macro_recorder import MacroRecorderGUI')

    # 3. Add Macro button next to Setup Guide button
    if "self.macro_btn" not in content:
        replacement = """        # Setup Guide and Macro Buttons
        btn_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        btn_frame.grid(row=1, column=0, padx=20, pady=5, sticky="ew")
        btn_frame.grid_columnconfigure(0, weight=1)
        btn_frame.grid_columnconfigure(1, weight=1)
        
        self.guide_btn = ctk.CTkButton(btn_frame, text="Setup Guide", fg_color="#443322", hover_color="#554433", text_color=FG_TAN, command=self.open_setup_guide)
        self.guide_btn.grid(row=0, column=0, padx=(0,2), sticky="ew")
        
        self.macro_btn = ctk.CTkButton(btn_frame, text="Macro", fg_color="#332211", hover_color="#443322", text_color="#d6a940", command=self.open_macro)
        self.macro_btn.grid(row=0, column=1, padx=(2,0), sticky="ew")
"""
        content = content.replace('        # Setup Guide Button\n        self.guide_btn = ctk.CTkButton(self.sidebar, text="ðŸ“– How to Setup", fg_color="#443322", hover_color="#554433", text_color=FG_TAN, command=self.open_setup_guide)\n        self.guide_btn.grid(row=1, column=0, padx=20, pady=10, sticky="ew")', replacement)

    # 4. Add Live Screenshot panel to right side
    if "self.screen_frame" not in content:
        ui_replacement = """        # --- Main Console Area ---
        self.console_frame = ctk.CTkFrame(self, fg_color=BG_BROWN)
        self.console_frame.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")
        self.console_frame.grid_columnconfigure(0, weight=1)
        self.console_frame.grid_rowconfigure(0, weight=1)
        
        self.textbox = ctk.CTkTextbox(self.console_frame, font=ctk.CTkFont(family="Consolas", size=13), fg_color="#120d07", text_color="#d6a940")
        self.textbox.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")
        self.textbox.insert("0.0", "Welcome to the OSRS Smart Bot Framework.\\nConfigure your settings on the left and click START.\\n\\n")
        self.textbox.configure(state="disabled")
        
        # --- Screenshot Area ---
        self.screen_frame = ctk.CTkFrame(self, fg_color=BG_BROWN)
        self.screen_frame.grid(row=0, column=2, padx=(0, 10), pady=10, sticky="nsew")
        
        self.screen_label = ctk.CTkLabel(self.screen_frame, text="Live Feed (Stopped)", text_color=FG_TAN)
        self.screen_label.pack(expand=True, fill="both", padx=10, pady=10)
        
        # Start screenshot loop
        self.after(2000, self.update_screenshot)
"""
        # We need to replace the old Main Console Area
        old_console = """        # --- Main Console Area ---
        self.console_frame = ctk.CTkFrame(self, fg_color=BG_BROWN)
        self.console_frame.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")
        self.console_frame.grid_columnconfigure(0, weight=1)
        self.console_frame.grid_rowconfigure(0, weight=1)
        
        self.textbox = ctk.CTkTextbox(self.console_frame, font=ctk.CTkFont(family="Consolas", size=13), fg_color="#120d07", text_color="#d6a940")
        self.textbox.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")
        self.textbox.insert("0.0", "Welcome to the OSRS Smart Bot Framework.\\nConfigure your settings on the left and click START.\\n\\n")
        self.textbox.configure(state="disabled")"""
        
        content = content.replace(old_console, ui_replacement)
        content = content.replace('self.geometry("1050x650")', 'self.geometry("1350x650")')

    # 5. Add methods
    if "def open_macro(self):" not in content:
        methods = """
    def open_macro(self):
        MacroRecorderGUI(self)

    def update_screenshot(self):
        if self.bot_process is not None and os.path.exists("latest_frame.jpg"):
            try:
                img = Image.open("latest_frame.jpg")
                ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=(400, 300))
                self.screen_label.configure(image=ctk_img, text="")
            except Exception:
                pass
        else:
            self.screen_label.configure(image="", text="Live Feed (Stopped)")
            
        self.after(2000, self.update_screenshot)
"""
        content = content.replace('    def open_setup_guide(self):', methods + '\n    def open_setup_guide(self):')

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    print("Patched GUI aggressively")

build_advanced_gui()
