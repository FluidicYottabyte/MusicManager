"""Lord forgive me for the contents present in this file- I simply started programming and never stopped."""


import array
from logging import warn, warning
import re
import sys
import os
import random
from telnetlib import theNULL
import time
import math
from typing import Type
from xmlrpc.client import TRANSPORT_ERROR
import numpy as np
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QLabel, QVBoxLayout, QHBoxLayout, QWidget,
    QSlider, QListWidget, QListWidgetItem, QPushButton, QDialog, QDialogButtonBox,
    QVBoxLayout, QHBoxLayout, QMessageBox, QFileDialog, QLineEdit, QAbstractItemView, 
    QSizePolicy, QFrame, QProgressBar
)
from PyQt6.QtGui import QPixmap, QFont, QPainter, QColor,QIcon
from PyQt6.QtCore import Qt, QTimer, QSize, pyqtSignal, QThread
from PyQt6 import QtCore
from mutagen import File
from mutagen.flac import FLAC, Picture
from PIL import Image
from mutagen.id3 import ID3
import json
import atexit
import shutil 
import codecs

from sympy import false, true
from voluptuous import ValueInvalid
from Updater import GitUpdater
import ctypes
import threading
from queue import Queue

import asyncio


from aioslsk.search.model import SearchRequest
from aioslsk.commands import GetUserStatusCommand
from aioslsk.user.model import UserStatus
from aioslsk.transfer.model import Transfer, TransferDirection


from SoulseekManager import Soulseek

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
settings_template["settings"]["slskusername"] = ''
settings_template["settings"]["slskpassword"] = ''


