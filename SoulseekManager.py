import asyncio
import threading
from aioslsk.client import SoulSeekClient
from aioslsk.settings import Settings, CredentialsSettings, SharesSettings
from aioslsk.search.model import SearchRequest
from aioslsk.transfer.model import Transfer, TransferDirection
from aioslsk.events import TransferAddedEvent, TransferProgressEvent, TransferRemovedEvent
from aioslsk.exceptions import PeerConnectionError
import os
import sys
from queue import Queue, Empty
from threading import Thread

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QLabel, QVBoxLayout, QHBoxLayout, QWidget,
    QSlider, QListWidget, QListWidgetItem, QPushButton, QDialog, QDialogButtonBox,
    QVBoxLayout, QHBoxLayout, QMessageBox, QFileDialog, QLineEdit, QAbstractItemView, 
    QSizePolicy, QFrame
)
from PyQt6.QtGui import QPixmap, QFont, QPainter, QColor,QIcon
from PyQt6.QtCore import Qt, QTimer, QSize, pyqtSignal, QThread
from PyQt6 import QtCore

import qasync

import time

from aioslsk.commands import GetUserStatusCommand

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    
    return os.path.join(base_path, relative_path)



class DownloadWorker(QThread):
    runloading = pyqtSignal()
    transfer_finished = pyqtSignal(Transfer)
    send_song = pyqtSignal(Transfer)

    def __init__(self):
        super().__init__()
        self.download_queue = asyncio.Queue()

    def enqueuesong(self, song):
        # Add the song to the asyncio queue
        asyncio.run_coroutine_threadsafe(self.download_queue.put(song), asyncio.get_event_loop())

    def run(self):
        loop = qasync.QEventLoop(self)
        asyncio.set_event_loop(loop)

        try:
            loop.run_until_complete(self.main())
        finally:
            loop.close()

    async def main(self):
        while True:
            transfer = await self.download_queue.get()
            await self.process_transfer(transfer)
            self.download_queue.task_done()

    async def process_transfer(self, transfer):
        if transfer.is_finalized():
            self.transfer_finished.emit(transfer)
        else:
            print("Transfer still downloading")



class Soulseek(QThread):
    """Main Soulseek manager class. Login, download files, etc."""

    download_finished = pyqtSignal(object)
    login_unsuccessfull = pyqtSignal(bool)

    def __init__(self, username, password) -> None:
        super().__init__()
        self.settings = Settings(
            credentials=CredentialsSettings(
                username=username,
                password=password
            ),
            shares=SharesSettings(
                download=resource_path("Songs"),
                scan_on_start=False
                
                
            )
        )
        self.client = SoulSeekClient(self.settings)
        self.task_queue = Queue()
        self.result_queue = Queue()
        self.downloads_queue = Queue()
        self.logged_in = False
        
        self.client.network.set_download_speed_limit(1000)
        self.client.network.load_speed_limits()

        self.loadingthread = QThread()
        self.worker = DownloadWorker()
        self.worker.send_song.connect(self.worker.enqueuesong)
        self.worker.transfer_finished.connect(self.fished_transfer)
        #self.worker.runloading.connect(self.worker.runMain)
        self.loadingthread.started.connect(self.worker.run)
        self.worker.moveToThread(self.loadingthread)
        
        self.loadingthread.start()
        
        print("started loading thread, moving on")
        #self.worker.runloading.emit()

        # Start the login process in a new thread
        self.thread = threading.Thread(target=self._start_event_loop)
        self.thread.start()

    def _start_event_loop(self):
        
        asyncio.run(self._start_and_login())

    async def _start_and_login(self):
        
        
        
        try:
            await self.client.start()
            await self.client.login()

        except Exception:
            self.login_unsuccessfull.emit(True)
            try:
                await self.client.stop()
            except:
                print("Client never logged in")
            self.loadingthread.terminate()
            print("Finished cleaning up emergency logout")
            return

        self.logged_in = True
                        
        print("Login successful")
        while True:
            task, args = self.task_queue.get()
            print("Soulseek Manager got new task: "+str(task))
            print("Args aquired: "+str(args))
            try:
                result = await task(*args)
                self.result_queue.put(result)
            except Exception as e:
                self.result_queue.put(e)
            finally:
                self.task_queue.task_done()
        
        
    def logout_client(self):
        return self._queue_task(self._logout_task)

    async def _logout_task(self):
        print("Loggin out....")
        await self.client.stop()
        
        
    def _queue_task(self, task, *args):
        self.task_queue.put((task, args))
        result = self.result_queue.get()
        if isinstance(result, Exception):
            raise result
        return result
    
    def _queue_download(self, task, *args):
        self.downloads_queue.put((task, args))

        

    def search(self, term):
        return self._queue_task(self._search_task, term)

    async def _search_task(self, term):
        print("searching....")
        if not self.logged_in:
            raise RuntimeError("Client is not logged in.")
        request = await self.client.searches.search(term)
        await asyncio.sleep(5)  # Wait for results to populate
        return request.results

    
    def get_transfer_thread(self):
        return self.worker
    


    def getUserStatus(self, username):
        return self._queue_task(self._user_status_task, username)
        
    async def _user_status_task(self, user):
        status, privileged = await self.client(
            GetUserStatusCommand(user), response=True)
        
        return status


    def begin_downloads(self):
        while not self.downloads_queue.empty():
            
            task, args = self.downloads_queue.get()
            
            result = self._queue_task(task, args[0], args[1])
            
            self.download_finished.emit(result)
            
        self.logout_client()


    def download(self, username, filename):
        self._queue_download(self._download_task, username, filename)


    async def _download_task(self, username, filename):
        
        if not self.logged_in:
            raise RuntimeError("Client is not logged in.")
        print("downloading to: "+ resource_path("Songs"))
        
        try:
            self.client.network.get_peer_connection(username)
        except PeerConnectionError:
            print("Cannot connect to peer! This must be invalid!")
            return False
        
        transfer = await self.client.transfers.download(username, filename)
        
        start_time = time.time()
        while True:
            print("Downloading transfer...")
            if transfer.is_finalized():
                print(f"transfer complete : {transfer}")
                break
            
            if time.time() - start_time >= 120:
                print("Download has taken more then two minutes to complete. Moving on.")
                return None

            await asyncio.sleep(0.5)
                
        print(self.client.transfers.cache.read())
        
        return transfer
    
    
    def fished_transfer(self, transfer):
        self.change_transfer_state.emit(transfer)
    
    async def on_transfer_progress(event: TransferProgressEvent):
        for transfer, previous, current in event.updates:
            if previous.state != current.state:
                print(f"A transfer moved from state {previous.state} to {current.state}!")
    

    def stopDownload(self, filepath):
        if not self.logged_in:
            raise RuntimeError("Client is not logged in.")
        
        # Temporary list to hold transfers that don't match the filepath
        remaining_downloads = Queue()
        
        try:
            while True:
                stuff = self.downloads_queue.get_nowait()
                
                task, args = stuff
                
                if args[1] != filepath:
                    remaining_downloads.put((task, args))
                else:
                    print(f"Download removed for {filepath}")
                
        except Empty:
            pass
        
        # Replace the old queue with the updated queue
        self.downloads_queue = remaining_downloads
        
    def close(self):
        self.task_queue.put((self._shutdown, ()))
        self.thread.join()

    async def _shutdown(self):
        await self.client.stop()
