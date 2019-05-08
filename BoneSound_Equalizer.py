#
# ---------- Import -------------------------------------------------------------------------------
#

from __future__ import unicode_literals

import contextlib
import json
import math
import os
import re
import subprocess
import sys
import urllib
from collections import OrderedDict
from threading import Thread
from tkinter import Button, Canvas, Entry, IntVar, Label, LabelFrame, Listbox, PhotoImage, Scale, StringVar, Tk, messagebox
from tkinter.ttk import Progressbar, Radiobutton, Style
from urllib.request import urlretrieve

import easygui
import numpy as np
import requests
import youtube_dl
from lxml import etree
from pydub import AudioSegment


#
# ---------- Classe Message -------------------------------------------------------------------
#


class Message():

    def __init__(self, text, actualLanguage, addon="", msg=None):
        """ Permet de changer le texte d'un Label, LabelFrame ou Button même si ce dernier est controllé par un thread
        itype : dict {fr: [], en:[]}, 'fr' / 'en', str, tkinter.StringVar
        """
        # Le StringVar perrmet de changer les labels et les bouttons
        self.msg = msg
        # Le dictionnaire contenant les phrases en français et en anglais
        self.text = text
        # La langue actuelle de l'application
        self.langue = actualLanguage
        # Le numéro du message actuel
        self.actualMsg = 0
        # Dans le cas ou le message contient un {} à formatter
        self.addon = addon


    def update(self):
        """ Change le StringVar
        """
        self.msg.set(self.getTxt())


    def getTxt(self):
        """ Retourne le texte correspondant à la langue, au numéro et avec le formattage s'il en faut un
        """
        return self.text[self.langue][self.actualMsg].format(self.addon)


    def switchLang(self, langue):
        """ Change la langue
        itype : str('fr' / 'en')
        """
        self.langue = langue


    def changeMsg(self, numMsg):
        """ Change le numéro du message
        itype : int
        """
        self.actualMsg = numMsg


    def addPrecision(self, text):
        """ Change l'addon
        itype : str
        """
        self.addon = text


#
# ---------- Classe ProgressBar -------------------------------------------------------------------
#


class ProgressBar():

    def __init__(self, progress, msg):
        """ Barre d'avancement, est appellé à chaque itération du téléchargement
        itype : Tkinter.ttk.ProgressBar, Tkinter.StringVar
        """
        # Progressbar de la fenêtre
        self.progress = progress
        # Message de la fenêtre
        self.msg = msg


    def __call__(self, block_num, block_size, total_size):
        """ Opération appelée à chaque itération du téléchargement
        itype : 3 int
        """
        # Niveau de progression
        downloaded = block_num * block_size
        # Si le téléchagement n'est pas finit
        if downloaded < total_size:
            # Change la barre
            self.progress["value"] = downloaded * 100 / total_size
        else:
            # Change le texte et la barre
            self.msg.changeMsg(1)
            self.progress["value"] = 0


#
# ---------- Classe SoundCloudDownloader ----------------------------------------------------------
#


