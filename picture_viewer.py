import os
import sys
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog, Toplevel, Scale, Label, Button, IntVar
from PIL import Image, ImageTk, ImageGrab
import winreg

class PictureViewer(tk.Tk):
    def __init__(self, image_path=None):
        super().__init__()
        self.overrideredirect(True)  # Borderless window
        self.attributes('-topmost', True)  # Always on top

        self.canvas = tk.Canvas(self, bg='black')
        self.canvas.pack(fill=tk.BOTH, expand=True)

        self.image_label = tk.Label(self.canvas, bg='black')
        self.image_label.pack()

        self.bind('<Escape>', lambda e: self.destroy())  # Close on Escape
        self.bind('<ButtonPress-1>', self.start_move)
        self.bind('<B1-Motion>', self.do_move)
        self.bind('<Button-3>', self.show_context_menu)  # Right-click to show context menu
        self.bind('<MouseWheel>', self.zoom)

        self.create_context_menu()
        self.img = None
        self.zoom_factor = 1.0
        self.last_image_path = None
        self.zoom_speed = 1.1
        self.save_quality = 95
        self.load_last_image = False

        if image_path:
            self.display_image(image_path)
        elif self.load_last_image and self.last_image_path:
            self.display_image(self.last_image_path)
        elif self.check_clipboard_for_image():
            if messagebox.askyesno("Clipboard Image", "There is an image in the clipboard. Do you want to open it?"):
                self.load_image_from_clipboard()
            else:
                self.load_image_from_file()
        else:
            self.load_image_from_file()

    def create_context_menu(self):
        self.context_menu = tk.Menu(self, tearoff=0)
        self.context_menu.add_command(label="Save Image", command=self.save_image)
        
        open_submenu = tk.Menu(self.context_menu, tearoff=0)
        open_submenu.add_command(label="From File", command=self.load_image_from_file)
        open_submenu.add_command(label="From Clipboard", command=self.load_image_from_clipboard)
        self.context_menu.add_cascade(label="Open Image", menu=open_submenu)
        
        convert_submenu = tk.Menu(self.context_menu, tearoff=0)
        for fmt in ['JPEG', 'PNG', 'BMP', 'GIF']:
            convert_submenu.add_command(label=fmt, command=lambda f=fmt: self.convert_image(f))
        self.context_menu.add_cascade(label="Convert To", menu=convert_submenu)
        
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Settings", command=self.open_settings)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Close", command=self.destroy)

    def show_context_menu(self, event):
        self.context_menu.tk_popup(event.x_root, event.y_root)

    def check_clipboard_for_image(self):
        try:
            image = ImageGrab.grabclipboard()
            if isinstance(image, Image.Image):
                self.clipboard_image = image
                return True
            return False
        except Exception as e:
            print(f"Error checking clipboard: {e}")
            return False

    def load_image_from_clipboard(self):
        self.display_image(self.clipboard_image)

    def load_image_from_file(self):
        file_path = filedialog.askopenfilename(
            filetypes=[
                ("Image files", "*.jpg *.jpeg *.png *.bmp *.gif"),
                ("All files", "*.*")
            ]
        )
        if file_path:
            self.display_image(file_path)

    def display_image(self, image_source):
        if isinstance(image_source, str):
            self.image = Image.open(image_source)
            self.last_image_path = image_source
        else:
            self.image = image_source

        self.zoom_factor = 1.0
        self.update_image()

    def update_image(self):
        width, height = int(self.image.width * self.zoom_factor), int(self.image.height * self.zoom_factor)
        self.img = ImageTk.PhotoImage(self.image.resize((width, height), Image.ANTIALIAS))
        self.image_label.config(image=self.img)
        self.image_label.place(x=0, y=0, anchor='nw')
        self.image_label.config(cursor="fleur" if self.zoom_factor > 1 else "")

    def zoom(self, event):
        if event.delta > 0:
            self.zoom_factor *= self.zoom_speed
        else:
            self.zoom_factor /= self.zoom_speed
        self.update_image()

    def start_move(self, event):
        self.x = event.x
        self.y = event.y

    def do_move(self, event):
        if self.zoom_factor == 1.0:
            x = (event.x_root - self.x)
            y = (event.y_root - self.y)
            self.geometry(f"+{x}+{y}")
        else:
            self.image_label.place(x=event.x_root - self.x, y=event.y_root - self.y)

    def save_image(self):
        file_path = filedialog.asksaveasfilename(
            defaultextension=".jpg",
            filetypes=[
                ("JPEG files", "*.jpg"),
                ("PNG files", "*.png"),
                ("BMP files", "*.bmp"),
                ("GIF files", "*.gif"),
                ("All files", "*.*")
            ]
        )
        if file_path:
            self.image.save(file_path, quality=self.save_quality)

    def convert_image(self, fmt):
        file_path = filedialog.asksaveasfilename(defaultextension=f".{fmt.lower()}",
            filetypes=[
                (f"{fmt} files", f"*.{fmt.lower()}"),
                ("All files", "*.*")
            ]
        )
        if file_path:
            self.image.save(file_path, format=fmt, quality=self.save_quality if fmt == 'JPEG' else None)

    def open_settings(self):
        settings_window = Toplevel(self)
        settings_window.title("Settings")
        settings_window.geometry("300x200")
        
        Label(settings_window, text="Zoom Speed:").pack(pady=5)
        zoom_speed_scale = Scale(settings_window, from_=1.01, to=2.0, resolution=0.01, orient=tk.HORIZONTAL)
        zoom_speed_scale.set(self.zoom_speed)
        zoom_speed_scale.pack(pady=5)

        Label(settings_window, text="Save Image Quality:").pack(pady=5)
        save_quality_scale = Scale(settings_window, from_=10, to=100, orient=tk.HORIZONTAL)
        save_quality_scale.set(self.save_quality)
        save_quality_scale.pack(pady=5)

        load_last_image_var = IntVar()
        load_last_image_var.set(1 if self.load_last_image else 0)
        load_last_image_check = tk.Checkbutton(settings_window, text="Load Last Image", variable=load_last_image_var)
        load_last_image_check.pack(pady=5)

        def save_settings():
            self.zoom_speed = zoom_speed_scale.get()
            self.save_quality = save_quality_scale.get()
            self.load_last_image = bool(load_last_image_var.get())
            settings_window.destroy()

        Button(settings_window, text="Save", command=save_settings).pack(pady=20)

