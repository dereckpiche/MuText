import tkinter as tk
from tkinter import filedialog, messagebox
import webbrowser
from datetime import datetime
import os


class LetterLock:
    def __init__(self, root):
        self.root = root
        self.root.title("LetterLock - HTML Editor")
        self.root.geometry("1200x800")
        
        # Default settings
        self.font_size = 24  # Increased font size
        self.default_open_folder = "./"
        self.current_file = None

        # Create text widget with requested styles
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
        file_menu.add_command(label="Exit", command=self.exit_editor)
        self.menu_bar.add_cascade(label="File", menu=file_menu)

        # Edit menu
        edit_menu = tk.Menu(self.menu_bar, tearoff=0)
        edit_menu.add_command(label="Undo", command=self.text_area.edit_undo)
        edit_menu.add_command(label="Redo", command=self.text_area.edit_redo)
        edit_menu.add_separator()
        edit_menu.add_command(label="Cut", command=lambda: self.root.focus_get().event_generate("<<Cut>>"))
        edit_menu.add_command(label="Copy", command=lambda: self.root.focus_get().event_generate("<<Copy>>"))
        edit_menu.add_command(label="Paste", command=lambda: self.root.focus_get().event_generate("<<Paste>>"))
        self.menu_bar.add_cascade(label="Edit", menu=edit_menu)

        # Render menu
        render_menu = tk.Menu(self.menu_bar, tearoff=0)
        render_menu.add_command(label="Render HTML", command=self.render_html, accelerator="Command+R")
        self.menu_bar.add_cascade(label="Render", menu=render_menu)

        # Help menu
        help_menu = tk.Menu(self.menu_bar, tearoff=0)
        help_menu.add_command(label="About", command=self.show_about)
        self.menu_bar.add_cascade(label="Help", menu=help_menu)

    def new_file(self):
        self.text_area.delete(1.0, tk.END)
        self.current_file = None
        self.root.title("New File - LetterLock")

    def open_file(self, event=None):
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

    def save_file(self, event=None):
        if self.current_file:
            with open(self.current_file, "w") as file:
                file.write(self.text_area.get(1.0, tk.END))
        else:
            self.save_as_file()

    def save_as_file(self):
        default_filename = datetime.now().strftime("Untitled_%Y-%m-%d.html")
        file_path = filedialog.asksaveasfilename(
            initialfile=default_filename,
            defaultextension=".html",
            filetypes=[("HTML Files", "*.html"), ("Text Files", "*.txt"), ("All Files", "*.*")]
        )
        if file_path:
            with open(file_path, "w") as file:
                file.write(self.text_area.get(1.0, tk.END))
            self.current_file = file_path
            self.root.title(f"{file_path} - LetterLock")

    def render_html(self, event=None):
        # Create a temporary HTML file with KaTeX support
        html_content = self.text_area.get(1.0, tk.END)
        katex_head = """
        <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.19/dist/katex.min.css" integrity="sha384-7lU0muIg/i1plk7MgygDUp3/bNRA65orrBub4/OSWHECgwEsY83HaS1x3bljA/XV" crossorigin="anonymous">

        <!-- The loading of KaTeX is deferred to speed up page rendering -->
        <script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.19/dist/katex.min.js" integrity="sha384-RdymN7NRJ+XoyeRY4185zXaxq9QWOOx3O7beyyrRK4KQZrPlCDQQpCu95FoCGPAE" crossorigin="anonymous"></script>

        <!-- To automatically render math in text elements, include the auto-render extension: -->
        <script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.19/dist/contrib/auto-render.min.js" integrity="sha384-hCXGrW6PitJEwbkoStFjeJxv+fSOOQKOPbJxSfM6G5sWZjAyWhXiTIIAmQqnlLlh" crossorigin="anonymous"
            onload="renderMathInElement(document.body);"></script>
        """
        full_html = f"<!DOCTYPE html><html><head>{katex_head}</head><body>{html_content}</body></html>"

        temp_file = "temp_render.html"
        with open(temp_file, "w") as file:
            file.write(full_html)

        # Open the temporary HTML file in the default browser
        webbrowser.open(f"file://{os.path.abspath(temp_file)}")

    def exit_editor(self):
        if messagebox.askokcancel("Exit", "Are you sure you want to exit?"):
            self.root.destroy()

    def show_about(self):
        messagebox.showinfo("About", "LetterLock - HTML Editor with KaTeX Support\nBuilt with Python and Tkinter")

    def increase_font_size(self, event=None):
        self.font_size += 2
        self.text_area.config(font=("Courier New", self.font_size))

    def decrease_font_size(self, event=None):
        if self.font_size > 6:  # Prevent the font from becoming too small
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
