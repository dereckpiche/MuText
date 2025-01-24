import tkinter as tk
from cefpython3 import cefpython as cef
import sys
import os
import threading

HTML_TEMPLATE = r"""
<!DOCTYPE html>
<html>
<head>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.19/dist/katex.min.css">
    <script src="https://cdn.jsdelivr.net/npm/katex@0.16.19/dist/katex.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/katex@0.16.19/dist/contrib/auto-render.min.js"
            onload="renderMathInElement(document.body);"></script>
</head>
<body>
    <h3>KaTeX Render Preview</h3>
    <p>You wrote:</p>
    <div id="mathArea">%s</div>
</body>
</html>
"""

class MainApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("MuText w/ Embedded Chromium")
        self.geometry("1200x800")

        # A frame to hold both the Text editor and the browser preview side by side
        container = tk.PanedWindow(self, orient=tk.HORIZONTAL, sashrelief=tk.RAISED)
        container.pack(fill=tk.BOTH, expand=True)

        # Left side: a text widget
        text_frame = tk.Frame(container)
        self.text_editor = tk.Text(text_frame, wrap="word")
        self.text_editor.pack(fill=tk.BOTH, expand=True)
        update_btn = tk.Button(text_frame, text="Render KaTeX", command=self.update_preview)
        update_btn.pack()
        container.add(text_frame, width=600)

        # Right side: a frame to hold the CEF browser
        self.browser_frame = tk.Frame(container, bg="gray")
        container.add(self.browser_frame, width=600)

        # Initialize CEF now (in main thread)
        self._browser = None
        settings = {}
        cef.Initialize(settings=settings)
        
        # Embed the browser. We will do it after idle, so that self.browser_frame is ready
        self.after(100, self.embed_browser)

        # Periodically let CEF do its work
        self._do_loop()

    def embed_browser(self):
        # Create window info so that CEF knows to embed in our Tk frame
        window_info = cef.WindowInfo()
        window_info.SetAsChild(self.browser_frame.winfo_id(),
                               [0, 0, self.browser_frame.winfo_width(), self.browser_frame.winfo_height()])
        self._browser = cef.CreateBrowserSync(window_info,
                                              url="data:text/html,<h3>Waiting for first render...</h3>")

        # Make sure we handle resizing
        self.browser_frame.bind("<Configure>", self.on_mainframe_configure)

    def on_mainframe_configure(self, event):
        if self._browser:
            # Update the browser window size to match browser_frame
            width = event.width
            height = event.height
            # If width/height is 0 or negative, skip to avoid errors
            if width < 10 or height < 10:
                return
            self._browser.SetBounds(0, 0, width, height)
            self._browser.WasResized()

    def update_preview(self):
        if not self._browser:
            return
        raw_text = self.text_editor.get("1.0", tk.END)
        # Escape any special characters if you like, or just insert as-is
        html_data = HTML_TEMPLATE % raw_text

        # 'LoadString' is a CEF call that can load raw HTML
        self._browser.GetMainFrame().LoadString(html_data, "about:blank")

    def _do_loop(self):
        """ Periodically tell CEF to do a single iteration of its message loop. """
        cef.MessageLoopWork()
        self.after(10, self._do_loop)  # schedule the next iteration

    def on_close(self):
        cef.Shutdown()
        self.destroy()

if __name__ == "__main__":
    app = MainApp()
    app.protocol("WM_DELETE_WINDOW", app.on_close)
    app.mainloop() 