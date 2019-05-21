# Égaliseur BoneSound / BoneSound-Equalizer

Un égaliseur pour le casque BoneSound.
An equalizer for the BoneSound headset.

### Prérequis / Prerequisites

Vous devez avoir installer ffmpeg et l'avoir mis dans le même dossier que le projet
You will need ffmpeg to be installed and in the same folder as the project.

Vous pouvez le télécharger depuis [ce lien](https://ffmpeg.org/).
You can download it from [here](https://ffmpeg.org/).

### Structure de fichier / Folder Structure

**image/** : La localisation des images utilisées par le programme.
**image/** : Location of the image used in the programme.

_Si vous voulez changer une image, nommez-la avec le nom de celle que vous voulez remplacer._
_If you want to change an image, named it with the name of the one you want to change._

### Aperçu de l'application / App Preview

![Alt text](./image/Screen.png "BoneSound Equalizer")

### Installation / Installing

Les librairies easygui, pydub, numpy et Pillow doivent être installées.
You will need to easygui, pydub, numpy and Pillow libraries to be installed.

Pour ce faire, entrer la commande suivante dans le console window:
To do so, just run on cmd:

```
pip install -r requirements.txt
```

## Lancer les tests / Running the tests

Lancez juste BoneSound_Equailzer.py et testez toutes les commandes.
Just run BoneSound_Equailzer.py and test all commands.

## Déploiement / Deployment

Vous pouvez construire le projet en exécutable en installant auto-py-to-exe avec la commande suivante et en le lançant.
You can build this as an exe by installing auto-py-to-exe with the following command and runnning it.

```
pip install auto-py-to-exe
```

_N'oubliez pas d'ajouter ffmpeg.exe, votre icône et le dossier image pour le faire fonctionner._
_Don't forget to add ffmpeg.exe, your icon and the image folder to make it work._

## Construit avec l'outil suivant /  Built with the following tool

- Le convertisseur de son :
- The Sound converter :
- [FFMPEG](https://ffmpeg.org/)

## Auteur / Author

- [**Maxime Roucher**](https://github.com/maximeroucher)