class SoundCloudDownloader(Thread):

    def __init__(self, url, name, sid, progress, msg, out):
        """ Téléchargeur de vidéos depuis Soundcloud
        itype : 3 str, Tkinter.ttk.ProgressBar, Tkinter.StringVar
        """
        # Code source : https://github.com/linnit/Soundcloud-Downloader/blob/master/soundcloud-downloader.py
        Thread.__init__(self)
        # Identifiant du client Soundcloud (A NE PAS CHANGER)
        self.client_id = "NmW1FlPaiL94ueEu7oziOWjYEzZzQDcK"
        # Lien de la musique
        self.url = url
        # Progressbar de la fenêtre
        self.progress = progress
        # Message de la fenêtre
        self.msg = msg
        # Identifiant de la musique
        self.song_id = sid
        # Nom de la musique
        self.title = name
        # Le dossier d'enregistrement de la musique
        self.out = out


    def download_file(self, url, filename):
        """ Télécharge le fichier avec ProgressBar comme hook
        itype : 2 str
        """
        urlretrieve(url, filename, ProgressBar(self.progress, self.msg))


    def get_stream_url(self, sid):
        """ Crée le stream de la musique
        itype : str
        rtype : str
        """
        return requests.get("https://api.soundcloud.com/i1/tracks/{0}/streams?client_id={1}".format(sid, self.client_id)).json()['http_mp3_128_url']


    def run(self):
        """ Télécharge la musique
        """
        # Change le message
        self.msg.changeMsg(2)
        # Update le texte
        self.update()
        # Récupère le stream de la musique
        stream_url = self.get_stream_url(self.song_id)
        # Change le message
        self.msg.changeMsg(3)
        # Ajoute le titre de la musique au message
        self.msg.addPrecision(self.title)
        # Update le texte
        self.update()
        # Télécharge la musique
        self.download_file(stream_url, f"{self.out}/{self.title}.mp3")
        # Change le message
        self.msg.changeMsg(0)
        # Update le texte
        self.update()


#
# ---------- Classe Equalizer ------------------------------------------------------------------
#


class Equalizer(Thread):

    def __init__(self, filename, nbRepetition, progress, msg, gain, outfile):
        """ Transforme la musique pour le casque
        itype : str, int, Tkinter.ttk.ProgressBar, Tkinter.StringVar
        """
        # Initailisation du Thread
        Thread.__init__(self)
        # Fréquence en dessous de laquelle, les fréquences sont descendus de 6 dB
        self.upperFrequency = 450
        # Fréquence au  dessus de laquelle, les fréquences sont descendus de 6 dB
        self.lowerFrequency = 9000
        # Le dossier d'enregistrement de la musique
        self.out = outfile
        # Nom du fichier à transformer (déjà en wav)
        self.filename = self.get_song(filename)
        # Nom de fichier en sortie
        ext = filename.split("\\")[-1].split('.')[0]
        self.outname = f'{self.out}/out - {ext}.wav'
        # Barre de progression de la fenêtre
        self.progress = progress
        # Message de la fenêtre
        self.msg = msg
        # Nombre de fois à appliquer le filtre
        self.nbRepetition = nbRepetition
        # Le gain à appliquer à la musique
        self.gain = gain


    def get_song(self, path):
        """ Récupère le chemin vers la musique et convertit en wav les autres formats
        itype : str (path)
        """
        # Si la musique n'est pas en .wav
        if not path.endswith(".wav"):
            # Récupère la nom de la musique sans l'extension
            ext = path.split("\\")[-1].split('.')[0]
            # Lieu de sauvgarde du fichier une fois converti en .wav
            outname = f'{self.out}/{ext}.wav'
            # Convertit le fchier en .wav
            subprocess.call(['ffmpeg', '-i', path, outname])
            # Retourne le chemin vers la musique convertie
            return os.path.abspath(outname)
        # Sinon, retourne le chemin sans modification
        return path


    def f(self, x):
        """ Fonction de transformation
        itype : float
        rtype : float
        """
        coefficients = [-52.1243, 0.228166, -3.56842e-4, 3.03014e-7, -1.61768e-10, 5.83724e-14, -1.48283e-17,
                        2.71372e-21, -3.61674e-25, 3.51071e-29, -2.45373e-33, 1.20192e-37, -3.91326e-42, 7.60244e-47, -6.66608e-52]
        if x >= 240 and x < 15000:
            return sum([coefficients[z] * x ** z for z in range(15)])
        return -15


    def run(self):
        """ Transformation de la musique
        """
        # Le nombre d'étape maximale
        max_value = 2 * self.nbRepetition + 2
        # Progression de la barre
        x = 1
        # Change le message de la fenêtre
        self.msg.changeMsg(4)
        # Ouvre le fichier à transformer
        song = AudioSegment.from_wav(self.filename)
        # Change la barre de progression de la fenêtre
        self.progress['value'] = x / max_value * 100
        for _ in range(self.nbRepetition):
            # HighPass Filter qui limite les fréquences basses
            song = song.high_pass_filter(self.upperFrequency)
            # Change la barre de progression de la fenêtre
            x += 1
            self.progress['value'] = x / max_value * 100
            # LowhPass Filter qui limite les fréquences hautes
            song = song.low_pass_filter(self.lowerFrequency)
            # Change la barre de progression de la fenêtre
            x += 1
            self.progress['value'] = x / max_value * 100
        # Change la barre de progression de la fenêtre
        x += 1
        self.progress['value'] = x / max_value * 100
        # Change le message de la fenêtre
        self.msg.changeMsg(5)
        # Augmente le volume pour compenser les filtres
        song = song + self.gain
        # Exporte le fichier
        song.export(self.outname, format="wav")
        # Change le message de la fenêtre
        self.msg.changeMsg(0)
        # Change la barre de progression de la fenêtre
        self.progress['value'] = 0


