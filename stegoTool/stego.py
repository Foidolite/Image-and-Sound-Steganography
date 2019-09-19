import sys
from PIL import Image
import pyaudio
from random import randrange
import wave
import math
import os

def padHex(string, length):
    while len(string) < length:
        string = "0" + string
    return string

def padBack(string, length):
    while len(string) < length:
        string += "0"
    return string

def luminance(r,g,b):
    r = (r/255)**2.2
    g = (g/255)**2.2
    b = (b/255)**2.2
    return 0.2126*r + 0.7152*g + 0.0722*b

#default pixel mapping for AnyImg/ImgAny. Maps row by row, left to right, top to bottom.
def linearMap(n, width, height):
    return (n % width, n // width)

def main():
    if len(sys.argv) == 1:
        print("""This script contains an Audio/Image steganography tool.

        Usage: python stego.py [commands] [args]

        Commands:
            AnyImg [input file] [input image] [output image] [bits] [style] [key(optional)]
                - embed file into png using [bits] number of least sig. bits.
                [key] - the input bits will be xor-ed by this string of characters before encoding.
                        if using a key, you will need the same key to xor the bits back when decoding.
                [style] - which channels to encode in. r: +1. g: +2. b: +4. a: +8.
                          e.g. encoding in red and blue channels: 1+4 = 5.

            ImgAny [input image] [output file] [bits] [style] [key(optional)]
                - retrieve file from png using [bits] number of least sig. bits.

            ImgImgE [base image] [secret image] [output image] [bits] [style]
                - encode secret image into the lsb of base image with [bits] number of bits.
                [style] - which channels to encode in. r: +1. g: +2. b: +4.

            ImgImgD [input image] [output image] [bits] [style]
                - retrieve the secret image hidden inside of the input image and normalizes it for viewing.

            ImgSnd [image] [output wav] [base freq.] [top freq.] [exp] [res] [width] [volume] [bitrate] [sample rate]
                - encode image into spectrogram of wav.
                [base freq.] - on a spectrogram, the bottom of the image will be at this frequency.
                                set this higher for better quality.
                [top freq.] - on a spectrogram, the top of the image will be at this frequency.
                [exp] - the image will be mapped logarithmically, so that pixels of y displacement above the base
                        are y^exp frequency above. set to 1 for linear mapping (which is usualy fine anyway).
                [res] - generete res number of sine waves. Be reasonable, Python tanks easily!
                [width] - width # of samples will be used to store one pixel of data. 1000-5000 is usually good.
                [volume] - how loud relative to 0dB the theoretical peak of the message will be. in -dB.
                            Usually, the sound turns out to be much quieter than this theoretical peak.
                [bitrate] - must be a multiple of 8. Again, be reasonable. 16 is usually as high as it needs to be.
                [sample rate] - the number of samples per second. 44100 will encode all audible frequencies.
                NOTE: If the output is silent, [res] was likely too high for your [bitrate].
        """)
    else:
        command = sys.argv[1]
        if command == "AnyImg":
            if len(sys.argv) < 7:
                raise Exception("""It seems like you're missing some arguments.
Run stego.py with no arguments for help.""")
            file = open(sys.argv[2], "rb")
            imgIn = Image.open(sys.argv[3]).convert("RGBA")
            imgOutPath = sys.argv[4]
            bits = abs(int(sys.argv[5]))
            style = padHex(bin(abs(int(sys.argv[6])))[2:], 4)
            R = int(style[3])
            G = int(style[2])
            B = int(style[1])
            A = int(style[0])
            if bits > 8:
                raise Exception("""stego.py does not export more than 8 bits per channel""")
            width, height = imgIn.size
            if (width*height*(bits * (R + G + B + A)))//8 < os.path.getsize(sys.argv[2]):
                raise Exception("""Can't fit file into image; use more bits or channels.""")
            key = chr(0)
            if len(sys.argv) > 7:
                key = sys.argv[7]

            #perform embedding
            #first read file, perform xor, and sort into appropriate lists per pixel
            binString = "" #sort all bytes into this linear binary string
            b = file.read(1)
            while b:
                b = int.from_bytes(b, byteorder = "big", signed = False) ^ ord(key[0])
                key = key[1:] + key[0]
                binString = binString + padHex(bin(b)[2:], 8)
                b = file.read(1)
            binString = binString + "0"*256 #a null terminus to mark the end of file
            lsbList = [] #sort binary into list of ints that can be added to pixels
            while len(binString) > 0:
                pix = [0, 0, 0, 0]
                if R and binString[:bits] != "":
                    pix[0] = int(binString[:bits], 2)
                    binString = binString[bits:]
                if G and binString[:bits] != "":
                    pix[1] = int(binString[:bits], 2)
                    binString = binString[bits:]
                if B and binString[:bits] != "":
                    pix[2] = int(binString[:bits], 2)
                    binString = binString[bits:]
                if A and binString[:bits] != "":
                    pix[3] = int(binString[:bits], 2)
                    binString = binString[bits:]
                lsbList.append(pix)
            #pad out rest of image with noise
            while len(lsbList) < width*height:
                lsbList.append([randrange(2**bits), randrange(2**bits), randrange(2**bits), randrange(2**bits)])
            #now, add values to pixels in image
            for n in range(width*height):
                pixXY = linearMap(n, width, height)
                r,g,b,a = imgIn.getpixel(pixXY)
                for i in range(bits): # set bits # of lsb to 0
                        r -= 2**i * int(padHex(bin(r)[2:], 8)[::-1][i:i+1]) * R
                        g -= 2**i * int(padHex(bin(g)[2:], 8)[::-1][i:i+1]) * G
                        b -= 2**i * int(padHex(bin(b)[2:], 8)[::-1][i:i+1]) * B
                        a -= 2**i * int(padHex(bin(a)[2:], 8)[::-1][i:i+1]) * A
                r += lsbList[n][0] * R
                g += lsbList[n][1] * G
                b += lsbList[n][2] * B
                a += lsbList[n][3] * A
                imgIn.putpixel(pixXY,(r,g,b,a))

            imgIn.save(imgOutPath, "PNG")
            print("finish!")
        elif command == "ImgAny":
            if len(sys.argv) < 6:
                raise Exception("""It seems like you're missing some arguments.
Run stego.py with no arguments for help.""")
            imgIn = Image.open(sys.argv[2]).convert("RGBA")
            file = open(sys.argv[3], "wb")
            bits = abs(int(sys.argv[4]))
            style = padHex(bin(abs(int(sys.argv[5])))[2:], 4)
            R = int(style[3])
            G = int(style[2])
            B = int(style[1])
            A = int(style[0])
            if bits > 8:
                raise Exception("""stego.py does not support more than 8 bits per channel""")
            key = chr(0)
            if len(sys.argv) > 6:
                key = sys.argv[6]

            #first extract out all lsb data
            binString = ""
            width, height = imgIn.size
            for n in range(width*height):
                pixXY = linearMap(n, width, height)
                r,g,b,a = imgIn.getpixel(pixXY)
                dr = 0
                dg = 0
                db = 0
                da = 0
                for i in range(bits):
                    dr += 2**i * int(padHex(bin(r)[2:], 8)[::-1][i:i+1])
                    dg += 2**i * int(padHex(bin(g)[2:], 8)[::-1][i:i+1])
                    db += 2**i * int(padHex(bin(b)[2:], 8)[::-1][i:i+1])
                    da += 2**i * int(padHex(bin(a)[2:], 8)[::-1][i:i+1])
                binString += (padHex(bin(dr)[2:],bits) if R else "") + (padHex(bin(dg)[2:], bits) if G else "") + (padHex(bin(db)[2:], bits) if B else "") + (padHex(bin(da)[2:], bits) if A else "")
            #now, apply xor and write string back into file
            while binString[:256] != "0"*256:
                b = int(binString[:8], 2) ^ ord(key[0])
                key = key[1:] + key[0]
                file.write(b.to_bytes(1, byteorder = "big"))
                binString = binString[8:]
            file.close()
            print("finish!")
        elif command == "ImgImgE":
            if len(sys.argv) < 7:
                raise Exception("""It seems like you're missing some arguments.
Run stego.py with no arguments for help.""")
            #take in all arguments
            imgIn = Image.open(sys.argv[2]).convert("RGB")
            imgSec = Image.open(sys.argv[3]).convert("RGB")
            imgOutPath = sys.argv[4]
            bits = abs(int(sys.argv[5]))
            style = padHex(bin(abs(int(sys.argv[6])))[2:], 3)
            R = int(style[2])
            G = int(style[1])
            B = int(style[0])
            if bits > 8:
                raise Exception("""stego.py does not export more than 8 bits per channel""")
            if imgIn.size != imgSec.size:
                imgSec = imgSec.resize(imgIn.size, Image.ANTIALIAS)

            #perform embedding!
            width, height = imgIn.size
            for x in range(width):
                for y in range(height):
                    r,g,b = imgIn.getpixel((x,y))
                    sr,sg,sb = imgSec.getpixel((x,y))
                    for i in range(bits): # set bits # of lsb to 0
                        r -= 2**i * int(padHex(bin(r)[2:], 8)[::-1][i:i+1]) * R
                        g -= 2**i * int(padHex(bin(g)[2:], 8)[::-1][i:i+1]) * G
                        b -= 2**i * int(padHex(bin(b)[2:], 8)[::-1][i:i+1]) * B
                    sr = math.floor((sr/255)*(2**bits - 1) + 0.5) #crush 'em bits
                    sg = math.floor((sg/255)*(2**bits - 1) + 0.5)
                    sb = math.floor((sb/255)*(2**bits - 1) + 0.5)
                    r += sr * R
                    g += sg * G
                    b += sb * B
                    imgIn.putpixel((x,y),(r,g,b))

            imgIn.save(imgOutPath, "PNG")
            print("finish!")

        elif command == "ImgImgD":
            if len(sys.argv) < 6:
                raise Exception("""It seems like you're missing some arguments.
Run stego.py with no arguments for help.""")
            #take in all arguments
            imgIn = Image.open(sys.argv[2]).convert("RGB")
            imgOutPath = sys.argv[3]
            bits = abs(int(sys.argv[4]))
            style = padHex(bin(abs(int(sys.argv[5])))[2:], 3)
            R = int(style[2])
            G = int(style[1])
            B = int(style[0])
            if bits > 8:
                raise Exception("""stego.py does not support more than 8 bits per channel""")

            #perform extraction!
            width, height = imgIn.size
            for x in range(width):
                for y in range(height):
                    r,g,b = imgIn.getpixel((x,y))
                    dr = 0
                    dg = 0
                    db = 0
                    for i in range(bits):
                        dr += 2**i * int(padHex(bin(r)[2:], 8)[::-1][i:i+1])
                        dg += 2**i * int(padHex(bin(g)[2:], 8)[::-1][i:i+1])
                        db += 2**i * int(padHex(bin(b)[2:], 8)[::-1][i:i+1])
                    dr = 255//(2**bits - 1) * dr * R
                    dg = 255//(2**bits - 1) * dg * G
                    db = 255//(2**bits - 1) * db * B
                    imgIn.putpixel((x,y),(dr,dg,db))

            imgIn.save(imgOutPath, "PNG")
            print("finish!")

        elif command == "ImgSnd":
            #collect arguments and perform sanitation
            if len(sys.argv) < 12:
                raise Exception("""It seems like you're missing some arguments.
Run stego.py with no arguments for help.""")
            imgIn = Image.open(sys.argv[2]).convert("RGB")
            outPath = sys.argv[3]
            baseFreq = abs(int(sys.argv[4]))
            topFreq = abs(int(sys.argv[5]))
            exp = float(sys.argv[6])
            sines = abs(int(sys.argv[7]))
            sampperpix = abs(int(sys.argv[8]))
            volume = abs(int(sys.argv[9]))

            width, height = imgIn.size
            BITDEPTH = abs(int(sys.argv[10])) #8 bit is unsigned. everything up is signed.
            SAMPRATE = abs(int(sys.argv[11]))

            if baseFreq > SAMPRATE//2 or topFreq > SAMPRATE//2:
                print("""Either your base frequency or your top frequency exceeded
                the Nyquist frequency of your sample rate. No frequency data can be stored
                above the Nyquist frequency, so consider lowering your frequency range.""")
            elif topFreq - baseFreq <= 0:
                print("""Your top frequency ought to be higher than your base.
                If you want to flip your image, do that in an image editor.""")
            elif exp <= 0:
                print("""Exponent must be greater than zero.
                If you want to flip your image, do that in an image editor""")
            elif BITDEPTH % 8 != 0 or BITDEPTH > 32 or BITDEPTH == 0:
                print("""The Bit Depth must be a multiple of 8 and not exceed 32 to abide by
                WAVE format standards.""")
            else:
                #perform embedding
                amplitude = int((2**BITDEPTH) * 1/(10**(volume/10)))//2
                amplitude = int(amplitude/sines)
                rng = topFreq - baseFreq

                audio = wave.open(outPath, "wb")
                audio.setparams((1,BITDEPTH//8,SAMPRATE,sampperpix*width, 'NONE', 'not compressed'))

                #generate all needed sine waves first, and store in this list
                waves = []
                for w in range(sines):
                    frequency = (w/sines)**exp * rng + baseFreq
                    data = bytearray()
                    for x in range(sampperpix):
                        sample = math.sin(x/((SAMPRATE/frequency)/(2*math.pi)))
                        #basically: sample = sin[2pi*frequency/SAMPRATE(x)]
                        #therefore, period = 2pi / (2pi*frequency/SAMPRATE)
                        #                  = SAMPRATE/frequency samples
                        #T(period in s) = (SAMPRATE/frequency) / SAMPRATE
                        #T = 1/frequency. f = 1/T. f = frequency. it works.
                        temp = padHex(hex(int(sample*amplitude)+(2**BITDEPTH)//2)[2:], BITDEPTH//4)
                        data += bytearray.fromhex(temp)
                    waves.append(data)

                #identify weights per each point in image by perceived luminosity.
                weights = []
                for pixel in range(width):
                    weights.append([])
                    for w in range(sines):
                        point = (w/sines)**exp * (height-1)
                        lowPx = height - int(point) - 1
                        highPx = height - int(point+1) - 1
                        interpol = point%1

                        r,g,b = imgIn.getpixel((pixel,lowPx))
                        lowLum = luminance(r,g,b)
                        r,g,b = imgIn.getpixel((pixel,highPx))
                        highLum = luminance(r,g,b)

                        weight = (1-interpol)*lowLum + interpol*highLum
                        weights[pixel].append(weight)

                #for the duration of the image, modulate wave volumes to match weights
                output = bytearray()
                for pixel in range(width):
                    data = bytearray(sampperpix*(BITDEPTH//8))
                    for i in range(sampperpix):
                        data[i*(BITDEPTH//8)] += int("80", 16)
                    for w in range(sines):
                        for sample in range(sampperpix):
                            s = int.from_bytes(waves[w][sample*(BITDEPTH//8):sample*(BITDEPTH//8)+BITDEPTH//8], byteorder = "big", signed = False)
                            temp = int((s-(2**BITDEPTH)//2)*weights[pixel][w])
                            res = int.from_bytes(data[sample*(BITDEPTH//8):sample*(BITDEPTH//8)+BITDEPTH//8], byteorder = "big", signed = False) + temp
                            b = int.to_bytes(res, length = BITDEPTH//8, byteorder = "big")
                            for byte in range(len(b)):
                                data[sample*(BITDEPTH//8)+byte] = b[byte]
                    output += data

                if BITDEPTH != 8: #we'll have to deal with signing and 2's complement
                    for sample in range(len(output)//(BITDEPTH//8)):
                        s = int.from_bytes(output[sample*(BITDEPTH//8):sample*(BITDEPTH//8)+BITDEPTH//8], byteorder = "big", signed = False)
                        s -= (2**BITDEPTH)//2
                        if s < 0:
                            s = 2**BITDEPTH + s
                        b = int.to_bytes(s, length = BITDEPTH//8, byteorder = "little")
                        for byte in range(len(b)):
                            output[sample*(BITDEPTH//8)+byte] = b[byte]

                audio.writeframes(output)
                audio.close()
                print("finish!")
        else:
            print("Run stego.py without any arguments for help.")

if __name__ == '__main__':
    main()
