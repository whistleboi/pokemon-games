    ##### run these 2 commands in terminal to create the .exe file (after installing pyinstaller and the required libraries):
    ##### cd "c:\Users\Dad\Games\Python Games\pokemon-games"
    ##### pyinstaller --noconsole --onefile --collect-all customtkinter pro_downloader.py

import os
import subprocess
import platform
import sys
import threading
import shutil
from tkinter import filedialog, messagebox

try:
    # --- Directory Fix ---
    # This forces the terminal to work inside the script's folder
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    import customtkinter as ctk
    import yt_dlp
except ModuleNotFoundError as e:
    print(f"Error: The library '{e.name}' is not installed for this Python.")
    print(f"Running from: {sys.executable}")
    print(f"To fix, run: & \"{sys.executable}\" -m pip install customtkinter yt-dlp")
    input("Press Enter to exit...")
    sys.exit(1)

def get_ffmpeg_path():
    # If running as a PyInstaller bundle (.exe)
    if getattr(sys, 'frozen', False):
        # The .exe is located in os.path.dirname(sys.executable)
        # We check for ffmpeg.exe right next to the application .exe
        exe_dir = os.path.dirname(sys.executable)
        path = os.path.join(exe_dir, "ffmpeg.exe")
        if os.path.exists(path):
            return path
        # Also check inside a bundled _MEIPASS folder, just in case
        if hasattr(sys, '_MEIPASS'):
            bundle_dir = sys._MEIPASS
            path = os.path.join(bundle_dir, 'ffmpeg.exe')
            if os.path.exists(path):
                return path
    
    # Fallback for running as a normal script (.py)
    # 1. Check if ffmpeg is in the system's PATH
    if shutil.which("ffmpeg"):
        return "ffmpeg"
    # 2. Check common local folders relative to the script's location
    script_dir = os.path.dirname(os.path.abspath(__file__))
    for folder in ["", "dist", "bin"]:
        path = os.path.join(script_dir, folder, "ffmpeg.exe")
        if os.path.exists(path):
            return path
    return None

def paste_link():
    # Automatically grabs text from your clipboard
    try:
        clipboard = app.clipboard_get()
        url_textbox.insert("end", clipboard + "\n")
    except:
        status_label.configure(text="Clipboard empty", text_color="orange")

def open_folder():
    # Opens the downloads folder automatically when clicked
    path = os.path.join(os.path.expanduser('~'), 'Downloads')
    if platform.system() == "Windows":
        os.startfile(path)
    elif platform.system() == "Darwin": # macOS
        subprocess.Popen(["open", path])
    else: # Linux
        subprocess.Popen(["xdg-open", path])

selected_files = []

def select_files():
    files = filedialog.askopenfilenames()
    if files:
        selected_files.clear()
        selected_files.extend(files)
        file_label.configure(text=f"{len(files)} files selected")

def convert_logic():
    if not selected_files:
        status_label.configure(text="Please select files first!", text_color="red")
        return

    ffmpeg_exe = get_ffmpeg_path()
    if not ffmpeg_exe:
        status_label.configure(text="Error: FFmpeg missing! Check dist/ folder.", text_color="red")
        return

    target_fmt = format_dropdown.get()
    download_btn.configure(state="disabled", text="Converting...")
    
    total = len(selected_files)
    for i, fpath in enumerate(selected_files):
        status_label.configure(text=f"Converting {i+1} of {total}...", text_color="yellow")
        try:
            fname = os.path.splitext(os.path.basename(fpath))[0]
            out = os.path.join(os.path.expanduser('~'), 'Downloads', f"{fname}.{target_fmt}")
            
            cmd = [ffmpeg_exe, "-y", "-i", fpath]
            
            if target_fmt == "mp3": cmd += ["-vn", "-c:a", "libmp3lame", "-q:a", "2"]
            elif target_fmt == "ogg": cmd += ["-vn", "-c:a", "libvorbis", "-q:a", "4"]
            elif target_fmt == "m4a": cmd += ["-vn", "-c:a", "aac", "-b:a", "192k"]
            elif target_fmt == "flac": cmd += ["-vn", "-c:a", "flac"]
            elif target_fmt == "wav": cmd += ["-vn", "-c:a", "pcm_s16le"]
            elif target_fmt == "mp4": cmd += ["-c:v", "libx264", "-c:a", "aac"]
            elif target_fmt == "avi": cmd += ["-c:v", "mpeg4", "-c:a", "mp3"]
            
            cmd.append(out)
            
            subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception as e:
            print(f"Error: {e}")
            
    status_label.configure(text="Conversion Complete!", text_color="#2ecc71")
    download_btn.configure(state="normal", text="START PROCESS")
    open_folder_btn.pack(pady=5)

