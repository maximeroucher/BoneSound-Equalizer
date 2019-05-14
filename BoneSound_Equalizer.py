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
from tkinter import Button, Canvas, Entry, IntVar, Label, LabelFrame, Listbox, PhotoImage, Scale, StringVar, Tk, Toplevel, messagebox
from tkinter.ttk import Progressbar, Radiobutton, Style
from tkinter.colorchooser import askcolor

import easygui
import numpy as np
from PIL import Image, ImageTk
from pydub import AudioSegment


#
# ---------- Classe Message -----------------------------------------------------------------------
#


class Message():

    def __init__(self, text, actualLanguage, addon="", msg=None):
        """ Permet de changer le texte d'un Label, LabelFrame ou Button même si ce dernier est controllé par un thread
        itype : dict {fr: [], en:[]}, 'fr' / 'en', str, tkinter.StringVar()
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
        itype : Tkinter.ttk.ProgressBar, Message()
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
        # Sinon
        else:
            # Change le texte et la barre
            self.msg.changeMsg(1)
            self.msg.update()
            self.progress["value"] = 0


#
# ---------- Classe Equalizer ---------------------------------------------------------------------
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
            subprocess.call(['ffmpeg', '-i', path, outname, '-y '])
            # Retourne le chemin vers la musique convertie
            return os.path.abspath(outname)
        # Sinon, retourne le chemin sans modification
        return path


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
# ---------- Classe PopupWindow -------------------------------------------------------------------
#

class PopupWindow(object):

    def __init__(self, master, msg, allLabel, error, errorMsg, langue):
        """ Pop-up pour demander le nombre de filtre à appliquer
        itype : tkinter.Tk(), Message(), 3 dict, str
        """
        # Fenêtre au dessus de la principale
        self.top = Toplevel(master)
        # Couleur de fond de la fenêtre
        self.top.configure(background='#202225')
        # Taille de fond de la fenêtre
        self.top.geometry(f"300x180")
        # Message de la fenêtre
        self.msg = msg
        # Cadre pour entrer le nombre
        self.l = LabelFrame(self.top, text=self.msg.getTxt(), padx=10, pady=10)
        # Placement du cadre
        self.l.place(x=30, y=20)
        # Configuration du cadre
        self.l.configure(background='#202225', foreground="#b6b9be")
        # Liste pour changer la langue du texte
        self.allLabel = allLabel
        # Permet de changer le texte de l'application
        self.allLabel['LabelFrame'].append([self.l, self.msg])
        # Entry pour le nombre à entrer
        self.e = Entry(self.l, width=35)
        # Inclusion de l'Entry dans le cadre
        self.e.pack()
        # Configuration de l'Entry
        self.e.configure(background="#484B52", foreground="#b6b9be", borderwidth=0, highlightthickness=0)
        # Bouton Ok
        self.b = Button(self.top, text='Ok', command=self.cleanup, width=15, height=2)
        # Placement du bouton
        self.b.place(x=90, y=110)
        # Configuration du bouton
        self.b.configure(background="#40444B", foreground="#b6b9be", activebackground="#40444B", activeforeground="#b6b9be",  borderwidth=0, highlightthickness=0)
        # Titre de la fenêtre d'erreur
        self.error = error
        # Titre de la fenêtre d'erreur
        self.errorMsg = errorMsg
        # Langue de la pop-up
        self.langue = langue
        # la valeur du nombre de filtre à appliquer
        self.value = None


    def cleanup(self):
        """ Au clic sur le bouton Ok
        """
        # Récupère la valeur de l'Entry
        value = self.e.get()
        # Si la valeur est un nombre
        if value.isdigit():
            # Convertit le texte en nombre
            self.value = int(value)
            # Détruit la fenêtre
            self.top.destroy()
        # Sinon
        else:
            # Pop-up d'erreur
            messagebox.showerror(self.error[self.langue][0], self.errorMsg[self.langue][4])


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
        self.fen.iconbitmap(default='./image/icon.ico')
        # Change la couleur de l'arrière plan
        self.fen.configure(background='#202225')
        # Le style de l'application
        style = Style(self.fen)
        # Initailisation par défaut
        style.theme_use('alt')
        # Le nom du fihier avec les paramètres
        self.ParamFile = "settings.json"
        # Le lien de sauvegarde et la langue de l'application
        self.saveLink, self.langue, self.client_id, self.color = self.getParam()
        # Liste de tout les objets contenant du texte
        self.alltxtObject = {'Stringvar': [], "LabelFrame": []}
        # Liste de tout les objets pouvant changer de couleur
        self.allColorObjet = []
        # Drapeau Français pour le boutton
        self.Fr = ImageTk.PhotoImage(Image.open('./image/Fr.png').resize((35, 35)))
        # Drapeau Français pour le boutton
        self.En = ImageTk.PhotoImage(Image.open('./image/En.png').resize((35, 35)))
        # Change l'icone au changement de langue
        self.FlagDict = {'fr': [self.Fr, 'left'], 'en': [self.En, 'right']}
        # Si l'utilisateur rentre une valeur du nombre de filtre à appliquer
        self.applyingPerso = False
        # Le nombre de filtre à appliquer
        self.nbFilter = 1
        # Le nom des erreurs
        self.error = {'fr': ['Erreur', "Erreur de téléchargement", "Problème", "Erreur de conversion"],
                      'en': ["Error", "Downloading error", "Problem", "Conversion error"]}
        # Tout les messages d'erreurs
        self.allErrorMsg = {
            'fr':
            ["Lien non valide", "Pas de lien", "Il n'y a aucune musique à convertir", "Le format n'est pas correct",
             'Il faut entrer un nombre'],
            'en': ["Invalid link", "No link", "There is no music to convert", "The format is incorrect", 'You must enter an number']}


        # Initialisation des variables

        # Fichiers actuellement ouvert dans l'application
        self.files = []
        # Différents types de musique et leur nombre de répétition du filtre associé
        self.tags = {"A capella / A cappella": 2, "Chanson française / French chanson": 2, "Musique Classique / Classical Music": 2, "Drum & bass / Drum & bass": 1, "Electro / Electro": 2, "Jazz / Jazz": 2, "Lofi / Lofi": 1, "Pop  / Pop": 1, "Rap / Rap": 1, "Rock / Rock": 1}
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
        self.MusicTags.place(x=50, y=self.height / 2 - 80)
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
            rdb = Radiobutton(self.MusicTags, text=m.getTxt(), value=x + 1, variable=self.musicType, width=30)
            # Ajout du Radiobouton à la liste de changement de couleur
            self.allColorObjet.append(rdb)
            # Ajoute à la liste des objets qui peuvent changer de texte
            self.alltxtObject['LabelFrame'].append([rdb, m])
            # Le nom du bouton
            style_name = rdb.winfo_class()
            # Configure la style du bouton
            style.configure(style_name, foreground="#b6b9be", background='#202225', indicatorcolor="#202225", borderwidth=0, selectcolor="#FAA61A")
            # Précise les couleurs en fonction des états du bouton
            style.map(style_name,
                      foreground=[('disabled', "#b6b9be"), ('pressed', self.color), ('active', self.color)],
                      background=[('disabled', '#202225'), ('pressed', '!focus', '#202225'), ('active', '#202225')],
                      indicatorcolor=[('selected', self.color), ('pressed', self.color)])
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
             "Télécharge: {} au format wav", "La musique à déjà été enregistrée",
             "Téléchargement"],
            'en':
            ["No operation currently", "End of the download", "Search for the song",
             "Downloading of {} at mp3 format", "Changing", "Saving", "End of the download of",
             "End estimated in {}", "Download: {} in wav format", "The song has already been downloaded",
             "Downloading"]}
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
        s.configure("red.Horizontal.TProgressbar", troughcolor='#40444B', background=self.color)
        # Barre de progression qui suit l'évolution des différentes opérations de l'application
        self.progressbar = Progressbar(self.Pgb, orient="horizontal", length=800, mode="determinate", style="red.Horizontal.TProgressbar")
        # La valeur maximale de la barre est 100 (100%)
        self.progressbar["maximum"] = 100
        # Inclusion de la barre de progression dans le cadre
        self.progressbar.pack()


        # Initialisation des boutons

        # Permet de changer le texte contenu dans le bouton
        self.optlabel = Message(msg=StringVar(), text={'fr': [" Ouvrir un fichier "], 'en': [" Open a file "]}, actualLanguage=self.langue)
        # Bouton "ouvrir un fichier" qui appelle openExplorateur au clic
        openFileButton = Button(self.fen, textvariable=self.optlabel.msg, command=self.openExplorateur, width=15, height=2)
        # Affiche le texte par défaut
        self.optlabel.update()
        # Ajoute à la liste des objets qui peuvent changer de texte
        self.alltxtObject['Stringvar'].append(self.optlabel)
        # Placement du bouton dans la fenêtre
        openFileButton.place(x=25, y=30)
        # Configure le bouton
        openFileButton.configure(background="#40444B", foreground="#b6b9be", activebackground="#40444B", activeforeground="#b6b9be",  borderwidth=0, highlightthickness=0)


        # Permet de changer le texte contenu dans le bouton
        self.colorlabel = Message(msg=StringVar(), text={'fr': [" Changer la couleur "], 'en': [" Change the color "]}, actualLanguage=self.langue)
        # Bouton "ouvrir un fichier" qui appelle openExplorateur au clic
        colorbtn = Button(self.fen, textvariable=self.colorlabel.msg, command=self.getColor, width=16, height=2)
        # Affiche le texte par défaut
        self.colorlabel.update()
        # Ajoute à la liste des objets qui peuvent changer de texte
        self.alltxtObject['Stringvar'].append(self.colorlabel)
        # Placement du bouton dans la fenêtre
        colorbtn.place(x=160, y=30)
        # Configure le bouton
        colorbtn.configure(background="#40444B", foreground="#b6b9be", activebackground="#40444B", activeforeground="#b6b9be",  borderwidth=0, highlightthickness=0)


        # Permet de changer le texte contenu dans le bouton
        self.convlabel = Message(msg=StringVar(), text={'fr': [" Conversion "], 'en': [" Convert "]}, actualLanguage=self.langue)
        # Bouton "Conversion" qui appelle conversion au clic
        convBtn = Button(self.fen, textvariable=self.convlabel.msg, command=self.conversion, width=15, height=2)
        # Affiche le texte par défaut
        self.convlabel.update()
        # Ajoute à la liste des objets qui peuvent changer de texte
        self.alltxtObject['Stringvar'].append(self.convlabel)
        # Placement du cadre dans la fenêtre
        convBtn.place(x=190, y=190)
        # Configure le bouton
        convBtn.configure(background="#40444B", foreground="#b6b9be", activebackground="#40444B", activeforeground="#b6b9be",  borderwidth=0, highlightthickness=0)


        # La position et le drapeau à utliser
        flag, pos = self.FlagDict[self.langue]
        # Bouton "Fr / En" qui appelle switchL au clic
        self.lbtn = Button(self.fen, text=" Fr / En ", image=flag, compound=pos, command=self.switchL, width=103, height=33, justify='left')
        # Placement du cadre dans la fenêtre
        self.lbtn.place(x=300, y=30)
        # Configure le bouton
        self.lbtn.configure(background="#40444B", foreground="#b6b9be", activebackground="#40444B", activeforeground="#b6b9be",  borderwidth=0, highlightthickness=0)


        # Permet de changer le texte contenu dans le bouton
        self.persolabel = Message(msg=StringVar(), text={'fr': [" Personaliser "], 'en': [" Personalize "]}, actualLanguage=self.langue)
        # Bouton "Conversion" qui appelle conversion au clic
        persoBtn = Button(self.fen, textvariable=self.persolabel.msg, command=self.popup, width=15, height=2)
        # Affiche le texte par défaut
        self.persolabel.update()
        # Ajoute à la liste des objets qui peuvent changer de texte
        self.alltxtObject['Stringvar'].append(self.persolabel)
        # Placement du cadre dans la fenêtre
        persoBtn.place(x=110, y=510)
        # Configure le bouton
        persoBtn.configure(background="#40444B", foreground="#b6b9be", activebackground="#40444B", activeforeground="#b6b9be",  borderwidth=0, highlightthickness=0)


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


    def getColor(self):
        """ Ouvre une fenêtre pour changer la couleur
        """
        # Ouvre la fenêtre
        color = askcolor()
        # Si une couleur est séléctionnée
        if color[1]:
            # Change la couleur
            self.color = color[1]
            # Sauvegarde les nouveaux paramètres
            self.saveParam()
            # Change la couleur des objets qui le peuvent
            self.switchColor()


    def popup(self):
        """ Crée une pop-up pour demander le nombre de filtre à applliquer
        """
        # Signale l'utilisation d'une valeur personelle
        self.applyingPerso = True
        # Permet de changer entre les deux langues
        self.persoMsg = Message(text={'fr': [" Entrer le nombre de filter à appliqer "], 'en': [" Enter the number of filter to apply "]}, actualLanguage=self.langue)
        # Crée une pop-up pour demander la valeur
        self.w = PopupWindow(self.fen, self.persoMsg, self.alltxtObject, self.error, self.allErrorMsg, self.langue)
        # Met la fenêtre au dessus de la principale
        self.fen.wait_window(self.w.top)
        # Récupère le nombre entré
        self.nbFilter = self.w.value
        # Si aucun nombre n'a été entré
        if not self.nbFilter:
            # On n'utilise pas le filtre personalisé
            self.applyingPerso = False


    def getParam(self):
        """ Récupère les paramètres de l'application
        rtype : str(path) / None, 'fr' / 'en', str / None
        """
        # Si le fichier de paramètre existe dans le dossier
        if self.ParamFile in os.listdir():
            # Ouvre le fichier
            f = json.load(open(self.ParamFile))
            # Retourne les paramètres
            return f["OutputFile"], f['Language'], f['Client_id'], f['Color']
        # Si le fichier n'est pas dans le dossier
        else:
            # Retourne des paramètres par défaut
            return None, 'fr', None, '#6580f1'


    def saveParam(self):
        """ Enregistre les paramètres
        """
        json.dump({"OutputFile": self.saveLink, "Language": self.langue, "Client_id": self.client_id, "Color": self.color}, open(self.ParamFile, "w"), indent=4, sort_keys=True)


    def switchColor(self):
        """ Change la couleur des objets qui le peuvent (la barre de progression et les radioboutons)
        """
        # Le style de l'application
        style = Style(self.fen)
        # Initailisation par défaut
        style.theme_use('alt')
        # Configure le style
        style.configure("red.Horizontal.TProgressbar", troughcolor='#40444B', background=self.color)
        # Barre de progression qui suit l'évolution des différentes opérations de l'application
        self.progressbar.configure(style="red.Horizontal.TProgressbar")
        # pour chaque bouton
        for rdb in self.allColorObjet:
            # Le nom du bouton
            style_name = rdb.winfo_class()
            # Configure la style du bouton
            style.configure(style_name, foreground="#b6b9be", background='#202225',
                            indicatorcolor="#202225", borderwidth=0, selectcolor="#FAA61A")
            # Précise les couleurs en fonction des états du bouton
            style.map(style_name,
                      foreground=[('disabled', "#b6b9be"), ('pressed', self.color), ('active', self.color)],
                      background=[('disabled', '#202225'), ('pressed', '!focus', '#202225'), ('active', '#202225')],
                      indicatorcolor=[('selected', self.color), ('pressed', self.color)])
            # Configure le style du bouton
            rdb.configure(style=style_name)


    def switchL(self):
        """ Change le langue de l'application
        """
        # Change 'fr' en 'en' et inversement en fonction de la langue actuelle
        self.langue = 'en' if self.langue == 'fr' else 'fr'
        # Pour chaque objet Message comportant un Stringvar
        for l in self.alltxtObject["Stringvar"]:
            # Change le langue du message
            l.switchLang(self.langue)
            # Change le message
            l.update()
        # Pour chaque objet Message ne comportant pas de Stringvar
        for l in self.alltxtObject['LabelFrame']:
            # Change le langue du message de l'objet Message
            l[1].switchLang(self.langue)
            # Reconfigure le texte du LabelFrame
            l[0].configure(text=l[1].getTxt())
        # Récupère le nouveau drapeau et sa position dans le bouton
        flag, pos = self.FlagDict[self.langue]
        # Reconfigure le bouton
        self.lbtn.configure(image=flag, compound=pos, justify=pos)
        self.saveParam()


    def getSaveLink(self):
        """ Récupère le lien vers le dossier de sauvegarde des musiques
        """
        # Ouvre une fenêtre explorer pour demander le chemin vers le dossier
        path = easygui.diropenbox("Séléctionner un fichier de sauvegarde des musiques")
        # Si le chemin est renseigné
        if path != None:
            # Sauvegarde le chemin dans le fichier paramètre
            json.dump({"OutputFile": path, 'Language': self.langue, "Client_id": self.client_id,
                       "Color": self.color}, open(self.ParamFile, "w"), indent=4, sort_keys=True)
        # Si le chemin n'est pas renseigné
        else:
            # Chemin par défaut
            path = './Music'
        # Retourne le chemin
        return path


    def conversion(self):
        """ Lance la conversion
        """
        # Le lien vers le fichier de sauvegarde
        if not self.saveLink:
            self.saveLink = self.getSaveLink()
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
            # Prend le nombre de filtre à appliquer
            nbRep = self.tags[musictype] if not self.applyingPerso else self.nbFilter
            self.nbFilter = 1
            self.applyingPerso = False
            # lance l'equalizer
            Equalizer(music, nbRep, self.progressbar, self.msg, gain, self.saveLink).start()
        # Si il y a une erreur
        except Exception as e:
            # Nom de l'erreur
            name = e.__class__.__name__
            # Si l'erreur est du au fait qu'il n'y ait pas de musique à transformer
            if name == "IndexError":
                # Pop-up d'erreur
                messagebox.showerror(self.error[self.langue][3], self.allErrorMsg[self.langue][2])
            # Si il s'agit d'une autre erreur
            else:
                # Pop-up d'erreur
                messagebox.showerror(self.error[self.langue][3], f"{name}: {e}")


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
                messagebox.showerror(self.error[self.langue][0], self.allErrorMsg[self.langue][3])


    def run(self):
        """ Fonction principale lance la fenêtre
        """
        self.fen.mainloop()


#
# ---------- Test ---------------------------------------------------------------------------------
#


if __name__ == "__main__":
    Inteface().run()
