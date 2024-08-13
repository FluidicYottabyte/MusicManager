import sys
import os
import random
import time
import math
import numpy as np
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QLabel, QVBoxLayout, QHBoxLayout, QWidget,
    QSlider, QListWidget, QListWidgetItem, QPushButton, QDialog, QDialogButtonBox,
    QVBoxLayout, QHBoxLayout, QMessageBox, QFileDialog, QLineEdit, QAbstractItemView, 
    QSizePolicy, QFrame
)
from PyQt6.QtGui import QPixmap, QFont, QPainter, QColor,QIcon
from PyQt6.QtCore import Qt, QTimer, QSize, pyqtSignal
from mutagen import File
from mutagen.flac import FLAC, Picture
from PIL import Image
from io import BytesIO
from mutagen.id3 import ID3
import json
import atexit
import shutil 
import codecs
from Updater import GitUpdater
import ctypes

try:
    import vlc
except ImportError:
    raise ImportError("The 'python-vlc' library is required. Install it using 'pip install python-vlc'.")


def resource_path(relative_path):
        """ Get absolute path to resource, works for dev and for PyInstaller """
        try:
            # PyInstaller creates a temp folder and stores path in _MEIPASS
            base_path = sys._MEIPASS
        except Exception:
            base_path = os.path.abspath(".")
        
        return os.path.join(base_path, relative_path)
    

def replace_unicode_errors(text, replacement='�'):
    result = []
    for char in text:
        try:
            # Check if the character can be encoded in UTF-8 without errors
            with open("bastard.txt", "w", encoding = "utf-8") as f:
                f.write(char)
            
            os.remove("bastard.txt")
            result.append(char)
        except UnicodeEncodeError:
            # If encoding fails, append the replacement character
            result.append(replacement)
    return ''.join(result)


def fix_unicode(s):
    try:
        with open("bastard.txt", "w", encoding = "utf-8") as f:
            f.write(s)
            
        os.remove("bastard.txt")
        return (s)
    except Exception as e:
        ret = replace_unicode_errors(s)
        print("Fixed unicode: "+ret)
        resource_path("Songs")
        return (ret)

def set_app_user_model_id(app_id):
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(app_id)
    
settings_template = {}

settings_template["settings"] = {}
settings_template["settings"]["volume"] = 50
settings_template["settings"]["text_color"] = '#000000'

system_volume = 50



