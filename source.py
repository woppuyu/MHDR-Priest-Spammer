import tkinter as tk
from tkinter import ttk
import keyboard
import threading
import time
from random import uniform as randfloat
import sys
import json
import os

class SkillSpammerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("MHDR Priest Skill Spammer")
        self.root.geometry("400x650")  # Increased height to 650
        self.root.resizable(False, False)  # Prevent window resizing
        
        # State variables
        self.is_running = True
        self.is_paused = False
        self.current_mode = None
        self.active_thread = None

        # Default settings structure
        self.default_settings = {
            "key_bindings": {
                "boss": {"key1": "", "key2": ""},
                "mob": {"key1": ""},
                "custom": {"keys": []}
            },
            "delay_settings": {
                "use_random_delay": True,
                "fixed_delay": 150,
                "random_delay_min": 100,
                "random_delay_max": 200
            },
            "activation_key": "j"  # Default activation key
        }
        
        # Load settings from JSON
        self.settings = self.load_settings()
        self.key_bindings = self.settings["key_bindings"]
        
        # Apply loaded delay settings
        self.use_random_delay = self.settings["delay_settings"]["use_random_delay"]
        self.delay_fixed = self.settings["delay_settings"]["fixed_delay"]
        self.delay_min = self.settings["delay_settings"]["random_delay_min"]
        self.delay_max = self.settings["delay_settings"]["random_delay_max"]

        # Store mode_frame reference
        self.mode_frame = None
        self.instructions_label = None  # Add this line

        # Create GUI elements
        self.setup_gui()
        
        # Start update loop
        self.update_status()

    def load_settings(self):
        try:
            with open('spammer_keybinds.json', 'r') as f:
                loaded_settings = json.load(f)
                # Ensure all required settings exist
                for key in self.default_settings:
                    if key not in loaded_settings:
                        loaded_settings[key] = self.default_settings[key]
                return loaded_settings
        except (FileNotFoundError, json.JSONDecodeError):
            return self.default_settings.copy()

    def save_settings(self):
        try:
            # Update delay settings before saving
            self.settings["delay_settings"].update({
                "use_random_delay": self.use_random_delay,
                "fixed_delay": self.delay_fixed,
                "random_delay_min": self.delay_min,
                "random_delay_max": self.delay_max
            })
            with open('spammer_keybinds.json', 'w') as f:
                json.dump(self.settings, f, indent=4)
        except Exception as e:
            print(f"Error saving settings: {e}")

    def setup_gui(self):
        # Mode Selection Frame
        self.mode_frame = ttk.LabelFrame(self.root, text="Mode Selection", padding=10)
        self.mode_frame.pack(fill="x", padx=10, pady=5)

        # Boss Mode Row
        boss_frame = ttk.Frame(self.mode_frame)
        boss_frame.pack(fill="x", pady=2)
        key_text = f"{self.key_bindings['boss']['key1']}+{self.key_bindings['boss']['key2']}"
        if not self.key_bindings['boss']['key1'] and not self.key_bindings['boss']['key2']:
            key_text = "No keys set"
        mode_btn = ttk.Button(boss_frame, text=f"Boss Mode ({key_text})", 
                  command=lambda: self.set_mode("boss"))
        mode_btn.pack(side=tk.LEFT, fill="x", expand=True, padx=(0,5))
        ttk.Button(boss_frame, text="⚙", width=3,
                  command=lambda: self.open_settings("boss")).pack(side=tk.LEFT)

        # Mob Mode Row
        mob_frame = ttk.Frame(self.mode_frame)
        mob_frame.pack(fill="x", pady=2)
        key_text = self.key_bindings['mob']['key1'] or "No key set"
        mode_btn = ttk.Button(mob_frame, text=f"Mob Mode ({key_text})", 
                  command=lambda: self.set_mode("mob"))
        mode_btn.pack(side=tk.LEFT, fill="x", expand=True, padx=(0,5))
        ttk.Button(mob_frame, text="⚙", width=3,
                  command=lambda: self.open_settings("mob")).pack(side=tk.LEFT)

        # Custom Mode Row
        custom_frame = ttk.Frame(self.mode_frame)
        custom_frame.pack(fill="x", pady=2)
        key_text = ", ".join(self.key_bindings['custom']['keys']) or "No keys"
        mode_btn = ttk.Button(custom_frame, 
                  text=f"Custom Mode ({key_text})", 
                  command=lambda: self.set_mode("custom"))
        mode_btn.pack(side=tk.LEFT, fill="x", expand=True, padx=(0,5))
        ttk.Button(custom_frame, text="⚙", width=3,
                  command=lambda: self.open_settings("custom")).pack(side=tk.LEFT)

        # Status Frame
        status_frame = ttk.LabelFrame(self.root, text="Status", padding=10)
        status_frame.pack(fill="x", padx=10, pady=5)

        self.mode_label = ttk.Label(status_frame, text="Current Mode: None")
        self.mode_label.pack(fill="x")
        
        self.status_label = ttk.Label(status_frame, text="Status: Ready")
        self.status_label.pack(fill="x")

        # Delay Settings Frame
        delay_frame = ttk.LabelFrame(self.root, text="Delay Settings", padding=10)
        delay_frame.pack(fill="x", padx=10, pady=5)

        # Delay Mode Selection
        self.delay_mode_var = tk.BooleanVar(value=True)  # Changed to True
        ttk.Checkbutton(delay_frame, text="Use Random Delay", 
                       variable=self.delay_mode_var,
                       command=self.toggle_delay_mode).pack(fill="x", pady=2)

        # Fixed Delay Input
        fixed_frame = ttk.Frame(delay_frame)
        fixed_frame.pack(fill="x", pady=2)
        ttk.Label(fixed_frame, text="Fixed Delay (ms):").pack(side=tk.LEFT)
        self.fixed_delay_var = tk.StringVar(value="150")
        self.fixed_delay_entry = ttk.Entry(fixed_frame, textvariable=self.fixed_delay_var, width=10)
        self.fixed_delay_entry.pack(side=tk.LEFT, padx=5)

        # Random Delay Range Inputs
        random_frame = ttk.Frame(delay_frame)
        random_frame.pack(fill="x", pady=2)
        ttk.Label(random_frame, text="Random Delay Range (ms):").pack(side=tk.LEFT)
        self.min_delay_var = tk.StringVar(value="100")
        self.max_delay_var = tk.StringVar(value="200")  # Changed to "200"
        self.min_delay_entry = ttk.Entry(random_frame, textvariable=self.min_delay_var, width=10)
        ttk.Label(random_frame, text="-").pack(side=tk.LEFT, padx=2)
        self.max_delay_entry = ttk.Entry(random_frame, textvariable=self.max_delay_var, width=10)
        self.min_delay_entry.pack(side=tk.LEFT, padx=2)
        self.max_delay_entry.pack(side=tk.LEFT, padx=2)

        # Initially disable fixed delay input instead of random delay inputs
        self.fixed_delay_entry.state(['disabled'])
        self.min_delay_entry.state(['!disabled'])
        self.max_delay_entry.state(['!disabled'])

        # Apply Button
        ttk.Button(delay_frame, text="Apply Delay Settings", 
                  command=self.apply_delay_settings).pack(fill="x", pady=2)

        # Control Frame
        control_frame = ttk.LabelFrame(self.root, text="Controls", padding=10)
        control_frame.pack(fill="x", padx=10, pady=5)

        ttk.Button(control_frame, text="Pause/Resume", 
                  command=self.toggle_pause).pack(fill="x", pady=2)
        ttk.Button(control_frame, text="Stop Spammer", 
                  command=self.stop_spammer).pack(fill="x", pady=2)
        ttk.Button(control_frame, text="Key Settings", 
                  command=self.open_activation_settings).pack(fill="x", pady=2)
        ttk.Button(control_frame, text="Exit", 
                  command=self.exit_program).pack(fill="x", pady=2)

        # Instructions Frame
        instructions_frame = ttk.LabelFrame(self.root, text="Instructions", padding=10)
        instructions_frame.pack(fill="x", padx=10, pady=5)

        self.instructions_label = ttk.Label(instructions_frame, justify=tk.LEFT)
        self.instructions_label.pack(fill="x", padx=5)
        self.update_instructions()  # Initial instructions setup

    def set_mode(self, mode):
        self.current_mode = mode
        self.is_paused = False
        self.mode_label.config(text=f"Current Mode: {mode.upper()}")
        self.status_label.config(text="Status: Ready")
        
    def toggle_pause(self):
        if not self.current_mode:
            return  # Don't toggle pause if no mode is active
        
        self.is_paused = not self.is_paused
        status = "PAUSED" if self.is_paused else "READY"
        self.status_label.config(text=f"Status: {status}")

    def stop_spammer(self):
        self.current_mode = None
        self.is_paused = False
        self.mode_label.config(text="Current Mode: None")
        self.status_label.config(text="Status: Stopped")
        if self.active_thread and self.active_thread.is_alive():
            self.active_thread.join(timeout=1)
        self.active_thread = None

    def toggle_delay_mode(self):
        if self.delay_mode_var.get():
            self.fixed_delay_entry.state(['disabled'])
            self.min_delay_entry.state(['!disabled'])
            self.max_delay_entry.state(['!disabled'])
        else:
            self.fixed_delay_entry.state(['!disabled'])
            self.min_delay_entry.state(['disabled'])
            self.max_delay_entry.state(['disabled'])

    def validate_delay(self, value, min_val=100, max_val=5000):
        try:
            delay = int(value)
            return min_val <= delay <= max_val
        except ValueError:
            return False

    def apply_delay_settings(self):
        if self.delay_mode_var.get():
            # Random delay mode
            if (self.validate_delay(self.min_delay_var.get()) and 
                self.validate_delay(self.max_delay_var.get())):
                min_delay = int(self.min_delay_var.get())
                max_delay = int(self.max_delay_var.get())
                if min_delay < max_delay:
                    self.delay_min = min_delay
                    self.delay_max = max_delay
                    self.use_random_delay = True
                    self.status_label.config(text="Status: Random delay settings applied")
                    self.save_settings()
                else:
                    self.status_label.config(text="Error: Min delay must be less than max delay")
            else:
                self.status_label.config(text="Error: Invalid delay values (100-5000 ms)")
        else:
            # Fixed delay mode
            if self.validate_delay(self.fixed_delay_var.get()):
                self.delay_fixed = int(self.fixed_delay_var.get())
                self.use_random_delay = False
                self.status_label.config(text="Status: Fixed delay settings applied")
                self.save_settings()
            else:
                self.status_label.config(text="Error: Invalid delay value (100-5000 ms)")

    def validate_key(self, key):
        """Validate that input is a single character"""
        return len(key) == 1

    def open_settings(self, mode):
        if mode != "custom":
            settings = tk.Toplevel(self.root)
            settings.title(f"{mode.upper()} Mode Settings")
            settings.geometry("300x150")
            settings.resizable(False, False)
            settings.transient(self.root)
            settings.grab_set()

            # Center the settings window relative to main window
            settings.withdraw()  # Hide temporarily
            # Calculate position
            main_x = self.root.winfo_rootx()
            main_y = self.root.winfo_rooty()
            main_width = self.root.winfo_width()
            
            settings_width = 300
            settings_height = 150
            
            x = main_x + (main_width - settings_width) // 2
            y = main_y + 50  # Fixed offset from top of main window
            
            settings.geometry(f"+{x}+{y}")
            settings.deiconify()  # Show window at calculated position

            frame = ttk.Frame(settings, padding="10")
            frame.pack(fill="both", expand=True)

            def validate_and_limit_entry(*args):
                """Limit entry to 1 character and convert to lowercase"""
                if key1_var.get():
                    key1_var.set(key1_var.get()[-1:].lower())
                if mode == "boss" and key2_var.get():
                    key2_var.set(key2_var.get()[-1:].lower())

            # Create key binding entries
            if mode == "boss":
                ttk.Label(frame, text="First Key:").grid(row=0, column=0, padx=5, pady=5)
                key1_var = tk.StringVar(value=self.key_bindings[mode]["key1"])
                key1_var.trace('w', validate_and_limit_entry)
                key1_entry = ttk.Entry(frame, textvariable=key1_var, width=2)
                key1_entry.grid(row=0, column=1, padx=5, pady=5)

                ttk.Label(frame, text="Second Key:").grid(row=1, column=0, padx=5, pady=5)
                key2_var = tk.StringVar(value=self.key_bindings[mode]["key2"])
                key2_var.trace('w', validate_and_limit_entry)
                key2_entry = ttk.Entry(frame, textvariable=key2_var, width=2)
                key2_entry.grid(row=1, column=1, padx=5, pady=5)
            else:
                ttk.Label(frame, text="Spam Key:").grid(row=0, column=0, padx=5, pady=5)
                key1_var = tk.StringVar(value=self.key_bindings[mode]["key1"])
                key1_var.trace('w', validate_and_limit_entry)
                key1_entry = ttk.Entry(frame, textvariable=key1_var, width=2)
                key1_entry.grid(row=0, column=1, padx=5, pady=5)

            def save_settings():
                if mode == "boss":
                    self.key_bindings[mode]["key1"] = key1_var.get().lower()
                    self.key_bindings[mode]["key2"] = key2_var.get().lower()
                else:
                    self.key_bindings[mode]["key1"] = key1_var.get().lower()
                
                # Update only the specific mode's button text
                for child in self.mode_frame.winfo_children():
                    for button in child.winfo_children():
                        if isinstance(button, ttk.Button) and button.cget("text") != "⚙":
                            # Check if this button is for the current mode
                            if (mode == "boss" and "Boss Mode" in button.cget("text")) or \
                               (mode == "mob" and "Mob Mode" in button.cget("text")):
                                if mode == "boss":
                                    button.configure(text=f"Boss Mode ({self.key_bindings[mode]['key1']}+{self.key_bindings[mode]['key2']})")
                                elif mode == "mob":
                                    button.configure(text=f"Mob Mode ({self.key_bindings[mode]['key1']})")
                                break
                
                self.save_settings()  # Save after updating bindings
                settings.destroy()

            ttk.Button(frame, text="Save", command=save_settings).grid(row=4, column=0, columnspan=2, pady=20)
            return

        # Custom mode settings window
        settings = tk.Toplevel(self.root)
        settings.title("Custom Mode Settings")
        settings.geometry("300x400")
        settings.resizable(False, False)
        settings.transient(self.root)
        settings.grab_set()

        # Center window
        settings.withdraw()
        main_x = self.root.winfo_rootx()
        main_y = self.root.winfo_rooty()
        main_width = self.root.winfo_width()
        settings_width = 300
        x = main_x + (main_width - settings_width) // 2
        y = main_y + 50
        settings.geometry(f"+{x}+{y}")
        settings.deiconify()

        frame = ttk.Frame(settings, padding="10")
        frame.pack(fill="both", expand=True)

        # Key list
        ttk.Label(frame, text="Current Keys:").pack(fill="x", pady=(0,5))
        key_list = tk.Listbox(frame, height=10)
        key_list.pack(fill="both", expand=True, pady=5)
        
        # Populate key list
        for key in self.key_bindings["custom"]["keys"]:
            key_list.insert(tk.END, key)

        # Add key section
        add_frame = ttk.Frame(frame)
        add_frame.pack(fill="x", pady=5)
        key_var = tk.StringVar()

        def validate_and_limit_entry(*args):
            if key_var.get():
                key_var.set(key_var.get()[-1:].lower())

        key_var.trace('w', validate_and_limit_entry)
        ttk.Entry(add_frame, textvariable=key_var, width=2).pack(side=tk.LEFT, padx=5)
        
        def add_key():
            key = key_var.get().lower()
            if key and len(key) == 1 and key not in self.key_bindings["custom"]["keys"]:
                self.key_bindings["custom"]["keys"].append(key)
                key_list.insert(tk.END, key)
                key_var.set("")
                update_button_text()
                self.save_settings()  # Save after adding key

        def remove_key():
            selection = key_list.curselection()
            if selection:
                idx = selection[0]
                key = key_list.get(idx)
                self.key_bindings["custom"]["keys"].remove(key)
                key_list.delete(idx)
                update_button_text()
                self.save_settings()  # Save after removing key

        def update_button_text():
            for child in self.mode_frame.winfo_children():
                for button in child.winfo_children():
                    if isinstance(button, ttk.Button) and "Custom Mode" in button.cget("text"):
                        keys_text = ", ".join(self.key_bindings["custom"]["keys"]) or "No keys"
                        button.configure(text=f"Custom Mode ({keys_text})")
                        break

        ttk.Button(add_frame, text="Add Key", command=add_key).pack(side=tk.LEFT, padx=5)
        ttk.Button(frame, text="Remove Selected Key", command=remove_key).pack(fill="x", pady=5)
        ttk.Button(frame, text="Close", command=settings.destroy).pack(fill="x", pady=20)

    def open_activation_settings(self):
        settings = tk.Toplevel(self.root)
        settings.title("Activation Key Settings")
        settings.geometry("300x150")
        settings.resizable(False, False)
        settings.transient(self.root)
        settings.grab_set()

        # Center window
        settings.withdraw()
        main_x = self.root.winfo_rootx()
        main_y = self.root.winfo_rooty()
        main_width = self.root.winfo_width()
        settings_width = 300
        x = main_x + (main_width - settings_width) // 2
        y = main_y + 50
        settings.geometry(f"+{x}+{y}")
        settings.deiconify()

        frame = ttk.Frame(settings, padding="10")
        frame.pack(fill="both", expand=True)

        def validate_and_limit_entry(*args):
            if key_var.get():
                key_var.set(key_var.get()[-1:].lower())

        ttk.Label(frame, text="Activation Key:").grid(row=0, column=0, padx=5, pady=5)
        key_var = tk.StringVar(value=self.settings["activation_key"])
        key_var.trace('w', validate_and_limit_entry)
        key_entry = ttk.Entry(frame, textvariable=key_var, width=2)
        key_entry.grid(row=0, column=1, padx=5, pady=5)

        def save_settings():
            new_key = key_var.get().lower()
            if new_key:
                self.settings["activation_key"] = new_key
                self.save_settings()
                self.status_label.config(text=f"Status: Activation key set to '{new_key}'")
                self.update_instructions()
                settings.destroy()

        ttk.Button(frame, text="Save", command=save_settings).grid(row=1, column=0, columnspan=2, pady=20)

    def add_key_to_custom(self, key_var, key_list):
        """Helper method for custom mode key validation"""
        key = key_var.get().lower()
        if key and len(key) == 1 and key not in self.key_bindings["custom"]["keys"]:
            self.key_bindings["custom"]["keys"].append(key)
            key_list.insert(tk.END, key)
            key_var.set("")
            return True
        return False

    def spam_keys(self):
        activation_key = self.settings["activation_key"]
        while self.is_running and keyboard.is_pressed(activation_key):
            if not self.is_paused:
                try:
                    # Calculate delay based on mode
                    if self.use_random_delay:
                        delay = randfloat(self.delay_min / 1000, self.delay_max / 1000)
                    else:
                        delay = self.delay_fixed / 1000

                    if self.current_mode == "boss":
                        if self.key_bindings["boss"]["key1"]:
                            keyboard.send(self.key_bindings["boss"]["key1"])
                        if self.key_bindings["boss"]["key2"]:
                            keyboard.send(self.key_bindings["boss"]["key2"])
                    elif self.current_mode == "mob":
                        if self.key_bindings["mob"]["key1"]:
                            keyboard.send(self.key_bindings["mob"]["key1"])
                    elif self.current_mode == "custom":
                        for key in self.key_bindings["custom"]["keys"]:
                            keyboard.send(key)
                    time.sleep(delay)
                except Exception:
                    pass
            else:
                time.sleep(0.1)

    def update_status(self):
        if self.is_running:
            activation_key = self.settings["activation_key"]
            if keyboard.is_pressed(activation_key) and self.current_mode:
                if not self.is_paused:
                    if self.active_thread is None or not self.active_thread.is_alive():
                        self.active_thread = threading.Thread(target=self.spam_keys)
                        self.active_thread.start()
                        self.status_label.config(text="Status: Spamming...")
                elif self.status_label.cget("text") == "Status: Spamming...":
                    self.status_label.config(text="Status: PAUSED")
            elif self.status_label.cget("text") == "Status: Spamming...":
                self.status_label.config(text="Status: READY" if not self.is_paused else "Status: PAUSED")
                
            self.root.after(100, self.update_status)

    def update_instructions(self):
        instructions = f"""1. Select a mode above
2. Hold '{self.settings["activation_key"].upper()}' to spam skills
3. Use Pause/Resume button to pause
4. Click Exit or close window to quit"""
        self.instructions_label.config(text=instructions)

    def exit_program(self):
        self.is_running = False
        if self.active_thread and self.active_thread.is_alive():
            self.active_thread.join(timeout=1)
        self.save_settings()  # Save all settings before exit
        self.root.quit()
        sys.exit()

if __name__ == "__main__":
    root = tk.Tk()
    app = SkillSpammerGUI(root)
    root.protocol("WM_DELETE_WINDOW", app.exit_program)
    root.mainloop()
