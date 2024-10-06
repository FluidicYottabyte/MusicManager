## Music Manager is an offline music & audio player with the ability to connect to SoulSeek.

Thank you for taking interest in my little side project! I started this in Senior year of High School a little over a year ago, I've never made a program so large, and thus, it's a little messy. I would certainly do it a lot differently knowing what I know now 😅 (I have considered rewriting it in C# or something idk)

### Installation Guide:

Clone the repo somewhere, and then install dependencies:

Music Manager runs in Python3, so it's probably a good idea to like, get that.

Currently, there are several libraries which need to be installed in order for MusicManager to work (installation executable tbd). The pip installations of which are listed here:

```
pip install PyQt6
pip install mutagen
pip install pillow
pip install numpy
pip install aioslsk
pip install qasync
pip install python-vlc
```

Additionally, **VLC media player must be installed in order for the program to work!**

It is also recommended you install Git in order for the application to do automatic update checks, though Music Manager can function without it.


### Notes:

The SoulSeek implimentation for Music Manager would not be possible without JergenR's [aioslsk repository](https://github.com/JurgenR/aioslsk)!


## Music Manager is <ins>mostly</ins> finished! Here's what I mean:

As an offline music player, it works as well as you would want, you can add files, create playlists, etc. A library has not been implimented in the way I would like it to be, but that is in the works.

Using SoulSeek is a bit more complex, and is prone to errors. As the way you interact with SoulSeek servers is.. unreliable to say the least. Downloads can fail for multiple reasons, and searching the network is slow. Everything should work, if you're patient enough.

If you want to use some other SoulSeek tool to dowload your songs, simply download them to `MusicManager/Songs ` and everything will work just fine.

![AppIcon](https://github.com/user-attachments/assets/9e74d8fc-1e6a-47c4-b3ab-9ba674247038)
