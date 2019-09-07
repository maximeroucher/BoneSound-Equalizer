#
# ---------- Import -------------------------------------------------------------------------------
#


from __future__ import unicode_literals

# Librairies intégrées par défaut à Python
import json
import math
import os
import re
import subprocess
import time
import webbrowser
from threading import Thread
from tkinter import Button, Canvas, Entry, Frame, IntVar, Label, LabelFrame, Listbox, Menu, PhotoImage, Scale, StringVar, Tk, Toplevel, messagebox, ttk
from tkinter.colorchooser import askcolor
from tkinter.ttk import Progressbar, Radiobutton, Style

# Librairies à installer
import easygui
import matplotlib.pyplot as plt
import numpy as np
from googletrans import Translator
from PIL import Image, ImageTk
from pydub import AudioSegment
from scipy.io import wavfile

#
# ---------- Fonctions ---------------------------------------------------------------------------
#


def makeHover(fen, btn, txt, n, return_msg=False):
    """ Créer un hover pour le widget donné
    itype : Tk() / Tk.TopLevel(), Tk.Button(), {code de la lange: [messages]}, int (le numéro associé au message)
    """
    if n == None:
        msg = txt
    else:
        # Permet de changer le texte contenu dans le bouton
        msg = Message(msg=StringVar(), text=txt, actualLanguage=fen.langue)
        # Affiche le texte par défaut
        msg.update()
        # Ajoute à la liste des objets qui peuvent changer de texte
        fen.alltxtObject['Stringvar'].append([msg, 'hovers', n])
    # Création d'un objet HoverInfo
    HoverInfo(btn, text=msg)
    # Si le message doit être renvoyé
    if return_msg:
        # Retourne le message
        return msg


def makeHoverMenu(fen, btn, txt, n):
    """ Créer un hover pour le widget donné
    itype : Tk() / Tk.TopLevel(), Tk.Button(), {code de la lange: [messages]}, int (le numéro associé au message)
    """
    # Permet de changer le texte contenu dans le bouton
    msg = Message(msg=StringVar(), text=txt, actualLanguage=fen.langue)
    # Affiche le texte par défaut
    msg.update()
    # Ajoute à la liste des objets qui peuvent changer de texte
    fen.alltxtObject['Stringvar'].append([msg, 'hovers', n])
    # Création d'un objet HoverInfo
    HoverMenu(btn, msg, fen)


def makeLBtn(fen, scr, txt, x, y, command, n, width=15, height=2, bg="#40444B", fg="#b6b9be"):
    """ Créer un bouton qui peut changer de langue
    itype : Tk() / Tk.TopLevel(), Interface() / PersoPopup() / ParamPopup(), {code de la lange: [messages]}, 2 int, func (la commande à exécuter au clic), 2 int, 2 str
    rtype: Tk.Button()
    """
    # Permet de changer le texte contenu dans le bouton
    msg = Message(msg=StringVar(), text=txt, actualLanguage=scr.langue)
    # Bouton "ouvrir un fichier" qui appelle openExplorateur au clic
    btn = Button(fen, textvariable=msg.msg, command=command, width=width, height=height)
    # Affiche le texte par défaut
    msg.update()
    # Ajoute à la liste des objets qui peuvent changer de texte
    scr.alltxtObject['Stringvar'].append([msg, 'btn', n])
    if x != None and y != None:
        # Placement du bouton dans la fenêtre
        btn.place(x=x, y=y)
    # Configure le bouton
    btn.configure(background=bg, foreground=fg, activebackground="#40444B", activeforeground="#b6b9be",  borderwidth=0, highlightthickness=0)
    return btn


def makeLLabel(fen, scr, txt, x, y, n):
    """ Créer un labelFrame qui peut changer de langue
    itype : Tk() / Tk.TopLevel(), Tk.Button(), {code de la lange: [messages]}, 2 int, int (le numéro associé au message)
    rtype : Tk.LabelFrame()
    """
    # Permet de changer le texte contenu dans le cadre
    msg = Message(text=txt, actualLanguage=scr.langue)
    # Cadre contenant la liste
    lblf = LabelFrame(fen, text=msg.getTxt(), padx=10, pady=10)
    # Placement du cadre dans la fenêtre
    lblf.place(x=x, y=y)
    # Configure l'affichage du cadre
    lblf.configure(background='#202225', foreground="#b6b9be")
    # Ajoute à la liste des objets qui peuvent changer de texte
    scr.alltxtObject['LabelFrame'].append([lblf, [msg, 'tags', n]])
    # Retourne le label
    return lblf


def makeScale(fen, param, low, high, res):
    """ Crér un Scale
    itype : Tk() / Tk.TopLevel(), IntVar(), 3 int
    rtype: Tk.Scale()
    """
    # Création du curseur
    scl = Scale(fen, from_=low, to=high, resolution=1, tickinterval=res, length=300, variable=param)
    # Configure le curseur
    scl.configure(background="#40444B", foreground="#b6b9be", borderwidth=0, highlightthickness=0, troughcolor="#b6b9be", takefocus=0)
    # Inclusion du curseur
    scl.pack()
    return scl