class MusicPlayer(QMainWindow):
    
    
    
    def __init__(self, settings):
        
        super().__init__()
        
        self.updater = GitUpdater()
        
        self.can_open_soulseek = True
        
        updateStatus = None
        
        try:
            updateStatus = self.updater.check_for_updates()
            
            if not updateStatus:
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
            
        except:
            print("Looks like there's an issue with the updater! Oh well!")
        
        
    
        self.utilities = resource_path('Utility')
        self.songs_path = resource_path('Songs')
        
        self.available_song_list = []
        
        self.setWindowTitle('Music Manager')
        self.setGeometry(100, 100, 800, 600)
        
        self.saved_position = 0
        self.stopped = True
        self.totalDownloads = 0
        
        self.playing = ""
        self.playing_a_single_song = False
        
        self.playlist_array = []
        
        self.librarysearch = ""
        self.playlistsearch = ""
        
        self.dedicated_song_button = None
        
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
        
        self.song_details = QLabel('No song playing',alignment=Qt.AlignmentFlag.AlignTop)
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
        self.volume_slider.setValue(settings["settings"]["volume"])  # Default volume level
        
        self.system_volume = settings["settings"]["volume"]
        
        self.volume_slider.valueChanged.connect(self.change_volume)
        self.song_info_layout.addWidget(self.volume_slider)
        
        self.otherLayout.addLayout(self.song_info_layout)

        # Control buttons
        self.control_layout = QHBoxLayout()
        
        self.play_button = QPushButton(u'\u25b6')
        self.play_button.clicked.connect(lambda : self.play_song(from_main = True))
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


        #Additional Buttons
        
        self.additionalButtonsLayout = QHBoxLayout()
        
        self.soulseek_open = QPushButton("Connect to Soulseek")
        self.soulseek_open.clicked.connect(self.openSoulseek)
        self.additionalButtonsLayout.addWidget(self.soulseek_open)
        
        self.library_open = QPushButton("Switch to library")
        self.library_open.clicked.connect(self.change_search_params)
        self.additionalButtonsLayout.addWidget(self.library_open)
        

        # Playlists
        self.PLaylistLayout = QVBoxLayout()
        
        self.PLaylistLayout.addLayout(self.additionalButtonsLayout)
        
        self.loading_progress_bar = QProgressBar()
        self.loading_progress_bar.setMinimum(0)
        self.loading_progress_bar.setMaximum(100)
        
        self.PLaylistLayout.addWidget(self.loading_progress_bar)
        
        self.searchBar = QLineEdit()
        self.searchBar.setPlaceholderText("Search your playlists")
        self.searchBar.textChanged.connect(self.update_search)
        
        self.searching_library = False
        
        self.PLaylistLayout.addWidget(self.searchBar)
        
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
        
        self.change_volume(self.system_volume)
        
        self.load_available_songs()
        
    
    
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
        
        self.load_available_songs()
        
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
        self.system_volume = value
        settings["settings"]["volume"] = value
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
                
                self.playlist_array.append({"name":os.path.splitext(playlist_file)[0]})
                
    
    
    def load_playlists_with_includion_list(self, lists_too_load):
        self.playlist_widget.clear()  # Clear existing items before loading
        playlists_path = resource_path('Playlists')
        for playlist_file in os.listdir(playlists_path):
            
            is_able_to_add = True
            
            try:
                print(lists_too_load.index(os.path.splitext(playlist_file)[0]))
            except ValueError:
                print("Playlist is not in inclusion list")
                is_able_to_add = False
            
            if playlist_file.endswith('.txt') and is_able_to_add:
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
    
    
    def change_search_params(self):
        print("Library and playlist search params saved as: ", self.librarysearch, self.playlistsearch)
        if self.searching_library:
            self.searching_library = False
            
            if self.librarysearch == "" and self.playlistsearch == "":
                self.update_search(self.playlistsearch)
                #self.load_playlists()
                
            self.searchBar.setPlaceholderText("Search your playlists")
            self.searchBar.setText(self.playlistsearch)
            self.library_open.setText("Switch to Library")
        else:
            self.searching_library = True
            
            if self.librarysearch == "" and self.playlistsearch == "":
                self.update_search(self.librarysearch)
                #self.load_available_songs(self.available_song_list)
                
            self.searchBar.setPlaceholderText("Search your library")
            self.searchBar.setText(self.librarysearch)
            self.library_open.setText("Switch to Playlists")
            

    def update_search(self, text):
        print(text)
        
        
        
        if self.searching_library:
            print("Now searching in the library")
            if text == "":
                self.load_song_list(self.available_song_list)
                self.librarysearch = text
                return
                
            search_results = self.non_exact_search(self.available_song_list, text)
            self.load_song_list(search_results)
            self.librarysearch = text
            
        else:
            if text == "":
                self.load_playlists()
                self.playlistsearch = text
                return
            print("Searching in the playlists")
            search_results = self.non_exact_search(self.playlist_array, text)
            print("Search results ",search_results)
            temp_playlist_array_reformatting = []
            for i in search_results:
                for key, value in i.items():
                    temp_playlist_array_reformatting.append(value)
                    
            search_results = temp_playlist_array_reformatting
            
            print("Reformatteds search results: ", search_results)
                
            self.playlistsearch = text
            
            self.load_playlists_with_includion_list(search_results)
            
            
            
            
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
        

    def load_song_list(self, song_list):
        self.playlist_widget.setUpdatesEnabled(False)

        if song_list != None:
            self.lastList = song_list
        else:
            song_list = self.lastList
            
        self.playlist_widget.clear()
        
        for song in song_list:
            
            
            item = QListWidgetItem()
            item.setData(Qt.ItemDataRole.UserRole, song["file"])
            item_widget = QWidget()
            
            line_text = QLabel(os.path.splitext(os.path.basename(song["file"]))[0])
            line_text.setObjectName("song")
            line_text.setSizePolicy(
                QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
            )
            
            print("Looking at song file: ", song["file"])
            
            if self.playing == song["file"] and self.playing != "":
                print("Setting button to pause")
                line_push_button = QPushButton('II')
                line_push_button.setObjectName("playlists")
                line_push_button.clicked.connect(self.stop_song)
                line_push_button.setSizePolicy(
                    QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed
                )
                line_push_button.setProperty('item_data', song["file"])
            else:
                print("Setting button to play")
                line_push_button = QPushButton(u'\u25b6')
                line_push_button.setObjectName("playlists")
                line_push_button.clicked.connect(lambda : self.play_song(noplaylist=True))
                line_push_button.setSizePolicy(
                    QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed
                )
                line_push_button.setProperty('item_data', song["file"])
            
            item_layout = QHBoxLayout()
            item_layout.addWidget(line_text)
            item_layout.addWidget(line_push_button)

            item_widget.setLayout(item_layout)
            
            item.setSizeHint(QSize(item_widget.width()-100, 35))
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
        
        self.playlist_widget.setUpdatesEnabled(True)

    
    
    def load_available_songs(self):
        
        self.available_song_list = []
        
        for song_file in os.listdir(self.songs_path):
            if song_file.endswith(('.mp3', '.flac', '.wav','.aiff', '.m4a')):
                title, artist, album = self.get_metadata(os.path.join(self.songs_path,song_file))
                
                self.available_song_list.append({"file":os.path.join(self.songs_path,song_file),"title":title, "artist":artist, "album":album})
                


    #
    # Note: Kill me, this should be callable from another method, but I hate myself. And didn't write it like that.
    # This stupid fucking program gets moe bloated by the minute. At least it still works.
    #
    
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
        
        try:
            return(title,artist,album[0])
        except:
            return(title,artist,album)



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

    
    def play_song(self, *args, **kwargs):
        
        noplaylist = kwargs.get('noplaylist', False)
        loop = kwargs.get('loop', False)
        from_main_button = kwargs.get('from_main', False)
        
        
        if from_main_button and self.dedicated_song_button != None:
            try:
                self.dedicated_song_button.clicked.disconnect()
            except TypeError:
                pass
            
            self.dedicated_song_button.setText("II")
            
            self.dedicated_song_button.clicked.connect(self.stop_song)  # Connect to remove_song method
        
        
        if noplaylist:
            print("No playlist required to play song")
            sender = self.sender()
            single_song_to_play = self.sender().property("item_data")
            
            sender.setText("II")
            
            if self.dedicated_song_button != None and self.dedicated_song_button != sender:
                self.dedicated_song_button.setText(u'\u25b6')
                
                try:
                    self.dedicated_song_button.clicked.disconnect()
                except TypeError:
                    pass
                
                self.dedicated_song_button.clicked.connect(lambda : self.play_song(noplaylist=True))

            try:
                sender.clicked.disconnect()
            except TypeError:
                pass
            
            sender.clicked.connect(self.stop_song)  # Connect to remove_song method
        
            sender.setStyle(sender.style())
            
            self.dedicated_song_button = sender
            
            print(single_song_to_play)
        elif self.dedicated_song_button != None and from_main_button:
            single_song_to_play = self.dedicated_song_button.property("item_data")
        else:
            self.dedicated_song_button = None
            single_song_to_play = False
            
        if loop:
            single_song_to_play = self.playing
        
        if not self.current_playlist and single_song_to_play == False:
            print("Required variables not present, must abort")
            return

        if self.current_index == -1 or ((self.playing != single_song_to_play) and self.playing != "" and single_song_to_play != False):
            self.current_index = 0

        if ((self.playing != single_song_to_play) and self.playing != "" and single_song_to_play != False):
            print("Resetting save position")
            self.saved_position = 0

        if single_song_to_play != False:
            song_path = single_song_to_play
            self.playing_a_single_song = True
        else:
            song_path = self.current_playlist[self.current_index]
            self.playing_a_single_song = False
            
            
        song_full_path = os.path.join(resource_path('Songs'), song_path)
        print(song_full_path)
        self.playing = song_full_path
        media = self.instance.media_new(song_full_path)
        

        # If there's a saved position, set it
        if self.saved_position > 0:
            print("save position valid")
            media.add_option(f'start-time={self.saved_position / 1000}')

        self.player.set_media(media)
        
        print("System volume: "+str(self.system_volume))
        
        self.player.play()
        
        self.timer.start()
        
        self.load_song_metadata(song_full_path)
        self.update_progress()
        
        time.sleep(.001)
        
        self.player.audio_set_volume(self.system_volume)
        
        self.stopped = False

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
                    try:
                        pict = tags.getall("APIC")[0].data
                    except IndexError:
                        print("Picture could not be aquied at all")
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
        
        try:
            if self.sender().property("item_data") == self.playing:
                self.sender().setText(u'\u25b6')
                
                try:
                    self.sender().clicked.disconnect()
                except TypeError:
                    pass
                
                self.sender().clicked.connect(lambda : self.play_song(noplaylist=True))
                
        except Exception as warn:
            print(warn)
        
        if self.dedicated_song_button != None:
            self.dedicated_song_button.setText(u'\u25b6')
            
            try:
                self.dedicated_song_button.clicked.disconnect()
            except TypeError:
                pass
            
            self.dedicated_song_button.clicked.connect(lambda : self.play_song(noplaylist=True))
        
        self.stopped = True
        # Save the current position before stopping
        self.saved_position = self.player.get_time()
        print(self.saved_position)
        self.player.stop()
        self.timer.stop()

    def skip_forward(self):
        if self.current_playlist and not self.playing_a_single_song:
            self.saved_position = 0
            self.current_index = (self.current_index + 1) % len(self.current_playlist)
            self.play_song()

    def skip_back(self):
        if self.current_playlist and not self.playing_a_single_song:
            self.saved_position = 0
            self.current_index = (self.current_index - 1) % len(self.current_playlist)
            self.play_song()

    def shuffle_songs(self):
        if self.current_playlist and not self.playing_a_single_song:
            self.saved_position = 0
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
            if self.playing_a_single_song:
                self.saved_position = 0
                self.play_song(loop = True)
            self.skip_forward()

    def set_position(self, position):
        self.player.set_position(position / 1000)

    def show_playlist_popup(self):
        button = self.sender()

        # Retrieve the data stored in the button
        playlist_file = button.property('item_data')
        dialog = CreatePlaylistDialog(self, playlist_file)
        dialog.exec()
        
        if not self.searching_library:
            self.load_playlists()

    def create_playlist(self):
        dialog = CreatePlaylistDialog(self, None)
        dialog.exec()
        if not self.searching_library:
            self.load_playlists()

    def openSoulseek(self):
        if not self.can_open_soulseek:
            error_popup = QMessageBox()
            error_popup.setIcon(QMessageBox.Icon.Information)
            error_popup.setWindowTitle("Downloads ongoing...")

            error_popup.setText("There are currently ongoing downloads. All SoulSeek related processees must wait for them to complete!")
            
            error_popup.exec()
            
            return
            
        localSoulseek = SoulseekConnect(self, settings=settings)
        localSoulseek.closing_event.connect(self.being_background_downloads)
        localSoulseek.exec()

    def being_background_downloads(self, SoulseekPassed : Soulseek, totalDownloads):
        self.can_open_soulseek = False
        self.finished_downloads = 0
                
        self.totalDownloads = totalDownloads
        
        self.download_thread = DownloadThread(SoulseekPassed, totalDownloads)
        
        # Connect the progress and finished signals to appropriate slots
        #self.download_thread.progress_updated.connect(self.on_progress_updated)
        self.download_thread.finished.connect(self.on_downloads_complete)
        self.download_thread.update_progress.connect(self.on_update_progress_bar)
        
        # Start the download thread
        self.download_thread.start()
        
    def on_update_progress_bar(self):
        self.finished_downloads += 1
        self.progress = int(self.finished_downloads / self.totalDownloads * 100)
        self.loading_progress_bar.setValue(self.progress)

    def on_downloads_complete(self, info):
        print("DOWNLOADS DONE")
        
        self.load_available_songs()
        
        self.can_open_soulseek = True
        
        self.loading_progress_bar.setValue(0)
        
        error_popup = QMessageBox()
        error_popup.setIcon(QMessageBox.Icon.Information)
        error_popup.setWindowTitle("Downloads Complete")
        if info["failed"] > 0:
            error_popup.setText(f"Downloads completed with {info['failed']} failed downloads.")
        else:
            error_popup.setText("Downloads completed with no issues!")
        
        error_popup.exec()





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
            if song_file.endswith(('.mp3', '.flac', '.wav','.aiff', '.m4a')):
                title, artist, album = self.get_metadata(os.path.join(self.songs_path,song_file))
                
                self.available_song_list.append({"file":os.path.join(self.songs_path,song_file),"title":title, "artist":artist, "album":album})
                
    def load_song_list(self, song_list):
        self.available_song_list_widget.setUpdatesEnabled(False)

        if song_list != None:
            self.lastList = song_list
        else:
            song_list = self.lastList
            
        self.available_song_list_widget.clear()
        
        for song in song_list:
            
            
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
        
        self.available_song_list_widget.setUpdatesEnabled(True)
                
                
                
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
        
        try:
            return(title,artist,album[0])
        except:
            return(title,artist,album)


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