class MusicPlayer(QMainWindow):
    
    
    
    def __init__(self, settings):
        
        super().__init__()
        
        self.updater = GitUpdater()
        
        if self.updater.check_for_updates():
            print("Behind")
            
            error_popup = QMessageBox()
            error_popup.setIcon(QMessageBox.Icon.Information)
            error_popup.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            error_popup.setWindowTitle("Update Available")
            error_popup.setText("An update to Music Manager has been detected. Would you like to update? (you will need to manually restart Music Manager to see effects.)")
            response = error_popup.exec()
            
            if response == QMessageBox.StandardButton.Yes:
                print("User clicked Yes")
                self.updater.update()
            else:
                print("User clicked No")
    
        self.utilities = resource_path('Utility')
        
        self.setWindowTitle('Music Manager')
        self.setGeometry(100, 100, 800, 600)
        
        self.saved_position = 0
        self.stopped = True
        
        # VLC player instance
        self.instance = vlc.Instance()
        self.player = self.instance.media_player_new()
        
        # Main layout
        self.main_layout = QVBoxLayout()
        self.otherLayout = QHBoxLayout()
        

        # Song progress bar
        self.progress_bar = QSlider(Qt.Orientation.Horizontal)
        self.progress_bar.setRange(0, 1000)
        self.progress_bar.sliderMoved.connect(self.set_position)

        # Timer to update progress bar
        self.timer = QTimer(self)
        self.timer.setInterval(100)
        self.timer.timeout.connect(self.update_progress)

        # Song time counter
        self.time_label = QLabel('No music playing')
        self.time_label.setObjectName("numbers")

        # Current song info
        self.song_info_layout = QVBoxLayout()
        
        self.album_art = QLabel()
        self.album_art.setFixedSize(200, 200)
        pixmap = QPixmap(os.path.join(self.utilities, "default.png"))
        self.album_art.setPixmap(pixmap)
        self.album_art.setScaledContents(True)
        self.song_info_layout.addWidget(self.album_art)
        
        self.song_details = QLabel('Song Name',alignment=Qt.AlignmentFlag.AlignTop)
        self.song_details.setWordWrap(True)
        self.song_details.setFixedWidth(200)
        self.song_info_layout.addWidget(self.song_details)
        

        """ self.audio_level_bars = AudioLevelBars(num_bars=20)

  
        self.song_info_layout.addWidget(self.audio_level_bars)

        self.timerq = QTimer(self)
        self.timerq.setInterval(100)  # Update every 100 ms
        self.timerq.timeout.connect(self.update_audio_levels)
        self.timerq.start() """
        
        
        self.volume_label = QLabel("Volume", alignment=Qt.AlignmentFlag.AlignBottom)
        self.volume_label.setObjectName("artistTitle")
        self.song_info_layout.addWidget(self.volume_label)
        
        
        self.volume_slider = QSlider(Qt.Orientation.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setFixedWidth(200)
        self.volume_slider.setValue(settings["volume"])  # Default volume level
        
        system_volume = settings["volume"]
        
        self.volume_slider.valueChanged.connect(self.change_volume)
        self.song_info_layout.addWidget(self.volume_slider)
        
        self.otherLayout.addLayout(self.song_info_layout)

        # Control buttons
        self.control_layout = QHBoxLayout()
        
        self.play_button = QPushButton(u'\u25b6')
        self.play_button.clicked.connect(self.play_song)
        self.control_layout.addWidget(self.play_button)
        
        self.stop_button = QPushButton(u'II')
        self.stop_button.clicked.connect(self.stop_song)
        self.control_layout.addWidget(self.stop_button)
        
        self.skip_back_button = QPushButton('<<')
        self.skip_back_button.clicked.connect(self.skip_back)
        self.control_layout.addWidget(self.skip_back_button)
        
        self.skip_forward_button = QPushButton('>>')
        self.skip_forward_button.clicked.connect(self.skip_forward)
        self.control_layout.addWidget(self.skip_forward_button)
        
        
        
        self.shuffle_button = QPushButton('\u2928')
        self.shuffle_button.clicked.connect(self.shuffle_songs)
        self.control_layout.addWidget(self.shuffle_button)

        # Playlists
        self.PLaylistLayout = QVBoxLayout()
        self.playlist_widget = QListWidget()
        self.playlist_widget.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        
        self.playlist_widget.setIconSize(QSize(self.playlist_widget.sizeHint().width(),50))
        self.playlist_widget.setMinimumSize(500, 100)
        font = QFont()
        font.setFamily("serif")
        font.setPointSize(13)
        font.setBold(False)
        font.setItalic(False)
        self.playlist_widget.setFont(font)
        self.PLaylistLayout.addWidget(self.playlist_widget)

        #new layout for playlist and add song buttons
        self.lotta_buttons_layout = QHBoxLayout()

        # Button to create a new playlist
        self.create_playlist_button = QPushButton('Create Playlist')
        self.create_playlist_button.clicked.connect(self.create_playlist)
        self.lotta_buttons_layout.addWidget(self.create_playlist_button)
        
        self.create_playlist_button = QPushButton('Add Songs')
        self.create_playlist_button.clicked.connect(self.open_drag_drop_window)
        self.lotta_buttons_layout.addWidget(self.create_playlist_button)
        
        self.PLaylistLayout.addLayout(self.lotta_buttons_layout)
        self.otherLayout.addLayout(self.PLaylistLayout)
        
        self.main_layout.addLayout(self.otherLayout)
        self.main_layout.addLayout(self.control_layout)
        self.main_layout.addWidget(self.time_label)

        self.main_layout.addWidget(self.progress_bar)


        # Load playlists
        self.load_playlists()

        # Set central widget
        central_widget = QWidget()
        central_widget.setLayout(self.main_layout)
        self.setCentralWidget(central_widget)

        # Initialize playlist and song management
        self.current_playlist = []
        self.current_index = -1
        
        self.change_volume(system_volume)
        
    
    
    def open_drag_drop_window(self):
        # Create the drag-and-drop window
        self.drag_drop_window = DragDropWidget()
        self.drag_drop_window.setWindowTitle('Drag and Drop Files/Folders')
        self.drag_drop_window.resize(400, 300)
        self.drag_drop_window.show()
        
        self.drag_drop_window.filesDropped.connect(self.handle_files_dropped)
        
    def handle_files_dropped(self, file_paths):
        # Handle the list of dropped files (received from the dialog)
        print("Received files from dialog:")
        for path1 in file_paths:
            if not os.path.isfile(path1):
                self.handle_files_dropped([os.path.join(path1, f) for f in os.listdir(path1)])
            else:
                if os.path.splitext(path1)[1].lower() in [".mp3", ".flac", ".aiff",".wav"]: 
                    if not os.path.isfile(os.path.join(resource_path("Songs"),os.path.basename(path1))): #Checks if file already exists, or not
                        shutil.copy(path1,os.path.join(resource_path("Songs"),os.path.basename(path1)))
                
        return
        
    def extract_pitch_range(self, media_player):
        # Get the audio samples from the media player
        return 0, media_player.audio_get_volume()
        
    def update_audio_levels(self):
        if self.player.is_playing():

            MIN_PITCH , MAX_PITCH = self.extract_pitch_range(self.player)
            # Simulate audio levels with logarithmic scale representing pitch
            pitch_levels = []
            # Normalize pitch levels to [0, 100]
            for i in range(20):
                pitch_levels.append(((((2/(((math.e)**(i-10))+((math.e)**-(i-10))*.05+10))*50)*10)/100)*MAX_PITCH)

            print(pitch_levels)
            self.audio_level_bars.set_audio_levels(pitch_levels)

    def change_volume(self, value):
        self.player.audio_set_volume(value)
        global system_volume
        system_volume = value
        print(f"Volume set to: {value}")
        

    def load_playlists(self):
        self.playlist_widget.clear()  # Clear existing items before loading
        playlists_path = resource_path('Playlists')
        for playlist_file in os.listdir(playlists_path):
            if playlist_file.endswith('.txt'):
                # item = QListWidgetItem(os.path.splitext(playlist_file)[0])
                # self.playlist_widget.addItem(item)
                # item.setData(Qt.ItemDataRole.UserRole, playlist_file)
                
                item = QListWidgetItem()
                item.setData(Qt.ItemDataRole.UserRole, playlist_file)
                item_widget = QWidget()
                line_text = QLabel(os.path.splitext(playlist_file)[0])
                line_text.setSizePolicy(
                    QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
                )
                
                line_push_button = QPushButton(u'\u25b6')
                line_push_button.setObjectName("playlists")
                line_push_button.clicked.connect(self.play_playlist)
                line_push_button.setSizePolicy(
                    QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed
                )
                line_push_button.setProperty('item_data', playlist_file)
                
                line_edit_button = QPushButton(u"\u26ED")
                line_edit_button.setObjectName("playlists")
                line_edit_button.clicked.connect(self.show_playlist_popup)
                line_edit_button.setSizePolicy(
                    QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed
                )
                line_edit_button.setProperty('item_data', playlist_file)
                
                item_layout = QHBoxLayout()
                item_layout.addWidget(line_text)
                item_layout.addWidget(line_push_button)
                item_layout.addWidget(line_edit_button)
                item_widget.setLayout(item_layout)
                
                item.setSizeHint(item_widget.sizeHint())
                self.playlist_widget.addItem(item)
                self.playlist_widget.setItemWidget(item, item_widget)
                
                seperator = QListWidgetItem()
                seperator.setSizeHint(QSize(0, 5))
                seperator.setFlags(Qt.ItemFlag.NoItemFlags)
                
                self.playlist_widget.addItem(seperator)
                
                lineFrame = QFrame()
                lineFrame.setFrameShape(QFrame.Shape.HLine)
                lineFrame.setFrameShadow(QFrame.Shadow.Sunken)
                
                self.playlist_widget.setItemWidget(seperator, lineFrame)
                
        


    def play_playlist(self):        
        button = self.sender()

        # Retrieve the data stored in the button
        playlist_file = button.property('item_data')
        self.load_songs_from_playlist(playlist_file)
        self.play_song()

    def load_songs_from_playlist(self, playlist_file):
        self.current_playlist.clear()
        self.current_index = -1
        playlist_path = os.path.join(resource_path('Playlists'), playlist_file)
        with open(playlist_path, 'r', encoding = "utf-8") as file:
            for line in file:
                song_path = line.strip()
                if os.path.isfile(os.path.join(resource_path('Songs'), song_path)):
                    self.current_playlist.append(song_path)

    
    def play_song(self):
        if not self.current_playlist:
            return

        if self.current_index == -1:
            self.current_index = 0

        song_path = self.current_playlist[self.current_index]
        song_full_path = os.path.join(resource_path('Songs'), song_path)
        print(song_full_path)
        media = self.instance.media_new(song_full_path)
        

        # If there's a saved position, set it
        if self.saved_position > 0:
            print("save position valid")
            media.add_option(f'start-time={self.saved_position / 1000}')

        self.player.set_media(media)
        
        self.player.play()
        self.timer.start()
        
        self.stopped = False
        
        self.load_song_metadata(song_full_path)
        self.update_progress()

    def load_song_metadata(self, song_path):
        audio = File(song_path)
        if os.path.splitext(song_path)[1].lower() in [".mp3", ".flac", ".aiff"]: 
            if audio:
                title = audio.tags.get('TIT2', ['Unknown Title'])[0]
                artist = audio.tags.get('TPE1', ['Unknown Artist'])[0]
                album = audio.tags.get('TALB', ['Unknown Album'])[0]
                
                
                pict= None
                
                if os.path.splitext(song_path)[1] == ".flac":
                    
                    
                    var = FLAC(song_path)
                    print("Song metadata: "+ str(var))
                    
                    try:
                        artist = var['artist'][0]
                    except KeyError:
                        print("There was an error fetching song artist.")
                         
                                    
                    try:
                        title = var['title'][0]
                    except KeyError:
                        print("There was an error fetching song title")
                        if title != 'Unknown Artist':
                            title = os.path.splitext(os.path.basename(song_path))[0] 
                        
                    self.song_details.setText(f"{title} - {artist}")
                    
                    pics = var.pictures
                    for p in pics:
                        if p.type == 3: #front cover
                            print("\nfound front cover") 
                            with open("cover.jpg", "wb") as f:
                                pict = (p.data)
                    
                    print(var)
                    
                    try:
                        album = var["ALBUM"]
                    except KeyError:
                        album = ["Unknown Album"]
                        
                
                
                else:    
                    tags = ID3(song_path)
                    
                    print(tags.pprint())
                    pict = tags.getall("APIC")[0].data
                    print(pict)
                # Load album art if available
                if pict != None:
                    print("Picture is available")
                    with open(os.path.join(self.utilities, "album-art.jpg"), 'wb') as img_file:
                        img_file.write(pict)
                    pixmap = QPixmap(os.path.join(self.utilities, "album-art.jpg"))
                    self.album_art.setPixmap(pixmap)
                    print("Picture done")
                else:
                    print("no picture found")
                    self.album_art.clear()
                    pixmap = QPixmap(os.path.join(self.utilities, "default.png"))
                    self.album_art.setPixmap(pixmap)
                    print("cleared picture")
                
                self.song_details.setText(f"{title}\nBy {artist}")
                print(" set song details")
        else:
            self.song_details.setText(os.path.splitext(os.path.basename(song_path))[0]) 
            pixmap = QPixmap(os.path.join(self.utilities, "default.png"))
            self.album_art.setPixmap(pixmap)

    def stop_song(self):
        if self.stopped:
            return
        
        self.stopped = True
        # Save the current position before stopping
        self.saved_position = self.player.get_time()
        print(self.saved_position)
        self.player.stop()
        self.timer.stop()

    def skip_forward(self):
        if self.current_playlist:
            self.saved_position = 0
            self.current_index = (self.current_index + 1) % len(self.current_playlist)
            self.play_song()

    def skip_back(self):
        if self.current_playlist:
            self.current_index = (self.current_index - 1) % len(self.current_playlist)
            self.play_song()

    def shuffle_songs(self):
        if self.current_playlist:
            random.shuffle(self.current_playlist)
            self.current_index = 0
            self.play_song()

    def update_progress(self):
        media = self.player.get_media()
        if media:
            duration = media.get_duration() // 1000
            current_time = self.player.get_time() // 1000
            self.time_label.setText(f"{current_time // 60}:{current_time % 60:02} / {duration // 60}:{duration % 60:02}")
            if duration > 0:
                self.progress_bar.setValue(int((current_time / duration) * 1000))
        if not self.player.is_playing():
            self.skip_forward()

    def set_position(self, position):
        self.player.set_position(position / 1000)

    def show_playlist_popup(self):
        button = self.sender()

        # Retrieve the data stored in the button
        playlist_file = button.property('item_data')
        dialog = CreatePlaylistDialog(self, playlist_file)
        dialog.exec()
        self.load_playlists()

    def create_playlist(self):
        dialog = CreatePlaylistDialog(self, None)
        dialog.exec()
        self.load_playlists()









class AudioLevelBars(QWidget):
    def __init__(self, num_bars=10):
        super().__init__()
        self.num_bars = num_bars
        self.audio_levels = [0] * num_bars

    def paintEvent(self, event):
        painter = QPainter(self)
        bar_width = self.width() / self.num_bars
        for i, level in enumerate(self.audio_levels):
            painter.setBrush(QColor(0, 0, 255))
            rect = self.rect()
            x = i * bar_width
            bar_height = (rect.height() * level) / 100  # Convert level to pixel height
            painter.drawRect(int(x), rect.height() - int(bar_height), int(bar_width), int(bar_height))

    def set_audio_levels(self, levels):
        self.audio_levels = levels
        self.update()
        
        
        
        
        

class CreatePlaylistDialog(QDialog):
    def __init__(self, parent, editing):
        super().__init__(parent)
        self.selected_songs = []
        self.isEditing = (editing != None)
        self.view = editing
        
        self.lastList = []
        
        self.available_song_list = []
        self.added_songs_list = []
        
        self.setWindowTitle(f"Create New Playlist")

        self.songs_path = resource_path('Songs')
        
        self.setGeometry(100, 100, 600, 300)
        
        layout = QHBoxLayout()
        main_layout = QVBoxLayout()
        
        if not self.isEditing:
            name_layout = QHBoxLayout()
            playlist_name_label = QLabel("Playlist Name:")
            self.playlist_name_edit = QLineEdit()
            self.playlist_name_edit.setPlaceholderText("Enter playlist name")
            name_layout.addWidget(playlist_name_label)
            name_layout.addWidget(self.playlist_name_edit)
            main_layout.addLayout(name_layout)
        else:
            name_layout = QHBoxLayout()
            playlist_name_label = QLabel("Change name:")
            self.playlist_name_edit = QLineEdit()
            self.playlist_name_edit.setPlaceholderText(os.path.splitext(self.view)[0])
            name_layout.addWidget(playlist_name_label)
            name_layout.addWidget(self.playlist_name_edit)
            main_layout.addLayout(name_layout)
        # Add name layout to main layout
        
        
        

        self.searchBar = QLineEdit()
        self.searchBar.setPlaceholderText("Search for a Title, Artist, or Album")
        self.searchBar.textChanged.connect(self.update_search)
        main_layout.addWidget(self.searchBar)

        self.available_song_list_widget = QListWidget()
        self.available_song_list_widget.setMinimumSize(600, 100)
        self.available_song_list_widget.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.available_song_list_widget.itemDoubleClicked.connect(self.add_song)
        layout.addWidget(self.available_song_list_widget)

        # self.added_song_list_widget = QListWidget()
        # self.added_song_list_widget.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        # self.added_song_list_widget.itemDoubleClicked.connect(self.remove_song)
        # layout.addWidget(self.added_song_list_widget)
        
        self.load_available_songs()
        if self.isEditing:
            print("loading songs")
            self.load_added_songs()
            
        self.lastList = self.available_song_list
            
        self.load_song_list(self.available_song_list)

        buttons_layout = QVBoxLayout()
        
        
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel,
            Qt.Orientation.Vertical, self)
        
        buttons_layout.addWidget(buttons)
        


        if self.isEditing:
            del_button = QPushButton("Delete")
            del_button.setObjectName("smaller")
            del_button.clicked.connect(self.delete_playlist)
            buttons_layout.addWidget(del_button)
            
        
        layout.addLayout(buttons_layout)
        
        layout.addWidget(buttons)
        
        buttons.accepted.connect(self.save_and_close)
        buttons.rejected.connect(self.reject)
        
        main_layout.addLayout(layout)
        
        self.setLayout(main_layout)
        
        

    def load_available_songs(self):
        
        for song_file in os.listdir(self.songs_path):
            if song_file.endswith(('.mp3', '.flac', '.wav','.aiff')):
                title, artist, album = self.get_metadata(os.path.join(self.songs_path,song_file))
                
                self.available_song_list.append({"file":os.path.join(self.songs_path,song_file),"title":title, "artist":artist, "album":album})
                
    def load_song_list(self, song_list):
        if song_list != None:
            self.lastList = song_list
        else:
            song_list = self.lastList
            
        self.available_song_list_widget.clear()
        
        for song in song_list:
            #self.available_song_list_widget.addItem(os.path.splitext(os.path.basename(song["file"]))[0])
            
            
            item = QListWidgetItem()
            item.setData(Qt.ItemDataRole.UserRole, song["file"])
            item_widget = QWidget()
            
            line_text = QLabel(os.path.splitext(os.path.basename(song["file"]))[0])
            line_text.setObjectName("song")
            line_text.setSizePolicy(
                QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
            )
            
            if self.already_added(song["file"]):
                line_push_button = QPushButton('X')
                line_push_button.setObjectName("remove")
                line_push_button.clicked.connect(self.remove_song)
                line_push_button.setSizePolicy(
                    QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed
                )
                line_push_button.setProperty('item_data', song["file"])
            else:
                line_push_button = QPushButton('+')
                line_push_button.setObjectName("add")
                line_push_button.clicked.connect(self.add_song)
                line_push_button.setSizePolicy(
                    QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed
                )
                line_push_button.setProperty('item_data', song["file"])
            
            item_layout = QHBoxLayout()
            item_layout.addWidget(line_text)
            item_layout.addWidget(line_push_button)

            item_widget.setLayout(item_layout)
            
            item.setSizeHint(QSize(item_widget.width()-100, 35))
            self.available_song_list_widget.addItem(item)
            self.available_song_list_widget.setItemWidget(item, item_widget)
            
            seperator = QListWidgetItem()
            seperator.setSizeHint(QSize(0, 5))
            seperator.setFlags(Qt.ItemFlag.NoItemFlags)
            
            self.available_song_list_widget.addItem(seperator)
            
            lineFrame = QFrame()
            lineFrame.setFrameShape(QFrame.Shape.HLine)
            lineFrame.setFrameShadow(QFrame.Shadow.Sunken)
            
            self.available_song_list_widget.setItemWidget(seperator, lineFrame)
                
                
                
    def already_added(self, to_check):
        for song in self.added_songs_list:
            if song["file"] == to_check:
                return True
        return False

    
    def load_added_songs(self):
        playlist_path = os.path.join(resource_path('Playlists'), self.view)
        with open(playlist_path, "r", encoding = "utf-8") as file:
            for line in file:
                line = line[:-1]
                if line.endswith(('.mp3', '.flac', '.wav','.aiff')):
                    title, artist, album = self.get_metadata(os.path.join(self.songs_path,line))
                    
                    self.added_songs_list.append({"file":os.path.join(self.songs_path,line),"title":title, "artist":artist, "album":album})
        print(self.added_songs_list)
                        
    def non_exact_search(self, data, search_term):
        results = []
        print(data)
        search_term_lower = search_term.lower()
        
        for entry in data:
            for key, value in entry.items():
                # Skip the key if it's "file"
                if key == "file":
                    continue
                
                # Check for the search term in the remaining values
                if search_term_lower in value.lower():
                    results.append(entry)
                    break
    
        return results
    
    def update_search(self, text):
        print(text)
        search_results = self.non_exact_search(self.available_song_list, text)
        self.load_song_list(search_results)


    def get_metadata(self, song_path):
        audio = File(song_path)
        
        title = os.path.splitext(song_path)[0]
        artist = ""
        album = ""
        
        if os.path.splitext(song_path)[1].lower() in [".mp3", ".flac", ".aiff"]: 
            if audio:
                title = audio.tags.get('TIT2', ['Unknown Title'])[0]
                artist = audio.tags.get('TPE1', ['Unknown Artist'])[0]
                album = audio.tags.get('TALB', ['Unknown Album'])[0]
                
                
                pict= None
                
                if os.path.splitext(song_path)[1] == ".flac":
                    
                    
                    var = FLAC(song_path)
                    print("Song metadata: "+ str(var))
                    
                    try:
                        artist = var['artist'][0]
                    except KeyError:
                        print("There was an error fetching song artist.")
                        
                                    
                    try:
                        title = var['title'][0]
                    except KeyError:
                        print("There was an error fetching song title")
                        if title != 'Unknown Artist':
                            title = os.path.splitext(os.path.basename(song_path))[0] 
                    
                    pics = var.pictures
                    for p in pics:
                        if p.type == 3: #front cover
                            print("\nfound front cover") 
                            with open("cover.jpg", "wb") as f:
                                pict = (p.data)
                    
                    print(var)
                    
                    try:
                        album = var["ALBUM"]
                    except KeyError:
                        album = "Unknown Album"
        
        return(title,artist,album[0])


    def add_song(self):
        print("Adding song!")
        button = self.sender()
        
        song_to_add = os.path.basename(button.property("item_data"))
        
        print("Adding song:" + str(song_to_add))
        title, artist, album = self.get_metadata(os.path.join(self.songs_path,song_to_add))
                
        self.added_songs_list.append({"file":os.path.join(self.songs_path,song_to_add),"title":title, "artist":artist, "album":album})
        
        button.setText('X')
        button.setObjectName("remove")
        button.clicked.disconnect()  # Disconnect the add_song method
        button.clicked.connect(self.remove_song)  # Connect to remove_song method
        
        button.setStyle(button.style())
        
        print(self.added_songs_list)


    def remove_song(self):
        print("Removing song!")
        button = self.sender()
        
        song_to_remove = button.property("item_data")
        
        print("Removing song:" + str(song_to_remove))

        tempSongs = []
        
        for song in self.added_songs_list:
            if song["file"] != song_to_remove:
                tempSongs.append(song)
                
        self.added_songs_list = tempSongs
        
        button.setText('+')
        button.setObjectName("add")
        button.clicked.disconnect()  # Disconnect the add_song method
        button.clicked.connect(self.add_song)  # Connect to remove_song method
        
        button.setStyle(button.style())
        
        print(self.added_songs_list)

    def get_playlist_info(self):
        playlist_name = self.playlist_name_edit.text().strip()
        selected_songs = [self.available_song_list_widget.item(index).text() for index in range(self.available_song_list_widget.count())]
        return playlist_name, selected_songs
    
    def delete_playlist(self):
        playlist_path2 = os.path.join(resource_path('Playlists'), f"{self.view}")
        os.remove(playlist_path2)
        self.accept()
    
    def save_and_close(self):
        """ 
            Playlists are formatted as such:
            Filename = Playlist name
            Every line is the name of a song from the songs folder
        
        """
        
        playlist_path = os.path.join(os.getcwd(), 'Playlists')
        print(self.playlist_name_edit.text())
        if self.playlist_name_edit.text() == "" and self.isEditing:
            playlist_path = os.path.join(resource_path('Playlists'), f"{self.view}")
            with open(playlist_path, "w", encoding="utf-8") as f:
                for song in self.added_songs_list:
                    print(song)
                    f.write(fix_unicode(os.path.basename(song["file"])) + "\n")
        elif self.isEditing:
            playlist_path2 = os.path.join(resource_path('Playlists'), f"{self.view}")
            os.remove(playlist_path2)
            
            for playlist_path in os.listdir(playlist_path):
                print(os.path.splitext(playlist_path)[0])
                if os.path.splitext(playlist_path)[0] == self.playlist_name_edit.text():
                    error_popup = QMessageBox()
                    error_popup.setIcon(QMessageBox.Icon.Warning)
                    error_popup.setWindowTitle("Error")
                    error_popup.setText("One or more playlists already have this name! Please choose a new name.")
                    error_popup.exec()
                    return
            
            if self.playlist_name_edit.text() == "":
                error_popup = QMessageBox()
                error_popup.setIcon(QMessageBox.Icon.Warning)
                error_popup.setWindowTitle("Error")
                error_popup.setText("You've entered an empty name field. While it might technically work, I'm not about to test the limitations of my code :)")
                error_popup.exec()
                return
                
            playlist_path = os.path.join(resource_path('Playlists'), f"{self.playlist_name_edit.text()}.txt")
            with open(playlist_path, "w", encoding = "utf-8") as f:
                for song in self.added_songs_list:
                    print(song)
                    f.write(fix_unicode(os.path.basename(song["file"])) + "\n")
        else:
            for playlist_path in os.listdir(playlist_path):
                print(os.path.splitext(playlist_path)[0])
                if os.path.splitext(playlist_path)[0] == self.playlist_name_edit.text():
                    error_popup = QMessageBox()
                    error_popup.setIcon(QMessageBox.Icon.Warning)
                    error_popup.setWindowTitle("Error")
                    error_popup.setText("One or more playlists already have this name! Please choose a new name.")
                    error_popup.exec()
                    return
            
            if self.playlist_name_edit.text() == "":
                error_popup = QMessageBox()
                error_popup.setIcon(QMessageBox.Icon.Warning)
                error_popup.setWindowTitle("Error")
                error_popup.setText("You've entered an empty name field. While it might technically work, I'm not about to test the limitations of my code.")
                error_popup.exec()
                return
            
            try:
                playlist_path = os.path.join(resource_path('Playlists'), f"{self.playlist_name_edit.text()}.txt")
                with open(playlist_path, "w", encoding = "utf-8") as f:
                    for song in self.added_songs_list:
                        print(song)
                        f.write(fix_unicode(os.path.basename(song["file"])) + "\n")
            except OSError:
                error_popup = QMessageBox()
                error_popup.setIcon(QMessageBox.Icon.Warning)
                error_popup.setWindowTitle("Error")
                error_popup.setText("Forbidden character detected! Name cannot contain the following characters: < > : \" / \\ | ? *")
                error_popup.exec()
                return
                
                
                        
        self.accept()