#
# ---------- Classe YoutubeDownloader -------------------------------------------------------------
#


class YoutubeDownloader(Thread):

    def __init__(self, url, name, progress, msg, out):
        """ Téléchargeur de vidéos depuis youtube
        itype : 2 str, Tkinter.ttk.ProgressBar, Tkinter.StringVar
        """
        # Initialisaiton du Thread
        Thread.__init__(self)
        # Lien de la vidéo
        self.url = url
        # Barre de progression de la fenêtre
        self.progressbar = progress
        # Message de la fenêtre
        self.msg = msg
        # Le dossier d'enregistrement de la musique
        self.out = out
        # Lieu de sauvegarde du fichier transformé
        self.musicFolder = f'{self.out}/%(title)s.%(ext)s'
        # Option de téléchargement de la musique
        self.ydl_opts_Mp3 = {
            # Meilleur format audio
            'format': 'bestaudio/best',
            # Sauvegarde dans un dossier musique a côté du programme
            'outtmpl': self.musicFolder,
            # Exportation en wav avec FFmpeg
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'wav',
                'preferredquality': '192'
            }],
            'postprocessor_args': [
                '-ar', '16000'
            ],
            # Gesitionnaire de progression
            'progress_hooks': [self.my_hook],
            # Utilisation de FFmpeg
            'prefer_ffmpeg': True,
            # Suppression de la vidéo après avoir extrait la musique
            'keepvideo': False
        }
        # Nom de la musique
        self.name = name


    def my_hook(self, d):
        """ Getstionnaire de progression, appellé à chaque itération du téléchargement
        itype : dict
        """
        # Si le téléchargement est terminé
        if d['status'] == 'finished':
            # Change le message est remet à 0 la barre de progression
            file_tuple = os.path.split(os.path.abspath(d['filename']))
            self.progressbar['value'] = 0
            self.msg.changeMsg(6)
            self.msg.addPrecision({file_tuple[1].split('.')[0]})
            self.msg.update()
        # Si le téléchargement est en cours
        if d['status'] == 'downloading':
            # Change le message est met à jour la barre de progression en fonction de l'avanecment du téléchargement
            self.progressbar['value'] = d['_percent_str'].split("%")[0]
            self.msg.changeMsg(7)
            self.msg.addPrecision({d['_eta_str']})
            self.msg.update()


    def run(self):
        """ Focntion pricipale, appellée quand .start() est appelé
        """
        # Si la musique n'a pas déjà été téléchargé
        if not f"{self.name}.wav" in os.listdir(f"{self.out}/"):
            # Change le message de la fenêtre
            self.msg.changeMsg(8)
            self.msg.addPrecision(self.name)
            self.msg.update()
            # Télécharge la musique avec les options définis précédemment
            with youtube_dl.YoutubeDL(self.ydl_opts_Mp3) as ydl:
                ydl.download([self.url])
            # Change le messageg à la fin du téléchargement du fichier
            self.msg.changeMsg(9)
            self.msg.update()
        # Si le fichier a déjà été téléchargé
        else:
            # Change le messageg de la fenêtre
            self.msg.changeMsg(0)
            self.msg.update()