def download_logic():
    raw_text = url_textbox.get("1.0", "end-1c")
    urls = [line.strip() for line in raw_text.split('\n') if line.strip()]

    if not urls:
        status_label.configure(text="Please paste at least one URL!", text_color="red")
        return

    # Check for FFmpeg (Required for conversion)
    ffmpeg_exe = get_ffmpeg_path()
    if not ffmpeg_exe:
        status_label.configure(text="Error: FFmpeg missing! Check dist/ folder.", text_color="red")
        return

    selected_format = format_dropdown.get()

    download_btn.configure(state="disabled", text="Downloading...")
    total = len(urls)
    success_count = 0
    error_count = 0
    last_error = None
    
    dl_folder = os.path.join(os.path.expanduser('~'), 'Downloads')
    if not os.path.exists(dl_folder):
        os.makedirs(dl_folder)
    
    for i, url in enumerate(urls):
        status_label.configure(text=f"Processing {i+1} of {total}...", text_color="yellow")
        try:
            download_path = os.path.join(dl_folder, '%(title)s.%(ext)s')
            
            # Common options to help bypass "Unavailable" errors
            ydl_opts = {
                'outtmpl': download_path,
                'ffmpeg_location': ffmpeg_exe,
                'quiet': True,
                'no_warnings': True,
                'geo_bypass': True,
                'nocheckcertificate': True,
            }

            if selected_format in ["mp3", "wav", "m4a", "flac", "ogg"]:
                codec = 'vorbis' if selected_format == 'ogg' else selected_format
                ydl_opts.update({
                    'format': 'bestaudio/best',
                    'postprocessors': [{
                        'key': 'FFmpegExtractAudio',
                        'preferredcodec': codec,
                        'preferredquality': '192',
                    }],
                })
            else:
                ydl_opts.update({
                    'format': 'bestvideo+bestaudio/best',
                })
                if selected_format in ["mp4", "mkv"]:
                    ydl_opts['merge_output_format'] = selected_format
                else:
                    ydl_opts['postprocessors'] = [{'key': 'FFmpegVideoConvertor', 'preferedformat': selected_format}]
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            success_count += 1
        except Exception as e:
            print(f"Error on {url}: {e}")
            error_count += 1
            last_error = e

    if success_count == 0 and error_count > 0:
        status_label.configure(text=f"Failed. See popup.", text_color="red")
        messagebox.showerror("Download Error", f"Failed to download.\nError: {last_error}")
    elif error_count > 0:
        status_label.configure(text=f"Done. {success_count} ok, {error_count} failed.", text_color="orange")
        messagebox.showwarning("Partial Error", f"{error_count} downloads failed.\nLast error: {last_error}")
    else:
        status_label.configure(text=f"Finished! {success_count} files saved.", text_color="#2ecc71")
        
    download_btn.configure(state="normal", text="START PROCESS")
    open_folder_btn.pack(pady=5)

def start_download():
    threading.Thread(target=download_logic, daemon=True).start()
def start_process():
    if tabview.get() == "Download URL":
        threading.Thread(target=download_logic, daemon=True).start()
    else:
        threading.Thread(target=convert_logic, daemon=True).start()

# UI Setup
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

app = ctk.CTk()
app.title("Audio Loader Pro")
app.geometry("500x450")

# Title
title = ctk.CTkLabel(app, text="Batch Audio Downloader", font=("Arial", 20, "bold"))
title.pack(pady=15)

# Textbox for multiple links
url_textbox = ctk.CTkTextbox(app, width=400, height=150)
# Tabs
tabview = ctk.CTkTabview(app, width=450, height=200)
tabview.pack(pady=5)
tab_dl = tabview.add("Download URL")
tab_cv = tabview.add("Convert File")

# Tab 1: Download
url_textbox = ctk.CTkTextbox(tab_dl, width=400, height=120)
url_textbox.pack(pady=10)
paste_btn = ctk.CTkButton(tab_dl, text="Paste Clipboard", width=120, command=paste_link, fg_color="gray")
paste_btn.pack(pady=5)

# Tab 2: Convert
select_btn = ctk.CTkButton(tab_cv, text="Select Files", command=select_files)
select_btn.pack(pady=30)
file_label = ctk.CTkLabel(tab_cv, text="No files selected")
file_label.pack()

# Controls Frame
controls_frame = ctk.CTkFrame(app, fg_color="transparent")
controls_frame.pack(pady=5)

paste_btn = ctk.CTkButton(controls_frame, text="Paste", width=80, command=paste_link, fg_color="gray")
paste_btn.pack(side="left", padx=10)

ctk.CTkLabel(controls_frame, text="Output Format:").pack(side="left", padx=5)
format_dropdown = ctk.CTkComboBox(controls_frame, values=["mp3", "wav", "m4a", "flac", "ogg", "mp4", "mkv", "avi"], width=100, state="readonly")
format_dropdown.pack(side="left", padx=10)
format_dropdown.set("mp3")

# Action Button
download_btn = ctk.CTkButton(app, text="START PROCESS", command=start_process, fg_color="#cc0000", hover_color="#aa0000", font=("Arial", 14, "bold"))
download_btn.pack(pady=20)

# Status and Folder Button
status_label = ctk.CTkLabel(app, text="")
status_label.pack()

open_folder_btn = ctk.CTkButton(app, text="Open Downloads Folder", command=open_folder, fg_color="transparent", border_width=1)

app.mainloop()