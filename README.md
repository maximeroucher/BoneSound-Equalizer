# BoneSound-Equalizer

An Equalizer for the BoneSound headset

### Prerequisites

You will need ffmpeg to be installed and in the same folder as the project.

You can download it from [here](https://ffmpeg.org/).

### Folder Structure

**image/** : the location of the image used in the programme. _If you want to change an image, named it with the name of the one you want to change_

### App Preview

![Alt text](./image/Screen.png "BoneSound Equalizer")

### Installing

You will need to easygui, requests, youtube_dl, lxml, pydub, spotdl and Pillow libraries to be installed.

To do so, just run on cmd:

```
pip install -r requirements.txt
```

After create a file called "settings.json" in the same folder as BoneSound_Equalizer.py file and put your SoundClound client id you can find [here](https://developers.soundcloud.com/docs/api/guide)

```
{
    "Client_id" : "your SoundClound client id"
}
```

## Running the tests

Just run BoneSound_Equailzer.py and test all commands

## Deployment

You can build this as an exe by installing auto-py-to-exe and runnning it.

_Don't forget to add ffmpeg.exe and your icon as "icon.ico" to make it work_

## Built with following tools

- [FFMPEG](https://ffmpeg.org/) - The Sound converter
- [Ryan Linnit](https://github.com/linnit/Soundcloud-Downloader/blob/master/soundcloud-downloader.py) - The SoundCloud Downloader
- [youtube-dl](https://github.com/ytdl-org/youtube-dl/blob/master/README.md#readme) - The YouTube Downloader
- [ritiek](https://github.com/ritiek/spotify-downloader) - The Spotify Dowloader

## Authors

- [**Maxime Roucher**](https://github.com/maximeroucher) - _Initial work_
