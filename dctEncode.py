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

def dct_encode(image, text, channel = 1):
    '''                                                                                                                                                                                                                                      
    Uses discrete cosine transform to encode text in coefficents of
    image.

    1. Break the image up into 8x8 blocks.
    2. Perform the DCT on each block.
    3. For each block, compare the coefficents in positions (6, 7) and
       (5, 1).
        - If (6, 7) = (5, 1), carry on.
        - If (6, 7) > (5, 1) the encoded bit is a 1.
        - Otherwise, the encoded bit is a zero.
    4. Swap the coefficents to properly encode the value needed.

    @param image cv2 image to encode text into.
    @param text ascii text to encode into image.
    @param the channel to encode the text into, R, G, or B.
    @return a new image with the ecoded text.
    
    TODO(zeke/noah): This function needs repition and / or a way to
    indicate the length of the encoded string. I think repitition is a
    nice way to go. I beleive that @noah has a couple ideas on how to
    best add that. At the moment it just encodes the message in the
    first blocks and decodes everyhing.

    TODO: We need to think more about the case where a == 0 and a is
    close to b. These cases are currently pretty vunreable to
    compression issues. One idea is to enforce that there be a
    distance of at least I between a and b. After things have all been
    calculated, we could add and subtract as appropriate to maintin
    that distance.
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
    text = ''.join([zero_padder(bin(c)[2:]) for c in bytearray(text, 'ascii')])
    text = iter(text)
    # Transform into frequency domain and swap bits as needed.
    for block in make_block_generator(the_channel, block_width, block_height):
        db = cv2.dct(block)
        a = db[6, 7]
        b = db[5, 1]
        if ( a != b):
            c = next(text, None)
            if not c:
                break
                
            if c == '1':
                if ( a < b ):
                    db[6, 7], db[5, 1] = db[5, 1], db[6, 7]
            if c == '0':
                if ( a > b):
                    db[6, 7], db[5, 1] = db[5, 1], db[6, 7]
                
        block[:, :] = cv2.idct(db)
            
    # Stack channels back together.
    channels[channel] = the_channel
    return np.dstack(channels)

def dct_decode(image, channel = 1):
    '''
    Recovers a message from the channels of the DCT of an image.
    
    1. Break the image up into 8x8 blocks.
    2. Perform the DCT on each block.
    3. For each block, compare the coefficents in positions (6, 7) and
       (5, 1).
        - If (6, 7) = (5, 1), carry on.
        - If (6, 7) > (5, 1) the encoded bit is a 1.
        - Otherwise, the encoded bit is a zero.
    4. Swap the coefficents to properly encode the value needed.
    '''
    if ( channel > 4 ):
        print("WARNING: Channel is {}. This is probably a mistake.".format(channel))
        print("         Color images typically only have three channels: R, G and B.")

    # The width and height of the blocks that we will perform the DCT                                                                                                                                                                            # on. The choice of 8 here is more or less standard across JPEG                                                                                                                                                                           
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
        
        if a != b:
            if a < b:
                text += '0'
            else:
                text += '1'
    
    # Convert text into string.
    # Break into 8 bit chunks
    chunks = [text[x:x + 8] for x in range(0, len(text), 8)]
    
    return ''.join([chr(int(c, 2)) for c in chunks])