def add_to_context_menu():
    exe_path = os.path.abspath(sys.argv[0])
    command = f'"{exe_path}" "%1"'

    try:
        key = winreg.CreateKey(winreg.HKEY_CLASSES_ROOT, r'*\shell\OpenWithPictureViewer')
        winreg.SetValue(key, '', winreg.REG_SZ, 'Open with Picture Viewer')
        key1 = winreg.CreateKey(key, r'command')
        winreg.SetValue(key1, '', winreg.REG_SZ, command)
        winreg.CloseKey(key)
        winreg.CloseKey(key1)
        print("Successfully added to context menu.")
    except Exception as e:
        print(f"Failed to add to context menu: {e}")

def remove_from_context_menu():
    try:
        winreg.DeleteKey(winreg.HKEY_CLASSES_ROOT, r'*\shell\OpenWithPictureViewer\command')
        winreg.DeleteKey(winreg.HKEY_CLASSES_ROOT, r'*\shell\OpenWithPictureViewer')
        print("Successfully removed from context menu.")
    except Exception as e:
        print(f"Failed to remove from context menu: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == 'add':
            add_to_context_menu()
        elif sys.argv[1] == 'remove':
            remove_from_context_menu()
        else:
            image_path = sys.argv[1]
            viewer = PictureViewer(image_path)
            viewer.mainloop()
    else:
        viewer = PictureViewer()
        viewer.mainloop()
