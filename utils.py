from PIL import Image
from zlib import adler32

def memoize(f):
    ''' Memoization decorator for functions taking one or more arguments. '''
    class memodict(dict):
        def __init__(self, f):
            self.f = f
        def __call__(self, *args):
            return self[args]
        def __missing__(self, key):
            ret = self[key] = self.f(*key)
            return ret
    return memodict(f)

def readImage(fileName):
    ''' Read an image from fileName returns a PIL Image. '''
    return Image.open(fileName)

@memoize
def makeZeroPadder(bitsPerColor):
    def zeroPad(binary):
        assert len(binary) <= bitsPerColor
        diff = bitsPerColor - len(binary)
        return diff*'0' + binary
    return zeroPad

@memoize
def rbgToBinary(r, g, b, bitsPerColor):
    zeroPad = makeZeroPadder(bitsPerColor)
    return zeroPad(bin(r)[2:]) + zeroPad(bin(g)[2:]) + zeroPad(bin(b)[2:])

def bits_list(chars):
    '''
    Convert a string to its bits representation as a list of 0's and 1's.
    >>>  bits_list("Hello World!")
    ['01001000',
    '01100101',
    '01101100',
    '01101100',
    '01101111',
    '00100000',
    '01010111',
    '01101111',
    '01110010',
    '01101100',
    '01100100',
    '00100001']
    '''
    # Non utf8 unputs will likely completely break this.
    return [bin(ord(x))[2:].rjust(8, "0") for x in chars]

def setLSB(number, bit):
    assert bit == "1" or bit == "0", "Bad call boy."
    return number & ~1 | int(bit)

def getBinaryPixels(image):
    '''
    Reads and returns the binary values of a PIL image.

    Returns: A string representing the concatinated binary values of the image.
    Zero padding is added as needed.
    '''
    width, height = image.size
    bitsPerColor = image.bits
    imagePixels = ""

    # Only load the image into memory when we need it.
    image = image.load()

    for x in range(width):
        for y in range(height):
            r, g, b = image[x, y]
            imagePixels += rbgToBinary(r, g, b, bitsPerColor)

    return imagePixels, image

def hashing_function_that_goddamn_works_correctly(b):
    return adler32(b) & 0xffffffff # Always returns an unsigned value. "& 0xffffffff" generates the same numeric value across all Python versions and platforms
