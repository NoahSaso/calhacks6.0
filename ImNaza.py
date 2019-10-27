#!/usr/bin/env python3

from utils import *
from PIL import Image
import random
import pgpy

"""
MAIN
"""

def sender_job(message, source_image_filepath, target_image_filepath, public_key_filepath):
  encrypted_message = encrypt(message, public_key_filepath)

  image = read_image(source_image_filepath)
  shape = image_shape(image)
  message_length = 3 * shape[0] * shape[1]

  transformed_image = transform(image)
  locations = generate_locations(public_key_filepath, message_length, message_length)
  transformed_encoded_image = encode(encrypted_message, transformed_image, locations)
  encoded_image = inverse_transform(transformed_encoded_image)

  write_image(encoded_image, target_image_filepath)

def receiver_job(encoded_image_filepath, public_key_filepath, private_key_filepath, passphrase):
  encoded_image = read_image(encoded_image_filepath)
  shape = image_shape(encoded_image)
  message_length = 3 * shape[0] * shape[1]

  transformed_encoded_image = transform(encoded_image)
  locations = generate_locations(public_key_filepath, message_length, message_length)

  try:
    encrypted_message = decode_transformed_image(transformed_encoded_image, locations)
    message = decrypt(encrypted_message, private_key_filepath, passphrase)
  except Exception as e:
    raise e

  return message

"""
ENCRYPTION ABSTRACTIONS
"""

UNIQUE_END_DELIMITER = '\n-----END PGP MESSAGE-----\n'

def encrypt(message, public_key_filepath):
  """Applies PGP encryption to message.
  Params:
  message - string
  public_key_filepath - string
  Returns:
  encrypted_message - string
  """

  key, _ = pgpy.PGPKey.from_file(public_key_filepath)
  msg = pgpy.PGPMessage.new(message)

  encrypted_message = key.encrypt(msg)

  return str(encrypted_message)

def decrypt(encrypted_message, private_key_filepath, passphrase):
  """Decrypts encrypted message.
  Params:
  encrypted_message - string
  private_key_filepath - string
  Returns:
  decrypted_message - string
  """

  key, _ = pgpy.PGPKey.from_file(private_key_filepath)
  msg = pgpy.PGPMessage.from_blob(encrypted_message)

  if not key.is_unlocked:
    with key.unlock(passphrase):
      decrypted_message = key.decrypt(msg)
  else:
    decrypted_message = key.decrypt(msg)

  return decrypted_message.message

"""
IMAGE PROCESSING (ENCODE/DECODE/TRANSFORM)
"""

def encode(eMess, img, locs):
  '''
  eMess: encrypted message
  img: cv img
  locs: locations for changing the indexes
  '''
  dim = image_shape(img)
  zeroPadder = makeZeroPadder(8)
  eMess = str(len(eMess)) + ":" + eMess
  #converts the message into 1's and zeros.
  binEMess = ''.join([zeroPadder(bin(ord(c))[2:]) for c in eMess]) #"100100101001001"

  def setVal(orig, b): # LSB helper function
    if orig % 2 == 0 and b == 1:
      return orig + 1
    if orig % 2 == 1 and b == 0:
      return orig - 1
    return orig

  for i in range(len(binEMess)):
    l = locs[i]
    bit = int(binEMess[i])
    row = l // (3 * dim[1])
    col = (l // 3) % dim[1]
    val = l % 3

    pixel_loc = (col, row)

    pixel = get_pixel(img, pixel_loc)
    pixel[val] = setVal(pixel[val], bit)
    set_pixel(img, pixel_loc, pixel)
  return img

def decode_transformed_image(transformed_image, locations):
  encrypted_message = ""
  current_bitstring = ""
  limit = None
  cols = image_shape(transformed_image)[1]

  for l in locations:
    row = l // (3 * cols)
    col = (l // 3) % cols

    val = get_pixel(transformed_image, (col, row))[l % 3]
    val_bit = val % 2
    current_bitstring += str(val_bit)
    if len(current_bitstring) == 8:
      # We've read a character.
      char_code = int(current_bitstring, 2)
      c = chr(char_code)
      encrypted_message += c
      current_bitstring = ""

      if not limit and c == ":":
        # We've found the header
        try:
          limit = int(encrypted_message[:-1])
        except:
          raise Exception('Bad length')

      # add/sub 1 because of the colon
      if len(encrypted_message) - len(str(limit)) - 1 == limit:
        return encrypted_message[len(str(limit)) + 1 :]
  return encrypted_message

def transform(image):
  """Applies discrete cosine transform to image.
  Params:
  image - 3 x n x m matrix representation of image
  Returns:
  transformed_image - 3 x n x m matrix representation of transformed image
  """
  transformed_image = image
  return transformed_image

def inverse_transform(transformed_image):
  """Applies discrete cosine transform to image.
  Params:
  transformed_image - 3 x n x m matrix representation of transformed image
  Returns:
  image - 3 x n x m matrix representation of image
  """
  image = transformed_image
  return image

# TODO: pass in more accurate length to this function later,
# but for now it just gets the all rgb values * 3 (So all possible bytes)
def generate_locations(public_key_filepath, length, max_index):
  with open(public_key_filepath, 'r') as f:
    public_key = f.read()
  pubHash = hash(public_key)
  random.seed(pubHash)
  result = random.sample(range(max_index), length)
  return result

### IMAGE DATA ABSTRACTIONS

def image_shape(image):
  return image.size

def get_pixel(image, location):
  return list(image.getpixel(location))

def set_pixel(image, location, rgb):
  return image.putpixel(location, tuple(rgb))

def read_image(filepath):
  """Retrieves image.
  Params:
  filepath - string filepath
  Returns:
  image - 3 x n x m matrix representation of image
  """
  return Image.open(filepath, 'r')

def write_image(image, filepath):
  """Writes image.
  Params:
  image - image - 3 x n x m matrix representation of image
  filepath - string of target filepath
  Returns:
  None
  """
  image.save(filepath, 'PNG')
