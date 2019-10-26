import numpy as np
import cv2
from utils import *
from PIL import Image
import random

def encode(eMess, img, locs):
  '''
  eMess: encrypted message
  img: cv img
  locs: locations for changing the indexes
  '''
  dim = img.shape
  zeroPadder = makeZeroPadder(8)
  #converts the message into 1's and zeros.
  binEMess = ''.join([zeroPadder(bin(ord(c))[2:]) for c in eMess]) #"100100101001001"

  def setVal(orig, b): # LSB helper function
    if orig % 2 == 0 and b == 1:
      return orig + 1
    if orig % 2 == 1 and b == 0:
      return orig - 1
    return orig

  for i in range(len(locs)):
    index = locs[i]
    bit = int(binEMess[i])
    row = index // (3 * dim[1])
    col = (index // 3) % dim[1])
    val = index % 3

    img[row][col][val] = setVal(img[row][col][val], bit)
  return img

### Real Thing

def encrypt(message, public_key):
  """Applies PGP encryption to message.
  Params:
  message - string
  public_key - string
  Returns:
  encrypted_message - string
  """
  return encrypted_message

def transform(image):
  """Applies discrete cosine transform to image.
  Params:
  image - 3 x n x m matrix representation of image
  Returns:
  transformed_image - 3 x n x m matrix representation of transformed image
  """
  image = transformed_image
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

def read_image(filepath):
  """Retrieves image.
  Params:
  filepath - string filepath
  Returns:
  image - 3 x n x m matrix representation of image
  """
  return image

def write_image(image, filepath):
  """Writes image.
  Params:
  image - image - 3 x n x m matrix representation of image
  filepath - string of target filepath
  Returns:
  None
  """
  return None

def generate_locations(public_key, length, max_index):
  pubHash = hash(public_key)
  random.seed(pubHash)
  result = random.sample(range(max_index), length)
  return locations

def decode_transformed_image(transformed_image, locations):
  """Retrieves encrypted message from image.
  Params:
  transformed_image - 3 x n x m matrix representation of image
  locations - list of locations for row-major indexed image
  Returns:
  encrypted_message - string
  """
  return encrypted_message

def decrypt(encrypted_message, public_key):
  """Decrypts encrypted message.
  Params:
  encrypted_message - string
  public_key - string
  Returns:
  decrypted_message - string
  """
  return decrypted_message

def sender_job(message, source_image_filepath, target_image_filepath, public_key):
  encrypted_message = encrypt(message, public_key)
  image = read_image(source_image_filepath)
  message_length = 3 * image.shape[1] * image.shape[2]
  transformed_image = transform(image)
  locations = generate_locations(public_key, message_length)
  transformed_encoded_image = encode(encrypted_message, transformed_image, locations)
  encoded_image = inverse_transform(transformed_encoded_image)
  write_image(encoded_image, target_image_filepath)

def receiver_job(encoded_image, public_key, private_key):
  transformed_encoded_image = transform(encoded_image)
  locations = generate_locations(public_key)
  encrypted_message = decode_transformed_image(transformed_encoded_image, locations)
  message = decrypt(encrypted_message, private_key)
  return message
