# https://github.com/RoliSoft/Steganography/blob/master/dct.hpp

import cv2
import numpy as np
from utils import makeZeroPadder

zero_padder = makeZeroPadder(8)

def make_block_generator(array, block_width, block_height):
    '''
    Makes a generator which yields blocks of size block_width x
    block_height.

    At the moment, this should ignore elements on the edge of
    arrays which are not evenly divided by block_widht/height.
    '''
    width, height = array.shape[:2]
    for x in range(0, width - block_width, block_width):
        for y in range(0, height - block_height, block_height):
            yield array[x:x + block_width, y:y+block_height]

def dct_encode(image, text, channel = 1, intensity = 30):
    '''                                                                                                                                                                                                                                      
    Uses discrete cosine transform to encode text in coefficents of
    image.

    1. Break the image up into 8x8 blocks.
    2. Perform the DCT on each block.
    3. jal encode
    4. Perform the inverse DCT on each block and reassemble into image.

    encode:
    -------
    * To encode the text in the dct, we compare the coefficents in
      positions (6, 7) and (5, 1). (6, 7) being greater than (5, 1)
      means that there is a 1 encoded, otherwise there is a zero
      encoded. We swap the coefficents to follow this endoding scheme.

    * In addition to swapping the coefficents, we also make sure that
      they are seperated by a distance of at least *intensity*. This
      is very useful for cases where (6, 7) and (5, 1) are very close
      to eachother.

    * At the moment, we also encode the message into the image as many
      times as it will fit. This means that even if jpeg breaks it
      (and it will occasionally) there are many duplicates that we can
      consider as well.

    @param image cv2 image to encode text into.
    @param text ascii text to encode into image.
    @param the channel to encode the text into, R, G, or B.
    @return a new image with the ecoded text.
    '''                                                                                                                                                                                                    
    if ( channel > 4 ):
        print("WARNING: Channel is {}. This is probably a mistake.".format(channel))
        print("         Color images typically only have three channels: R, G and B.")

    # The width and height of the blocks that we will perform the DCT                                                                                                                                                                         
    # on. The choice of 8 here is more or less standard across JPEG                                                                                                                                                                           
    # compression as far as I know.       
    block_width = 8
    block_height = 8

    width, height, _ = image.shape
    grid_width = width / block_width
    grid_height = height / block_height

    # Split image into channels. For a color image this is R, G, B.                                                                                                                                                                         
    channels = cv2.split(image)
    the_channel = channels[channel]
    
    # Convert the text to binary enforcing that its ascii only.
    bintext = ''.join([zero_padder(bin(c)[2:]) for c in bytearray(text, 'ascii')])
    text = iter(bintext)
    
    # Transform into frequency domain and swap bits as needed.
    for block in make_block_generator(the_channel, block_width, block_height):
        db = cv2.dct(block)
        a = db[6, 7]
        b = db[5, 1]

        c = next(text, None)
        if not c:
            text = iter(bintext)
            c = next(text, None)
        
        if c == '1':
            if ( a < b ):
                a, b = b, a
        if c == '0':
            if a > b:
                a, b = b, a

        # We add an intensity constant to boost the diff between
        # the two coefficents.
        if a > b:
            d = (intensity - (a - b))/2
            a += d
            b -= d
        elif a < b:
            d = (intensity - (b - a))/2
            a -= d
            b += d
        # In the a == b case we just want to nudge them in the right
        # direction. Not doing this will lead to bad decoding.
        elif a == b:
            if c == '1':
                a += intensity / 2
                b -= intensity / 2
            if c == '0':
                b += intensity / 2
                a -= intensity / 2
                
        db[6, 7] = a
        db[5, 1] = b
        block[:, :] = cv2.idct(db)
            
    # Stack channels back together.
    channels[channel] = the_channel
    
    # Normalize values.
    return np.dstack(channels)

def dct_decode(image, channel = 1):
    '''
    Recovers a message from the channels of the DCT of an image.

    1. Break the image up into 8x8 blocks.
    2. Perform the DCT on each block.
    3. jal decode
    4. Convert the binary into a string.

    decode:
    -------
    * To decode the text, we move over the blocks. If the coefficent
      in position (6, 7) is greater than the one in (5, 1) the block
      contains a 1, otherwise a zero.

    TODO: At the moment, this method has no way to average across
    repitions added by dct_encode and just prints the whole block of
    text. We should explore automating the extraction of the stored
    text.
    '''
    if ( channel > 4 ):
        print("WARNING: Channel is {}. This is probably a mistake.".format(channel))
        print("         Color images typically only have three channels: R, G and B.")

    # The width and height of the blocks that we will perform the DCT                                                                                                                                                                         
    # on. The choice of 8 here is more or less standard across JPEG                                                                                                                                                                           
    # compression as far as I know.       
    block_width = 8
    block_height = 8

    width, height, _ = image.shape
    grid_width = width / block_width
    grid_height = height / block_height

    # Split image into channels. For a color image this is R, G, B.                                                                                                                                                                         
    channels = cv2.split(image)
    the_channel = channels[channel]
    
    text = ''
    # Transform into frequency domain and swap bits as needed.
    for block in make_block_generator(the_channel, block_width, block_height):
        db = cv2.dct(block)
        a = db[6, 7]
        b = db[5, 1]
        
        if a <= b:
            text += '0'
        else:
            text += '1'
    
    # Convert text into string.
    # Break into 8 bit chunks
    chunks = [text[x:x + 8] for x in range(0, len(text), 8)]
    
    return ''.join([chr(int(c, 2)) for c in chunks])
