# translator_project/translator_app/gui/tooltip.py
import tkinter as tk
import customtkinter as ctk

class Tooltip:
    def __init__(self, widget, text='위젯 정보'):
        self.widget = widget
        self.text = text
        self.tooltip_window = None
        self.widget.bind("<Enter>", self.enter, add="+")
        self.widget.bind("<Leave>", self.leave, add="+")
        self.widget.bind("<ButtonPress>", self.leave, add="+")

    def enter(self, event=None):
        if self.tooltip_window or not self.text: return
        try:
            x = self.widget.winfo_rootx() + self.widget.winfo_width() // 2
            y = self.widget.winfo_rooty() + self.widget.winfo_height() + 5
        except tk.TclError: 
            if hasattr(self.widget, 'master') and self.widget.master:
                try:
                    x = self.widget.master.winfo_rootx() + self.widget.winfo_x() + self.widget.winfo_width() // 2
                    y = self.widget.master.winfo_rooty() + self.widget.winfo_y() + self.widget.winfo_height() + 5
                except tk.TclError: x = event.x_root + 10; y = event.y_root + 10
            else: x = event.x_root + 10; y = event.y_root + 10
        self.tooltip_window = tk.Toplevel(self.widget)
        self.tooltip_window.wm_overrideredirect(True)
        current_mode = ctk.get_appearance_mode()
        bg_color = "#2E2E2E" if current_mode == "Dark" else "#FFFFE0" 
        fg_color = "#DCE4EE" if current_mode == "Dark" else "#333333" 
        border_color = "#4A4A4A" if current_mode == "Dark" else "#AAAAAA"
        self.tooltip_window.configure(bg=border_color) 
        label_frame = tk.Frame(self.tooltip_window, bg=bg_color) 
        label_frame.pack(padx=1, pady=1) 
        label_inner = tk.Label(label_frame, text=self.text, justify='left', background=bg_color, foreground=fg_color, font=("Arial", 9, "normal"))
        label_inner.pack(ipadx=3, ipady=3)
        self.tooltip_window.update_idletasks() 
        tooltip_width = self.tooltip_window.winfo_width()
        screen_width = self.widget.winfo_screenwidth()
        if x + tooltip_width > screen_width - 10: x = screen_width - tooltip_width - 10
        if x < 10: x = 10
        self.tooltip_window.wm_geometry(f"+{int(x)}+{int(y)}")

    def leave(self, event=None):
        if self.tooltip_window: self.tooltip_window.destroy()
        self.tooltip_window = None
    
    def update_text(self, new_text):
        self.text = new_text
        if self.tooltip_window and self.tooltip_window.winfo_exists():
            for child_frame in self.tooltip_window.winfo_children():
                if isinstance(child_frame, tk.Frame):
                    for child_label in child_frame.winfo_children():
                        if isinstance(child_label, tk.Label): child_label.configure(text=new_text); return