class InputMessageBox(QMessageBox):
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle("Input Dialog")
        
        # Create layout
        layout = QVBoxLayout()
        
        # Create two QLineEdit widgets
        self.textInfo = QLabel("Login:")

        
        self.input1 = QLineEdit(self)
        self.input1.setPlaceholderText("Username")
        self.input2 = QLineEdit(self)
        self.input2.setPlaceholderText("Password")
        
        # Add QLineEdit widgets to layout
        layout.addWidget(self.textInfo)
        layout.addWidget(self.input1)
        layout.addWidget(self.input2)
        
        # Set the layout to the message box
        self.layout().addLayout(layout, 0, 0)
        
        # Add standard buttons (OK and Cancel)
        self.addButton(QMessageBox.StandardButton.Ok)
        self.addButton(QMessageBox.StandardButton.Cancel)
        
        # Connect buttons to functions
        self.button(QMessageBox.StandardButton.Ok).clicked.connect(self.accept)
        self.button(QMessageBox.StandardButton.Cancel).clicked.connect(self.reject)

    def getInputs(self):
        # Return the text entered in the QLineEdit widgets
        return self.input1.text(), self.input2.text()





class LoadingWorker(QThread):
    beginloading = pyqtSignal()
    finished = pyqtSignal()
    send_song = pyqtSignal(list)
    send_to_main_thread = pyqtSignal(object)

    def __init__(self, loading_queue, loaded_songs_queue, adding_song_funct):
        super().__init__()
        self.loading_queue = loading_queue
        self.loaded_songs_queue = loaded_songs_queue
        self.add_song = adding_song_funct

    def enqueuesongs(self, songs):
        self.loading_queue.put(songs)


    def run(self):
        while not self.loading_queue.empty():
                
                
            task, args = self.loading_queue.get()
            if task:
                print("Got task!: "+ str(task))
            if task is None:
                break
            try:
                task(*args)
            except Exception as e:
                print(f"Exception: {e}")
            finally:
                print("Finished task")
                self.loading_queue.task_done()
                print("Sent task")

        print("Queue empty")
        self.finished.emit()



    def load_song_list(self, song_list):
        widget_items_to_return = []

        for song in song_list:
            item = QListWidgetItem()
            item.setData(Qt.ItemDataRole.UserRole, song["title"])
            item_widget = QWidget()

            line_text = QLabel(os.path.splitext(os.path.basename(song["title"]))[0]+"   --  "+str.upper(os.path.splitext(os.path.basename(song["title"]))[1]))
            line_text.setObjectName("song")
            line_text.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

            line_push_button = QPushButton(u'\u2913')
            line_push_button.setObjectName("add")
            line_push_button.clicked.connect(self.add_song)
            line_push_button.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
            line_push_button.setProperty('item_data', song)

            item_layout = QHBoxLayout()
            item_layout.addWidget(line_text)
            item_layout.addWidget(line_push_button)

            item_widget.setLayout(item_layout)
            item.setSizeHint(QSize(item_widget.width() - 100, 35))

            self.send_to_main_thread.emit([item, item_widget])
            #self.loaded_songs_queue.put([item, item_widget])

            separator = QListWidgetItem()
            separator.setSizeHint(QSize(0, 5))
            separator.setFlags(Qt.ItemFlag.NoItemFlags)

            line_frame = QFrame()
            line_frame.setFrameShape(QFrame.Shape.HLine)
            line_frame.setFrameShadow(QFrame.Shadow.Sunken)

            #self.loaded_songs_queue.put([separator, line_frame])
            self.send_to_main_thread.emit([separator, line_frame])








