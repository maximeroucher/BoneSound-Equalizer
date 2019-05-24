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

    def __init__(self, fen):
        """ Barre d'avancement, est appellé à chaque itération du téléchargement
        itype : Tkinter.ttk.ProgressBar, Message()
        """
        # La fenêtre principale
        self.fen = fen
        # Progressbar de la fenêtre
        self.progress = self.fen.progress
        # Message de la fenêtre
        self.msg = self.fen.msg


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

    def __init__(self, nbRepetition, fen, gain):
        """ Transforme la musique pour le casque
        itype : str, int, Tkinter.ttk.ProgressBar, Tkinter.StringVar
        """
        # Initailisation du Thread
        Thread.__init__(self)
        # Fréquence en dessous de laquelle, les fréquences sont descendus de 6 dB
        self.upperFrequency = 450
        # Fréquence au  dessus de laquelle, les fréquences sont descendus de 6 dB
        self.lowerFrequency = 9000
        # La fenêtre
        self.fen = fen
        # Le dossier d'enregistrement de la musique
        self.out = self.fen.saveLink
        # Message de la fenêtre
        self.msg = self.fen.msg
        # Change le message de la fenêtre
        self.msg.changeMsg(4)
        self.msg.update()
        # La liste des musiques
        self.files = self.fen.files
        # Récupère la première musique de la liste
        filename = self.files[0]
        # La suppression du fichier .wav de transition
        self.delWav = False
        # Nom du fichier à transformer (déjà en wav)
        self.filename = self.get_song(filename)
        # Nom de fichier en sortie
        ext = filename.split("\\")[-1].split('.')[0]
        self.outname = f'{self.out}/out - {ext}.wav'
        # Barre de progression de la fenêtre
        self.progress = self.fen.progressbar
        # Nombre de fois à appliquer le filtre
        self.nbRepetition = nbRepetition
        # Le gain à appliquer à la musique
        self.gain = gain
        # La liste des musiquesà afficher
        self.filesList = self.fen.filesList


    def get_song(self, path):
        """ Récupère le chemin vers la musique et convertit en wav les autres formats
        itype : str (path)
        """
        # Si le fichier n'existe pas
        if self.out == "./Music" and not 'Music' in os.listdir():
            # Crée le fichier
            os.makedirs("Music")
        # Changement de nom pour la commande cmd
        changeBack = False
        # Si la musique n'est pas en .wav
        if path[-4:] != ".wav":
            # Récupère la nom de la musique sans l'extension
            ext = path.split("\\")[-1].split('.')[0]
            if f'{ext}.wav' in os.listdir(self.out):
                return f'{self.out}/{ext}.wav'
            else:
                # Il faut enlever le fichier wav de transition
                self.delWav = True
                # Enleve les espaces pour éviter les problèmes de cmd
                if " " in path:
                    # Il faudra rechanger le nom
                    changeBack = True
                    # Change le nom pour éviter le problème cmd
                    path2 = "-".join(path.split(' '))
                    # Renomme le fichier
                    os.renames(path, path2)
                    # Sauvegarde le nouveau fichier
                    path = path2
                    # Lieu de sauvgarde du fichier une fois converti en .wav
                    outname = f'{self.out}/{ext}.wav'
                    # Convertit le fchier en .wav
                    subprocess.call(f'ffmpeg -y -i "{path}" -vn "{outname}"')
                    # Si il faut rechanger le nom
                    if changeBack:
                        # Renomme les deux fichiers
                        os.renames(path, " - ".join(" ".join(path.split("-")).split("   ")))
                        os.renames(outname, " - ".join(" ".join(outname.split("-")).split("   ")))
                    # Retourne le chemin vers la musique convertie
                    return os.path.abspath(" - ".join(" ".join(outname.split("-")).split("   ")))
        # Sinon, retourne le chemin sans modification
        return path


    def run(self):
        """ Transformation de la musique
        """
        # Le nombre d'étape maximale
        max_value = 2 * self.nbRepetition + 2
        # Progression de la barre
        x = 1
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
        self.msg.update()
        # Augmente le volume pour compenser les filtres
        song = song + self.gain
        # Exporte le fichier
        song.export(self.outname, format="wav")
        # Change le message de la fenêtre
        self.msg.changeMsg(0)
        self.msg.update()
        # Change la barre de progression de la fenêtre
        self.progress['value'] = 0
        # La supprime de l'affichage
        self.filesList.delete(0)
        # Enlève de la liste la musique
        self.files.pop(0)
        # Supprime la musique wav de transition
        if self.delWav:
            # Récupère et supprime le fichier
            os.remove("".join(self.outname.split("out - ")))


