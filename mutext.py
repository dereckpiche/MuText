import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog
import webbrowser
import os
import sys
import threading
import json
from http.server import HTTPServer, BaseHTTPRequestHandler
from datetime import datetime
import tkinter.font as tkfont


class MuText:
    """
    MuText - HTML Editor with Additional Features:
    1) Default proposed name when saving is the current date.
    2) Do not open the last file by default when opening the app. Start with a blank editor.
    3) Ask for confirmation when opening a recent file.
    4) Dark mode setting (background dark grey, not black).
    5) Shortcut for "Save As" (Command+Shift+S).
    6) Optional autosave with configurable interval.
    7) Prompt when closing unsaved files.
    """

    CONFIG_NAME = "config.json"

    def __init__(self, root):
        self.root = root
        self.root.title("MuText - HTML Editor")
        self.root.geometry("1200x800")

        # Determine the path to store the config file
        script_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
        self.config_file_path = os.path.join(script_dir, self.CONFIG_NAME)

        # Default settings
        self.current_font = "Times New Roman"
        self.font_size = 24
        self.default_open_folder = "./"
        self.current_file = None
        self.recent_files = []
        self.server_thread = None
        self.live_preview_port = 8000
        self.dark_mode = False  # Dark mode is off by default
        self.autosave_enabled = True
        self.autosave_interval = 5  # Autosave every 60 seconds
        self.autosave_file_path = os.path.join(script_dir, "autosave.txt")  # Temporary autosave file
        self.unsaved_changes = False

        # Load settings from config file
        self.load_config()

        # Create text widget
        self.text_area = tk.Text(
            self.root,
            wrap="word",
            undo=True,
            font=(self.current_font, self.font_size),
            insertwidth=4,
            tabs=("1c",),  # Single tuple for tab size
            bd=0,  # Remove border
            highlightthickness=0  # Remove focus highlight border
        )

        self.text_area.pack(fill="both", expand=True, padx=0, pady=0)
        self.text_area.configure(insertofftime=0)  # Prevent cursor blinking
        self.apply_theme()

        # Detect unsaved changes
        self.text_area.bind("<Key>", self.mark_unsaved)

        # Bind keyboard shortcuts
        self.text_area.bind_all("<Command-o>", self.open_file)
        self.text_area.bind_all("<Command-s>", self.save_file)
        self.text_area.bind_all("<Command-Shift-S>", self.save_as_file)
        self.text_area.bind_all("<Command-r>", self.render_html)
        self.text_area.bind_all("<Command-minus>", self.decrease_font_size)
        self.text_area.bind_all("<Command-+>", self.increase_font_size)
        self.text_area.bind_all("<Command-equal>", self.increase_font_size)  # For Cmd+=
        self.text_area.bind_all("<Command-0>", self.reset_font_size)
        self.text_area.bind_all("<Command-n>", self.new_file)
        self.root.protocol("WM_DELETE_WINDOW", self.exit_editor)

        # Create menu bar
        self.menu_bar = tk.Menu(self.root)
        self.root.config(menu=self.menu_bar)

        # File menu
        file_menu = tk.Menu(self.menu_bar, tearoff=0)
        file_menu.add_command(label="New", command=self.new_file, accelerator="Command+N")
        file_menu.add_command(label="Open", command=self.open_file, accelerator="Command+O")
        file_menu.add_command(label="Save", command=self.save_file, accelerator="Command+S")
        file_menu.add_command(label="Save As", command=self.save_as_file, accelerator="Command+Shift+S")
        file_menu.add_separator()
        file_menu.add_command(label="Change Default Open Folder", command=self.change_open_folder)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.exit_editor)
        self.menu_bar.add_cascade(label="File", menu=file_menu)

        # Recent Files menu
        self.recent_files_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.update_recent_files_menu()
        self.menu_bar.add_cascade(label="Recent Files", menu=self.recent_files_menu)

        # View menu
        view_menu = tk.Menu(self.menu_bar, tearoff=0)
        view_menu.add_command(label="Toggle Dark Mode", command=self.toggle_dark_mode)
        self.menu_bar.add_cascade(label="View", menu=view_menu)

        # Autosave menu
        autosave_menu = tk.Menu(self.menu_bar, tearoff=0)
        autosave_menu.add_command(label="Enable Autosave", command=self.enable_autosave)
        autosave_menu.add_command(label="Disable Autosave", command=self.disable_autosave)
        autosave_menu.add_command(label="Set Autosave Interval", command=self.set_autosave_interval)
        self.menu_bar.add_cascade(label="Autosave", menu=autosave_menu)

        # Render menu
        render_menu = tk.Menu(self.menu_bar, tearoff=0)
        render_menu.add_command(label="Render HTML", command=self.render_html, accelerator="Command+R")
        self.menu_bar.add_cascade(label="Render", menu=render_menu)

        # Help menu
        help_menu = tk.Menu(self.menu_bar, tearoff=0)
        help_menu.add_command(label="About", command=self.show_about)
        self.menu_bar.add_cascade(label="Help", menu=help_menu)

        # Add Font menu
        font_menu = tk.Menu(self.menu_bar, tearoff=0)
        font_menu.add_command(label="Choose Font", command=self.choose_font)
        self.menu_bar.add_cascade(label="Font", menu=font_menu) 

        
        self.text_area.config(font=(self.current_font, self.font_size))

        # Start autosave if enabled
        if self.autosave_enabled:
            self.start_autosave()

    def load_config(self):
        if os.path.exists(self.config_file_path):
            try:
                with open(self.config_file_path, "r") as config_file:
                    config = json.load(config_file)
                    self.default_open_folder = config.get("default_open_folder", "./")
                    self.recent_files = config.get("recent_files", [])
                    self.dark_mode = config.get("dark_mode", False)
                    self.autosave_enabled = config.get("autosave_enabled", False)
                    self.autosave_interval = config.get("autosave_interval", 60)
            except json.JSONDecodeError:
                self.default_open_folder = "./"
                self.recent_files = []
                self.dark_mode = False
                self.autosave_enabled = False
                self.autosave_interval = 60
        else:
            self.save_config()

    def save_config(self):
        config = {
            "default_open_folder": self.default_open_folder,
            "recent_files": self.recent_files[:10],
            "dark_mode": self.dark_mode,
            "autosave_enabled": self.autosave_enabled,
            "autosave_interval": self.autosave_interval,
        }
        with open(self.config_file_path, "w") as config_file:
            json.dump(config, config_file)

    def mark_unsaved(self, event=None):
        self.unsaved_changes = True

    def enable_autosave(self):
        self.autosave_enabled = True
        self.save_config()
        self.start_autosave()

    def disable_autosave(self):
        self.autosave_enabled = False
        self.save_config()

    def set_autosave_interval(self):
        interval = simpledialog.askinteger("Set Autosave Interval", "Enter interval in seconds:", minvalue=1)
        if interval:
            self.autosave_interval = interval
            self.save_config()

    def autosave(self):
        if self.autosave_enabled:
            if self.current_file:
                try:
                    with open(self.current_file, "w", encoding="utf-8") as file:
                        file.write(self.text_area.get(1.0, tk.END))
                except Exception as e:
                    print(f"Autosave failed: {e}")
            else:
                try:
                    with open(self.autosave_file_path, "w", encoding="utf-8") as file:
                        file.write(self.text_area.get(1.0, tk.END))
                except Exception as e:
                    print(f"Autosave failed: {e}")
            self.root.after(self.autosave_interval * 1000, self.autosave)

    def start_autosave(self):
        self.autosave()

    def exit_editor(self):
        if self.unsaved_changes:
            if not messagebox.askyesno("Unsaved Changes", "You have unsaved changes. Do you want to exit without saving?"):
                return
        self.save_config()
        self.root.destroy()

    def update_recent_files_menu(self):
        self.recent_files_menu.delete(0, tk.END)
        if self.recent_files:
            for file in self.recent_files:
                self.recent_files_menu.add_command(
                    label=file,
                    command=lambda f=file: self.confirm_and_open_recent(f)
                )
        else:
            self.recent_files_menu.add_command(label="No recent files", state=tk.DISABLED)

    def add_to_recent_files(self, file_path):
        if file_path in self.recent_files:
            self.recent_files.remove(file_path)
        self.recent_files.insert(0, file_path)
        self.update_recent_files_menu()
        self.save_config()

    def new_file(self, event=None):
        self.text_area.delete(1.0, tk.END)
        self.current_file = None
        self.root.title("New File - MuText")

    def open_file(self, event=None, file_path=None):
        if not file_path:
            file_path = filedialog.askopenfilename(
                initialdir=self.default_open_folder,
                filetypes=[("Text Files", "*.txt"), ("HTML Files", "*.html"), ("All Files", "*.*")]
            )
        if file_path:
            try:
                with open(file_path, "r", encoding="utf-8") as file:
                    self.text_area.delete(1.0, tk.END)
                    self.text_area.insert(1.0, file.read())
                self.current_file = file_path
                self.root.title(f"{os.path.basename(file_path)} - MuText")
                self.add_to_recent_files(file_path)
            except Exception as e:
                messagebox.showerror("Error", f"Could not open file:\n{e}")

    def confirm_and_open_recent(self, file_path):
        if messagebox.askyesno("Confirm", f"Open recent file:\n{file_path}?"):
            self.open_file(file_path=file_path)

    def save_file(self, event=None):
        if self.current_file:
            try:
                with open(self.current_file, "w", encoding="utf-8") as file:
                    file.write(self.text_area.get(1.0, tk.END))
                self.root.title(f"{os.path.basename(self.current_file)} - MuText")
                self.add_to_recent_files(self.current_file)
            except Exception as e:
                messagebox.showerror("Error", f"Could not save file:\n{e}")
        else:
            self.save_as_file()

    def save_as_file(self, event=None):
        default_filename = datetime.now().strftime("%Y-%m-%d.txt")
        file_path = filedialog.asksaveasfilename(
            initialdir=self.default_open_folder,
            initialfile=default_filename,
            defaultextension=".txt",
            filetypes=[("Text Files", "*.txt"), ("HTML Files", "*.html"), ("All Files", "*.*")]
        )
        if file_path:
            try:
                with open(file_path, "w", encoding="utf-8") as file:
                    file.write(self.text_area.get(1.0, tk.END))
                self.current_file = file_path
                self.root.title(f"{os.path.basename(file_path)} - MuText")
                self.add_to_recent_files(file_path)
            except Exception as e:
                messagebox.showerror("Error", f"Could not save file:\n{e}")

    def change_open_folder(self):
        folder = filedialog.askdirectory(initialdir=self.default_open_folder)
        if folder:
            self.default_open_folder = folder
            messagebox.showinfo("Folder Changed", f"Default open folder set to:\n{folder}")
            self.save_config()

    def toggle_dark_mode(self):
        self.dark_mode = not self.dark_mode
        self.apply_theme()
        self.save_config()

    def apply_theme(self):
        if self.dark_mode:
            self.text_area.config(bg="#111212", fg="white", insertbackground="white")
        else:
            self.text_area.config(bg="white", fg="black", insertbackground="black")

    def render_html(self, event=None):
        """
        Render the current text in a local web server with KaTeX support, then open it in a browser.
        """
        class LivePreviewHandler(BaseHTTPRequestHandler):
            def do_GET(self):
                self.send_response(200)
                self.send_header("Content-type", "text/html")
                self.end_headers()
                html_content = self.server.editor_instance.text_area.get(1.0, tk.END)
                katex_head = """
                <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.19/dist/katex.min.css">
                <script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.19/dist/katex.min.js"></script>
                <script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.19/dist/contrib/auto-render.min.js"
                        onload="renderMathInElement(document.body);"></script>
                """
                full_html = f"<!DOCTYPE html><html><head>{katex_head}</head><body>{html_content}</body></html>"
                self.wfile.write(full_html.encode("utf-8"))

        def start_server():
            server = HTTPServer(("localhost", self.live_preview_port), LivePreviewHandler)
            server.editor_instance = self
            server.serve_forever()

        if not self.server_thread or not self.server_thread.is_alive():
            self.server_thread = threading.Thread(target=start_server, daemon=True)
            self.server_thread.start()

        webbrowser.open(f"http://localhost:{self.live_preview_port}")

    def exit_editor(self):
            if self.unsaved_changes:
                choice = messagebox.askyesnocancel(
                    "Unsaved Changes",
                    "You have unsaved changes. Do you want to save them before exiting?"
                )
                if choice:  # Yes, save changes
                    self.save_file()
                    self.root.destroy()
                elif choice is None:  # Cancel
                    return
            self.root.destroy()

    def show_about(self):
        messagebox.showinfo(
            "About",
            "MuText - HTML Editor with KaTeX Support\n"
            "Built with Python and Tkinter\n"
            "Features:\n"
            " - KaTeX rendering\n"
            " - Recent files with confirmation\n"
            " - Configurable dark mode\n"
            " - Config stored in JSON"
        )

    def increase_font_size(self, event=None):
        self.font_size += 2
        self.text_area.config(font=(self.current_font, self.font_size))

    def decrease_font_size(self, event=None):
        if self.font_size > 6:
            self.font_size -= 2
            self.text_area.config(font=(self.current_font, self.font_size))

    def reset_font_size(self, event=None):
        self.font_size = 16
        self.text_area.config(font=(self.current_font, self.font_size))

    def choose_font(self):
        """
        Open a font selection window where users can preview and select a font.
        """
        def preview_font(event):
            # Get the selected font from the listbox and update the preview label
            selected_font = font_listbox.get(font_listbox.curselection())
            preview_label.config(text=f"Preview: {selected_font}", font=(selected_font, 16))

        def apply_font():
            # Set the selected font as the current font and apply it to the text area
            self.current_font = font_listbox.get(font_listbox.curselection())
            self.text_area.config(font=(self.current_font, self.font_size))
            font_window.destroy()

        # Create the font selection window
        font_window = tk.Toplevel(self.root)
        font_window.title("Choose Font")
        font_window.geometry("400x300")

        # Listbox to display fonts
        fonts = sorted(tkfont.families())
        font_listbox = tk.Listbox(font_window, height=15, exportselection=False)
        for font in fonts:
            font_listbox.insert(tk.END, font)
        font_listbox.pack(fill="both", expand=True, padx=10, pady=10)
        font_listbox.bind("<<ListboxSelect>>", preview_font)

        # Preview label to show selected font
        preview_label = tk.Label(font_window, text=f"Preview: {self.current_font}", font=(self.current_font, 16))
        preview_label.pack(pady=10)

        # Buttons to apply or close the font selection window
        button_frame = tk.Frame(font_window)
        button_frame.pack(pady=10)
        apply_button = tk.Button(button_frame, text="Apply Font", command=apply_font)
        apply_button.pack(side=tk.LEFT, padx=5)
        close_button = tk.Button(button_frame, text="Close", command=font_window.destroy)
        close_button.pack(side=tk.LEFT, padx=5)



if __name__ == "__main__":
    root = tk.Tk()
    editor = MuText(root)
    root.attributes("-fullscreen", True)
    root.mainloop()