#
# ---------- Classe Inteface ----------------------------------------------------------------------
#


class Inteface:

    def __init__(self):

        # Initialisation de la fenêtre

        # Déclaration d'un objet Tkinter
        self.fen = Tk()
        # Largeur de la fenêtre
        self.width = 1000
        # Hauteur de la fenêtre
        self.height = 650
        # Dimmensionne la fenêtre
        self.fen.geometry(f"{self.width}x{self.height}")
        # Change le titre de la fenêtre
        self.fen.title("BoneSound Equalizer")
        # Change l'icone de la fenêtre
        self.fen.iconbitmap(default='./BONESOUND.ico')
        # Change la couleur de l'arrière plan
        self.fen.configure(background='#202225')
        # Le style d'la'pplication
        style = Style(self.fen)
        # Initailisation par défaut
        style.theme_use('alt')
        # Le nom du fihier avec les paramètres
        self.ParamFile = "saveLink.json"
        # Le lien de sauvegarde et la langue de l'application
        self.saveLink, self.langue = self.getParam()
        # Liste de tout les objets contenant du texte
        self.alltxtObject = {'Stringvar': [], "LabelFrame": []}


        # Initialisation des variables

        # Fichiers actuellement ouvert dans l'application
        self.files = []
        # Différents types de musique et leur nombre de répétition du filtre associé
        self.tags = {"Rap / Rap": 5, "Musique Classique / Classical Music": 4, "Jazz / Jazz": 6, "Hip-Hop / Hip-Hop": 7, "Rock / Rock": 8, "Métal / Metal": 9, "RnB / RnB": 10, "Pop  / Pop": 3, "Blues / Blues": 1}
        # Triés dans l'ordre alphabétique
        self.tags = OrderedDict(sorted(self.tags.items(), key=lambda t: t[0]))
        # Type de musique séléctionné (IntVar permet de modifier la valeru des Radioboutons en le modifiant)
        self.musicType = IntVar()
        # Coche par défaut le premier élément de la liste
        self.musicType.set(1)
        # le gain de volume
        self.volumeGain = IntVar()
        # 10 Par défaut
        self.volumeGain.set(10)


        # Initialisation de la liste des musique à convertir

        # Permet de changer le texte contenu dans le cadre
        self.musicLabel = Message(text={'fr': [" Liste des musiques à convertir "], 'en': [' List of music to convert ']}, actualLanguage=self.langue)
        # Cadre contenant la liste
        self.MusicFiles = LabelFrame(self.fen, text=self.musicLabel.getTxt(), padx=10, pady=10)
        # Placement du cadre dans la fenêtre
        self.MusicFiles.place(x=self.width - 550, y=25)
        # Configure l'affichage du cadre
        self.MusicFiles.configure(background='#202225', foreground="#b6b9be")
        # Ajoute à la liste des objets qui peuvent changer de texte
        self.alltxtObject['LabelFrame'].append([self.MusicFiles, self.musicLabel])
        # Liste contenant les musiques
        self.filesList = Listbox(self.MusicFiles, width=82, height=30)
        # Configure l'affichage de la listbox
        self.filesList.configure(background="#484B52", foreground="#b6b9be", borderwidth=0, highlightthickness=0)
        # Inclusion de la liste dans le cadre
        self.filesList.pack()


        # Initialisation de la liste des types de musiques

        # Permet de changer le texte contenu dans le cadre
        self.tagLabel = Message(text={'fr': [" Liste des différents types de musiques "], 'en': [' List of the different type of music ']}, actualLanguage=self.langue)
        # Cadre contenant la liste
        self.MusicTags = LabelFrame(self.fen, text=self.tagLabel.getTxt(), padx=10, pady=10)
        # Placement du cadre dans la fenêtre
        self.MusicTags.place(x=75, y=self.height / 2 - 50)
        # Configure l'affichage du cadre
        self.MusicTags.configure(background='#202225', foreground="#b6b9be")
        # Ajoute à la liste des objets qui peuvent changer de texte
        self.alltxtObject['LabelFrame'].append([self.MusicTags, self.tagLabel])


        # Crée un RadioBouton ayant accès à self.MusicType pour chaque type de musique
        for x, t in enumerate(self.tags.keys()):
            # Sépare le français de l'anglais
            fr, en = t.split(' / ')
            # Permet de changer le texte contenu du texte
            m = Message(text={'fr': [fr], 'en': [en]}, actualLanguage=self.langue)
            # text est le message écrit à côté du bouton, value est la valeur que le bouton donne à self.MusicType quand il est séléctionné (x + 1 car 0 n'est pas admis)
            rdb = Radiobutton(self.MusicTags, text=m.getTxt(), value=x + 1, variable=self.musicType)
            # Ajoute à la liste des objets qui peuvent changer de texte
            self.alltxtObject['LabelFrame'].append([rdb, m])
            # Le nom du bouton
            style_name = rdb.winfo_class()
            # Configure la style du bouton
            style.configure(style_name, foreground="#b6b9be", background='#202225', indicatorcolor="#202225", borderwidth=0, selectcolor="#FAA61A")
            # Précise les couleurs en fonction des états du bouton
            style.map(style_name,
                    foreground=[('disabled', "#b6b9be"), ('pressed', "#FAA61A"), ('active', "#FAA61A")],
                      background=[('disabled', '#202225'), ('pressed', '!focus', '#202225'), ('active', '#202225')],
                      indicatorcolor=[('selected', "#FAA61A"), ('pressed', "#FAA61A")])
            # Inclusion du bouton
            rdb.pack()


        # Initialisation de la barre de progression

        # Permet de changer le texte contenu dans le cadre
        self.pgbLabel = Message(text={'fr': [" Progrès de l'opération "], 'en': [' Progress of the operation ']}, actualLanguage=self.langue)
        # Cadre contenant la barre
        self.Pgb = LabelFrame(self.fen, text=self.pgbLabel.getTxt(), padx=10, pady=10)
        # Placement du cadre dans la fenêtre
        self.Pgb.place(x=75, y=560)
        # Configure l'affichage du cadre
        self.Pgb.configure(background='#202225', foreground="#b6b9be")
        # Ajoute à la liste des objets qui peuvent changer de texte
        self.alltxtObject['LabelFrame'].append([self.Pgb, self.pgbLabel])
        # Liste de tout les messages que peut afficher le label
        allMsgPossible = {
            'fr':
            ["Aucune opération actuellement", "Fin du téléchargement", "Recherche du morceau",
             "Téléchargement de {} au format mp3", "Modification", "Sauvegarde",
             "Fin du téléchargement de {}", "Fin du téléchargement éstimé dans {}",
             "Télécharge: {} au format wav", "La musique à déjà été enregistrée"],
            'en':
            ["No operation currently", "End of the download", "Search for the song",
             "Downloading of {} at mp3 format", "Changing", "Saving", "End of the download of",
             "End estimated in {}", "Download: {} in wav format", "The song has already been downloaded"]}
        # Permet de changer le texte contenu dans le label
        self.msg = Message(msg=StringVar(), text=allMsgPossible, actualLanguage=self.langue)
        # Affiche le texte par défaut
        self.msg.update()
        # Ajoute à la liste des objets qui peuvent changer de texte
        self.alltxtObject['Stringvar'].append(self.msg)
        # Explique l'opération en cours
        operatingLabel = Label(self.Pgb, textvariable=self.msg.msg)
        # Inclusion du label dans le cadre
        operatingLabel.pack()
        # Configure l'affichage du label
        operatingLabel.configure(background='#202225', foreground="#b6b9be")
        # Style de la barre de progression
        s = Style()
        # Charge un style par défaut
        s.theme_use('alt')
        # Configure le style
        s.configure("red.Horizontal.TProgressbar", troughcolor='#40444B', background='#8d93fa')
        # Barre de progression qui suit l'évolution des différentes opérations de l'application
        self.progressbar = Progressbar(self.Pgb, orient="horizontal", length=800, mode="determinate", style="red.Horizontal.TProgressbar")
        # La valeur maximale de la barre est 100 (100%)
        self.progressbar["maximum"] = 100
        # Inclusion de la barre de progression dans le cadre
        self.progressbar.pack()


        # Initialisation de la saisie de texte

        # Permet de changer le texte contenu dans le cadre
        self.ytlabel = Message(text={'fr': [" Lien Youtube ou SoundCloud de la musique à convertir "], 'en': [" Youtube or SoundCloud link of the music to convert "]}, actualLanguage=self.langue)
        # Cadre pour entrer le lien
        self.YtLink = LabelFrame(self.fen, text=self.ytlabel.getTxt(), padx=10, pady=10)
        # Placement du cadre dans la fenêtre
        self.YtLink.place(x=25, y=100)
        # Configure le cadre
        self.YtLink.configure(background='#202225', foreground="#b6b9be")
        # Ajoute à la liste des objets qui peuvent changer de texte
        self.alltxtObject['LabelFrame'].append([self.YtLink, self.ytlabel])
        # Une Entry permet à l'utilisateur de rentrer du texte
        self.Link = Entry(self.YtLink, width=50)
        # Configure l'affichage de la saisie
        self.Link.configure(background="#484B52", foreground="#b6b9be", borderwidth=0, highlightthickness=0)
        # Inclusion du champ d'entrée dans le cadre
        self.Link.pack()


        # Initialisation des boutons

        # Permet de changer le texte contenu dans le bouton
        self.optlabel = Message(msg=StringVar(), text={'fr': [" Ouvrir un fichier "], 'en': [" Open a file "]}, actualLanguage=self.langue)
        # Bouton "ouvrir un fichier" qui appelle openExplorateur au clic
        openFileButton = Button(self.fen, textvariable=self.optlabel.msg, command=self.openExplorateur)
        # Affiche le texte par défaut
        self.optlabel.update()
        # Ajoute à la liste des objets qui peuvent changer de texte
        self.alltxtObject['Stringvar'].append(self.optlabel)
        # Placement du bouton dans la fenêtre
        openFileButton.place(x=20, y=30)
        # Configure le bouton
        openFileButton.configure(background="#40444B", foreground="#b6b9be", activebackground="#40444B", activeforeground="#b6b9be",  borderwidth=0, highlightthickness=0)


        # Permet de changer le texte contenu dans le bouton
        self.dlytlabel = Message(msg=StringVar(), text={'fr': [" Télécharger "], 'en': [" Download "]}, actualLanguage=self.langue)
        # Bouton "Télécharger" qui appelle downloadMusic au clic
        dlYtButton = Button(self.fen, textvariable=self.dlytlabel.msg, command=self.downloadMusic)
        # Affiche le texte par défaut
        self.dlytlabel.update()
        # Ajoute à la liste des objets qui peuvent changer de texte
        self.alltxtObject['Stringvar'].append(self.dlytlabel)
        # Placement du cadre dans la fenêtre
        dlYtButton.place(x=25, y=190)
        # Configure le bouton
        dlYtButton.configure(background="#40444B", foreground="#b6b9be", activebackground="#40444B", activeforeground="#b6b9be", borderwidth=0, highlightthickness=0)


        # Permet de changer le texte contenu dans le bouton
        self.convlabel = Message(msg=StringVar(), text={'fr': [" Conversion "], 'en': [" Convert "]}, actualLanguage=self.langue)
        # Bouton "Conversion" qui appelle conversion au clic
        convBtn = Button(self.fen, textvariable=self.convlabel.msg, command=self.conversion)
        # Affiche le texte par défaut
        self.convlabel.update()
        # Ajoute à la liste des objets qui peuvent changer de texte
        self.alltxtObject['Stringvar'].append(self.convlabel)
        # Placement du cadre dans la fenêtre
        convBtn.place(x=150, y=190)
        # Configure le bouton
        convBtn.configure(background="#40444B", foreground="#b6b9be", activebackground="#40444B", activeforeground="#b6b9be",  borderwidth=0, highlightthickness=0)


        # Bouton "Fr / En" qui appelle switchL au clic
        lbtn = Button(self.fen, text=" Fr / En ", command=self.switchL)
        # Placement du cadre dans la fenêtre
        lbtn.place(x=300, y=30)
        # Configure le bouton
        lbtn.configure(background="#40444B", foreground="#b6b9be", activebackground="#40444B", activeforeground="#b6b9be",  borderwidth=0, highlightthickness=0)


        # Curseur du gain de volume

        # Cadre du curseur
        VolumeLabel = LabelFrame(self.fen, text=' Volume (dB) ')
        # Configure le cadre
        VolumeLabel.configure(background="#202225", foreground="#b6b9be", borderwidth=0, highlightthickness=0)
        # Place le cadre dans la fenêtre
        VolumeLabel.place(x=340, y=190)
        # Création du curseur
        scale = Scale(VolumeLabel, from_=-10, to=100, resolution=1, tickinterval=10, length=300, variable=self.volumeGain)
        # Configure le curseur
        scale.configure(background="#40444B", foreground="#b6b9be", borderwidth=0, highlightthickness=0, troughcolor="#b6b9be", takefocus=0)
        # Inclusion du curseur
        scale.pack()


        # Le lien vers le fichier de sauvegarde
        if not self.saveLink:
            self.saveLink = self.getSaveLink()


    def getParam(self):
        if self.ParamFile in os.listdir():
            f = json.load(open(self.ParamFile))
            return f["OutputFile"], f['Language']
        else:
            return None, 'fr'


    def switchL(self):
        self.langue = 'en' if self.langue == 'fr' else 'fr'
        for l in self.alltxtObject["Stringvar"]:
            l.switchLang(self.langue)
            l.update()
        for l in self.alltxtObject['LabelFrame']:
            l[1].switchLang(self.langue)
            l[0].configure(text=l[1].getTxt())


    def getSaveLink(self):
        path = easygui.diropenbox("Séléctionner un fichier de sauvegarde des musiques")
        if path != None:
            json.dump({"OutputFile": path, 'Language': self.langue}, open(self.ParamFile, "w"), indent=4, sort_keys=True)
        else:
            path = './Music'
        return path


    def downloadMusic(self):
        """ Récupère le lien et télécharge si le lien est correct
        """
        # Récupère ce que Link contient
        link = self.Link.get().split("&")[0]
        # Si Link contenait quelque chose
        if link != "":
            # Getsion des erreurs
            try:
                # Si le lien est un lien SoundCloud
                if "soundcloud" in link:

                    def clean_title(title):
                        """ Formatage du titre de la musique
                        itype : str
                        rtype : str
                        """
                        allowed = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ 0123456789-_()$"
                        title = ''.join(c for c in title if c in allowed)
                        a = title.split("by")
                        a.reverse()
                        return ' - '.join([x.strip() for x in a])

                    def get_title(html):
                        """ Récupère le titre de la musique
                        itype : str
                        rtype : str
                        """
                        title_re = re.search(
                            '<title>([^|]+) | Free Listening on SoundCloud</title>', html.text, re.IGNORECASE)
                        if title_re:
                            return clean_title(title_re.group(1))
                        return False

                    def get_sid(html):
                        """ Récupère l'identifiant de la musique
                        itype : str
                        rtype : bool
                        """
                        id_re = re.search(r'soundcloud://sounds:(\d+)', html.text, re.IGNORECASE)
                        if id_re:
                            return id_re.group(1)
                        return False

                    # Ouvre la page coorespondante au lien
                    page = requests.get(link)
                    # Récupère le nom de la musique
                    name = get_title(page)
                    # Récupère l'identifiant de la musique
                    sid = get_sid(page)
                    # Télécharge le lien avec le Téléchargeur SoundCloud
                    SoundCloudDownloader(link, name, sid, self.progressbar, self.msg, self.saveLink).start()
                    # Ajoute le fichier au fichiers à convertir
                    self.files.append(os.path.abspath(f'{self.saveLink}/{name}.mp3'))
                    # Affiche le fichier dans la liste des fichiers à convertir
                    self.filesList.insert(len(self.files) - 1, self.files[-1].split("\\")[-1])
                # Si le lien un lien Youtube
                elif "youtube" in link:
                    # Récupère le nom de la musique
                    name = etree.HTML(urllib.request.urlopen(link).read()).xpath("//span[@id='eow-title']/@title")[0]
                    # Télécharge le lien avec le Téléchargeur Youtube
                    YoutubeDownloader(link, name, self.progressbar, self.msg, self.saveLink).start()
                    # Ajoute le fichier au fichiers à convertir
                    self.files.append(os.path.abspath(f'{self.saveLink}/{name}.wav'))
                    # Affiche le fichier dans la liste des fichiers à convertir
                    self.filesList.insert(len(self.files) - 1, self.files[-1].split("\\")[-1])
                # Si la lien n'est pas correct
                else:
                    # Pop-up d'erreur
                    messagebox.showerror("Erreur de téléchargement", "Lien non valide")
            # Si il y a une erreur dans le téléchargement
            except Exception as e:
                # Pop-up d'erreur
                messagebox.showerror("Erreur de téléchargement", f"{e.__class__.__name__}: {e}")
        # Si Link ne contien rien
        else:
            # Pop-up d'erreur
            messagebox.showwarning("Problème", "Pas de lien")


    def conversion(self):
        """ Lance la conversion
        """
        # Gestion d'erreur
        try:
            # Récupère la première musique de la liste
            music = self.files.pop(0)
            # La supprime de l'affichage
            self.filesList.delete(0)
            # Récupère le type de musiqye séléctionné
            musictype = list(self.tags.keys())[int(self.musicType.get()) - 1]
            # Récupère la valeur du gain de volume
            gain = self.volumeGain.get()
            self.volumeGain.set(10)
            # lance l'equalizer
            Equalizer(music, self.tags[musictype], self.progressbar, self.msg, gain, self.saveLink).start()
        # Si il y a une erreur
        except Exception as e:
            # Nom de l'erreur
            name = e.__class__.__name__
            # Si l'erreur est du au fait qu'il n'y ait pas de musique à transformer
            if name == "IndexError":
                # Pop-up d'erreur
                messagebox.showerror("Erreur de conversion", "Il n'y a aucune musique à convertir")
            # Si il s'agit d'une autre erreur
            else:
                # Pop-up d'erreur
                messagebox.showerror("Erreur de conversion", f"{name}: {e}")


    def openExplorateur(self):
        # Ouvre un explorateur de fichier qui retourne le chemin depuis la racine jusqu'au ficier séléstionné
        f = easygui.fileopenbox()
        if f:
            # Si le fichier est un fichier wav est n'est pas déjà dans la liste
            if f[-4:] in [".wav", ".mp3"] and f not in self.files:
                # Ajoute le fichier à la liste des fichiers à convertir
                print(f)
                self.files.append(f)
                # Enléve ce qui précede le nom du fichier pour plus de compréhesion de l'utilisateur
                if "\\" in f:
                    f = f.split("\\")[-1]
                # Ajoute à l'affichage le nom de fichier
                self.filesList.insert(len(self.files) - 1, f)
            # Sinon
            else:
                # Pop-up d'erreur
                messagebox.showerror("Erreur", "Le format n'est pas correct")


    def run(self):
        """ Fonction principale lance la fenêtre
        """
        self.fen.mainloop()


#
# ---------- Test ----------------------------------------------------------------------
#


Inteface().run()