class SoulseekConnect(QDialog):
    
    
    closing_event = pyqtSignal(Soulseek, int)
    
    
    def __init__(self, parent, settings):
        super().__init__(parent)
        
        if settings["settings"]["slskusername"] == '': 
            msg_box = InputMessageBox()
            result = msg_box.exec()
            print(result)
            if result == 1:
                input1, input2 = msg_box.getInputs()
                
                settings["settings"]["slskusername"] = input1
                settings["settings"]["slskpassword"] = input2
                print("Got username and password as: "+str(input1) + " and "+str(input2))
            else:
                print("Cancelled")
                self.reject()
                return
            
        if settings["settings"]["slskpassword"] == "":
            self.show_login_error()
            return
                
        try:
            self.soul_seek_client = Soulseek(username= settings["settings"]["slskusername"], password= settings["settings"]["slskpassword"])
            self.soul_seek_client.login_unsuccessfull.connect(self.show_login_error)
        except Exception:
            print("Could not connect. Possible error occured.")
            self.show_login_error()
            return
            

        print("client created")
    
        
        #asyncio.run(self.runAsync())
        
        self.selected_songs = []
        
        self.lastList = []
        
        self.download_count = 0
        
        self.available_song_list = []
        self.added_songs_list = []
        
        self.loading_queue = Queue()
        self.loaded_songs_queue = Queue()
        
        
        self.all_transfers = []
        
        
        self.setWindowTitle(f"Soulseek Manager")

        self.songs_path = resource_path('Songs')
        
        self.setGeometry(100, 100, 600, 300)
        
        layout = QHBoxLayout()
        main_layout = QVBoxLayout()
        final_layout = QHBoxLayout()
        
        print("layouts created")

        name_layout = QHBoxLayout()
        playlist_name_label = QLabel("Search Soulseek (Downloads will inititate once window is closed):")
        name_layout.addWidget(playlist_name_label)
        main_layout.addLayout(name_layout)

        # Add name layout to main layout
        
        
        self.searchWidget = QHBoxLayout()

        self.searchBar = QLineEdit()
        self.searchBar.setPlaceholderText("Search for a Title, Artist, or Album")
        self.searchWidget.addWidget(self.searchBar)
        
        self.searchButton = QPushButton("Search")
        self.searchButton.clicked.connect(self.update_search)
        self.searchWidget.addWidget(self.searchButton)
        
        main_layout.addLayout(self.searchWidget)

        self.available_song_list_widget = QListWidget()
        self.available_song_list_widget.setMinimumSize(600, 100)
        self.available_song_list_widget.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.available_song_list_widget.itemDoubleClicked.connect(self.add_song)
        layout.addWidget(self.available_song_list_widget)
        
        self.available_song_list_widget.verticalScrollBar().valueChanged.connect(self.scrolled)
        
        
        downloadsLayout = QVBoxLayout()
        
        queued_label = QLabel("Download Queue:")
        downloadsLayout.addWidget(queued_label)
        
        self.queued_song_download_widget = QListWidget()
        self.queued_song_download_widget.setMinimumSize(250, 100)
        self.queued_song_download_widget.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        downloadsLayout.addWidget(self.queued_song_download_widget)
        
        print("finished soulseek UI")


        # self.added_song_list_widget = QListWidget()
        # self.added_song_list_widget.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        # self.added_song_list_widget.itemDoubleClicked.connect(self.remove_song)
        # layout.addWidget(self.added_song_list_widget)
        
        #self.load_available_songs()

        self.load_added_songs()
            
        self.lastList = self.available_song_list
        
        buttons_layout = QVBoxLayout()
        
        
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel,
            Qt.Orientation.Vertical, self)
        
        buttons_layout.addWidget(buttons)
            
        
        #layout.addLayout(buttons_layout)
        
        #layout.addWidget(buttons)
        
        buttons.accepted.connect(self.save_and_close)
        buttons.rejected.connect(self.close_without_downloading)
        
        main_layout.addLayout(layout)
        
        final_layout.addLayout(main_layout)
        final_layout.addLayout(downloadsLayout)
        final_layout.addLayout(buttons_layout)
        
        self.setLayout(final_layout)
        
        print("SOULSEEK INIT FINISH")
        
        
    def scrolled(self, value):

        if value == self.available_song_list_widget.verticalScrollBar().maximum():
             self.waiting_loader()
        
    async def searchAsync(self, toSearch):
        # Run the synchronous search method in an executor to avoid blocking the event loop
        loop = asyncio.get_event_loop()
        results = await loop.run_in_executor(None, self.soul_seek_client.search, toSearch)
        print("GOT RESULTS ON CLIENT SIDE")
        return results
    
    async def downloadAsynch(self, downloadinfo):
        loop = asyncio.get_event_loop()
        results = await loop.run_in_executor(None, self.soul_seek_client.download, downloadinfo["user"], downloadinfo["file"])
        print("Got results for download in main")
        return results

    def load_available_songs(self):

        for song_file in os.listdir(self.songs_path):
            if song_file.endswith(('.mp3', '.flac', '.wav','.aiff')):
                title, artist, album = self.get_metadata(os.path.join(self.songs_path,song_file))
                
                self.available_song_list.append({"file":os.path.join(self.songs_path,song_file),"title":title, "artist":artist, "album":album})
                
                
    def loading_thread(self, songstoload):
        print("creating thread")
        
        
        with self.loading_queue.mutex:
            self.loading_queue.queue.clear()

        with self.loaded_songs_queue.mutex:
            self.loaded_songs_queue.queue.clear()

        
        self.loadingthread = QThread()
        self.worker = LoadingWorker(self.loading_queue, self.loaded_songs_queue, self.add_song)
        self.worker.send_to_main_thread.connect(self.handle_object_from_worker)
        self.worker.beginloading.connect(self.worker.run)
        self.worker.send_song.connect(self.worker.enqueuesongs)
        self.worker.finished.connect(self.waiting_loader)
        self.worker.moveToThread(self.loadingthread)
        #self.loadingthread.started.connect(self.loadingthread.run)
        self.loadingthread.start()
        
        print("started thread")
        
        """ self.loadingThread = QThread(target=self.loading_thread_target)
        self.loadingThread.start() """
        self.loading_manager(songstoload)
        
        
        
    def handle_object_from_worker(self, obj):
        print("Got objects in main thread!")
        self.loaded_songs_queue.put(obj)
        
    def waiting_loader(self):
        self.loadingthread.quit()
        
        self.available_song_list_widget.setUpdatesEnabled(True)
        print("Initializing waiting loader")
        
        song_limit = 50
        
        time.sleep(.01)
        
        if self.loaded_songs_queue.empty():
            print("No songs returned")
            return
        
        for item in range(song_limit):
            preloaded_songs = self.loaded_songs_queue.get()
            print(preloaded_songs)
            item = preloaded_songs[0]
            iteamdeclaration = preloaded_songs[1]
            
            self.available_song_list_widget.addItem(item)
            self.available_song_list_widget.setItemWidget(item,iteamdeclaration)
            
            if self.loaded_songs_queue.empty():
                break

            
        print("Finished loading songs into ui")
            
            
                
             
    def loading_thread_target(self):
        while True:
            task, args = self.loading_queue.get()
            if task:
                print("Got task: " + str(task))
            else:
                time.sleep(.01)
                print("no task")
                
            try:
                task(*args)
                #self.loaded_songs_queue.put(result)
            except Exception as e:
                #self.loaded_songs_queue.put(e)
                raise e
            finally:
                self.loading_queue.task_done()

                
    def loading_manager(self, result_list):
        
        runningTime = 0
        print(len(result_list))
        while len(result_list) > 0:
            runningTime +=1
            print(len(result_list))
            if len(result_list) <= 10:
                self.loading_queue.put((self.worker.load_song_list, [result_list]))
                self.worker.send_song.emit((self.worker.load_song_list, [result_list]))
                del result_list[:len(result_list)]
            else:
                self.loading_queue.put((self.worker.load_song_list, [result_list[:10]]))
                self.worker.send_song.emit((self.worker.load_song_list, [result_list[:10]]))
                del result_list[:10]
        
        print("finished populating loading thread queue after running "+str(runningTime)+" times")
        self.worker.beginloading.emit()
                
        
                
                
                
    def already_added(self, to_check):
        for song in self.added_songs_list:
            if song["file"] == to_check:
                return True
        return False

    
    def load_added_songs(self):
        for song in self.songs_path:
            if song.endswith(('.mp3', '.flac', '.wav','.aiff')):
                title, artist, album = self.get_metadata(os.path.join(self.songs_path,song))
                
                self.added_songs_list.append({"file":os.path.join(self.songs_path,song),"title":title, "artist":artist, "album":album})

                        
    async def ParseSearch(self, term):
        results = await self.searchAsync(term)
        
        print("Aquired search information!")
        
        sortedResultList = []
        
        for userResult in results:
            #UserCheck = self.soul_seek_client.getUserStatus(userResult.username)
            #print(str(UserCheck))
            for item in userResult.shared_items:

                sortedResultList.append({"file":item.filename,"user":userResult.username,"title":os.path.basename(item.filename)})
                print(item.filename)
        
        print("Finished parsing search")
        
        return sortedResultList
    
    def update_search(self):
        text = self.searchBar.text()
        self.available_song_list_widget.clear()
        print(text)
        
        # Schedule the ParseSearch coroutine
        asyncio.ensure_future(self.run_search(text))

    async def run_search(self, text):
        search_results = await self.ParseSearch(text)
        print(search_results)
        self.loading_thread(search_results)


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

    async def download_buffer(self, info):
        return await self.downloadAsynch(info)


    def add_song(self):
        print("Downloading song!")
        button = self.sender()
        
        self.download_count +=1

        song_to_add = button.property("item_data")
        print(song_to_add)

        # Schedule the download_buffer coroutine to run without blocking
        asyncio.create_task(self.download_and_handle_song(button, song_to_add))

    async def download_and_handle_song(self, button, song_to_add):
        await self.download_buffer(song_to_add)


        # Update UI with the transfer details
        self.queued_song_download_widget.addItem(
            os.path.splitext(os.path.basename(song_to_add["file"]))[0]
        )

        # Update the button to reflect the song's downloaded state
        button.setText('X')
        button.setObjectName("remove")
        button.clicked.disconnect()  # Disconnect the add_song method
        button.clicked.connect(self.stop_song_download)  # Connect to remove_song method
        button.setStyle(button.style())
        

    def change_transfer_state(self, transfer):
        print("State changed")
    

    def stop_song_download(self):
        print("Stopping song download!")
        button = self.sender()
        
        self.download_count -=1
        
        download_to_stop = button.property("item_data")["file"]
        
        self.soul_seek_client.stopDownload(download_to_stop)
        
        items = self.queued_song_download_widget.findItems( os.path.splitext(os.path.basename(download_to_stop))[0], Qt.MatchFlag.MatchExactly)

        if items:
            # Remove the found item
            item = items[0]
            row = self.queued_song_download_widget.row(item)
            self.queued_song_download_widget.takeItem(row)
            print(f"Item with text '{os.path.splitext(os.path.basename(download_to_stop))[0]}' removed.")
        else:
            print(f"No item with text '{os.path.splitext(os.path.basename(download_to_stop))[0]}' found.")
        
        button.setText(u'\u2913')
        button.setObjectName("add")
        button.clicked.disconnect()  # Disconnect the add_song method
        button.clicked.connect(self.add_song)  # Connect to remove_song method
        
        button.setStyle(button.style())
        
        print(self.added_songs_list)
    
    def save_and_close(self):
        
        self.closing_event.emit(self.soul_seek_client, self.download_count)
        
        self.accept()
        
        
    def close_without_downloading(self):
        loop = asyncio.get_event_loop()
        asyncio.ensure_future(self.AsyncLogout())

    def show_login_error(self):
        error_popup = QMessageBox()
        error_popup.setIcon(QMessageBox.Icon.Warning)
        error_popup.setWindowTitle("Error")
        error_popup.setText("Invalid SoulSeek login.")
        error_popup.exec()

        settings["settings"]["slskusername"] = ""
        settings["settings"]["slskpassword"] = ""

        self.reject()
        
    async def AsyncLogout(self):
        loop = asyncio.get_event_loop()
        results = await loop.run_in_executor(None, self.soul_seek_client.logout_client)
        self.reject()
        
    def song_download_complete(self):
        print("Understood song is complete")
        
        self.progress_popup.update_progress()