class DragDropWidget(QWidget):
    
    
    filesDropped = pyqtSignal(list)
    
    def __init__(self):
        super().__init__()
        
        # Set up the label to display the drop target
        self.label = QLabel("Drag files or folders here", self)
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label.setStyleSheet("border: 2px dashed #aaa; padding: 50px;")
        self.dropped_files = []
        
        # Set up the close button
        self.close_button = QPushButton("Finish", self)
        self.close_button.clicked.connect(self.close)
        
        # Set up the layout
        layout = QVBoxLayout()
        layout.addWidget(self.label)
        self.setLayout(layout)
        
        # Enable drag and drop
        self.setAcceptDrops(True)

    def dragEnterEvent(self, event):
        # Accept the event if it contains URLs (files or folders)
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event):
        # Get the list of dropped URLs
        urls = event.mimeData().urls()
        
        # Extract the file paths and display them
        if urls:
            file_paths = [url.toLocalFile() for url in urls]
            self.label.setText("\n".join(file_paths))
            print("Dropped files/folders:")
            for path in file_paths:
                self.dropped_files.append(path)
        event.acceptProposedAction()
        
    def closeEvent(self, event):
        # Emit the signal with the list of file paths when the dialog is closed
        self.filesDropped.emit(self.dropped_files)
        event.accept()
        
        
        
        

