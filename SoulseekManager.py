import asyncio
import threading
from aioslsk.client import SoulSeekClient
from aioslsk.settings import Settings, CredentialsSettings, SharesSettings
from aioslsk.search.model import SearchRequest
from aioslsk.transfer.model import Transfer, TransferDirection
from aioslsk.events import TransferAddedEvent, TransferProgressEvent, TransferRemovedEvent
import os
import sys
from queue import Queue, Empty

from aioslsk.commands import GetUserStatusCommand

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    
    return os.path.join(base_path, relative_path)

class Soulseek:
    """Main Soulseek manager class. Login, download files, etc."""

    def __init__(self, username, password) -> None:
        self.settings = Settings(
            credentials=CredentialsSettings(
                username=username,
                password=password
            ),
            shares=SharesSettings(
                #download=r'E:/Soulseek Downloads',
                scan_on_start=False
                
                
            )
        )
        self.client = SoulSeekClient(self.settings)
        self.task_queue = Queue()
        self.result_queue = Queue()
        self.logged_in = False
        
        self.client.network.set_download_speed_limit(1000)
        self.client.network.load_speed_limits()

        # Start the login process in a new thread
        self.thread = threading.Thread(target=self._start_event_loop)
        self.thread.start()

    def _start_event_loop(self):
        asyncio.run(self._start_and_login())

    async def _start_and_login(self):
        await self.client.start()
        await self.client.login()
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
        
    def _queue_task(self, task, *args):
        self.task_queue.put((task, args))
        result = self.result_queue.get()
        if isinstance(result, Exception):
            raise result
        return result

    def search(self, term):
        return self._queue_task(self._search_task, term)

    async def _search_task(self, term):
        print("searching....")
        if not self.logged_in:
            raise RuntimeError("Client is not logged in.")
        request = await self.client.searches.search(term)
        await asyncio.sleep(5)  # Wait for results to populate
        return request.results

    def getUserStatus(self, username):
        return self._queue_task(self._user_status_task, username)
        
    async def _user_status_task(self, user):
        status, privileged = await self.client(
            GetUserStatusCommand(user), response=True)
        
        return status

    def download(self, username, filename):
        transfer = self._queue_task(self._download_task, username, filename)
        while transfer == []:
            print("retrying download...")
            transfer = self._queue_task(self._download_task, username, filename)
            
        return transfer

    async def _download_task(self, username, filename):
        if not self.logged_in:
            raise RuntimeError("Client is not logged in.")
        print("downloading to: "+ resource_path("Songs"))
        transfer = await self.client.transfers.download(username, filename)
        
        while True:

            print(f"transfer still transferring...")
            await asyncio.sleep(0.5)
            if transfer.is_finalized():
                print(f"transfer complete : {transfer}")
                break

        await asyncio.sleep(0.5)
        
        self.client.transfers.queue(transfer)
        
        print(self.client.transfers.get_downloading)
        print(self.client.transfers.get_download_speed)
        print(self.client.transfers.get_unfinished_transfers)
        print(self.client.transfers.get_finished_transfers)
        
        return transfer
    
    
    async def on_transfer_progress(event: TransferProgressEvent):
        for transfer, previous, current in event.updates:
            if previous.state != current.state:
                print(f"A transfer moved from state {previous.state} to {current.state}!")
    

    def stopDownload(self, transfer):
        self._queue_task(self._stop_download_task, transfer)

    async def _stop_download_task(self, transfer):
        if not self.logged_in:
            raise RuntimeError("Client is not logged in.")
        await self.client.transfers.abort(transfer)
        print(f"Download stopped for {transfer.filename}")

    def close(self):
        self.task_queue.put((self._shutdown, ()))
        self.thread.join()

    async def _shutdown(self):
        await self.client.stop()
