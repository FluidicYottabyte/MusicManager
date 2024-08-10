import sys
import os
import random
import time
import math
import numpy as np
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QLabel, QVBoxLayout, QHBoxLayout, QWidget,
    QSlider, QListWidget, QListWidgetItem, QPushButton, QDialog, QDialogButtonBox,
    QVBoxLayout, QHBoxLayout, QMessageBox, QFileDialog, QLineEdit, QAbstractItemView
)
from PyQt6.QtGui import QPixmap, QFont, QPainter, QColor
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

    
settings_template = {}

settings_template["settings"] = {}
settings_template["settings"]["volume"] = 50

system_volume = 50


class MusicPlayer(QMainWindow):
    
    
    
    def __init__(self, settings):
        
        super().__init__()
        
        self.utilities = resource_path('Utility')
        
        self.setWindowTitle('Music Manager')
        self.setGeometry(100, 100, 800, 600)
        
        self.saved_position = 0
        
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
        self.playlist_widget.setIconSize(QSize(self.playlist_widget.sizeHint().width(),50))
        font = QFont()
        font.setFamily("serif")
        font.setPointSize(13)
        font.setBold(False)
        font.setItalic(False)
        self.playlist_widget.setFont(font)
        self.playlist_widget.itemClicked.connect(self.play_playlist)
        
        self.playlist_widget.itemDoubleClicked.connect(self.show_playlist_popup)
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
            if not os.path.isfile(os.path.join(resource_path("Songs"),os.path.basename(path1))): #Checks if file already exists, or not
                shutil.copy(path1,os.path.join(resource_path("Songs"),os.path.basename(path1)))
        
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
                item = QListWidgetItem(os.path.splitext(playlist_file)[0])
                self.playlist_widget.addItem(item)
                item.setData(Qt.ItemDataRole.UserRole, playlist_file)
        


    def play_playlist(self, item):
        playlist_file = item.data(Qt.ItemDataRole.UserRole)
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
        
        
        self.load_song_metadata(song_full_path)
        self.update_progress()

    def load_song_metadata(self, song_path):
        audio = File(song_path)
        if os.path.splitext(song_path)[1] == ".mp3" or os.path.splitext(song_path)[1] == ".flac" or os.path.splitext(song_path)[1] == ".aiff":
            if audio:
                title = audio.tags.get('TIT2', ['Unknown Title'])[0]
                artist = audio.tags.get('TPE1', ['Unknown Artist'])[0]
                album = audio.tags.get('TALB', ['Unknown Album'])[0]
                self.song_details.setText(f"{title} - {artist}")
                
                pict= None
                
                if os.path.splitext(song_path)[1] == ".flac":
                    
                    
                    var = FLAC(song_path)
                    artist = var['artist'][0]
                    title = var['title'][0]
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
                else:
                    self.album_art.clear()
                    
        else:
            self.song_details.setText(os.path.splitext(os.path.basename(song_path))[0]) 
            pixmap = QPixmap(os.path.join(self.utilities, "default.png"))
            self.album_art.setPixmap(pixmap)

    def stop_song(self):
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

    def show_playlist_popup(self, item):
        playlist_file = item.data(Qt.ItemDataRole.UserRole)
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
        
        self.setWindowTitle(f"Create New Playlist")

            
        
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
        

        self.available_song_list_widget = QListWidget()
        self.available_song_list_widget.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.available_song_list_widget.itemDoubleClicked.connect(self.add_song)
        layout.addWidget(self.available_song_list_widget)

        self.added_song_list_widget = QListWidget()
        self.added_song_list_widget.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.added_song_list_widget.itemDoubleClicked.connect(self.remove_song)
        layout.addWidget(self.added_song_list_widget)
        
        self.load_available_songs()
        if self.isEditing:
            self.load_added_songs()

        buttons_layout = QVBoxLayout()

        add_button = QPushButton("Add >")
        add_button.setObjectName("smaller")
        add_button.clicked.connect(self.add_song)
        buttons_layout.addWidget(add_button)

        remove_button = QPushButton("< Remove")
        remove_button.setObjectName("smaller")
        remove_button.clicked.connect(self.remove_song)
        buttons_layout.addWidget(remove_button)
        
        if self.isEditing:
            del_button = QPushButton("Delete Playlist")
            del_button.setObjectName("smaller")
            del_button.clicked.connect(self.delete_playlist)
            buttons_layout.addWidget(del_button)
        
        layout.addLayout(buttons_layout)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel,
            Qt.Orientation.Vertical, self)
        
        layout.addWidget(buttons)
        
        buttons.accepted.connect(self.save_and_close)
        buttons.rejected.connect(self.reject)
        
        main_layout.addLayout(layout)
        
        self.setLayout(main_layout)
        
        

    def load_available_songs(self):
        songs_path = resource_path('Songs')
        for song_file in os.listdir(songs_path):
            if song_file.endswith(('.mp3', '.flac', '.wav')):
                self.available_song_list_widget.addItem(song_file)
                
    def load_added_songs(self):
        playlist_path = os.path.join(resource_path('Playlists'), self.view)
        with open(playlist_path, "r", encoding = "utf-8") as file:
            for line in file:
                song_path = line.strip()
                if os.path.isfile(os.path.join(resource_path('Songs'), song_path)):
                    self.selected_songs.append(song_path)
                    self.added_song_list_widget.addItem(song_path)

    def add_song(self):
        print("aDDING SONG")
        selected_item = self.available_song_list_widget.currentItem()
        if selected_item:
            print("We are selected")
            selected_song = selected_item.text()
            song_path = os.path.join(resource_path('Songs'), selected_song)
            song_name = os.path.basename(song_path)
            print(song_name)
            self.selected_songs.append(song_name)
            print(self.selected_songs)
            self.added_song_list_widget.addItem(song_name)
        else:
            return None

    def remove_song(self):
        for item in self.added_song_list_widget.selectedItems():
            self.added_song_list_widget.takeItem(self.added_song_list_widget.row(item))
            self.selected_songs.remove(item.text())

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
                for song in self.selected_songs:
                    print(song)
                    f.write(fix_unicode(song) + "\n")
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
                for song in self.selected_songs:
                    print(song)
                    f.write(fix_unicode(song) + "\n")
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
                
            playlist_path = os.path.join(resource_path('Playlists'), f"{self.playlist_name_edit.text()}.txt")
            with open(playlist_path, "w", encoding = "utf-8") as f:
                for song in self.selected_songs:
                    print(song)
                    f.write(fix_unicode(song) + "\n")
                
                
                        
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


    data["settings"]['volume'] = system_volume

    with open(os.path.join(utility_path,'Settings.json'),"w") as f:
        json.dump(data, f)
        
    print("Settings saved.")
            
            
            
if __name__ == '__main__':
    utility_path = resource_path('Utility')
    style_path = os.path.join(utility_path, f"Style.txt")
    settings = None
    
    
    #See if settings already exists; if not, create from template.
    
    try:
        with open(os.path.join(utility_path,'Settings.json'), 'r') as f:
            settings = json.load(f)
            
    except FileNotFoundError or FileExistsError:
        with open(os.path.join(utility_path,'Settings.json'), 'w') as f:
            json.dump(settings_template, f)
            
    with open(os.path.join(utility_path,'Settings.json'), 'r') as f:
            settings = json.load(f)

    app = QApplication(sys.argv)
    with open(style_path, "r") as f:
        style = f.read().replace('\n', '')
        print(style)
        app.setStyleSheet(style)
    player = MusicPlayer(settings["settings"])
    player.show()
    atexit.register(exit_handler)
    sys.exit(app.exec())
    

        


        
        
