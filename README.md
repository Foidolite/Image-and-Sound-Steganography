# Image-and-Sound-Steganography
A python script containing functions for embedding hidden data in images and sound.  
Requires Pillow: https://pypi.org/project/Pillow/
and pyaudio: https://www.lfd.uci.edu/~gohlke/pythonlibs/#pyaudio

Contains the following capabilities:

1. Secret Image within Another Image's Least Significant Bits (ImgImgE/ImgImgD):

Using the ImgImgE command, an image can be bitcrushed and stored within 1-8 of the least significant bits of another image.
As an example, say we want to hide this image (secret.png):<br/>
![alt text](stegoTool/imgimg_example/secret.png)<br/>
within this one (base.png):<br/>
![alt text](stegoTool/imgimg_example/base.png)

Using the following command:  
"python stego.py ImgImgE base.png secret.png loaded.png 1 7"  
with stego.py in the same folder as base.png and secret.png, we can embed secret.png within the least significant bit of base.png:<br/>
![alt text](stegoTool/imgimg_example/loaded1bit.png)<br/>
It looks unchanged, but the data is there and retrievable via the command:  
"python stego.py ImgImgD loaded.png out.png 1 7"<br/>
![alt text](stegoTool/imgimg_example/out1bit.png)<br/>

Optionally, you can use more bits for a better output image (although the secret may become more visible), or even embed different images in each color channel.

2. Secret Image within an Audio File's Spectrogram (ImgSnd):

Using the ImgSnd command, an image can be translated into an audio file whose spectrogram displays as the original image.
As an example, let's use this image:<br/>
![alt text](stegoTool/imgsnd_example/secret.png)<br/>

Using a command like this:  
"python stego.py ImgSnd secret.png secret.wav 12000 20000 1 20 4000 0 16 41000"  
We can obtain a sound file with the appropriate spectrogram (see imgsnd example/secret.wav).
Then, we can mix it with some other audio or music (imgsnd example/base.wav), to create a sound file in which you cannot hear the secret audio, but if opened in a program like Audacity, the secret image can be made plainly visible (imgsnd example/mixed.wav):<br/>
![alt text](stegoTool/imgsnd_example/example.PNG)<br/>

3. Secret File within an Images' Least Significant Bits (AnyImg/ImgAny):

Using the AnyImg command, any file can be embedded into the LSB of an image file.
For example, see the anyimg example folder. There, we have our familiar base image, as well as two secret files. 
One, secretLamp.obj, is a 3d model of a lamp. The other, secret.txt, is a list of the 1000 most common English words listed alphabetically.
We can hide the lamp within the RGB channels of the image using:  
"python stego.py AnyImg secretLamp.obj base.png temp.png 1 7"  
and then hide the text within the Alpha channel of the image using:  
"python stego.py AnyImg secret.txt temp.png loaded.png 1 8"  
Then extract both using:  
"python stego.py ImgAny loaded.png outLamp.obj 1 7"  
"python stego.py ImagAny loaded.png out.txt 1 8"

In addition, and xor key can be used as an optional argument at the end to encrypt the bits of your file and prevent other steganography tools from picking up on the data.
