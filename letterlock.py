import tkinter as tk
from tkinter import filedialog, messagebox
import webbrowser
import os
import threading
import json
from http.server import HTTPServer, BaseHTTPRequestHandler


class LetterLock:
    CONFIG_FILE = "config.json"

    def __init__(self, root):
        self.root = root
        self.root.title("LetterLock - HTML Editor")
        self.root.geometry("1200x800")
        
        # Default settings
        self.font_size = 24
        self.default_open_folder = "./"
        self.current_file = None
        self.recent_files = []
        self.server_thread = None
        self.live_preview_port = 8000

        # Load settings from config file
        self.load_config()

        # Create text widget
        self.text_area = tk.Text(
            self.root, wrap="word", undo=True,
            bg="white", fg="black", insertbackground="black",
            font=("Courier New", self.font_size), insertwidth=4, tabs=("1c")
        )
        self.text_area.pack(fill="both", expand=True, padx=5, pady=5)
        self.text_area.configure(insertofftime=0)  # Prevent cursor flashing

        # Bind keyboard shortcuts
        self.root.bind("<Command-o>", self.open_file)
        self.root.bind("<Command-s>", self.save_file)
        self.root.bind("<Command-r>", self.render_html)
        self.root.bind("<Command-minus>", self.decrease_font_size)
        self.root.bind("<Command-+>", self.increase_font_size)
        self.root.bind("<Command-equal>", self.increase_font_size)  # Support for Command += key
        self.root.bind("<Command-0>", self.reset_font_size)

        # Create menu bar
        self.menu_bar = tk.Menu(self.root)
        self.root.config(menu=self.menu_bar)

        # File menu
        file_menu = tk.Menu(self.menu_bar, tearoff=0)
        file_menu.add_command(label="New", command=self.new_file)
        file_menu.add_command(label="Open", command=self.open_file, accelerator="Command+O")
        file_menu.add_command(label="Save", command=self.save_file, accelerator="Command+S")
        file_menu.add_command(label="Save As", command=self.save_as_file)
        file_menu.add_separator()
        file_menu.add_command(label="Change Default Open Folder", command=self.change_open_folder)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.exit_editor)
        self.menu_bar.add_cascade(label="File", menu=file_menu)

        # Recent Files menu
        self.recent_files_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.update_recent_files_menu()
        self.menu_bar.add_cascade(label="Recent Files", menu=self.recent_files_menu)

        # Render menu
        render_menu = tk.Menu(self.menu_bar, tearoff=0)
        render_menu.add_command(label="Render HTML", command=self.render_html, accelerator="Command+R")
        self.menu_bar.add_cascade(label="Render", menu=render_menu)

        # Help menu
        help_menu = tk.Menu(self.menu_bar, tearoff=0)
        help_menu.add_command(label="About", command=self.show_about)
        self.menu_bar.add_cascade(label="Help", menu=help_menu)

        # Open the last file, if it exists
        if self.current_file:
            self.open_file(file_path=self.current_file)

    def load_config(self):
        """Load configuration from the config file."""
        if os.path.exists(self.CONFIG_FILE):
            with open(self.CONFIG_FILE, "r") as config_file:
                config = json.load(config_file)
                self.default_open_folder = config.get("default_open_folder", "./")
                self.current_file = config.get("last_opened_file", None)
                self.recent_files = config.get("recent_files", [])
        else:
            self.default_open_folder = "./"
            self.current_file = None
            self.recent_files = []

    def save_config(self):
        """Save configuration to the config file."""
        config = {
            "default_open_folder": self.default_open_folder,
            "last_opened_file": self.current_file,
            "recent_files": self.recent_files[:10]  # Limit to the last 10 files
        }
        with open(self.CONFIG_FILE, "w") as config_file:
            json.dump(config, config_file)

    def update_recent_files_menu(self):
        """Update the Recent Files menu."""
        self.recent_files_menu.delete(0, tk.END)
        for file in self.recent_files:
            self.recent_files_menu.add_command(
                label=file,
                command=lambda f=file: self.open_file(file_path=f)
            )
        if not self.recent_files:
            self.recent_files_menu.add_command(label="No recent files", state=tk.DISABLED)

    def add_to_recent_files(self, file_path):
        """Add a file to the recent files list."""
        if file_path in self.recent_files:
            self.recent_files.remove(file_path)
        self.recent_files.insert(0, file_path)
        self.update_recent_files_menu()
        self.save_config()

    def new_file(self):
        self.text_area.delete(1.0, tk.END)
        self.current_file = None
        self.root.title("New File - LetterLock")

    def open_file(self, event=None, file_path=None):
        if not file_path:
            file_path = filedialog.askopenfilename(
                initialdir=self.default_open_folder,
                filetypes=[("HTML Files", "*.html"), ("Text Files", "*.txt"), ("All Files", "*.*")]
            )
        if file_path:
            with open(file_path, "r") as file:
                self.text_area.delete(1.0, tk.END)
                self.text_area.insert(1.0, file.read())
            self.current_file = file_path
            self.root.title(f"{file_path} - LetterLock")
            self.add_to_recent_files(file_path)

    def save_file(self, event=None):
        if self.current_file:
            with open(self.current_file, "w") as file:
                file.write(self.text_area.get(1.0, tk.END))
        else:
            self.save_as_file()

    def save_as_file(self):
        file_path = filedialog.asksaveasfilename(
            initialdir=self.default_open_folder,
            defaultextension=".html",
            filetypes=[("HTML Files", "*.html"), ("Text Files", "*.txt"), ("All Files", "*.*")]
        )
        if file_path:
            with open(file_path, "w") as file:
                file.write(self.text_area.get(1.0, tk.END))
            self.current_file = file_path
            self.root.title(f"{file_path} - LetterLock")
            self.add_to_recent_files(file_path)

    def change_open_folder(self):
        folder = filedialog.askdirectory(initialdir=self.default_open_folder)
        if folder:
            self.default_open_folder = folder
            messagebox.showinfo("Folder Changed", f"Default open folder set to:\n{folder}")
            self.save_config()

    def render_html(self, event=None):
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
            server.editor_instance = self  # Pass instance to handler
            server.serve_forever()

        if not self.server_thread or not self.server_thread.is_alive():
            self.server_thread = threading.Thread(target=start_server, daemon=True)
            self.server_thread.start()

        webbrowser.open(f"http://localhost:{self.live_preview_port}")

    def exit_editor(self):
        if messagebox.askokcancel("Exit", "Are you sure you want to exit?"):
            self.save_config()
            self.root.destroy()

    def show_about(self):
        messagebox.showinfo("About", "LetterLock - HTML Editor with KaTeX Support\nBuilt with Python and Tkinter")

    def increase_font_size(self, event=None):
        self.font_size += 2
        self.text_area.config(font=("Courier New", self.font_size))

    def decrease_font_size(self, event=None):
        if self.font_size > 6:
            self.font_size -= 2
            self.text_area.config(font=("Courier New", self.font_size))


    def reset_font_size(self, event=None):
        self.font_size = 16
        self.text_area.config(font=("Courier New", self.font_size))


if __name__ == "__main__":
    root = tk.Tk()
    editor = LetterLock(root)
    root.attributes("-fullscreen", True)  # Open in fullscreen mode
    root.mainloop()