#
# ---------- Classe PopupWindow -------------------------------------------------------------------
#

class PopupWindow():

    def __init__(self, master, fen):
        """ Pop-up pour demander le nombre de filtre à appliquer
        itype : tkinter.Tk(), Interface()
        """
        # Fenêtre au dessus de la principale
        self.top = Toplevel(master)
        # Couleur de fond de la fenêtre
        self.top.configure(background='#202225')
        # Taille de fond de la fenêtre
        self.top.geometry(f"300x180")
        # La fenêtre derrière
        self.fen = fen
        # Message de la fenêtre
        self.msg = self.fen.popupMsg
        # La langue de la fenêtre
        self.langue = self.fen.langue
        # Change le titre de la pop-up
        self.top.title(self.msg.getTxt())
        # Permet de changer entre les deux langues
        self.popupMsg = Message(text={'fr': [" Entrer le nombre de filtre(s) à appliquer "], 'en': [" Enter the number of filter(s) to apply "]}, actualLanguage=self.langue)
        # Cadre pour entrer le nombre
        self.lblFrame = LabelFrame(self.top, text=self.popupMsg.getTxt(), padx=10, pady=10)
        # Placement du cadre
        self.lblFrame.place(x=30, y=20)
        # Configuration du cadre
        self.lblFrame.configure(background='#202225', foreground="#b6b9be")
        # Liste pour changer la langue du texte
        self.allLabel = self.fen.alltxtObject
        # Permet de changer le texte de l'application
        self.allLabel['LabelFrame'].append([self.lblFrame, self.popupMsg])
        # Entry pour le nombre à entrer
        self.entry = Entry(self.lblFrame, width=35)
        # Inclusion de l'Entry dans le cadre
        self.entry.pack()
        # Configuration de l'Entry
        self.entry.configure(background="#484B52", foreground="#b6b9be", borderwidth=0, highlightthickness=0)
        # Bouton Ok
        self.btn = Button(self.top, text='Ok', command=self.cleanup, width=15, height=2)
        # Placement du bouton
        self.btn.place(x=90, y=110)
        # Configuration du bouton
        self.btn.configure(background="#40444B", foreground="#b6b9be", activebackground="#40444B", activeforeground="#b6b9be",  borderwidth=0, highlightthickness=0)
        # Titre de la fenêtre d'erreur
        self.error = self.fen.error
        # Titre de la fenêtre d'erreur
        self.errorMsg = self.fen.allErrorMsg
        # Langue de la pop-up
        self.langue = self.fen.langue
        # la valeur du nombre de filtre à appliquer
        self.value = None
        # Retourne le filtre : Bouton Entrée
        self.top.bind('<Return>', self.cleanup)
        # Focus la fenêtre
        self.top.focus_set()


    def cleanup(self):
        """ Au clic sur le bouton Ok
        """
        # Récupère la valeur de l'Entry
        value = self.entry.get()
        # Si la valeur est un nombre
        if value.isdigit():
            # Convertit le texte en nombre
            self.value = int(value)
            # Détruit la fenêtre
            self.top.destroy()
            # Déclare la fermeture de la fenêtre
            self.fen.popupFen = False
        # Sinon
        else:
            # Pop-up d'erreur
            messagebox.showerror(self.error[self.langue][0], self.errorMsg[self.langue][4])


#
# ---------- Classe PopupParamWindow -------------------------------------------------------------------
#


