#!/usr/bin/env python3

from utils import *
from PIL import Image
import random
import pgpy
import cv2
import traceback

ENCRYPTED_MESSAGE_LENGTH = 2048
# change to 1 if not compressing at all, super fast too
DUPLICATES = 50

# change to 1 if not compressing at all, super fast too
BIT_IDX = 3 # 0 = MSB, 7 = LSB

zeroPadder = makeZeroPadder(8)
def get_val(orig, b):
  bits = zeroPadder(bin(orig)[2:])
  return int(bits[0:BIT_IDX] + str(b) + bits[BIT_IDX + 1 :], 2)

def get_modified_bit(orig):
  bits = zeroPadder(bin(orig)[2:])
  return bits[BIT_IDX]

"""
MAIN
"""

def sender_job(message, source_image_filepath, target_image_filepath, public_key_filepath):
  encrypted_message = encrypt(message, public_key_filepath)

  image = read_image(source_image_filepath)
  shape = image_shape(image)
  message_length = ENCRYPTED_MESSAGE_LENGTH * 8 * DUPLICATES
  max_index = shape[0] * shape[1] * 3

  transformed_image = transform(image)
  locations = generate_locations(public_key_filepath, message_length, max_index)
  transformed_encoded_image = encode(encrypted_message, transformed_image, locations)
  encoded_image = inverse_transform(transformed_encoded_image)

  write_image(encoded_image, target_image_filepath)

def receiver_job(encoded_image_filepath, public_key_filepath, private_key_filepath, passphrase):
  encoded_image = read_image(encoded_image_filepath)
  shape = image_shape(encoded_image)
  message_length = ENCRYPTED_MESSAGE_LENGTH * 8 * DUPLICATES
  max_index = shape[0] * shape[1] * 3

  transformed_encoded_image = transform(encoded_image)
  locations = generate_locations(public_key_filepath, message_length, max_index)

  try:
    encrypted_message = decode_transformed_image(transformed_encoded_image, locations)
    message = decrypt(encrypted_message, private_key_filepath, passphrase)
  except Exception as e:
    traceback.print_exc()
    if 'passphrase' not in str(e).lower():
      raise Exception("{0} (image probably doesn't contain any data)".format(str(e)))
    raise e

  return message

"""
ENCRYPTION ABSTRACTIONS
"""

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

  if 'PGP' not in encrypted_message:
    raise Exception('Invalid PGP Message')

  key, _ = pgpy.PGPKey.from_file(private_key_filepath)
  msg = pgpy.PGPMessage.from_blob(encrypted_message)

  if not key.is_unlocked:
    with key.unlock(passphrase):
      decrypted_message = key.decrypt(msg)
  else:
    decrypted_message = key.decrypt(msg)

  msg = decrypted_message.message

  return bytes(msg, 'utf-8').decode('unicode_escape') # unescape string

"""
IMAGE PROCESSING (ENCODE/DECODE/TRANSFORM)
"""

def encode(encrypted_msg, img, locs):
  '''
  encrypted_msg: encrypted message
  img: cv img
  locs: locations for changing the indexes
  '''
  # encrypted_msg = str(len(encrypted_msg)) + ":" + encrypted_msg
  #converts the message into 1's and zeros.
  if len(encrypted_msg) > ENCRYPTED_MESSAGE_LENGTH:
    raise Exception('Encrypted message too long')
  # length = ENCRYPTED_MESSAGE_LENGTH
  padded_encrypted_msg = encrypted_msg + ' ' * (ENCRYPTED_MESSAGE_LENGTH - len(encrypted_msg))
  # length = ENCRYPTED_MESSAGE_LENGTH * 8
  bin_encrypted_msg = ''.join([zeroPadder(bin(ord(c))[2:]) for c in padded_encrypted_msg]) #"100100101001001"

  shape = image_shape(img)
  cols = shape[1]

  # ENCRYPTED_MESSAGE_LENGTH * 8 * DUPLICATES
  for i in range(len(bin_encrypted_msg) * DUPLICATES):
    l = locs[i]
    bit = int(bin_encrypted_msg[i % len(bin_encrypted_msg)])
    row = l // (3 * cols)
    col = (l // 3) % cols
    val = l % 3

    pixel_loc = (row, col)

    pixel = get_pixel(img, pixel_loc)
    pixel[val] = get_val(pixel[val], bit)
    set_pixel(img, pixel_loc, pixel)
  return img

def decode_transformed_image(transformed_image, locations):
  bitstring_duplicates = ['' for _ in range(DUPLICATES)]

  shape = image_shape(transformed_image)
  cols = shape[1]

  for i in range(ENCRYPTED_MESSAGE_LENGTH * 8 * DUPLICATES):
    duplicate_idx = i // (ENCRYPTED_MESSAGE_LENGTH * 8)
    l = locations[i]

    row = l // (3 * cols)
    col = (l // 3) % cols

    val = get_pixel(transformed_image, (row, col))[l % 3]
    bitstring_duplicates[duplicate_idx] += get_modified_bit(val)

  encrypted_message = ""
  curr_bitstring = ""
  for i in range(ENCRYPTED_MESSAGE_LENGTH * 8):
    bit_duplicates = [bitstring[i] for bitstring in bitstring_duplicates]
    bit = max(bit_duplicates, key=bit_duplicates.count)
    curr_bitstring += bit
    if len(curr_bitstring) == 8:
      # We've read a character.
      char_code = int(curr_bitstring, 2)
      c = chr(char_code)
      encrypted_message += c
      curr_bitstring = ""

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

def generate_locations(public_key_filepath, length, max_index):
  with open(public_key_filepath, 'rb') as f:
    public_key = f.read()
  pubHash = hashing_function_that_goddamn_works_correctly(public_key)
  random.seed(pubHash)
  result = random.sample(range(max_index), length)
  return result

### IMAGE DATA ABSTRACTIONS

def image_shape(image):
  return image.shape[:-1]
  # return image.size

def get_pixel(image, location):
  return image[location[0], location[1]]
  # return list(image.getpixel(location))

def set_pixel(image, location, rgb):
  image[location[0], location[1]] = rgb
  # image.putpixel(location, tuple(rgb))

def read_image(filepath):
  """Retrieves image.
  Params:
  filepath - string filepath
  Returns:
  image - PIL Image object
  """
  return cv2.imread(filepath)
  # return Image.open(filepath, 'r')

def write_image(image, filepath):
  """Writes image.
  Params:
  image - PIL Image object
  filepath - string of target filepath
  Returns:
  None
  """
  cv2.imwrite(filepath, image)
  # image.save(filepath)
