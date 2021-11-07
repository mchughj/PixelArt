
# Pixel Art

Looking at expanding the images that I'm seeing in my PixelPanel.

1. Install necessary prerequisites
```
sudo apt install -y python3
python3 -m pip install --user --upgrade pip
python3 -m pip install --user virtualenv
```
Then, to allow PyQT - along with QtCreator - to work do:
```
sudo apt-get update -y
sudo apt-get install libxcb-icccm4 libxcb-xkb1 libxcb-icccm4 libxcb-image0 libxcb-render-util0 libxcb-randr0 libxcb-keysyms1 libxcb-xinerama0
sudo apt-get install qtcreator qt5-default qt5-doc qtbase5-examples qt5-doc-html qtbase5-doc-html
```
1. Create a new virtual environment within the same directory as the git checkout.
```
cd PixelArt
python3 -m virtualenv --python=python3 env
```
1. Activate the new virtual environment
```
source env/bin/activate
```
1. Install, into the new virtual environment, the required python modules for this specific environment.  This will be installed within the virtual env which was activated earlier.
```
python3 -m pip install -r requirements.txt
