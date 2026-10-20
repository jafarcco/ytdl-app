import mimetypes
import os
import threading

import certifi

os.environ.setdefault("SSL_CERT_FILE", certifi.where())

import yt_dlp
from kivy.app import App
from kivy.clock import Clock
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.progressbar import ProgressBar
from kivy.uix.scrollview import ScrollView
from kivy.uix.spinner import Spinner
from kivy.uix.textinput import TextInput
from kivy.utils import platform

# No ffmpeg on the phone, so only formats that already contain video+audio.
FORMATS = {
    "Best": "best",
    "720p": "best[height<=720]/best",
    "480p": "best[height<=480]/best",
    "Audio (M4A)": "bestaudio[ext=m4a]/bestaudio",
}


def save_to_downloads(path):
    """Move a finished file into the phone's Download/yt-dlp folder."""
    if platform != "android":
        return path
    from jnius import autoclass

    PythonActivity = autoclass("org.kivy.android.PythonActivity")
    ContentValues = autoclass("android.content.ContentValues")
    Downloads = autoclass("android.provider.MediaStore$Downloads")
    FileUtils = autoclass("android.os.FileUtils")
    FileInputStream = autoclass("java.io.FileInputStream")

    name = os.path.basename(path)
    resolver = PythonActivity.mActivity.getContentResolver()
    values = ContentValues()
    values.put("_display_name", name)
    values.put("mime_type", mimetypes.guess_type(path)[0] or "application/octet-stream")
    values.put("relative_path", "Download/yt-dlp")
    uri = resolver.insert(Downloads.EXTERNAL_CONTENT_URI, values)
    out = resolver.openOutputStream(uri)
    inp = FileInputStream(path)
    FileUtils.copy(inp, out)
    inp.close()
    out.close()
    os.remove(path)
    return "Download/yt-dlp/" + name


class QuietLogger:
    def __init__(self, fn):
        self.fn = fn

    def debug(self, msg):
        pass

    def info(self, msg):
        pass

    def warning(self, msg):
        pass

    def error(self, msg):
        self.fn("Error: " + msg)


class DownloaderApp(App):
    def build(self):
        self.title = "YT Downloader"
        root = BoxLayout(orientation="vertical", padding=12, spacing=8)

        self.urls = TextInput(hint_text="Paste links, one per line", size_hint_y=0.28)
        self.quality = Spinner(text="Best", values=list(FORMATS),
                               size_hint_y=None, height=48)
        self.btn = Button(text="Download", size_hint_y=None, height=56)
        self.btn.bind(on_release=self.start)
        self.bar = ProgressBar(max=100, size_hint_y=None, height=16)
        self.status = Label(te
