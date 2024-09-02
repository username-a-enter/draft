import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
import fitz  # PyMuPDF
import io
import threading
import hashlib

class PDFCropperGUI:
    def __init__(self, master):
        self.master = master
        self.master.title("PDF Image Extractor")
        self.master.geometry("800x600")

        self.pdf_path = None
        self.current_page = 0
        self.total_pages = 0
        self.crop_coords = []
        self.zoom_factor = 1.0
        self.temp_rect = None
        self.selection_rectangles = []
        self.doc = None

        self.setup_ui()

    def setup_ui(self):
        # Create a frame to hold the canvas and scrollbars
        self.frame = tk.Frame(self.master)
        self.frame.pack(fill=tk.BOTH, expand=True)

        # Create horizontal and vertical scrollbars
        self.h_scrollbar = tk.Scrollbar(self.frame, orient=tk.HORIZONTAL)
        self.h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        self.v_scrollbar = tk.Scrollbar(self.frame)
        self.v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Create the canvas with scrollbars
        self.canvas = tk.Canvas(self.frame, bg="white", 
                                xscrollcommand=self.h_scrollbar.set,
                                yscrollcommand=self.v_scrollbar.set)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Configure the scrollbars
        self.h_scrollbar.config(command=self.canvas.xview)
        self.v_scrollbar.config(command=self.canvas.yview)

        self.canvas.bind("<ButtonPress-1>", self.on_press)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)
        self.canvas.bind("<MouseWheel>", self.on_mousewheel)
        self.canvas.bind("<Shift-MouseWheel>", self.on_shift_mousewheel)
        self.canvas.bind("<Control-MouseWheel>", self.on_zoom)
        self.canvas.bind("<Button-3>", self.on_right_click)

        button_frame = tk.Frame(self.master)
        button_frame.pack(fill=tk.X)

        tk.Button(button_frame, text="Open PDF", command=self.open_pdf).pack(side=tk.LEFT)


        prev_page_button = tk.Button(button_frame, text="Previous Page", command=self.prev_page)
        prev_page_button.pack(side=tk.LEFT)
        prev_page_button.bind("<Left>", lambda event: self.prev_page())
        prev_page_button.bind("<Prior>", lambda event: self.prev_page())
        next_page_button = tk.Button(button_frame, text="Next Page", command=self.next_page)
        next_page_button.pack(side=tk.LEFT)
        next_page_button.bind("<Right>", lambda event: self.next_page())
        next_page_button.bind("<Next>", lambda event: self.next_page())
        tk.Button(button_frame, text="Extract Images", command=self.extract_images).pack(side=tk.LEFT)
        tk.Button(button_frame, text="Clear Selections", command=self.clear_selections).pack(side=tk.LEFT)

        # Add page navigation input and indicators
        self.page_var = tk.StringVar()
        self.page_entry = tk.Entry(button_frame, textvariable=self.page_var, width=5)
        self.page_entry.pack(side=tk.LEFT)
        self.page_entry.bind("<Return>", lambda event: self.go_to_page())
        tk.Button(button_frame, text="Go to Page", command=self.go_to_page).pack(side=tk.LEFT)
        
        self.page_indicator = tk.Label(button_frame, text="Page: 0 / 0")
        self.page_indicator.pack(side=tk.LEFT)

        # Bind Page Up and Page Down keys to the main window
        self.master.bind("<Prior>", lambda event: self.prev_page())
        self.master.bind("<Next>", lambda event: self.next_page())

    def open_pdf(self):
        self.pdf_path = filedialog.askopenfilename(filetypes=[("PDF files", "*.pdf")])
        if self.pdf_path:
            self.clear_everything()
            self.doc = fitz.open(self.pdf_path)
            self.total_pages = self.doc.page_count
            self.current_page = 0
            self.update_page_indicator()
            self.load_page()

    def clear_everything(self):
        self.current_page = 0
        self.total_pages = 0
        self.crop_coords = []
        self.zoom_factor = 1.0
        self.temp_rect = None
        self.selection_rectangles = []
        if self.doc:
            self.doc.close()
        self.doc = None
        self.canvas.delete("all")
        self.update_page_indicator()

    def load_page(self):
        if self.pdf_path:
            threading.Thread(target=self._load_page_thread, daemon=True).start()

    def _load_page_thread(self):
        page = self.doc.load_page(self.current_page)
        pix = page.get_pixmap(matrix=fitz.Matrix(2 * self.zoom_factor, 2 * self.zoom_factor))
        img_data = pix.samples
        img = Image.frombytes("RGB", [pix.width, pix.height], img_data)
        self.tk_img = ImageTk.PhotoImage(image=img)
        self.master.after(0, self._update_canvas, img)

    def _update_canvas(self, img):
        self.canvas.config(scrollregion=(0, 0, img.width, img.height))
        self.canvas.delete("all")
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self.tk_img)
        self.update_page_indicator()
        self.redraw_selections()

    def next_page(self):
        if self.current_page < self.total_pages - 1:
            self.current_page += 1
            self.load_page()

    def prev_page(self):
        if self.current_page > 0:
            self.current_page -= 1
            self.load_page()

    def go_to_page(self):
        try:
            page = int(self.page_var.get()) - 1
            if 0 <= page < self.total_pages:
                self.current_page = page
                self.load_page()
            else:
                messagebox.showerror("Error", f"Page number must be between 1 and {self.total_pages}")
        except ValueError:
            messagebox.showerror("Error", "Please enter a valid page number")

    def update_page_indicator(self):
        self.page_indicator.config(text=f"Page: {self.current_page + 1} / {self.total_pages}")

    def on_press(self, event):
        self.start_x = self.canvas.canvasx(event.x)
        self.start_y = self.canvas.canvasy(event.y)

    def on_drag(self, event):
        cur_x = self.canvas.canvasx(event.x)
        cur_y = self.canvas.canvasy(event.y)

        if self.temp_rect:
            self.canvas.delete(self.temp_rect)

        self.temp_rect = self.canvas.create_rectangle(self.start_x, self.start_y, cur_x, cur_y, outline="red")

    def on_release(self, event):
        self.end_x = self.canvas.canvasx(event.x)
        self.end_y = self.canvas.canvasy(event.y)
        coords = (min(self.start_x, self.end_x), min(self.start_y, self.end_y),
                  max(self.start_x, self.end_x), max(self.start_y, self.end_y))
        
        if abs(coords[2] - coords[0]) > 5 and abs(coords[3] - coords[1]) > 5:
            self.crop_coords.append((self.current_page, coords))
            if self.temp_rect:
                self.canvas.delete(self.temp_rect)
            self.redraw_selections()
        else:
            if self.temp_rect:
                self.canvas.delete(self.temp_rect)

        self.temp_rect = None

    def redraw_selections(self):
        self.selection_rectangles = []
        for page, coords in self.crop_coords:
            if page == self.current_page:
                rect = self.canvas.create_rectangle(coords, outline="red")
                self.selection_rectangles.append(rect)

    def on_mousewheel(self, event):
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def on_shift_mousewheel(self, event):
        self.canvas.xview_scroll(int(-1 * (event.delta / 120)), "units")

    def on_zoom(self, event):
        old_zoom = self.zoom_factor
        if event.delta > 0:
            self.zoom_factor *= 1.1
        else:
            self.zoom_factor /= 1.1

        # Get the current view
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)

        # Calculate the new view
        new_x = x * (self.zoom_factor / old_zoom) - event.x
        new_y = y * (self.zoom_factor / old_zoom) - event.y

        self.load_page()

        # Set the new view
        self.canvas.xview_moveto(new_x / self.canvas.winfo_width())
        self.canvas.yview_moveto(new_y / self.canvas.winfo_height())

    def clear_selections(self):
        self.crop_coords = []
        self.load_page()

    def extract_images(self):
        if not self.pdf_path or not self.crop_coords:
            messagebox.showerror("Error", "Please open a PDF and select at least one area to extract.")
            return

        output_dir = filedialog.askdirectory()
        if not output_dir:
            return

        threading.Thread(target=self._extract_images_thread, args=(output_dir,), daemon=True).start()

    def _extract_images_thread(self, output_dir):
        for i, (page_num, coords) in enumerate(self.crop_coords):
            page = self.doc[page_num]
            
            x0, y0, x1, y1 = coords
            crop_rect = fitz.Rect(x0/(2*self.zoom_factor), y0/(2*self.zoom_factor), 
                                  x1/(2*self.zoom_factor), y1/(2*self.zoom_factor))
            
            pix = page.get_pixmap(matrix=fitz.Matrix(4, 4), clip=crop_rect)
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            
            # Generate a 6 digit hash
            hash_object = hashlib.md5(img.tobytes())
            hash_hex = hash_object.hexdigest()
            short_hash = hash_hex[:6]
            
            output_path = f"{output_dir}/{short_hash}.png"
            img.save(output_path, "PNG", dpi=(300, 300))

        self.master.after(0, lambda: messagebox.showinfo("Success", f"High-resolution extracted images saved to {output_dir}"))

    def on_right_click(self, event):
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)
        for i, rect in enumerate(self.selection_rectangles):
            coords = self.canvas.coords(rect)
            if coords[0] <= x <= coords[2] and coords[1] <= y <= coords[3]:
                self.delete_selection(i)
                break

    def delete_selection(self, index):
        del self.crop_coords[index]
        self.load_page()

if __name__ == "__main__":
    root = tk.Tk()
    app = PDFCropperGUI(root)
    root.mainloop()