class PopupParamWindow():

    def __init__(self, master, fen):
        """ Pop-up de paramètre
        itype : tkinter.Tk(), Interface()
        """
        # Accède aux propriétés de la fenêtre
        self.fen = fen
        # Les objets qui change de couleur
        self.allColorObjet = fen.allColorObjet
        # Les objets qui change de texte
        self.alltxtObject = fen.alltxtObject
        # La langue de la fenêtre
        self.langue = self.fen.langue
        # Le nom de la pop-up
        self.msg = self.fen.persoMsg
        # Les drapeaux de la pop-up
        self.FlagDict = self.fen.FlagDict
        # Fenêtre au dessus de la principale
        self.top = Toplevel(master)
        # Couleur de fond de la fenêtre
        self.top.configure(background='#202225')
        # Taille de fond de la fenêtre
        self.top.geometry(f"250x150")
        # Change le titre de la pop-up
        self.top.title(self.msg.getTxt())
        # Permet de changer le texte contenu dans le bouton
        self.colorlabel = Message(msg=StringVar(), text={'fr': [" Changer la couleur "], 'en': [" Change the color "]}, actualLanguage=self.langue)
        # Bouton "ouvrir un fichier" qui appelle openExplorateur au clic
        colorbtn = Button(self.top, textvariable=self.colorlabel.msg, command=self.fen.getColor, width=16, height=2)
        # Affiche le texte par défaut
        self.colorlabel.update()
        # Ajoute à la liste des objets qui peuvent changer de texte
        self.alltxtObject['Stringvar'].append(self.colorlabel)
        # Placement du bouton dans la fenêtre
        colorbtn.place(x=70, y=25)
        # Configure le bouton
        colorbtn.configure(background="#40444B", foreground="#b6b9be", activebackground="#40444B", activeforeground="#b6b9be",  borderwidth=0, highlightthickness=0)
        # La position et le drapeau à utliser
        flag, pos = self.FlagDict[self.langue]
        # Bouton "Fr / En" qui appelle switchL au clic
        self.lbtn = Button(self.top, text=" Fr / En ", image=flag, compound=pos, command=self.fen.switchL, width=103, height=33, justify='left')
        # Placement du cadre dans la fenêtre
        self.lbtn.place(x=75, y=85)
        # Configure le bouton
        self.lbtn.configure(background="#40444B", foreground="#b6b9be", activebackground="#40444B", activeforeground="#b6b9be",  borderwidth=0, highlightthickness=0)
        # Supprimer la première music de la liste : Bouton Suppr
        self.top.bind('<Delete>', self.cleanup)
        # Changer la couleur : Bouton c
        self.top.bind('<c>', self.fen.getColor)
        # Change la langue : Bouton Tab
        self.top.bind('<Shift_L>', self.fen.switchL)
        # Focus la fenêtre
        self.top.focus_set()


    def cleanup(self):
        """ Au clic sur le bouton Ok
        """
        # Ferme la fenêtre
        self.top.destroy()
        # Déclare la fermeture de la fenêtre
        self.fen.popupParamFen = False


#
# ---------- Classe Inteface ----------------------------------------------------------------------
#