class DownloadThread(QThread):
    progress_updated = pyqtSignal(int, str)  # Signal to update progress
    update_progress = pyqtSignal()
    finished = pyqtSignal(object)  # Signal emitted when all downloads are complete

    def __init__(self, soul_seek, total_downloads):
        super().__init__()
        self.soul_seek = soul_seek
        self.total_downloads = total_downloads
        self.finished_downloads = 0
        self.progress_report = {"failed" : 0}
        
        # Connect the soulseekclient's signal to update progress
        self.soul_seek.download_finished.connect(self.on_download_finished)

    def run(self):
        # Start the download process
        self.soul_seek.begin_downloads()
        
        # When downloads are complete, emit the finished signal
        self.finished.emit(self.progress_report)

    def on_download_finished(self, transferInfo):
        # Handle each finished download
        if transferInfo is None:
            song_name = "Failed to download song"
            self.progress_report["failed"] += 1
        else:
            song_name = "Finished downloading: " + os.path.splitext(os.path.basename(transferInfo.remote_path))[0]

        self.update_progress.emit()

        # Increment finished download count
        self.finished_downloads += 1
        
        # Calculate progress percentage
        progress = int(self.finished_downloads / self.total_downloads * 100)
        
        # Emit the progress updated signal
        self.progress_updated.emit(progress, song_name)


