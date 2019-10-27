#!/usr/bin/env python3

from utils import *
from PIL import Image
import random
import pgpy
import scipy
import numpy as np
import cv2
import scipy.fftpack

"""
MAIN
"""

def sender_job(message, source_image_filepath, target_image_filepath, public_key_filepath):
  encrypted_message = encrypt(message, public_key_filepath)

  image = read_image(source_image_filepath)
  dim_change = False
  
  #if image.shape[0] % 2 != 0 or image.shape[1] % 2 != 0:
    #dim_change = True
    #new_rows = image.shape[0] + (image.shape[0] % 2)
    #new_cols = image.shape[1] + (image.shape[1] % 2)
    #image = (Image.new("RGB", (new_rows, new_cols))).paste(image)

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
  #converts the message into 1's and zeros.
  binEMess = ''.join([zeroPadder(bin(ord(c))[2:]) for c in eMess]) #"100100101001001"

  def setVal(orig, b): # LSB helper function
    if orig % 2 == 0 and b == 1:
      return orig + 1
    if orig % 2 == 1 and b == 0:
      return orig - 1
    return orig
  #now going to place in the top dct's of the image

  l = 0
  for i in range(len(binEMess)):
    for j in range(i+1):
      index = locs[l] % 3 #update later
      bit = binEMess[l]
      img[j][i-j][index] = setVal(img[j][i-j][index], bit)
      l += 1
  return img



def decode_transformed_image(transformed_image, locations):
  encrypted_message = ""
  current_bitstring = ""
  limit = None
  cols = image_shape(transformed_image)[1]

  l = 0
  for i in range(len(locations)):
    for j in range(i+1):
      index = locations[l] % 3 #update later
      col = j
      row = i - j
      val = get_pixel(transformed_image, (col, row))[index]
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
    l += 1
  return encrypted_message

def transform(image):
  """Applies discrete cosine transform to image.
  Params:
  image - 3 x n x m matrix representation of image
  Returns:
  transformed_image - 3 x n x m matrix representation of transformed image
  """
  rows = image.shape[0]
  cols = image.shape[1]
  r, g, b = cv2.split(image)

  #CODE BASED OFF OF UC BERKELEY EE123 CODE

  #making r-transform
  rfloat = np.float64(r)
  rt = np.zeros(image.shape[:2])
  for i in np.r_[:rows:8]:
    for j in np.r_[:cols:8]:
      rt[i:(i+8), j:(j+8)] = dct2(rfloat[i:(i+8), j:(j+8)])

  #making g-transform
  gfloat = np.float64(g)
  gt = np.zeros(image.shape[:2])
  for i in np.r_[:rows:8]:
    for j in np.r_[:cols:8]:
      gt[i:(i+8), j:(j+8)] = dct2(gfloat[i:(i+8), j:(j+8)])
  
  #making b-transform
  bfloat = np.float64(b)
  bt = np.zeros(image.shape[:2])
  for i in np.r_[:rows:8]:
    for j in np.r_[:cols:8]:
      bt[i:(i+8), j:(j+8)] = dct2(bfloat[i:(i+8), j:(j+8)])
  #transformed_image = (np.dstack((rt,gt,bt)) * 255)).astype(np.uint8)
  transformed_image = np.uint8(np.dstack((rt,gt,bt)) / 8.0)
  for row in transformed_image:
    print(row)
  print(np.amax(transformed_image))
  return transformed_image

def inverse_transform(transformed_image):
  """Applies discrete cosine transform to image.
  Params:
  transformed_image - 3 x n x m matrix representation of transformed image
  Returns:
  image - 3 x n x m matrix representation of image
  """
  rows = transformed_image.shape[0]
  cols = transformed_image.shape[1]
  rt, gt, bt = cv2.split(transformed_image)

  #CODE BASED OFF OF UC BERKELEY EE123 CODE

  #making r-transform
  rtfloat = np.float64(rt)

  r = np.zeros(transformed_image.shape[:2])
  for i in np.r_[:rows:8]:
    for j in np.r_[:cols:8]:
      r[i:(i+8), j:(j+8)] = idct2(rtfloat[i:(i+8), j:(j+8)])

  #making g-transform
  gtfloat = np.float64(gt)

  g = np.zeros(transformed_image.shape[:2])
  for i in np.r_[:rows:8]:
    for j in np.r_[:cols:8]:
      g[i:(i+8), j:(j+8)] = idct2(gtfloat[i:(i+8), j:(j+8)])
  
  #making b-transform
  btfloat = np.float64(bt)

  b = np.zeros(transformed_image.shape[:2])
  for i in np.r_[:rows:8]:
    for j in np.r_[:cols:8]:
      b[i:(i+8), j:(j+8)] = idct2(btfloat[i:(i+8), j:(j+8)])
  
  image = np.uint8((np.dstack((r,g,b))) * 8)
  for row in transformed_image:
    print(row)
  print(np.amax(transformed_image))
  for row in image:
    print(row)
  print(np.amax(image))

  #for i in range(rows):
  #  for j in range(cols):
  #    for v in range(3):
   #     image[i][j][v] = (image[i][j][v] + 224) % 256
  return image

def dct2(block):
  #does dct2 on block
  return cv2.dct(block)

def idct2(block):
  #does exactly what you think it does
  return cv2.idct(block)
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