class Inteface:

    def __init__(self):

        # Initialisation de la fenêtre

        # Déclaration d'un objet Tkinter
        self.fen = Tk()
        # Largeur de la fenêtre
        self.width = 1366
        # Hauteur de la fenêtre
        self.height = 700
        # Dimmensionne la fenêtre
        #self.fen.geometry(f"{self.width}x{self.height}")
        self.fen.state('zoomed')
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
        self.saveLink, self.langue, self.color, self.MusicLink = self.getParam()
        # Liste de tout les objets contenant du texte
        self.alltxtObject = {'Stringvar': [], "LabelFrame": []}
        # Liste de tout les objets pouvant changer de couleur
        self.allColorObjet = []
        # Drapeau Français pour le boutton
        self.Fr = ImageTk.PhotoImage(Image.open('./image/Fr.png').resize((35, 35)))
        # Drapeau Français pour le boutton
        self.En = ImageTk.PhotoImage(Image.open('./image/En.png').resize((35, 35)))
        # Image des paramètres
        self.ParamImg = ImageTk.PhotoImage(Image.open('./image/Param.png').resize((35, 35)))
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
        # Ouvre l'image
        self.image = ImageTk.PhotoImage(Image.open('./image/Image.png').resize((140, 140)))
        # L'élément séléctionné dans la liste des musiques à transformer
        self.delElement = StringVar()
        # Si la fenêtre "personnaliser" est ouverte
        self.popupFen = False
        # Si la fenêtre "paramètres" est ouverte
        self.popupParamFen = False


        # Initialisation des variables

        # Fichiers actuellement ouvert dans l'application
        self.files = []
        # Différents types de musique et leur nombre de répétition du filtre associé
        self.tags = {"A capella / A cappella": 2, "Chanson française / French song": 2, "Musique Classique / Classical Music": 2, "Drum & bass / Drum & bass": 1, "Electro / Electro": 2, "Jazz / Jazz": 2, "Lofi / Lofi": 1, "Pop  / Pop": 1, "Rap / Rap": 1, "Rock / Rock": 1, "RnB / RnB": 1, "Hard Rock / Hard Rock": 1, "Reggae / Reggae":1}
        # Triés dans l'ordre alphabétique
        self.tags = OrderedDict(sorted(self.tags.items(), key=lambda t: t[0]))
        # Type de musique séléctionné (IntVar permet de modifier la valeru des Radioboutons en le modifiant)
        self.musicType = IntVar()
        # Coche par défaut le premier élément de la liste
        self.musicType.set(1)
        # le gain de volume
        self.volumeGain = IntVar()
        # 10 Par défaut
        self.volumeGain.set(5)


        # Image qui change de couleur
        self.LabelImage = Label(self.fen, image=self.image, width=140, height=140, borderwidth=0, highlightthickness=0, background=self.color)
        # Ajoute l'image à la fenêtre
        self.LabelImage.place(x=450, y=30)

        # Bouton pour changer la langue
        flag, _ = self.FlagDict[self.langue]
        # Création du bouton
        self.lblFlag = Button(self.fen, image=flag, width=35, height=35, background='#202225', command=self.switchL)
        # Place le bouton
        self.lblFlag.place(x=1300, y=640)
        # Configure le bouton
        self.lblFlag.configure(background="#202225", foreground="#b6b9be", activebackground="#202225", activeforeground="#b6b9be",  borderwidth=0, highlightthickness=0)


        # Initialisation de la liste des musique à convertir

        # Permet de changer le texte contenu dans le cadre
        self.musicLabel = Message(text={'fr': [" Liste des musiques à convertir "], 'en': [' List of musics to convert ']}, actualLanguage=self.langue)
        # Cadre contenant la liste
        self.MusicFiles = LabelFrame(self.fen, text=self.musicLabel.getTxt(), padx=10, pady=10)
        # Placement du cadre dans la fenêtre
        self.MusicFiles.place(x=700, y=25)
        # Configure l'affichage du cadre
        self.MusicFiles.configure(background='#202225', foreground="#b6b9be")
        # Ajoute à la liste des objets qui peuvent changer de texte
        self.alltxtObject['LabelFrame'].append([self.MusicFiles, self.musicLabel])
        # Liste contenant les musiques
        self.filesList = Listbox(self.MusicFiles, width=100, height=33)
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
        self.MusicTags.place(x=130, y=160)
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


        # Espace entre la liste et le bouton
        lbl = Label(self.MusicTags, height=1)
        lbl.pack()
        lbl.configure(background="#202225")

        # Permet de changer le texte contenu dans le bouton
        self.persolabel = Message(msg=StringVar(), text={'fr': [" Personnaliser "], 'en': [" Personalize "]}, actualLanguage=self.langue)
        # Bouton "Conversion" qui appelle conversion au clic
        persoBtn = Button(self.MusicTags, textvariable=self.persolabel.msg, command=self.popup, width=15, height=2)
        # Affiche le texte par défaut
        self.persolabel.update()
        # Ajoute à la liste des objets qui peuvent changer de texte
        self.alltxtObject['Stringvar'].append(self.persolabel)
        # Placement du cadre dans la fenêtre
        persoBtn.pack(anchor='w')
        # Configure le bouton
        persoBtn.configure(background="#40444B", foreground="#b6b9be", activebackground="#40444B", activeforeground="#b6b9be",  borderwidth=0, highlightthickness=0)


        # Initialisation de la barre de progression

        # Permet de changer le texte contenu dans le cadre
        self.pgbLabel = Message(text={'fr': [" Progrès de l'opération "], 'en': [' Progress of the operation ']}, actualLanguage=self.langue)
        # Cadre contenant la barre
        self.Pgb = LabelFrame(self.fen, text=self.pgbLabel.getTxt(), padx=10, pady=10)
        # Placement du cadre dans la fenêtre
        self.Pgb.place(x=75, y=600)
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
        self.progressbar = Progressbar(self.Pgb, orient="horizontal", length=1150, mode="determinate", style="red.Horizontal.TProgressbar")
        # La valeur maximale de la barre est 100 (100%)
        self.progressbar["maximum"] = 100
        # Inclusion de la barre de progression dans le cadre
        self.progressbar.pack()


        # Initialisation des boutons

        # Bouton "ouvrir un fichier" qui appelle openExplorateur au clic
        openFileButton = Button(self.fen, image=self.ParamImg, command=self.popupParam, width=35, height=35)
        # Placement du bouton dans la fenêtre
        openFileButton.place(x=10, y=10)
        # Configure le bouton
        openFileButton.configure(background="#202225", activebackground="#202225", borderwidth=0, highlightthickness=0)


        # Permet de changer le texte contenu dans le bouton
        self.optlabel = Message(msg=StringVar(), text={'fr': [" Ouvrir un fichier "], 'en': [" Open a file "]}, actualLanguage=self.langue)
        # Bouton "ouvrir un fichier" qui appelle openExplorateur au clic
        openFileButton = Button(self.fen, textvariable=self.optlabel.msg, command=self.openExplorateur, width=15, height=2)
        # Affiche le texte par défaut
        self.optlabel.update()
        # Ajoute à la liste des objets qui peuvent changer de texte
        self.alltxtObject['Stringvar'].append(self.optlabel)
        # Placement du bouton dans la fenêtre
        openFileButton.place(x=190, y=90)
        # Configure le bouton
        openFileButton.configure(background="#40444B", foreground="#b6b9be", activebackground="#40444B", activeforeground="#b6b9be",  borderwidth=0, highlightthickness=0)


        # Permet de changer le texte contenu dans le bouton
        self.convlabel = Message(msg=StringVar(), text={'fr': [" Conversion "], 'en': [" Convert "]}, actualLanguage=self.langue)
        # Bouton "Conversion" qui appelle conversion au clic
        convBtn = Button(self.fen, textvariable=self.convlabel.msg, command=self.conversion, width=15, height=2)
        # Affiche le texte par défaut
        self.convlabel.update()
        # Ajoute à la liste des objets qui peuvent changer de texte
        self.alltxtObject['Stringvar'].append(self.convlabel)
        # Placement du cadre dans la fenêtre
        convBtn.place(x=190, y=550)
        # Configure le bouton
        convBtn.configure(background="#40444B", foreground="#b6b9be", activebackground="#40444B", activeforeground="#b6b9be",  borderwidth=0, highlightthickness=0)


        # Permet de changer le texte contenu dans le bouton
        self.folderLabel = Message(msg=StringVar(), text={'fr': [" Dossier de sortie "], 'en': [" Output folder "]}, actualLanguage=self.langue)
        # Bouton "Conversion" qui appelle conversion au clic
        folderbtn = Button(self.fen, textvariable=self.folderLabel.msg, command=self.getSaveLink, width=15, height=2)
        # Affiche le texte par défaut
        self.folderLabel.update()
        # Ajoute à la liste des objets qui peuvent changer de texte
        self.alltxtObject['Stringvar'].append(self.folderLabel)
        # Placement du cadre dans la fenêtre
        folderbtn.place(x=190, y=30)
        # Configure le bouton
        folderbtn.configure(background="#40444B", foreground="#b6b9be", activebackground="#40444B", activeforeground="#b6b9be",  borderwidth=0, highlightthickness=0)


        # Permet de changer le texte contenu dans le bouton
        self.supprLabel = Message(msg=StringVar(), text={'fr': [" Supprimer la musique "], 'en': [" Delete music "]}, actualLanguage=self.langue)
        # Bouton "Suuprimer" qui appelle delMusic au clic
        supprbtn = Button(self.fen, textvariable=self.supprLabel.msg, command=self.delMusic, width=20, height=2)
        # Affiche le texte par défaut
        self.supprLabel.update()
        # Ajoute à la liste des objets qui peuvent changer de texte
        self.alltxtObject['Stringvar'].append(self.supprLabel)
        # Placement du cadre dans la fenêtre
        supprbtn.place(x=1167, y=545)
        # Configure le bouton
        supprbtn.configure(background="#484B52", foreground="#b6b9be", activebackground="#40444B", activeforeground="#b6b9be",  borderwidth=0, highlightthickness=0)


        # Curseur du gain de volume

        # Cadre du curseur
        VolumeLabel = LabelFrame(self.fen, text=' Gain (dB) ')
        # Configure le cadre
        VolumeLabel.configure(background="#202225", foreground="#b6b9be", borderwidth=0, highlightthickness=0)
        # Place le cadre dans la fenêtre
        VolumeLabel.place(x=490, y=200)
        # Création du curseur
        scale = Scale(VolumeLabel, from_=-10, to=20, resolution=1, tickinterval=3, length=300, variable=self.volumeGain)
        # Configure le curseur
        scale.configure(background="#40444B", foreground="#b6b9be", borderwidth=0, highlightthickness=0, troughcolor="#b6b9be", takefocus=0)
        # Inclusion du curseur
        scale.pack()


        # Raccourci clavier

        # Supprimer la première music de la liste : Bouton Suppr
        self.fen.bind('<Delete>', self.delMusic)
        # Lancer la conversion : Bouton Entrée
        self.fen.bind('<Return>', self.conversion)
        # Ouvrir les paramètres : Bouton p (minuscule)
        self.fen.bind('<p>', self.popupParam)
        # Ouvrir le dossier de sauvegarde : Ctrl + s (minuscule)
        self.fen.bind('<Control-s>', self.getSaveLink)
        # Ouvrir la fenêtre d'accès au musiques : Ctrl + n (minuscule)
        self.fen.bind('<Control-o>', self.openExplorateur)
        # Change la langue : Bouton Tab
        self.fen.bind('<Shift_L>', self.switchL)


    def popup(self, event=None):
        """ Crée une pop-up pour demander le nombre de filtre à applliquer
        """
        # Envoi la fenêtre à l'avant si elle existe
        try:
            # Place la fenêtre devant la fenêtre principale
            self.w.top.lift()
            self.w.top.attributes('-topmost', True)
            self.w.top.attributes('-topmost', False)
            # Focus la fenêtre
            self.w.top.focus_set()
        # Sinon la créer
        except:
            self.popupFen = True
            # Signale l'utilisation d'une valeur personelle
            self.applyingPerso = True
            # Permet de changer entre les deux langues
            self.popupMsg = Message(text={'fr': [" Personnalisation "], 'en': [" Personalization "]}, actualLanguage=self.langue)
            # Crée une pop-up pour demander la valeur
            self.w = PopupWindow(self.fen, self)
            # Met la fenêtre au dessus de la principale
            self.fen.wait_window(self.w.top)
            # Récupère le nombre entré
            self.nbFilter = self.w.value
            # Si aucun nombre n'a été entré
            if not self.nbFilter:
                # On n'utilise pas le filtre personalisé
                self.applyingPerso = False


    def popupParam(self, event=None):
        """ Crée une pop-up pour demander le nombre de filtre à applliquer
        """
        # Envoi la fenêtre à l'avant si elle existe
        try:
            # Place la fenêtre devant la fenêtre principale
            self.p.top.lift()
            self.p.top.attributes('-topmost', True)
            self.p.top.attributes('-topmost', False)
            # Focus la fenêtre
            self.p.top.focus_set()
        # Sinon la créer
        except:
            self.popupParamFen = True
            # Signale l'utilisation d'une valeur personelle
            # Signale l'utilisation d'une valeur personelle
            self.applyingPerso = True
            # Permet de changer entre les deux langues
            self.persoMsg = Message(text={'fr': [" Paramètres "], 'en': [" Settings "]}, actualLanguage=self.langue)
            # Crée une pop-up pour demander la valeur
            self.p = PopupParamWindow(self.fen, self)
            # Met la fenêtre au dessus de la principale
            self.fen.wait_window(self.p.top)


    def getParam(self):
        """ Récupère les paramètres de l'application
        rtype : str(path) / None, 'fr' / 'en', str / None
        """
        # Si le fichier de paramètre existe dans le dossier
        if self.ParamFile in os.listdir():
            # Ouvre le fichier
            f = json.load(open(self.ParamFile))
            # Retourne les paramètres
            return f["OutputFile"], f['Language'], f['Color'], f['MusicLink']
        # Si le fichier n'est pas dans le dossier
        else:
            # Retourne des paramètres par défaut
            return None, 'fr', '#6580f1', None


    def switchColor(self):
        """ Change la couleur des objets qui le peuvent (la barre de progression et les radioboutons)
        """
        self.LabelImage.configure(background=self.color)
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


    def switchL(self, event=None):
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
            # Si une fenêtre est ouverte
            try:
                # Reconfigure le texte du LabelFrame
                l[0].configure(text=l[1].getTxt())
            # Sinon
            except:
                pass
        # Récupère le nouveau drapeau et sa position dans le bouton
        flag, pos = self.FlagDict[self.langue]
        self.lblFlag.configure(image=flag)
        # Si la fenêtre des paramètres est ouverte
        try:
            if self.p:
                # Change le titre de la fenêtre
                self.p.top.title(self.persoMsg.text[self.langue][0])
                # Reconfigure le bouton
                self.p.lbtn.configure(image=flag, compound=pos, justify=pos)
        # Sinon
        except:
            pass
        # Si la fenêtre de personnalisation est ouverte
        try:
            if self.w:
                # Change le titre de la fenêtre
                self.w.top.title(self.popupMsg.text[self.langue][0])
        # Sinon
        except:
            pass
        # Sauvegarde les paramètres (la langue ici)
        self.saveParam()


    def getColor(self, event=None):
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
        # Place la fenêtre devant la fenêtre principale
        self.p.top.lift()
        self.p.top.attributes('-topmost', True)
        self.p.top.attributes('-topmost', False)
        # Focus la fenêtres
        self.p.top.focus_set()


    def delMusic(self, event=None):
        # Si il y a une musique à supprimer
        try:
            # Récupère la place de la musique à supprimer
            value = self.filesList.get(self.filesList.curselection())
            # Récupère son nom complet (l'affichage le limite)
            for x in self.files:
                if x.endswith(value):
                    index = self.files.index(x)
                    break
            # Le supprime de la liste d'affichage et de celle des musiques
            self.files.pop(index)
            self.filesList.delete(index)
        # Sinon
        except:
            pass


    def saveParam(self):
        """ Enregistre les paramètres
        """
        json.dump({"OutputFile": self.saveLink, "Language": self.langue, "Color": self.color, "MusicLink": self.MusicLink}, open(self.ParamFile, "w"), indent=4, sort_keys=True)


    def getSaveLink(self, event=None):
        """ Récupère le lien vers le dossier de sauvegarde des musiques
        """
        # Change le texte
        self.openMsg = {'fr': [" Séléction du dossier de sauvegarde "], 'en': [" Saving folder selection "]}
        # Ouvre une fenêtre explorer pour demander le chemin vers le dossier
        path = easygui.diropenbox(self.openMsg[self.langue][0], default=f"{self.saveLink}\\")
        # Si le chemin est renseigné
        if path != None:
            self.saveLink = path
            # Sauvegarde le chemin dans le fichier paramètre
            self.saveParam()


    def conversion(self, event=None):
        """ Lance la conversion
        """
        # Le lien vers le fichier de sauvegarde
        if self.saveLink == None:
            self.getSaveLink()
        # Gestion d'erreur
        try:
            # Récupère le type de musiqye séléctionné
            musictype = list(self.tags.keys())[int(self.musicType.get()) - 1]
            # Récupère la valeur du gain de volume
            gain = self.volumeGain.get()
            # Prend le nombre de filtre à appliquer
            nbRep = self.tags[musictype] if not self.applyingPerso else self.nbFilter
            # Reset le nombre de filtre à appliquer
            self.nbFilter = 1
            # Remet par défaut l'utilisation du nombre de filtre personalisé
            self.applyingPerso = False
            # lance l'equalizer
            Equalizer(nbRep, self, gain).start()
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


    def openExplorateur(self, event=None):
        # Ouvre un explorateur de fichier qui retourne le chemin depuis la racine jusqu'au ficiers séléstionnés
        files = easygui.fileopenbox(multiple=True, default=f"{self.MusicLink}\\")
        if files:
            # Pour chaque fichier de la liste
            for f in files:
                # Si le fichier est un fichier wav est n'est pas déjà dans la liste
                if f[-4:] in [".wav", ".mp3"]:
                    if f not in self.files:
                        # Ajoute le fichier à la liste des fichiers à convertir
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
            # Change le fichier de musique
            self.MusicLink = "\\".join(files[0].split("\\")[:-1])
            self.saveParam()


    def run(self):
        """ Fonction principale lance la fenêtre
        """
        self.fen.mainloop()


#
# ---------- Test ---------------------------------------------------------------------------------
#


if __name__ == "__main__":
    Inteface().run()