def exit_handler():
    print("closing musicmanager")
        
    with open(os.path.join(utility_path,'Settings.json')) as f:
        data = json.load(f)

    with open(os.path.join(utility_path,'Settings.json'),"w") as f:
        json.dump(settings, f)
        
    print("Settings saved.")
            
            
            
if __name__ == '__main__':
    
    set_app_user_model_id("com.musicmanager.myapp")
        
    
    utility_path = resource_path('Utility')
    style_path = os.path.join(utility_path, f"Style.txt")
    settings = None
    
    fontcolor = "#000000"
    
    #See if settings already exists; if not, create from template.
    
    try:
        with open(os.path.join(utility_path,'Settings.json'), 'r') as f:
            settings = json.load(f)
            
    except FileNotFoundError or FileExistsError:
        with open(os.path.join(utility_path,'Settings.json'), 'w') as f:
            json.dump(settings_template, f)
            
    #then load settings
    with open(os.path.join(utility_path,'Settings.json'), 'r') as f:
            settings = json.load(f)
            
    #If settings already exists, but there's a change tothe default settings, this will catch it
    for key in settings_template["settings"]:
        try:
            settings["settings"][key]
        except KeyError:
            print("Old settings detected, adding new features")
            settings["settings"][key] = settings_template["settings"][key]
            print("added "+str(key))
            
            

    app = QApplication(sys.argv)
    with open(style_path, "r") as f:
        style = f.read().replace('\n', '')
        
        style = style.replace('(font_color)',fontcolor)
        
        print(style)
        app.setStyleSheet(style)
        
    app.setWindowIcon(QIcon(os.path.join(utility_path,"AppIcon.png")))
    player = MusicPlayer(settings["settings"])
    player.show()
    atexit.register(exit_handler)
    sys.exit(app.exec())
    

        


        
        