class ProgressPopup(QDialog):
    def __init__(self, total_downloads, soulseekclient: SoulseekConnect):
        super().__init__()
        self.setWindowTitle("Download Progress")
        self.setGeometry(100, 100, 300, 100)

        self.soul_seek = soulseekclient
        self.soul_seek.download_finished.connect(self.update_progress)

        self.total_downloads = total_downloads
        self.finished_downloads = 0

        layout = QVBoxLayout()

        self.info_label = QLabel("Your songs are being downloaded. Download times will vary, and some downloads may be unable to complete.\n(the program can hang, but things are happening)")
        self.info_label.setObjectName("numbers")
        layout.addWidget(self.info_label)

        self.current_song = QLabel(alignment=Qt.AlignmentFlag.AlignCenter)
        self.current_song.setObjectName("numbers")
        layout.addWidget(self.current_song)

        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)

        layout.addWidget(self.progress_bar)
        self.setLayout(layout)

    def start_progress(self):
        self.progress = 0
        self.progress_bar.setValue(self.progress)

        self.download_thread = DownloadThread(self.soul_seek)
        self.download_thread.finished.connect(self.on_download_finished)
        self.download_thread.start()

    def update_progress(self, transferInfo):
        if transferInfo is None:
            self.current_song.setText("Failed to download song")
        else:
            self.current_song.setText("Finished downloading: " + os.path.splitext(os.path.basename(transferInfo.remote_path))[0])

        self.finished_downloads += 1
        self.progress = int(self.finished_downloads / self.total_downloads * 100)
        self.progress_bar.setValue(self.progress)

    def on_download_finished(self):
        self.current_song.setText("All downloads completed.")
        self.close()






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
        
    print(settings)
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
    player = MusicPlayer(settings)
    player.show()
    atexit.register(exit_handler)
    sys.exit(app.exec())
    

        


        
        
