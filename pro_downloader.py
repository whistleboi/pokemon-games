import os
import subprocess
import platform
import sys
import threading
import shutil

try:
    import customtkinter as ctk
    import yt_dlp
except ModuleNotFoundError as e:
    print(f"Error: The library '{e.name}' is not installed for this Python.")
    print(f"Running from: {sys.executable}")
    print(f"To fix, run: & \"{sys.executable}\" -m pip install customtkinter yt-dlp")
    input("Press Enter to exit...")
    sys.exit(1)

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

def download_logic():
    raw_text = url_textbox.get("1.0", "end-1c")
    urls = [line.strip() for line in raw_text.split('\n') if line.strip()]

    if not urls:
        status_label.configure(text="Please paste at least one URL!", text_color="red")
        return

    # Check for FFmpeg (Required for conversion)
    if shutil.which("ffmpeg") is None and not os.path.exists("ffmpeg.exe"):
        status_label.configure(text="Error: FFmpeg missing! Place ffmpeg.exe here.", text_color="red")
        return

    selected_format = format_dropdown.get()
    codec = 'vorbis' if selected_format == 'ogg' else selected_format

    download_btn.configure(state="disabled", text="Downloading...")
    total = len(urls)
    
    for i, url in enumerate(urls):
        status_label.configure(text=f"Processing {i+1} of {total}...", text_color="yellow")
        try:
            download_path = os.path.join(os.path.expanduser('~'), 'Downloads', '%(title)s.%(ext)s')
            
            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': download_path,
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': codec,
                    'preferredquality': '192',
                }],
                'quiet': True,
                'no_warnings': True,
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
        except Exception as e:
            print(f"Error on {url}: {e}")

    status_label.configure(text=f"Finished! {total} files processed.", text_color="#2ecc71")
    download_btn.configure(state="normal", text="DOWNLOAD ALL")
    open_folder_btn.pack(pady=5)

def start_download():
    threading.Thread(target=download_logic, daemon=True).start()

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
url_textbox.pack(pady=10)

# Controls Frame
controls_frame = ctk.CTkFrame(app, fg_color="transparent")
controls_frame.pack(pady=5)

paste_btn = ctk.CTkButton(controls_frame, text="Paste", width=80, command=paste_link, fg_color="gray")
paste_btn.pack(side="left", padx=10)

format_dropdown = ctk.CTkComboBox(controls_frame, values=["mp3", "wav", "m4a", "flac", "ogg"], width=100, state="readonly")
format_dropdown.pack(side="left", padx=10)
format_dropdown.set("mp3")

# Action Button
download_btn = ctk.CTkButton(app, text="DOWNLOAD ALL", command=start_download, fg_color="#cc0000", hover_color="#aa0000", font=("Arial", 14, "bold"))
download_btn.pack(pady=20)

# Status and Folder Button
status_label = ctk.CTkLabel(app, text="")
status_label.pack()

open_folder_btn = ctk.CTkButton(app, text="Open Downloads Folder", command=open_folder, fg_color="transparent", border_width=1)

app.mainloop()