def makeRdbList(fen, src, liste):
    """ Création d'une liste de radioboutons
    itype : Tk() / Tk.TopLevel(), Interface() / PersoPopup() / ParamPopup(), {}
    """
    # Compteur des radioboutons
    x = 0
    # Pour chaque langue de la liste des drapeaux
    for f in liste:
        # Récupèration du drapeau
        flag = liste[f]
        # Création d'un radiobouton
        rdb = Radiobutton(fen, text="   " + src.allLanguages[f]['nom'][0] , image=flag, compound='left', width=30, variable=src.selectedLanguage, value=list(src.allLanguages.keys()).index(f) + 1)
        # Placement du radiobouton en fonction de sa place dans la liste
        rdb.place(x=(x % 8) * 165 + 12, y=(x // 8) * 45 + 100)
        # Incrémentation du compteur
        x += 1


#
# ---------- Classe Message -----------------------------------------------------------------------
#


class Message():

    def __init__(self, text, actualLanguage, addon="", msg=None):
        """ Permet de changer le texte d'un Label, LabelFrame ou Button même si ce dernier est controllé par un thread
        itype : {code de la lange: [messages]}, code de la langue, str, tkinter.StringVar()
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
        itype : str(code de la langue)
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


    def addLang(self, l, msg):
        """ Ajoute une langue au différente langues disponible
        itype : str (code de la langue), list (messages)
        """
        if l not in self.text.keys():
            self.text[l] = msg


#
# ---------- Classe HoverInfo ---------------------------------------------------------------------
#

class HoverInfo():

    def __init__(self, widget, text):
        """
        Message d'aide

        Code source:

        - https://stackoverflow.com/questions/3221956/what-is-the-simplest-way-to-make-tooltips-in-tkinter/36221216#36221216
        - http://www.daniweb.com/programming/software-development/code/484591/a-tooltip-class-for-tkinter

        itype : tkinter.Button(), Message()
        """
        # Le temps avant l'affichage
        self.waittime = 400
        # Le longueur de la fenêtre
        self.wraplength = 250
        # Le bouton sur lequel le texte va s'afficher
        self.widget = widget
        # Le texte à afficher
        self.text = text
        if isinstance(self.text, Message):
        # Met le texte par défaut
            self.text.update()
        # Quand la souris passe sur le bouton, active la fonction
        self.widget.bind("<Enter>", self.onEnter)
        # Quand la souris part du bouton, active la fonction
        self.widget.bind("<Leave>", self.onLeave)
        # Quand l'utilisatuer clique sur le bouton
        self.widget.bind("<ButtonPress>", self.onLeave)
        # Couleur de fond du message
        self.bg = '#36393f'
        # Couleur du message
        self.fg = '#b6b9be'
        # Espace entre les bords et le texte
        self.pad = (5, 3, 5, 3)
        # L'identifiant du message
        self.id = None
        # La fenêtre comprenant le message
        self.tw = None


    def onEnter(self, event=None):
        """ Quand la souris passe sur le bouton
        """
        self.schedule()


    def onLeave(self, event=None):
        """ Quand la souris part du bouton
        """
        self.unschedule()
        self.hide()


    def schedule(self):
        """ Réinitialise l'identifiant du message
        """
        self.unschedule()
        self.id = self.widget.after(self.waittime, self.show)


    def unschedule(self):
        """ Supprime l'identifiant du message
        """
        id_ = self.id
        self.id = None
        if id_:
            self.widget.after_cancel(id_)


    def show(self):
        """ Affiche le message
        """

        def tip_pos_calculator(widget, label, tip_delta=(10, 5), pad=(5, 3, 5, 3)):
            """ calcule l'emplacement du message à partir de celui de la souris
            """
            # Appropriation du bouton
            w = widget
            # récupération des dimmensions de l'écran
            s_width, s_height = w.winfo_screenwidth(), w.winfo_screenheight()
            # Calcul des dimensions de la fenêtre
            width, height = (pad[0] + label.winfo_reqwidth() + pad[2], pad[1] + label.winfo_reqheight() + pad[3])
            # Récupération des coordonnées de la souris
            mouse_x, mouse_y = w.winfo_pointerxy()
            # Décale l'emplacement de la fenêtre pour ne pas être géné par la souris (x1 et y1 sont les coordonnées du coin supérieur gauche de la fenêtre)
            x1, y1 = mouse_x + tip_delta[0], mouse_y + tip_delta[1]
            # Calcul des coordonnées du coin inférieur droit de la fenêtre
            x2, y2 = x1 + width, y1 + height

            # Calcul de la distance entre le bord droit de l'écran et celui de la fenêtre
            x_delta = x2 - s_width
            # Si la fenêtre sort de l'écran
            if x_delta < 0:
                # Colle le fenêtre au bord droit de l'écran
                x_delta = 0

            # Calcul de la distance entre le bord supérieur de l'écran et celui de la fenêtre
            y_delta = y2 - s_height
            # Si la fenêtre sort de l'écran
            if y_delta < 0:
                # Colle le fenêtre au bord droit de l'écran
                y_delta = 0

            # Si le coin supérieur droit de la fenêtre n'est pas dans celui de l'écran
            if (x_delta, y_delta) != (0, 0):
                if x_delta:
                    x1 = mouse_x - tip_delta[0] - width
                if y_delta:
                    y1 = mouse_y - tip_delta[1] - height
            if y1 < 0:
                y1 = 0

            return x1, y1

        # Couleur du fond
        bg = self.bg
        # Marge de la fenêtre
        pad = self.pad
        # Le bouton duquel le fenêtre doit appaître
        widget = self.widget
        # Création d'une pop-up
        self.tw = Toplevel(widget)
        # Enlève les boutons fermer, réduire et plein écran de la fenêtre
        self.tw.wm_overrideredirect(True)
        # Création de l'emplacement pour le texte
        win = Frame(self.tw, background=bg, borderwidth=0)
        if isinstance(self.text, Message):
            # Mise en place du texte à afficher
            label = ttk.Label(win, textvariable=self.text.msg, justify='left', background=bg, foreground=self.fg, relief='solid', borderwidth=0, wraplength=self.wraplength)
        else:
            # Mise en place du texte à afficher
            label = ttk.Label(win, text=self.text, justify='left', background=bg, foreground=self.fg, relief='solid', borderwidth=0, wraplength=self.wraplength)
        # Place le texte dans la zone dédiée
        label.grid(padx=(pad[0], pad[2]), pady=(pad[1], pad[3]), sticky='nsew')
        # Passe la fenêtre en mode grid pour pouvoir la placer sur l'écran
        win.grid()
        # Calcul des coordonnées de la fenêtre
        x, y = tip_pos_calculator(widget, label)
        # Dimensionne la fenêtre
        self.tw.wm_geometry(f"+{x}+{y}")


    def hide(self):
        # Appropriation de la fenêtre
        tw = self.tw
        # Si elle existe
        if tw:
            # Déstruction de la fenêtre
            tw.destroy()
        # La fenêtre n'esiste plus
        self.tw = None
        del self


#
# ---------- Classe HoverMenu ---------------------------------------------------------------------
#


class HoverMenu():

    def __init__(self, widget, text, fen):
        """
        Message d'aide

        Code source:

        - https://stackoverflow.com/questions/3221956/what-is-the-simplest-way-to-make-tooltips-in-tkinter/36221216#36221216
        - http://www.daniweb.com/programming/software-development/code/484591/a-tooltip-class-for-tkinter

        itype : tkinter.Button(), Message()
        """
        # Le temps avant l'affichage
        self.waittime = 400
        # Le longueur de la fenêtre
        self.wraplength = 250
        # Le bouton sur lequel le texte va s'afficher
        self.widget = widget
        # Le texte à afficher
        self.text = text
        # Met le texte par défaut
        self.text.update()
        # Quand la souris passe sur le bouton, active la fonction
        self.widget.bind("<Enter>", self.onEnter)
        # Quand la souris part du bouton, active la fonction
        self.widget.bind("<Button-1>", self.onLeave)
        # Quand l'utilisatuer clique sur le bouton
        self.widget.bind("<ButtonPress>", self.onLeave)
        # Couleur de fond du message
        self.bg = '#36393f'
        # Couleur du message
        self.fg = '#b6b9be'
        # Espace entre les bords et le texte
        self.pad = (5, 3, 5, 3)
        # L'identifiant du message
        self.id = None
        # La fenêtre comprenant le message
        self.tw = None
        # La fenêtre principale
        self.fen = fen


    def onEnter(self, event=None):
        """ Quand la souris passe sur le bouton
        """
        if not self.fen.flagMenu:
            self.schedule()
            self.fen.flagMenu = self


    def onLeave(self, event=None):
        """ Quand la souris part du bouton
        """
        self.unschedule()
        self.hide()
        self.fen.flagMenu = None


    def schedule(self):
        """ Réinitialise l'identifiant du message
        """
        self.unschedule()
        self.id = self.widget.after(self.waittime, self.show)


    def unschedule(self):
        """ Supprime l'identifiant du message
        """
        id_ = self.id
        self.id = None
        if id_:
            self.widget.after_cancel(id_)


    def show(self):
        """ Affiche le message
        """

        def tip_pos_calculator(widget, label, tip_delta=(10, 5), pad=(5, 3, 5, 3), h=40, w=100):
            """ calcule l'emplacement du message à partir de celui de la souris
            """
            # récupération des dimmensions de l'écran
            s_width, s_height = widget.winfo_screenwidth(), widget.winfo_screenheight()
            # Calcul des dimensions de la fenêtre
            width, height = (pad[0] + w + pad[2], pad[1] + h + pad[3])
            # Récupération des coordonnées de la souris
            mouse_x, mouse_y = widget.winfo_pointerxy()
            # Décale l'emplacement de la fenêtre pour ne pas être géné par la souris (x1 et y1 sont les coordonnées du coin supérieur gauche de la fenêtre)
            x1, y1 = mouse_x + tip_delta[0], mouse_y + tip_delta[1]
            # Calcul des coordonnées du coin inférieur droit de la fenêtre
            x2, y2 = x1 + width, y1 + height

            # Calcul de la distance entre le bord droit de l'écran et celui de la fenêtre
            x_delta = x2 - s_width
            # Si la fenêtre sort de l'écran
            if x_delta < 0:
                # Colle le fenêtre au bord droit de l'écran
                x_delta = 0

            # Calcul de la distance entre le bord supérieur de l'écran et celui de la fenêtre
            y_delta = y2 - s_height
            # Si la fenêtre sort de l'écran
            if y_delta < 0:
                # Colle le fenêtre au bord droit de l'écran
                y_delta = 0

            # Si le coin supérieur droit de la fenêtre n'est pas dans celui de l'écran
            if (x_delta, y_delta) != (0, 0):
                if x_delta:
                    x1 = mouse_x - tip_delta[0] - width
                if y_delta:
                    y1 = mouse_y - tip_delta[1] - height
            if y1 < 0:
                y1 = 0

            return x1, y1

        # Couleur du fond
        bg = self.bg
        # Marge de la fenêtre
        pad = self.pad
        # Le bouton duquel le fenêtre doit appaître
        widget = self.widget
        # Création d'une pop-up
        self.tw = Toplevel(widget)
        # Enlève les boutons fermer, réduire et plein écran de la fenêtre
        self.tw.wm_overrideredirect(True)
        # Création de l'emplacement pour le texte
        win = Frame(self.tw, background=bg, borderwidth=0)
        # cadre autour des boutons
        label = LabelFrame(win)
        # Configuration du cadre
        label.configure(background="#40444B", foreground="#b6b9be", borderwidth=0, highlightthickness=0)
        # Liste des radioboutons
        self.rdblist = []
        h = 40 * len(self.fen.languages)
        # Pour chaque langue disponible
        for l in self.fen.languages:
            # RadioBouton affichant la langue et son drapeau
            btn = Button(label, text="   " + self.fen.allLanguages[l]['nom'][0] , image=self.fen.FlagDict[l], compound='left', width=100, height=40, command=self.switchfenLang) #variable=self.selectedLanguage, value=list(self.fen.languages.keys()).index(l) + 1
            # Inclusion du bouton
            btn.pack()
            # Configuration du bouton
            btn.configure(background="#40444B", foreground="#b6b9be", activebackground="#40444B", activeforeground="#b6b9be",  borderwidth=0, highlightthickness=0, justify='center')
            # Ajout à la liste
            self.rdblist.append(btn)
        # Place le texte dans la zone dédiée
        label.grid(padx=(pad[0], pad[2]), pady=(pad[1], pad[3]), sticky='nsew')
        # Passe la fenêtre en mode grid pour pouvoir la placer sur l'écran
        win.grid()
        # Calcul des coordonnées de la fenêtre
        x, y = tip_pos_calculator(widget, label, h=h)
        # Dimensionne la fenêtre
        self.tw.wm_geometry(f"+{x}+{y}")


    def switchfenLang(self):
        """ CHange la langue de l'applucation
        """
        # Par défaut, la langue de l'application
        l = self.fen.langue
        # La coordonnée y de la souris au clic
        my = self.fen.fen.winfo_pointery()
        # Pour chaque boutons
        for x, btn in enumerate(self.rdblist):
            # La coordonnée y des boutons
            wy = btn.winfo_rooty()
            # La hauteur du boutons
            h = btn.winfo_height()
            # Si la position de la souris est entre les deux bords du boutons
            if wy < my and wy + h > my:
                # La langue est celle du bouton
                l = list(self.fen.languages.keys())[x]
        # Change la langue de l'application
        self.fen.langue = l
        # Change la langue des widgets
        self.fen.switchL()
        # Ferme le menu
        self.onLeave()


    def hide(self):
        # Appropriation de la fenêtre
        tw = self.tw
        # Si elle existe
        if tw:
            # Déstruction de la fenêtre
            tw.destroy()
        # La fenêtre n'esiste plus
        self.tw = None
        del self


#
# ---------- Classe Equalizer ---------------------------------------------------------------------
#


class Equalizer(Thread):

    def __init__(self, nbRepetition, fen, gain):
        """ Transforme la musique pour le casque
        itype : int, Interface(), int
        """
        # Initialisation du Thread
        Thread.__init__(self)


        # Paramètres de la fenêtre principale

        # La fenêtre
        self.fen = fen
        # Le dossier d'enregistrement de la musique
        self.out = self.fen.saveLink
        # Message de la fenêtre
        self.msg = self.fen.msg
        # La liste des musiques
        self.files = self.fen.files
        # Récupère la première musique de la liste
        filename = self.files[0]
        # Barre de progression de la fenêtre
        self.progress = self.fen.progressbar
        # La liste des musiquesà afficher
        self.filesList = self.fen.filesList
        # Les langues de l'application
        self.languages = self.fen.languages


        # Paramètres internes

        # Fréquence en dessous de laquelle, les fréquences sont descendus de 6 dB
        self.upperFrequency = 450
        # Fréquence au  dessus de laquelle, les fréquences sont descendus de 6 dB
        self.lowerFrequency = 9000
        # La suppression du fichier .wav de transition
        self.delWav = False
        # Le gain à appliquer à la musique
        self.gain = gain
        # Nombre de fois à appliquer le filtre
        self.nbRepetition = nbRepetition


        # Message et fichier de sortie

        # Nom du fichier à transformer (déjà en wav)
        self.filename = self.get_song(filename)
        # Nom de fichier en sortie
        ext = ".".join(filename.split("/")[-1].split('.')[:-1])
        self.outname = f'{self.out}/out - {ext}.wav'
        # Change le message de la fenêtre
        self.msg.changeMsg(4)
        self.msg.update()


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
            ext = ".".join(path.split("/")[-1].split('.')[:-1])
            # Si un fichier wav avec le même nom existe
            if f'{ext}.wav' in os.listdir(self.out):
                # Retourne le fichier wav pour éciter la conversion
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
                    # Lance la commande sans créer de pop-up externe
                    p = subprocess.Popen(f'ffmpeg -y -i "{path}" -vn "{outname}"', stdin=None, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    p_out, p_err = p.communicate(input=None)
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
        max_value = 2 * self.nbRepetition + 5
        # Progression de la barre
        x = 1

        # Ouverture du fichier

        # Change le message de la fenêtre
        self.msg.changeMsg(2)
        self.msg.update()
        # Ouvre le fichier à transformer
        song = AudioSegment.from_wav(self.filename)
        # Change la barre de progression de la fenêtre
        self.progress['value'] = x / max_value * 100

        # Apllication filter

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

        # Application du gain

        # Change la barre de progression de la fenêtre
        x += 1
        self.progress['value'] = x / max_value * 100
        # Change le message de la fenêtre
        self.msg.changeMsg(1)
        self.msg.update()
        # Augmente le volume pour compenser les filtres
        song = song + self.gain

        # Application du compresseur

        # Change le message de la fenêtre
        self.msg.changeMsg(3)
        self.msg.update()
        # Change la barre de progression de la fenêtre
        x += 1
        self.progress['value'] = x / max_value * 100
        # Applique un compresseur dynaimque
        song = song.compress_dynamic_range(threshold=-.3, ratio=1000000, attack=0.003, release=.1)

        # Exportation du fichier

        # Progression de la barre
        x += 1
        self.progress['value'] = x / max_value * 100
        # Exporte le fichier
        song.export(self.outname, format="wav")
        # Change la barre de progression de la fenêtre
        self.progress['value'] = 0

        # Suppression du fichier de l'espace de travail

        # La supprime de l'affichage
        self.filesList.delete(0)
        # Enlève de la liste la musique
        self.files.pop(0)
        # Supprime la musique wav de transition
        if self.delWav:
            # Récupère et supprime le fichier
            os.remove("".join(self.outname.split("out - ")))
        # Nom de fichier en sortie
        ext = ".".join(self.outname.split("/out - ")[-1].split('.')[:-1])
        correct = f'{self.out}/out - {ext}.mp3'
        # Change le message de la fenêtre
        self.msg.changeMsg(4)
        self.msg.update()
        # Progression de la barre
        x += 1
        self.progress['value'] = x / max_value * 100
        # Convertit le fchier en .wav
        p = subprocess.Popen(f'ffmpeg -y -i "{self.outname}" -vn "{correct}"', stdin=None, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        p_out, p_err = p.communicate(input=None)
        # Supprimer
        os.remove(self.outname)
        # La langue de la fenêtre principale
        self.langue = self.fen.langue
        # Change le message de la fenêtre
        self.msg.changeMsg(0)
        self.msg.update()
        self.progress['value'] = 0
        # Affiche un message de fin de conversion
        messagebox.showinfo(self.languages[self.langue]['infoTitle'][0], self.languages[self.langue]['infoMsg'][0])
        # Ouvre le fichier
        os.startfile(correct)
        # Supprime l'objet
        del self


#
# ---------- Classe LanguageManager ---------------------------------------------------------------
#


class LanguageManager(Thread):

    def __init__(self, fen, langue):
        """ Permet de charger un paquet linguistique dans l'application
        itype : Interface() / PersoPopup() / ParamPopup(), str(code de la langue)
        """
        # Initialisation du Thread
        Thread.__init__(self)


        # Paramètre de la fenêtre principale

        # La fenêtre
        self.fen = fen
        # Les textes qui changent de langue
        self.alltxtObject = self.fen.alltxtObject
        # Les langues disponibles
        self.languages = self.fen.languages
        # La langue de la fenêtre
        self.l = self.fen.langue
        # La couleur de la fenêtre principale
        self.color = self.fen.color
        # Les donnée de la fenêtre
        self.data = self.fen.allLanguages

        # Indicateur sur la fenêtre principale

        # Image du téléchargement de la langue
        self.InfoImage = Label(self.fen.fen, image=self.fen.infoImage, width=25, height=25, borderwidth=0, highlightthickness=0, background=self.color)
        # Ajoute l'image à la fenêtre
        self.InfoImage.place(x=1330, y=10)

        # Message sur le point d'interrogation
        self.Infomsg = makeHover(self.fen, self.InfoImage, {l: [self.languages[l]['hovers'][9]] for l in self.languages}, 9, True)


        # Paramètres internres

        # Les langues demandée
        self.langue = [langue]
        # La première des langues demandées
        self.actualLangue = self.langue[0]
        # Le traducteur
        self.translator = Translator()


        # Création de la fenêtre

        # Fenêtre au dessus de la principale
        self.top = Toplevel(self.fen.fen)
        # Couleur de fond de la fenêtre
        self.top.configure(background='#202225')
        # Taille de fond de la fenêtre
        self.top.minsize(400, 180)
        # Les messages
        self.tradMsg = Message(text={l: [self.languages[l]['popup'][4]] for l in self.languages}, actualLanguage=self.l)
        # Le titre de la fenêtre
        self.top.title(self.tradMsg.getTxt())

        # Permet de changer le texte contenu dans le label
        self.msg = Message(msg=StringVar(), text={l: [self.languages[l]['tradMsg'][0]] for l in self.languages}, actualLanguage=self.l)
        # Affiche le texte par défaut
        self.msg.update()
        # Ajoute à la liste des objets qui peuvent changer de texte
        self.alltxtObject['Stringvar'].append([self.msg, 'tradMsg', 0])
        # Explique l'opération en cours
        operatingLabel = Label(self.top, textvariable=self.msg.msg,  justify='center', width=55)
        # Inclusion du label dans le cadre
        operatingLabel.place(x=0, y=30)
        # Configure l'affichage du label
        operatingLabel.configure(background='#202225', foreground="#b6b9be")

        # Le cadre autour de la barre
        self.TradPgb = makeLLabel(self.top, self.fen, {l: [self.languages[l]['tags'][5]] for l in self.languages}, 25, 70, 5)
        # Style de la barre de progression
        s = Style()
        # Charge un style par défaut
        s.theme_use('alt')
        # Configure le style
        s.configure("red.Horizontal.TProgressbar", troughcolor='#40444B', background=self.color)
        # Barre de progression qui suit l'évolution des différentes opérations de l'application
        self.progressbar = Progressbar(self.TradPgb, orient="horizontal", length=325, mode="determinate", style="red.Horizontal.TProgressbar")
        # Inclusion de la barre de progression dans le cadre
        self.progressbar.pack()
        # Change la langue : Bouton Shift
        self.top.bind('<Shift_L>', self.fen.switchLwithoutL)
        # Focus la fenêtre
        self.top.focus_set()


    def translate(self):
        """ Traduit tout les textes de l'application dans la langue demandée
        """
        while len(self.langue) > 0:
            # Récupère la première langue de la liste
            self.actualLangue = self.langue.pop(0)
            # Change le message du hover
            self.Infomsg.addPrecision(len(self.langue))
            # Met à jour le message du hover
            self.Infomsg.update()
            # Récupèration du texte en anglais
            sec = self.data['en']
            # Ouvre le set de la algnue étrangère
            to = self.data[self.actualLangue]
            # Récupèration des traductions qui doivent comporter un espace
            spF = sec["Spacing"]
            # Compteur pour la barre de progression
            x = 0
            # La valeur maximale de la barre est 100 (100%)
            maxm = sum([len(sec[x]) for x in sec.keys()])
            # Si la barre existe (si la fenêtre existe)
            try:
                # Le maximun de la barre
                self.progressbar["maximum"] = maxm
                # Sa valeur
                self.progressbar['value'] = x
            except:
                pass
            # Pour chaque groupe de texte en anglais
            for k in sec.keys():
                # Si le groupe n'est pas celui du nom ou de l'espacement
                if k != "nom" and k != "Spacing":
                    # Créer le même groupe dans la langue demandée
                    to[k] = []
                    # Pour chaque élément du groupe en anglais
                    for el in sec[k]:
                        # Traduit l'élément dans la langue demandée
                        tx = self.translator.translate(el, src='en', dest=self.actualLangue).text.capitalize()
                        # Si il faut ajouter les espaces
                        if k in spF:
                            # Ajoute le texte
                            to[k].append(f' {tx} ')
                        # Si le text n'a pas besoin d'espace
                        else:
                            # Ajoute le texte
                            to[k].append(tx)
                        # fait progresser la barre """
                        x += 1
                        # Si la fenêtre est fermée
                        try:
                            self.progressbar['value'] = x
                        except:
                            pass


    def save(self):
        """ Sauvegarde le dictionnaire dans un fichier json
        """
        json.dump(self.data, open(self.fen.LanguageFile, "w"), sort_keys=True, indent=4)


    def run(self):
        """ La fonction appelée quand start() est appelé
        """
        # Traduit dans la langue demandée
        self.translate()
        # Sauvagarde la nouvelle langue dans la fichier de langue
        self.save()
        # Change la langue de la fenêtre principale
        self.fen.langue = self.actualLangue
        # Ajoute la traduction dans la liste des langues disponibles de la fenêtre
        self.fen.languages[self.actualLangue] = self.data[self.actualLangue]
        # Change la langue des widgets de la fenêtre principale
        self.fen.switchL()
        # Affiche un message de fin de traduction
        messagebox.showinfo(self.languages[self.actualLangue]['infoTitle'][1], self.languages[self.actualLangue]['infoMsg'][1])
        # Détruit l'indicateur
        self.InfoImage.destroy()
        # Détruit la fenêtre
        self.top.destroy()
        # Inidque à la fenêtre principale la fin de la traduction
        self.fen.lm = None
        # Se supprime
        del self


#
# ---------- Classe SearchBar ---------------------------------------------------------------------
#


class SearchBar(Thread):

    def __init__(self, fen, src):
        """ Transforme la musique pour le casque
        itype : Tk.TopLevel(), ParamPopup()
        """
        # Initialisation du Thread
        Thread.__init__(self)


        # Paramètres de le fenêtre principale

        # La fenêtre
        self.fen = fen
        # L'héritage des variabls
        self.src = src
        # Le dictionnaire de langue disponible
        self.allLanguages = self.src.allLanguages
        # Le dictionnaire de drapeau
        self.FlagDict = self.src.FlagDict
        # L'entry de la fenêtre
        self.entry = self.src.entry


        # Paramètres de la classe

        # Ferme le thread quand l'application est ferméee
        self.daemon = True
        # Boucle infinie
        self.on = True
        # Le deernier texte entré par l'utilisateur
        self.lastentry = ""


    def closest_result(self, l):
        """ Retourne les langues les plus proche de l'entrée de l'utilisateur
        itype : str
        rtype : {code de la langue: image(drapeaux)}
        """
        # Dictionnaire qui garde les langues à retourner
        final = {}
        # Pour chaque langue possible
        for key in self.allLanguages:
            # Récupèration du nom anglais de langue
            name = self.allLanguages[key]['nom'][1].lower()
            # Compteur de coïncidence entre le nom et l'entrée
            ct = 0
            # Pour chaque lettre entrées
            for x in l:
                # Si la lettre n'est pas dans le nom de la langue
                if x not in name:
                    # Passe à la langue suivante
                    break
                # Sinon
                else:
                    # Incrémente le compteur
                    ct += 1
                # Si toute les lettres entrées correspondent au nom de la langue
                if ct == len(l):
                    # Ajout de la langue dans celle à retourner, avec son drapeux associé
                    final[key] = self.FlagDict[key]
        # Retourne le dictionnaire
        return final


    def run(self):
        """ Fonction appelée quand start() est appelé
        """
        # Boucle infinie tant que self.on est vrai
        while self.on:
            # Évite de crash quand il y a une erreur
            try:
                # Récupère le message entré
                l = self.entry.get()
                # Si il est différent du dernier message enregistré
                if l != self.lastentry:
                    # Si le message n'est pas vide
                    if l != "":
                        # Récupère la liste des langues à montrer
                        liste = self.closest_result(l)
                    # Si le message est vide
                    else:
                        # La liste est alotrs celle de toute les langues
                        liste = self.FlagDict
                    # Récupère tout les widgets de la fenêtre
                    allWidget = self.fen.winfo_children()
                    # Pour chaque widget
                    for w in allWidget:
                        # Si il s'agit d'un radiobouton
                        if isinstance(w, ttk.Radiobutton):
                            # Le supprime de la fenêtre
                            w.destroy()
                    # Recréer la liste de radionouton
                    makeRdbList(self.fen, self.src, liste)
                    # Sauvegarde le message comme dernier message enregistré
                    self.lastentry = l
                # Attent pour éviter de planter
                time.sleep(.1)
            # Si il y a une erreur
            except:
                # Sort de la boucle infinie
                self.on = False


#
# ---------- Classe PersoPopup --------------------------------------------------------------------
#


class PersoPopup():

    def __init__(self, fen):
        """ Pop-up pour demander le nombre de filtre à appliquer
        itype : Interface()
        """

        # Récupération des varriables de la fenêtre principale

        # La fenêtre derrière
        self.fen = fen
        # Message de la fenêtre
        self.msg = self.fen.popupMsg
        # La langue de la fenêtre
        self.langue = self.fen.langue
        # Titre de la fenêtre d'erreur
        self.error = self.fen.error
        # Titre de la fenêtre d'erreur
        self.errorMsg = self.fen.allErrorMsg
        # Liste pour changer la langue du texte
        self.alltxtObject = self.fen.alltxtObject
        # Les langues de la fenêtre principale
        self.languages = self.fen.languages
        # la valeur du nombre de filtre à appliquer
        self.value = None


        # Initialisation de la fenêtre

        # Fenêtre au dessus de la principale
        self.top = Toplevel(self.fen.fen)
        # Couleur de fond de la fenêtre
        self.top.configure(background='#202225')
        # Taille de fond de la fenêtre
        self.top.minsize(300, 200)
        # Change le titre de la pop-up
        self.top.title(self.msg.getTxt())

        # Création d'un bouton
        self.btn = makeLBtn(self.top, self.fen, {l: [self.languages[l]['btn'][6]] for l in self.languages}, 90, 120, self.cleanup, 6)

        # Le message qui change en fonction de la langue
        msg = Message(msg=StringVar(), text={l: [self.languages[l]['tags'][3]] for l in self.languages}, actualLanguage=self.langue)
        # Ajoute à la liste des objets qui peuvent changer de texte
        self.fen.alltxtObject['Stringvar'].append([msg, 'hovers', 3])
        # Affiche le message de base
        msg.update()
        # Création d'un label au dessus de l'entry
        lbl = Label(self.top, textvariable=msg.msg, width=42, justify='center')
        # Placement du label
        lbl.place(x=0, y=30)
        # Configuration du label
        lbl.configure(background="#202225", foreground="#b6b9be", borderwidth=0, highlightthickness=0)


        # Cadre autour de l'entry
        lbf = LabelFrame(self.top, padx=10, pady=10)
        # Place le Labelframe dans la fenêtre
        lbf.place(x=40, y=60)
        # Configure le Labelframe
        lbf.configure(background='#202225', foreground="#b6b9be")
        # Entry pour le nombre à entrer
        self.entry = Entry(lbf, width=35)
        self.entry.pack()
        # Configuration de l'Entry
        self.entry.configure(background="#484B52", foreground="#b6b9be", borderwidth=0, highlightthickness=0)
        # Focus l'entry
        self.entry.focus_set()

        # Message quand la souris passe au dessus du bouton
        makeHover(self.fen, self.btn, {l: [self.languages[l]['hovers'][8]] for l in self.languages}, 8)


        # Binding et focus

        # Retourne le filtre : Bouton Entrée
        self.top.bind('<Return>', self.cleanup)
        # Change la langue : Bouton Tab
        self.top.bind('<Shift_L>', self.fen.switchLwithoutL)


    def cleanup(self, event=None):
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
            del self
        # Sinon
        else:
            # Pop-up d'erreur
            messagebox.showerror(self.error[self.langue][0], self.errorMsg[self.langue][2])
            # Place la fenêtre devant la fenêtre principale
            self.top.lift()
            self.top.attributes('-topmost', True)
            self.top.attributes('-topmost', False)
            # Focus la fenêtre
            self.top.focus_set()


#
# ---------- Classe PersoMenu ---------------------------------------------------------------------
#


class MenuPopup():

    def __init__(self, fen):
        """ Pop-up pour demander le nombre de filtre à appliquer
        itype : Interface()
        """

        # Récupération des varriables de la fenêtre principale

        # La fenêtre derrière
        self.fen = fen
        # Message de la fenêtre
        self.msg = self.fen.menuMsg
        # La langue de la fenêtre
        self.langue = self.fen.langue
        # Titre de la fenêtre d'erreur
        self.error = self.fen.error
        # Titre de la fenêtre d'erreur
        self.errorMsg = self.fen.allErrorMsg
        # Liste pour changer la langue du texte
        self.alltxtObject = self.fen.alltxtObject
        # Les langues de la fenêtre principale
        self.languages = self.fen.languages
        # la valeur du nombre de filtre à appliquer
        self.value = None

        # Initialisation de la fenêtre

        # Fenêtre au dessus de la principale
        self.top = Toplevel(self.fen.fen)
        # Couleur de fond de la fenêtre
        self.top.configure(background='#202225')
        # Taille de fond de la fenêtre
        self.top.minsize(800, 600)
        # Change le titre de la pop-up
        self.top.title(self.msg.getTxt())

        # Bouton du menu d'analyse
        self.analytics = makeLBtn(self.top, self.fen, {l: [self.languages[l]['btn'][8]] for l in self.languages}, 350, 25, self.fen.analyse, 5,  width=16)
        # Message au survol de la souris
        makeHover(self.fen, self.analytics, {l: [self.languages[l]['hovers'][11]] for l in self.languages}, 11)

        # Label contenant de "A propos"
        self.about = makeLLabel(self.top, self.fen, {l: [self.languages[l]['tags'][7]] for l in self.languages}, 50, 100, 7)
        # Le mesaage du "A propos"
        msg = Message(msg=StringVar(), text={l: [self.languages[l]['about'][0]] for l in self.languages}, actualLanguage=self.fen.langue)
        # Affiche le texte par défaut
        msg.update()
        # Ajoute à la liste des objets qui peuvent changer de texte
        self.fen.alltxtObject['Stringvar'].append([msg, 'hovers', 0])
        # Explique l'opération en cours
        operatingLabel = Label(self.about, textvariable=msg.msg, width=93, height=27)
        # Inclusion du label dans le cadre
        operatingLabel.pack()
        # Configure l'affichage du label
        operatingLabel.configure(background='#202225', foreground="#b6b9be")

        # Associe le bouton "a" à l'ouverture de menu d'analyse
        self.top.bind('<a>', self.fen.analyse)

        # Focus la fenêtre
        self.top.focus_set()


    def cleanup(self, event=None):
        """ Au clic sur le bouton Ok
        """
        self.top.destroy()


#
# ---------- Classe ParamPopup --------------------------------------------------------------------
#


class ParamPopup():

    def __init__(self, fen):
        """ Pop-up de paramètre
        itype : Interface()
        """
        # Accède aux propriétés de la fenêtre

        # La fenêtre
        self.fen = fen
        # Les objets qui change de couleur
        self.allColorObjet = self.fen.allColorObjet
        # Les objets qui change de texte
        self.alltxtObject = self.fen.alltxtObject
        # La langue de la fenêtre
        self.langue = self.fen.langue
        # Le nom de la pop-up
        self.msg = self.fen.persoMsg
        # Les drapeaux de la pop-up
        self.FlagDict = self.fen.FlagDict
        # Les langues de la fenêtre principale
        self.languages = self.fen.languages
        # Toutes les langues de la fenêtre principale
        self.allLanguages = self.fen.allLanguages
        # La couleur de l'application
        self.color = self.fen.color
        # le style de la fenêtre principale
        self.style = self.fen.style


        # Paramètres internes

        # Variable qui stocke la langue séléctionnée
        self.selectedLanguage = IntVar()
        # Met par défaut la valuer de la langue actuelle
        self.selectedLanguage.set(list(self.allLanguages.keys()).index(self.langue) + 1)


        # Création de la fenêtre

        # Fenêtre au dessus de la principale
        self.top = Toplevel(self.fen.fen)
        # Couleur de fond de la fenêtre
        self.top.configure(background='#202225')
        # La taille minimale de la fenêtre
        self.top.minsize(1335, 600)
        # Change le titre de la pop-up
        self.top.title(self.msg.getTxt())

        # Bouton de changement de couleur
        colorbtn = makeLBtn(self.top, self.fen, {l: [self.languages[l]['btn'][5]] for l in self.languages}, 200, 25, self.fen.getColor, 5,  width=16)

        # Bouton de validation de changment de langue
        lbtn = makeLBtn(self.top, self.fen, {l: [self.languages[l]['btn'][7]] for l in self.languages}, 1000, 25, self.changeLanguage, 7, width=17)

        # Cadre contenant l'entry
        self.lblFrame = makeLLabel(self.top, self.fen, {l: [self.languages[l]['tags'][6]] for l in self.languages}, 500, 20, 3)

        # Entry pour le nombre à entrer
        self.entry = Entry(self.lblFrame, width=40)
        # Inclusion de l'Entry dans le cadre
        self.entry.pack()
        # Configuration de l'Entry
        self.entry.configure(background="#484B52", foreground="#b6b9be", disabledbackground="black", borderwidth=0, highlightthickness=0)


        # Liste des différentes langues possibles
        makeRdbList(self.top, self, self.FlagDict)

        # Affiche un message quand la souris passe sur le bouton
        makeHover(self.fen, colorbtn, {l: [self.languages[l]['hovers'][7]] for l in self.languages}, 7)
        # Affiche un message quand la souris passe sur le bouton
        makeHover(self.fen, lbtn, {l: [self.languages[l]['hovers'][5]] for l in self.languages}, 5)


        # Binding et focus

        # Sauvegarde les changements
        self.top.bind('<Return>', self.cleanup)
        # Changer la couleur : Bouton c
        self.top.bind('<Control-c>', self.fen.getColor)
        # Change la langue : Bouton Tab
        self.top.bind('<Shift_L>', self.fen.switchLwithoutL)
        # Focus la fenêtre
        self.entry.focus_set()
        # la barre de recherche interactive
        self.Sb = SearchBar(self.top, self)
        # Lance le thread
        self.Sb.start()


    def cleanup(self, event=None):
        """ Au clic sur le bouton Ok
        """
        # Arrète la boucle du thread
        self.Sb.on = False
        # Arrète le thread
        self.Sb.join()
        # Change la langue de l'application
        self.changeLanguage()


    def changeLanguage(self):
        """ Récupère la langue séléctionnée, télécharge sa traduction si elle n'existe pas, et change la langue de l'application
        """
        # Récupère la langue séléctionnée
        langue = list(self.allLanguages.keys())[self.selectedLanguage.get() - 1]
        # Si la langue est différente de celle de la fenêtre
        if langue != self.langue:
            # Si la traduction est disponible
            if langue in self.languages:
                # Change la langue de la fenêtre
                self.fen.langue = langue
                # Chnage la langue des widgets
                self.fen.switchL()
            # Si la langue n'est pas disponible
            else:
                # Si la fenêtre n'existe pas
                if not self.fen.lm:
                    # Créer un objet qui télécharge la traduction
                    self.fen.lm = LanguageManager(self.fen, langue)
                    # Lance la fenêtree
                    self.fen.lm.start()
                # Si la fenêtre extiste
                else:
                    # Ajoute la langue demandée
                    self.fen.lm.langue.append(langue)
        # Ferme la fenêtre
        self.top.destroy()
        # Déclare la fermeture de la fenêtre
        self.fen.popupParamFen = False
        # Se supprime
        del self


#
# ---------- Classe Interface ---------------------------------------------------------------------
#


class Interface:

    def __init__(self):

        # Initialisation de la fenêtre

        # Déclaration d'un objet Tkinter
        self.fen = Tk()
        # Largeur de la fenêtre
        self.width = 1366
        # Hauteur de la fenêtre
        self.height = 768
        # La taille minimale de la fenêtre
        self.fen.minsize(self.width, self.height)
        # Dimmensionne la fenêtre
        #self.fen.state('zoomed')
        # Change le titre de la fenêtre
        self.fen.title("BoneSound Equalizer")
        # Change l'icone de la fenêtre
        self.fen.iconbitmap(default='./image/icon.ico')
        # Change la couleur de l'arrière plan
        self.fen.configure(background='#202225')
        # Le style de l'application
        self.style = Style(self.fen)
        # Initailisation par défaut
        self.style.theme_use('alt')


        # Initialisation des variables

        # Fichiers actuellement ouvert dans l'application
        self.files = []
        self.FilterList = [2, 2, 2, 1, 2, 2, 1, 1, 1, 1, 1, 1, 1]
         # Type de musique séléctionné (IntVar permet de modifier la valeru des Radioboutons en le modifiant)
        self.musicType = IntVar()
        # Coche par défaut le premier élément de la liste
        self.musicType.set(1)
        # le gain de volume
        self.volumeGain = IntVar()
        # 10 Par défaut
        self.volumeGain.set(5)
        # Le nom du fihier avec les paramètres
        self.ParamFile = "settings.json"
        # Le nom du fichier avec les traductions de l'application
        self.LanguageFile = "language.json"
        # Le lien de sauvegarde et la langue de l'application
        self.saveLink, self.langue, self.color, self.MusicLink = self.getParam()
        # La base de données de langue
        self.languages, self.allLanguages = self.getAvailableLanguage()
        # Si la langue n'est pas dans les traductions
        if self.langue not in self.languages.keys():
            # Passe l'apllication en anglais
            self.langue = 'en'
        # Liste de tout les objets contenant du texte
        self.alltxtObject = {'Stringvar': [], "LabelFrame": []}
        # Liste de tout les objets pouvant changer de couleur
        self.allColorObjet = []
        # Image des paramètres
        self.ParamImg = ImageTk.PhotoImage(Image.open('./image/Param.png').resize((35, 35)))
        # Le menu
        self.MenuImg = ImageTk.PhotoImage(Image.open('./image/menu.png').resize((36, 36)))
        # Change l'icone au changement de langue
        self.FlagDict = self.loadIcons()
        # Si l'utilisateur rentre une valeur du nombre de filtre à appliquer
        self.applyingPerso = False
        # Le nombre de filtre à appliquer
        self.nbFilter = 1
        # Le nom des erreurs en fonctions des languages disponibles
        self.error = {l: self.languages[l]['error'] for l in self.languages}
        # Tout les messages d'erreurs
        self.allErrorMsg = {l: self.languages[l]['allErrorMsg'] for l in self.languages}
        # Ouvre l'image
        self.image = ImageTk.PhotoImage(Image.open('./image/Image.png').resize((140, 140)))
        # L'image d'info
        self.infoImage = ImageTk.PhotoImage(Image.open('./image/info.png').resize((25, 25)))
        # L'élément séléctionné dans la liste des musiques à transformer
        self.delElement = StringVar()
        # Si la fenêtre "personnaliser" est ouverte
        self.popupFen = False
        # Si la fenêtre "paramètres" est ouverte
        self.popupParamFen = False
        # Si la fenêtre "menu" est ouverte
        self.popupMenuFen = False
        # Le seuil maximal de compression du volume
        self.threshold = -20
        # Le ratio de compression (par analogie avec un compresseur physique)
        self.ratio = 4
        # Le delai d'attente entre une valeur supérieur au seuil et la réduction
        self.attack = 5
        # Le delai d'attente après une valuer inférieur au seuil et l'arrêt de la rédcution
        self.release = 50
        # La liste des formats de musiques suppotées
        self.AllMusicExtPossibles = [".wav", ".mp3"]
        # La pop-up de traduction de l'application
        self.lm = None
        # Le menu des drapeaux
        self.flagMenu = None


        # Le style

        # Le nom du bouton
        style_name = Radiobutton().winfo_class()
        # Configure la style du bouton
        self.style.configure(style_name, foreground="#b6b9be", background='#202225', indicatorcolor="#202225", borderwidth=0, selectcolor="#FAA61A")
        # Précise les couleurs en fonction des états du bouton
        self.style.map(style_name,  foreground=[('disabled', "#b6b9be"), ('pressed', self.color), ('active', self.color)], background=[('disabled', '#202225'), ('pressed', '!focus', '#202225'), ('active', '#202225')], indicatorcolor=[('selected', self.color), ('pressed', self.color)])
        # Configure le style
        self.style.configure("red.Horizontal.TProgressbar", troughcolor='#40444B', background=self.color)


        # Création des widgets de la fenêtre

        self.labelImageRatio = [.329, .039]
        # Image qui change de couleur
        self.LabelImage = Button(self.fen, image=self.image, width=140, height=140, background=self.color, command=self.open_site)
        # Ajoute l'image à la fenêtre
        self.LabelImage.place(x=450, y=30)
        # Configure le bouton
        self.LabelImage.configure(background=self.color, activebackground=self.color,  borderwidth=0, highlightthickness=0)
        # Affcihe le lien de la page au survol
        makeHover(self.fen, self.LabelImage, "https://bonesound.wordpress.com/", None)


        self.MusicFilesRatio = [.512, .033]
        # Initialisation de la liste des musique à convertir
        self.MusicFiles = makeLLabel(self.fen, self, {l: [self.languages[l]['tags'][0]] for l in self.languages}, 700, 25, 0)

        self.filesListratio = [.073, .046]
        # Liste contenant les musiques
        self.filesList = Listbox(self.MusicFiles, width=100, height=35)
        # Configure l'affichage de la listbox
        self.filesList.configure(background="#484B52", foreground="#b6b9be", borderwidth=0, highlightthickness=0)
        # Inclusion de la liste dans le cadre
        self.filesList.pack()

        # Initialisation de la liste des types de musiques

        self.MusictagsRatio = [.088, .234]
        self.MusicTags = makeLLabel(self.fen, self, {l: [self.languages[l]['tags'][1]] for l in self.languages}, 120, 180, 1)

        # Crée un RadioBouton ayant accès à self.MusicType pour chaque type de musique
        for x in range(len(self.FilterList)):
            # Permet de changer le texte contenu du texte
            m = Message(text={l: [self.languages[l]["musicName"][x]] for l in self.languages}, actualLanguage=self.langue)
            # text est le message écrit à côté du bouton, value est la valeur que le bouton donne à self.MusicType quand il est séléctionné (x + 1 car 0 n'est pas admis)
            rdb = Radiobutton(self.MusicTags, text=m.getTxt(), value=x + 1, variable=self.musicType, width=35)
            # Ajout du Radiobouton à la liste de changement de couleur
            self.allColorObjet.append(rdb)
            # Ajoute à la liste des objets qui peuvent changer de texte
            self.alltxtObject['LabelFrame'].append([rdb, [m, "musicName", x]])
            # Inclusion du bouton
            rdb.pack()

        # Espace entre la liste et le bouton
        lbl = Label(self.MusicTags, height=1)
        lbl.pack()
        lbl.configure(background="#202225")

        # Le bouton "personnaliser"
        persoBtn = makeLBtn(self.MusicTags, self, {l: [self.languages[l]['btn'][2]] for l in self.languages}, None, None, self.popup, 2)
        # Placement du cadre dans la fenêtre
        persoBtn.pack(anchor='w')


        # Initialisation de la barre de progression

        self.PgbRatio = [.055, .846]
        # Le cadre autour de la barre
        self.Pgb = makeLLabel(self.fen, self, {l: [self.languages[l]['tags'][2]] for l in self.languages}, 75, 650, 2)
        # Permet de changer le texte contenu dans le label
        self.msg = Message(msg=StringVar(), text={l: self.languages[l]['allMsgPossible'] for l in self.languages}, actualLanguage=self.langue)
        # Affiche le texte par défaut
        self.msg.update()
        # Ajoute à la liste des objets qui peuvent changer de texte
        self.alltxtObject['Stringvar'].append([self.msg, 'tags', 2])
        # Explique l'opération en cours
        operatingLabel = Label(self.Pgb, textvariable=self.msg.msg)
        # Inclusion du label dans le cadre
        operatingLabel.pack()
        # Configure l'affichage du label
        operatingLabel.configure(background='#202225', foreground="#b6b9be")
        self.progressbarRatio = .842
        # Barre de progression qui suit l'évolution des différentes opérations de l'application
        self.progressbar = Progressbar(self.Pgb, orient="horizontal", length=1150, mode="determinate", style="red.Horizontal.TProgressbar")
        # La valeur maximale de la barre est 100 (100%)
        self.progressbar["maximum"] = 100
        # Inclusion de la barre de progression dans le cadre
        self.progressbar.pack()


        # Initialisation des boutons

        # Bouton pour changer la langue
        flag = self.FlagDict[self.langue]
        self.lblFlagRatio = [.952, .912]
        # Création du bouton
        self.lblFlag = Button(self.fen, image=flag, width=35, height=35, background='#202225', command=self.switchLwithoutL)
        # Place le bouton
        self.lblFlag.place(x=1300, y=700)
        # Configure le bouton
        self.lblFlag.configure(background="#202225", foreground="#b6b9be", activebackground="#202225", activeforeground="#b6b9be", borderwidth=0, highlightthickness=0)


        self.menubtnRatio = [.007, .013]
        # Bouton "menu"
        self.menubtn = Button(self.fen, image=self.MenuImg, command=self.popupMenu, width=36, height=36)
        # Placement du bouton
        self.menubtn.place(x=10, y=10)
        # Configure le bouton
        self.menubtn.configure(background="#202225", activebackground="#202225", borderwidth=0, highlightthickness=0)


        self.parambtnRatio = [.007, .941]
        # Bouton "paramètres"
        self.parambtn = Button(self.fen, image=self.ParamImg, command=self.popupParam, width=35, height=35)
        # Placement du bouton dans la fenêtre
        self.parambtn.place(x=10, y=723)
        # Configure le bouton
        self.parambtn.configure(background="#202225", activebackground="#202225", borderwidth=0, highlightthickness=0)

        # Bouton "Ouvrir un fichier"
        self.openfileRatio = [.139, .130]
        self.openFileButton = makeLBtn(self.fen, self, {l: [self.languages[l]['btn'][1]] for l in self.languages}, 190, 100, self.openExplorateur, 1)
        # Bouton "conversion"
        self.convbtnRatio = [.139, .755]
        self.convBtn = makeLBtn(self.fen, self, {l: [self.languages[l]['btn'][3]] for l in self.languages}, 190, 580, self.conversion, 3)
        # Bouton "dossier de sortie"
        self.folderbtnRatio = [.139, .039]
        self.folderbtn = makeLBtn(self.fen, self, {l: [self.languages[l]['btn'][0]] for l in self.languages}, 190, 30, self.getSaveLink, 0)
        # Bouton "supprimer la musique"
        self.supprbtnRatio = [.850, .747]
        self.supprbtn = makeLBtn(self.fen, self, {l: [self.languages[l]['btn'][4]] for l in self.languages}, 1150, 580, self.delMusic, 4, width=20, bg="#484B52")

        self.VolumeLabelRatio = [.359, .260]
        # Cadre contenant le scale
        self.VolumeLabel = makeLLabel(self.fen, self, {l: [self.languages[l]['tags'][4]] for l in self.languages}, 490, 200, 4)
        # Configure des paramètres suplémentaires
        self.VolumeLabel.configure(borderwidth=0, highlightthickness=0, labelanchor='n', width=120, height=400)
        # Force la fenêtre
        self.VolumeLabel.pack_propagate(0)
        # Curseur du gain de volume
        scale = makeScale(self.VolumeLabel, self.volumeGain, -10, 20, 3)


        # Hovers

        # Message sur le bouton "supprimer la musique"
        makeHover(self, self.supprbtn, {l: [self.languages[l]['hovers'][0]] for l in self.languages}, 0)
        # Message sur le bouton "dossier de sauvegarde"
        makeHover(self, self.folderbtn, {l: [self.languages[l]['hovers'][1]] for l in self.languages}, 1)
        # Message sur le bouton "conversion"
        makeHover(self, self.convBtn, {l: [self.languages[l]['hovers'][2]] for l in self.languages}, 2)
        # Message sur le bouton paramètres
        makeHover(self, self.parambtn, {l: [self.languages[l]['hovers'][3]] for l in self.languages}, 3)
        # Message sur le bouton "ouvrir un fichier"
        makeHover(self, self.openFileButton, {l: [self.languages[l]['hovers'][4]] for l in self.languages}, 4)
        # Message sur le bouton "personnaliser"
        makeHover(self, persoBtn, {l: [self.languages[l]['hovers'][7]] for l in self.languages}, 7)
        # Message sur le bouton menu
        makeHover(self, self.menubtn, {l: [self.languages[l]['hovers'][10]] for l in self.languages}, 10)
        # Message sur le bouton drapeau
        makeHoverMenu(self, self.lblFlag, {l: [self.languages[l]['hovers'][6]] for l in self.languages}, 6)


        # Raccourci clavier

        # Supprimer la première music de la liste : Bouton Suppr
        self.fen.bind('<Delete>', self.delMusic)
        # Lancer la conversion : Bouton Entrée
        self.fen.bind('<Return>', self.conversion)
        # Ouvrir les paramètres : Bouton p (minuscule)
        self.fen.bind('<p>', self.popupParam)
        # Ouvrir le dossier de sauvegarde : Ctrl + s (minuscule)
        self.fen.bind('<Control-s>', self.getSaveLink)
        # Ouvrir la fenêtre d'accès au musiques : Ctrl + o (minuscule)
        self.fen.bind('<Control-o>', self.openExplorateur)
        # Change la langue : Bouton Tab
        self.fen.bind('<Shift_L>', self.switchLwithoutL)
        # Change la langue : Bouton Tab
        self.fen.bind('<Control-p>', self.popup)
        # Ouvre le site : Bouton Ctrl + n
        self.fen.bind('<Control-n>', self.open_site)
        # Si on clique à côté du menu, le supprime
        self.fen.bind("<Button-1>", self.del_flag_menu)
        # Tracking du changement de dimension
        self.fen.bind("<Configure>", self.changeSize)
        # Si on clicque sur "m"
        self.fen.bind("<m>", self.popupMenu)


    def changeSize(self, event=None):
        # Si il s'agit d'un changement de largeur
        w = self.fen.winfo_width()
        h = self.fen.winfo_height()
        if w != self.width or h != self.height:
            # Logo
            self.LabelImage.place(x=self.labelImageRatio[0] * w, y = self.labelImageRatio[1] * h)

            # MusicFile
            self.MusicFiles.place(x=self.MusicFilesRatio[0] * w, y=self.MusicFilesRatio[1] * h)

            # filesList
            self.filesList['width'] = int(self.filesListratio[0] * w)
            self.filesList['height'] = int(self.filesListratio[1] * h)

            # MusicTags
            self.MusicTags.place(x=self.MusictagsRatio[0] * w, y=self.MusictagsRatio[1] * h)

            # Pgb
            self.Pgb.place(x=self.PgbRatio[0] * w, y=self.PgbRatio[1] * h)

            # Progressbar
            self.progressbar['length'] = int(self.progressbarRatio * w)

            # Drapeau
            self.lblFlag.place(x=self.lblFlagRatio[0] * w, y=self.lblFlagRatio[1] * h)

            # parambtn
            self.parambtn.place(x=self.parambtnRatio[0] * w, y=self.parambtnRatio[1] * h)

            # openfile
            self.openFileButton.place(x=self.openfileRatio[0] * w, y=self.openfileRatio[1] * h)

            # convbtn
            self.convBtn.place(x=self.convbtnRatio[0] * w, y=self.convbtnRatio[1] * h)

            # folderbtn
            self.folderbtn.place(x=self.folderbtnRatio[0] * w, y=self.folderbtnRatio[1] * h)

            # supprbtn TODO: à refaire
            self.supprbtn.place(x=self.supprbtnRatio[0] * w, y=self.supprbtnRatio[1] * h)
            #self.supprbtn.place(x=1161, y=575)

            # Volume
            self.VolumeLabel.place(x=self.VolumeLabelRatio[0] * w, y=self.VolumeLabelRatio[1] * h)

            self.width = w
            self.height = h


    def del_flag_menu(self, event=None):
        if self.flagMenu:
            self.flagMenu.onLeave()


    def open_site(self, event=None):
        """ Ouvre le site
        """
        webbrowser.open("https://bonesound.wordpress.com/")


    def loadIcons(self):
        """ Load the app icons
        Icons are from : https://www.flaticon.com/home
        """
        return {flag.split('.')[0]: ImageTk.PhotoImage(Image.open("./flags/" + flag).resize((35, 35))) for flag in os.listdir("./flags")}


    def getAvailableLanguage(self):
        """ Retourne les languages disponible
        """
        # Si le fichier de paramètre existe dans le dossier
        if self.LanguageFile in os.listdir():
            # Ouvre le fichier
            f = json.load(open(self.LanguageFile))
            data = json.load(open(self.LanguageFile))
            return {l: data[l] for l in data.keys() if len(data[l].keys()) > 2}, data
        # Si le fichier n'est pas dans le dossier
        else:
            # Le contenue du fichier de base (seulement l'anglais)
            resp = {
                "af": {"nom": ["Afrikaans", "Afrikaans"]}, "am": {"nom": ["\u12a0\u121b\u122d\u129b", "Amharic"]}, "ar": {"nom": ["\u0639\u0631\u0628\u0649", "Arabic"]}, "az": {"nom": ["Azeri", "Azeri"]},
                "be": {"nom": ["\u0431\u0435\u043b\u0430\u0440\u0443\u0441\u043a\u0456", "Belarusian" ]}, "bg": {"nom": ["\u0431\u044a\u043b\u0433\u0430\u0440\u0441\u043a\u0438", "Bulgarian"]}, "bs": {"nom": ["Bosanski", "Bosnian"]},
                "ceb": {"nom": ["Cebuano", "Cebuano"]}, "cs": {"nom": ["\u010de\u0161tina", "Czech"]}, "cy": {"nom": ["Cymraeg", "Welsh"]}, "da": {"nom": ["Dansk", "Danish"]}, "de": {"nom": ["Deutch", "German"]},
                "el": {"nom": ["\u0395\u03bb\u03bb\u03b7\u03bd\u03b9\u03ba\u03ac", "Greek"]},
                "en": {"about": ["A text about the project"],"Spacing": ["tags","btn","popup"],"allErrorMsg": ["There is no music to convert","The format is incorrect","You must enter an number"],"allMsgPossible": ["No operation currently","Application of the volume gain","Application of the filters","Application of the compression","Saving the file"],"btn": [" Output folder "," Open a file "," Personalize "," Convert "," Delete music "," Change the color "," Ok "," Change the language "," Music analytics "],"error": ["Error","Problem","Conversion error"],"hovers": ["Delete selected music\nKeyboard shortcut : Suppr","Select the output folder\nKeyboard shortcut : Ctrl + s","Start the musique conversion\nKeyboard shortcut : Enter","Open the settings window\nKeyboard shortcut : p","Open the music selection window\nKeyboard shortcut : Ctrl + o","Change language\nKeyboard shortcut : Shift","Open the personailze window\nKeyboard shortcut : Ctrl + p","Open the selection color window\nKeyboard shortcut : c","Validate your settings\nKeyboard shortcut : Enter","Download the translation\nThere are {} left","Open the menu window\nKeyboard shortcut : m","Open the music analyser menu\nKeyboard shortcut : m"],"infoMsg": ["The conversion is complete","The translation is complete"],"infoTitle": ["Conversion completed","Translation completed"],"musicName": ["Voice","French song","Classical Music","Drum & bass","Electro","Jazz","Lofi","Pop","Rap","Rock","RnB","Hard Rock","Reggae"],"nom": ["English","English"],"popup": [" Personalization "," Settings "," Output folder selection "," Files selection "," Languages "," Menu "],"tags": [" List of musics to convert "," List of the different type of music "," Progress of the operation "," Enter the number of filter(s) to apply "," Gain (dB) "," Operation in progress "," Search bar "," About "],"tradMsg": ["Download language pack"]},
                "es": {"nom": ["Espa\u00f1ol", "Spanish"]}, "et": {"nom": ["Eesti keel", "Estonian"]}, "eu": {"nom": ["Euskal", "Basque"]},
                "fa": {"nom": ["\u0641\u0627\u0631\u0633\u06cc", "Persian"]}, "fi": {"nom": ["Suomalainen", "Finnish"]}, "fr": {"nom": ["Fran\u00e7ais", "French"]},
                "ga": {"nom": ["Gaeilge", "Irish"]}, "gd": {"nom": ["G\u00e0idhlig", "Gaelic"]}, "gu": {"nom": ["\u0a97\u0ac1\u0a9c\u0ab0\u0abe\u0aa4\u0ac0", "Gujarati"]},
                "haw": {"nom": ["\u014clelo Hawai\u02bbi", "Hawaiian"]}, "he": {"nom": ["\u05e2\u05d1\u05e8\u05d9\u05ea", "Hebrew"]}, "hi": {"nom": ["\u0939\u093f\u0902\u0926\u0940", "Hindi"]}, "hr": {"nom": ["Hrvatski", "Croatian"]}, "ht": {"nom": ["Krey\u00f2l ayisyen", "Haitian creole"]}, "hu": {"nom": ["Magyar", "Hungarian"]}, "hy": {"nom": ["\u0570\u0561\u0575\u0565\u0580\u0565\u0576", "Armenian"]},
                "id": {"nom": ["bahasa Indonesia", "Indonesian"]},"is": {"nom": ["\u00cdslensku", "Icelandic"]}, "it": {"nom": ["italiano", "Italian"]}, "ja": {"nom": ["\u65e5\u672c\u4eba", "Japanese"]},
                "ka": {"nom": ["\u10e5\u10d0\u10e0\u10d7\u10e3\u10da\u10d8", "Georgian"]}, "kk": {"nom": ["\u049a\u0430\u0437\u0430\u049b\u0448\u0430", "Kazakh"]}, "km": {"nom": ["\u1797\u17b6\u179f\u17b6\u1781\u17d2\u1798\u17c2\u179a", "Khmer"]}, "kn": {"nom": ["\u0c95\u0ca8\u0ccd\u0ca8\u0ca1", "Kannada"]}, "ko": {"nom": ["\ud55c\uad6d\uc5b4", "Korean"]}, "ky": {"nom": ["Kirghiz", "Kirghyz"]},
                "lb": {"nom": ["L\u00ebtzebuergesch", "Luxembourgish"]}, "lo": {"nom": ["Laotian", "Laotian"]}, "lt": {"nom": ["Lietuvi\u0173", "Lithuanian"]}, "lv": {"nom": ["Latvie\u0161u valoda", "Latvian"]},
                "mg": {"nom": ["Malagasy", "Malagasy"]}, "mk": {"nom": ["\u041c\u0430\u043a\u0435\u0434\u043e\u043d\u0441\u043a\u0438", "Macedonian"]}, "ml": {"nom": ["\u0d2e\u0d32\u0d2f\u0d3e\u0d33\u0d02", "Malayalam"]}, "mn": {"nom": ["\u041c\u043e\u043d\u0433\u043e\u043b \u0445\u044d\u043b \u0434\u044d\u044d\u0440", "Mongolian"]}, "mr": {"nom": ["\u092e\u0930\u093e\u0920\u0940", "Marathi"]}, "mt": {"nom": ["Malti", "Maltese"]},
                "ne": {"nom": ["\u0928\u0947\u092a\u093e\u0932", "Nepalese"]}, "nl": {"nom": ["Nederlands", "Dutch"]}, "no": {"nom": ["norsk", "Norwegian"]},
                "pa": {"nom": ["\u0a2a\u0a70\u0a1c\u0a3e\u0a2c\u0a40", "Panjabi"]}, "pl": {"nom": ["Polskie", "Polish"]}, "ps": {"nom": ["\u067e\u069a\u062a\u0648", "Pashto"]}, "pt": {"nom": ["Portugu\u00eas", "Portuguese"]},
                "ro": {"nom": ["Rom\u00e2n\u0103", "Romanian"]}, "ru": {"nom": ["\u0440\u0443\u0441\u0441\u043a\u0438\u0439", "Russian"]},
                "sd": {"nom": ["\u0633\u0646\u068c\u064a", "Sindhi"]}, "si": {"nom": ["\u0dc3\u0dd2\u0d82\u0dc4\u0dbd\u0dba\u0dd2\u0db1\u0dca", "Singhalese"]}, "sk": {"nom": ["slovensk\u00fd", "Slovak"]}, "sl": {"nom": ["Sloven\u0161\u010dina", "Slovenian"]}, "sm": {"nom": ["Samoa", "Samoan"]}, "sn": {"nom": ["Shona", "Shona"]}, "so": {"nom": ["Somali", "Somali"]}, "sq": {"nom": ["shqiptar", "Albanian"]}, "sr": {"nom": ["\u0421\u0440\u043f\u0441\u043a\u0438", "Serbian"]}, "st": {"nom": ["Sesotho", "Sesotho"]}, "su": {"nom": ["Soundanais", "Soundanais"]}, "sv": {"nom": ["svenska", "Swedish"]}, "sw": {"nom": ["Kiswahili", "Swahili"]},
                "ta": {"nom": ["\u0ba4\u0bae\u0bbf\u0bb4\u0bcd", "Tamil"]}, "te": {"nom": ["\u0c24\u0c46\u0c32\u0c41\u0c17\u0c41", "Telugu"]}, "tg": {"nom": ["\u0422\u043e\u04b7\u0438\u043a\u04e3", "Tajik"]}, "th": {"nom": ["\u0e44\u0e17\u0e22", "Thai"]}, "tl": {"nom": ["Tagalog", "Tagalog"]}, "tr": {"nom": ["T\u00fcrk", "Turkish"]},
                "uk": {"nom": ["\u0423\u043a\u0440\u0430\u0457\u043d\u0441\u044c\u043a\u0430", "Ukrainian"]},
                "uz": {"nom": ["O'zbek", "Uzbek"]}, "vi": {"nom": ["Ti\u1ebfng Vi\u1ec7t", "Vietnamese"]}, "xh": {"nom": ["isiXhosa", "Xhosa"]}, "yo": {"nom": ["Yor\u00f9b\u00e1", "Yoruba"]},
                "zh-CN": {"nom": ["\u7b80\u4f53\u4e2d\u6587", "Simplified Chinese"]}, "zh-TW": {"nom": ["\u7e41\u9ad4\u4e2d\u6587", "Traditional Chinese"]}, "zu": {"nom": ["Zulu", "Zulu"]}
            }
            json.dump(resp, open(self.LanguageFile, "w"), sort_keys=True, indent=4)
            # Retourne des paramètres par défaut
            return resp['en'], resp


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
            self.popupMsg = Message(text={l: [self.languages[l]['popup'][0]] for l in self.languages}, actualLanguage=self.langue)
            # Crée une pop-up pour demander la valeur
            self.w = PersoPopup(self)
            # Met la fenêtre au dessus de la principale
            self.fen.wait_window(self.w.top)
            # Récupère le nombre entré
            self.nbFilter = self.w.value
            # Si aucun nombre n'a été entré
            if self.nbFilter == None:
                # On n'utilise pas le filtre personalisé
                self.applyingPerso = False


    def popupParam(self, event=None):
        """ Crée une pop-up de paramètres
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
            # Permet de changer entre les deux langues
            self.persoMsg = Message(text={l: [self.languages[l]['popup'][1]] for l in self.languages}, actualLanguage=self.langue)
            # Crée une pop-up pour demander la valeur
            self.p = ParamPopup(self)
            # Met la fenêtre au dessus de la principale
            self.fen.wait_window(self.p.top)


    def popupMenu(self, event=None):
        # Envoi la fenêtre à l'avant si elle existe
        try:
            # Place la fenêtre devant la fenêtre principale
            self.m.top.lift()
            self.m.top.attributes('-topmost', True)
            self.m.top.attributes('-topmost', False)
            # Focus la fenêtre
            self.m.top.focus_set()
        # Sinon la créer
        except:
            self.popupMenuFen = True
            # Permet de changer entre les deux langues
            self.menuMsg = Message(text={l: [self.languages[l]['popup'][5]]
                                          for l in self.languages}, actualLanguage=self.langue)
            # Crée une pop-up pour demander la valeur
            self.m = MenuPopup(self)
            # Met la fenêtre au dessus de la principale
            self.fen.wait_window(self.m.top)


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
        # Le nom du bouton
        style_name = Radiobutton().winfo_class()
        # Configure la style du bouton
        style.configure(style_name, foreground="#b6b9be", background='#202225', indicatorcolor="#202225", borderwidth=0, selectcolor="#FAA61A")
        # Précise les couleurs en fonction des états du bouton
        style.map(style_name, foreground=[('disabled', "#b6b9be"), ('pressed', self.color), ('active', self.color)], background=[('disabled', '#202225'), ('pressed', '!focus', '#202225'), ('active', '#202225')], indicatorcolor=[('selected', self.color), ('pressed', self.color)])
        # Pour chaque bouton
        for rdb in self.allColorObjet:
            # Configure le style du bouton
            rdb.configure(style=style_name)


    def switchL(self):
        """ Change la langue de l'application
        """
        # Pour chaque objet Message comportant un Stringvar
        for l in self.alltxtObject["Stringvar"]:
            msg, name, n = l
            if self.langue not in msg.text.keys():
                msg.addLang(self.langue, [self.languages[self.langue][name][n]])
            # Change le langue du message
            msg.switchLang(self.langue)
            # Change le message
            msg.update()
        # Pour chaque objet Message ne comportant pas de Stringvar
        for l in self.alltxtObject['LabelFrame']:
            msg, name, n = l[1]
            if self.langue not in msg.text.keys():
                msg.addLang(self.langue, [self.languages[self.langue][name][n]])
            # Change le langue du message de l'objet Message
            msg.switchLang(self.langue)
            # Si une fenêtre est ouverte
            try:
                # Reconfigure le texte du LabelFrame
                l[0].configure(text=msg.getTxt())
            # Sinon
            except:
                pass
        # Récupère le nouveau drapeau et sa position dans le bouton
        flag  = self.FlagDict[self.langue]
        self.lblFlag.configure(image=flag)
        # Si la fenêtre des paramètres est ouverte
        if self.popupParamFen:
            if not self.langue in self.persoMsg.text.keys():
                self.persoMsg.addLang(self.langue, [self.languages[self.langue]['popup'][1]])
            try:
                # Change le titre de la fenêtre
                self.p.top.title(self.persoMsg.text[self.langue][0])
            except:
                pass
        # Si la fenêtre de personnalisation est ouverte
        if self.popupFen:
            if not self.langue in self.popupMsg.text.keys():
                self.popupMsg.addLang(self.langue, [self.languages[self.langue]['popup'][0]])
            try:
                # Change le titre de la fenêtre
                self.w.top.title(self.popupMsg.text[self.langue][0])
            except:
                pass

        if self.popupMenuFen:
            if not self.langue in self.menuMsg.text.keys():
                self.menuMsg.addLang(self.langue, [self.languages[self.langue]['popup'][0]])
            try:
                # Change le titre de la fenêtre
                self.m.top.title(self.menuMsg.text[self.langue][0])
            except:
                pass
        # Si la fenêtre de traduction est ouverte
        if self.lm:
            if not self.langue in self.lm.tradMsg.text.keys():
                self.lm.tradMsg.addLang(self.langue, [self.languages[self.langue]['tradMsg'][0]])
            # Si la fenêtre n'est pas fermée
            try:
                # Change le titre de la fenêtre
                self.lm.top.title(self.lm.tradMsg.text[self.langue][0])
            except:
                pass
        # Sauvegarde les paramètres (la langue ici)
        self.saveParam()


    def switchLwithoutL(self, event=None):
        """ Chnage la langue de l'application vers la langue suivante dans la liste des langues disponible
        """
        # Liste des codes des langues disponibles
        listelencode = list(self.languages.keys())
        # La position de la langue actuelle dans la liste
        pos = listelencode.index(self.langue)
        # Code de la langue suivante (la modulation évite un IndexError)
        self.langue = listelencode[(pos + 1) % len(listelencode)]
        # Change la langue de l'apllication
        self.switchL()


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
        self.openMsg = {l: [self.languages[l]['popup'][2]] for l in self.languages}
        # Ouvre une fenêtre explorer pour demander le chemin vers le dossier
        path = easygui.diropenbox(self.openMsg[self.langue][0], default=f"{self.saveLink}/")
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
            musictype = int(self.musicType.get()) - 1
            # Récupère la valeur du gain de volume
            gain = self.volumeGain.get()
            # Prend le nombre de filtre à appliquer
            nbRep = self.FilterList[musictype] if not self.applyingPerso else self.nbFilter
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
                messagebox.showerror(self.error[self.langue][2], self.allErrorMsg[self.langue][0])
            # Si il s'agit d'une autre erreur
            else:
                # Pop-up d'erreur
                messagebox.showerror(self.error[self.langue][0], f"{name}: {e}")


    def openExplorateur(self, event=None):
        """ Ouvre l'explorateur pour récupérer la musique à modifier
        """
        # Change le texte
        self.openExpMsg = {l: [self.languages[l]['popup'][3]] for l in self.languages}
        # Ouvre un explorateur de fichier qui retourne le chemin depuis la racine jusqu'au ficiers séléstionnés
        files = easygui.fileopenbox(self.openExpMsg[self.langue][0], multiple=True, default=f"{self.MusicLink}/")
        # Si il y a des fichiers
        if files:
            # Pour chaque fichier de la liste
            for f in files:
                # Si le fichier est un fichier wav est n'est pas déjà dans la liste
                if f[-4:] in self.AllMusicExtPossibles:
                    if f not in self.files:
                        # Ajoute le fichier à la liste des fichiers à convertir
                        self.files.append(f)
                        # Ajoute à l'affichage le nom de fichier
                        self.filesList.insert(len(self.files) - 1, os.path.basename(f))
                # Sinon
                else:
                    # Pop-up d'erreur
                    messagebox.showerror(self.error[self.langue][0], self.allErrorMsg[self.langue][1])
            # Change le fichier de musique
            self.MusicLink, _ = os.path.split(f)
            # Sauvegarde le dossier d'ouverture de fichier
            self.saveParam()


    def analyse(self, event=None):
        """ Ouvre l'explorateur et ouvre les musiques séléctionnées
        """
        # Change le texte
        self.openExpMsg = {l: [self.languages[l]['popup'][3]] for l in self.languages}
        # Ouvre un explorateur de fichier qui retourne le chemin depuis la racine jusqu'au ficiers séléstionnés
        files = easygui.fileopenbox(self.openExpMsg[self.langue][0], multiple=True, default=f"{self.MusicLink}/")
        # Si il y a des fichiers
        if files:
            # Fenêtre pour afficher les musiques
            plt.figure()
            # S'il n'y a qu'une musique
            if len(files) == 1:
                # L'ouvre
                sr, signal = wavfile.read(files[0])
                # Récupère le signal d'une oreille
                y = signal[:, 0]
                # Mise à l'échelle de la coordonnée x
                x = np.arange(len(y)) / float(sr)
                # Affihe la musique
                plt.plot(x, y)
                # Ajoute le titre de la musique
                plt.xlabel(files[0].split('\\')[-1])
            # S'il y a plusieurs musiques
            else:
                # Pour chaque musique
                for x, f in enumerate(files):
                    # L'ouvre
                    sr, signal = wavfile.read(f)
                    # Récupère le signal d'une oreille
                    y = signal[:, 0]
                    # Mise à l'échelle de la coordonnée x
                    z = np.arange(len(y)) / float(sr)
                    # INdique la position de la musique
                    plt.subplot(lf, 1, x + 1)
                    # Affihe la musique
                    plt.plot(z, y)
                    # Ajoute le titre de la musique
                    plt.xlabel(f.split('\\')[-1])
            # Affiche la fenêtre
            plt.show()


    def run(self):
        """ Fonction principale lance la fenêtre
        """
        self.fen.mainloop()


#
# ---------- Test ---------------------------------------------------------------------------------
#


if __name__ == "__main__":
    Interface().run()

    # TODO:
    # installer (?)
