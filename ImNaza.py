#!/usr/bin/env python3

from utils import *
from PIL import Image
import random
import pgpy
import scipy
import numpy as np
import cv2
import scipy.fftpack

DUPLICATES = 50
ENCRYPTED_MESSAGE_LENGTH = 880
zeroPadder = makeZeroPadder(8)

"""
MAIN
"""

def sender_job(message, source_image_filepath, target_image_filepath, public_key_filepath):
  encrypted_message = encrypt(message, public_key_filepath)

  image = read_image(source_image_filepath)
  shape = image_shape(image)
  message_length = ENCRYPTED_MESSAGE_LENGTH * 8 * DUPLICATES
  max_length = 3 * shape[0] * shape[1]

  transformed_image = transform(image)
  locations = generate_locations(public_key_filepath, message_length, max_length)
  transformed_encoded_image = encode(encrypted_message, transformed_image, locations)
  encoded_image = inverse_transform(transformed_encoded_image)

  write_image(encoded_image, target_image_filepath)

def receiver_job(encoded_image_filepath, public_key_filepath, private_key_filepath, passphrase):
  encoded_image = read_image(encoded_image_filepath)
  shape = image_shape(encoded_image)
  message_length = ENCRYPTED_MESSAGE_LENGTH * 8 * DUPLICATES
  max_length = 3 * shape[0] * shape[1]

  transformed_encoded_image = transform(encoded_image)
  locations = generate_locations(public_key_filepath, message_length, max_length)

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

def encode(encrypted_msg, img, locs):
  '''
  encrypted_msg: encrypted message
  img: cv img
  locs: locations for changing the indexes
  '''

  def setVal(orig, b):  # LSB helper function
    orig = np.round(orig)
    if orig % 2 == 0 and b == 1:
      return orig + 1
    if orig % 2 == 1 and b == 0:
      return orig - 1
    return orig

  # encrypted_msg = str(len(encrypted_msg)) + ":" + encrypted_msg
  #converts the message into 1's and zeros.
  if len(encrypted_msg) > ENCRYPTED_MESSAGE_LENGTH:
    raise Exception('Encrypted message too long')
  # length = ENCRYPTED_MESSAGE_LENGTH
  print(len(encrypted_msg))
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

    img[row, col, val] = setVal(img[row, col, val], bit)

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

    val = transformed_image[row, col, l % 3]
    print(int(val))
    bitstring_duplicates[duplicate_idx] += str(int(val) % 2)

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
  b, g, r = cv2.split(image)

  #CODE BASED OFF OF UC BERKELEY EE123 CODE

  shape = image_shape(image)
  rows = shape[0]
  cols = shape[1]

  #making r-transform
  rfloat = np.float32(r)
  rt = np.zeros(shape)
  for i in np.r_[:rows:8]:
    for j in np.r_[:cols:8]:
      rt[i:(i+8), j:(j+8)] = dct2(rfloat[i:(i+8), j:(j+8)])

  #making g-transform
  gfloat = np.float32(g)
  gt = np.zeros(shape)
  for i in np.r_[:rows:8]:
    for j in np.r_[:cols:8]:
      gt[i:(i+8), j:(j+8)] = dct2(gfloat[i:(i+8), j:(j+8)])

  #making b-transform
  bfloat = np.float32(b)
  bt = np.zeros(shape)
  for i in np.r_[:rows:8]:
    for j in np.r_[:cols:8]:
      bt[i:(i+8), j:(j+8)] = dct2(bfloat[i:(i+8), j:(j+8)])
  #transformed_image = (np.dstack((rt,gt,bt)) * 255)).astype(np.uint8)
  transformed_image = np.dstack((rt,gt,bt)) * 255.0
  return transformed_image

def inverse_transform(transformed_image):
  """Applies discrete cosine transform to image.
  Params:
  transformed_image - 3 x n x m matrix representation of transformed image
  Returns:
  image - 3 x n x m matrix representation of image
  """

  bt, gt, rt = cv2.split(transformed_image / 255.0)

  #CODE BASED OFF OF UC BERKELEY EE123 CODE

  #making r-transform
  #rtfloat = np.float32(rt)
  rtfloat = rt

  shape = image_shape(transformed_image)
  rows = shape[0]
  cols = shape[1]

  r = np.zeros(shape)
  for i in np.r_[:rows:8]:
    for j in np.r_[:cols:8]:
      r[i:(i+8), j:(j+8)] = idct2(rtfloat[i:(i+8), j:(j+8)])

  #making g-transform
  #gtfloat = np.float32(gt)
  gtfloat = gt
  g = np.zeros(shape)
  for i in np.r_[:rows:8]:
    for j in np.r_[:cols:8]:
      g[i:(i+8), j:(j+8)] = idct2(gtfloat[i:(i+8), j:(j+8)])

  #making b-transform
  #btfloat = np.float32(bt)
  btfloat = bt
  b = np.zeros(shape)
  for i in np.r_[:rows:8]:
    for j in np.r_[:cols:8]:
      b[i:(i+8), j:(j+8)] = idct2(btfloat[i:(i+8), j:(j+8)])

  image = np.round(np.dstack((r,g,b)))

  return image

def dct2(block):
  #does dct2 on block
  return cv2.dct(block)

def idct2(block):
  #does exactly what you think it does
  return cv2.idct(block)

def generate_locations(public_key_filepath, length, max_index):
  with open(public_key_filepath, 'rb') as f:
    public_key = f.read()
  pubHash = hashing_function_that_goddamn_works_correctly(public_key)
  random.seed(pubHash)
  result = random.sample(range(max_index), length)
  return result

### IMAGE DATA ABSTRACTIONS

def image_shape(image):
  return image.shape[:-1] # ignore last dim
  # return image.size

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
