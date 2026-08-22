import customtkinter as ctk
from tkinter import filedialog, messagebox
import threading
import os
import shutil
from pathlib import Path

from analyzer import analyze_pdf
from converter import convert_pdf, DPI, JPEG_QUALITY

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class PDFConverterApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("PDF Converter — eLibrary Fix")
        self.geometry("580x750")
        self.resizable(False, False)

        self.input_path: str | None = None
        self.output_path: str | None = None

        self._build_ui()

    # ─── UI ──────────────────────────────────────────────────────────────────

    def _build_ui(self):
        self.grid_columnconfigure(0, weight=1)

        # Header
        ctk.CTkLabel(
            self, text="PDF Converter", font=ctk.CTkFont(size=26, weight="bold")
        ).grid(row=0, column=0, pady=(24, 4))

        ctk.CTkLabel(
            self,
            text="แก้ปัญหา PDF สำหรับ eLibrary Upload",
            font=ctk.CTkFont(size=13),
            text_color="gray",
        ).grid(row=1, column=0, pady=(0, 20))

        # File selection
        file_frame = ctk.CTkFrame(self, corner_radius=12)
        file_frame.grid(row=2, column=0, padx=24, sticky="ew")
        file_frame.grid_columnconfigure(0, weight=1)

        self.file_label = ctk.CTkLabel(
            file_frame,
            text="ยังไม่ได้เลือกไฟล์",
            font=ctk.CTkFont(size=13),
            text_color="gray",
            wraplength=460,
        )
        self.file_label.grid(row=0, column=0, padx=16, pady=(16, 8))

        self.browse_btn = ctk.CTkButton(
            file_frame,
            text="เลือกไฟล์ PDF",
            command=self.select_file,
            height=36,
        )
        self.browse_btn.grid(row=1, column=0, padx=16, pady=(0, 16))

        # Convert button
        self.convert_btn = ctk.CTkButton(
            self,
            text="Convert PDF",
            command=self.start_convert,
            height=46,
            font=ctk.CTkFont(size=15, weight="bold"),
            state="disabled",
        )
        self.convert_btn.grid(row=3, column=0, padx=24, pady=18, sticky="ew")

        # Progress
        self.progress_label = ctk.CTkLabel(
            self, text="", font=ctk.CTkFont(size=12), text_color="gray"
        )
        self.progress_label.grid(row=4, column=0)

        self.progress_bar = ctk.CTkProgressBar(self, height=8)
        self.progress_bar.grid(row=5, column=0, padx=24, pady=(4, 0), sticky="ew")
        self.progress_bar.set(0)
        self.progress_bar.grid_remove()

        # Summary
        self.summary_frame = ctk.CTkFrame(self, corner_radius=12)
        self.summary_frame.grid(row=6, column=0, padx=24, pady=16, sticky="ew")
        self.summary_frame.grid_columnconfigure(0, weight=1)
        self.summary_frame.grid_remove()

        ctk.CTkLabel(
            self.summary_frame,
            text="สรุปผลการ Convert",
            font=ctk.CTkFont(size=14, weight="bold"),
        ).grid(row=0, column=0, padx=16, pady=(14, 6))

        self.summary_text = ctk.CTkTextbox(
            self.summary_frame,
            height=240,
            font=ctk.CTkFont(family="Courier New", size=12),
            wrap="word",
        )
        self.summary_text.grid(row=1, column=0, padx=16, pady=(0, 16), sticky="ew")

        # Download button
        self.download_btn = ctk.CTkButton(
            self,
            text="💾  บันทึกไฟล์ที่แปลงแล้ว",
            command=self.save_output,
            height=46,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#2d7a2d",
            hover_color="#1f5c1f",
        )
        self.download_btn.grid(row=7, column=0, padx=24, pady=(0, 24), sticky="ew")
        self.download_btn.grid_remove()

    # ─── Actions ─────────────────────────────────────────────────────────────

    def select_file(self):
        path = filedialog.askopenfilename(
            title="เลือกไฟล์ PDF",
            filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")],
        )
        if not path:
            return
        self.input_path = path
        size_mb = round(os.path.getsize(path) / (1024 * 1024), 2)
        self.file_label.configure(
            text=f"{Path(path).name}\n{size_mb} MB", text_color="white"
        )
        self.convert_btn.configure(state="normal")
        self.summary_frame.grid_remove()
        self.download_btn.grid_remove()
        self.progress_bar.grid_remove()
        self.progress_label.configure(text="")

    def start_convert(self):
        if not self.input_path:
            return
        self.convert_btn.configure(state="disabled", text="กำลัง Convert...")
        self.browse_btn.configure(state="disabled")
        self.summary_frame.grid_remove()
        self.download_btn.grid_remove()
        self.progress_bar.set(0)
        self.progress_bar.grid()
        self.progress_label.configure(text="กำลังวิเคราะห์ไฟล์...")
        threading.Thread(target=self._worker, daemon=True).start()

    def _worker(self):
        try:
            self._update(lambda: self.progress_label.configure(text="กำลังวิเคราะห์ปัญหา..."))
            analysis = analyze_pdf(self.input_path)
            self._update(lambda: self.progress_bar.set(0.1))

            src = Path(self.input_path)
            self.output_path = str(src.parent / (src.stem + "_converted.pdf"))

            def on_progress(pct: float):
                val = 0.1 + pct * 0.85
                self._update(lambda: self.progress_bar.set(val))
                self._update(
                    lambda: self.progress_label.configure(
                        text=f"กำลัง Convert... {int(pct * 100)}%"
                    )
                )

            result = convert_pdf(self.input_path, self.output_path, on_progress)
            self._update(lambda: self.progress_bar.set(1.0))
            self._update(lambda: self._show_result(analysis, result))

        except Exception as exc:
            self._update(lambda: self._show_error(str(exc)))

    # ─── Result helpers ──────────────────────────────────────────────────────

    def _show_result(self, analysis: dict, result: dict):
        self.convert_btn.configure(state="normal", text="Convert อีกครั้ง")
        self.browse_btn.configure(state="normal")
        self.progress_label.configure(text="✅ Convert สำเร็จ!")

        lines = []
        lines.append("── ปัญหาที่ตรวจพบ ─────────────────────")
        if analysis["issues"]:
            for issue in analysis["issues"]:
                lines.append(f"  ⚠  {issue}")
        else:
            lines.append("  ✅ ไม่พบปัญหาพิเศษ")

        lines.append("")
        lines.append("── สิ่งที่แก้ไป ────────────────────────")
        new_size_str = (
            f"{result['new_size_mb']} MB"
            if result["new_size_mb"] >= 0.1
            else f"{result['new_size_kb']} KB"
        )
        lines.append(
            f"  ขนาดไฟล์ : {result['original_size_mb']} MB → {new_size_str}"
        )
        lines.append(
            f"  ลดลง     : {result['size_reduction_mb']} MB "
            f"({result['size_reduction_pct']}%)"
        )
        lines.append(f"  วิธีแก้   : Re-render ทุกหน้า DPI={DPI}, JPEG {JPEG_QUALITY}%")

        lines.append("")
        lines.append("── ข้อมูลไฟล์ ──────────────────────────")
        lines.append(f"  จำนวนหน้า : {result['total_pages']} หน้า")
        if analysis["large_images_count"]:
            lines.append(f"  รูปขนาดใหญ่ (ต้นฉบับ): {analysis['large_images_count']} ภาพ")

        self.summary_text.configure(state="normal")
        self.summary_text.delete("1.0", "end")
        self.summary_text.insert("1.0", "\n".join(lines))
        self.summary_text.configure(state="disabled")

        self.summary_frame.grid()
        self.download_btn.grid()

    def _show_error(self, error: str):
        self.convert_btn.configure(state="normal", text="Convert PDF")
        self.browse_btn.configure(state="normal")
        self.progress_label.configure(text="❌ เกิดข้อผิดพลาด")
        messagebox.showerror("Error", f"เกิดข้อผิดพลาด:\n{error}")

    def save_output(self):
        if not self.output_path or not os.path.exists(self.output_path):
            messagebox.showerror("Error", "ไม่พบไฟล์ผลลัพธ์")
            return
        save_path = filedialog.asksaveasfilename(
            title="บันทึกไฟล์",
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf")],
            initialfile=Path(self.output_path).name,
        )
        if save_path:
            shutil.copy2(self.output_path, save_path)
            messagebox.showinfo("สำเร็จ", f"บันทึกไฟล์เรียบร้อย\n{save_path}")

    def _update(self, fn):
        self.after(0, fn)


if __name__ == "__main__":
    app = PDFConverterApp()
    app.mainloop()
