#!/usr/bin/env python3

import cv2
from utils import *
from PIL import Image
import random
import pgpy

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
    col = (index // 3) % dim[1]
    val = index % 3

    img[row][col][val] = setVal(img[row][col][val], bit)
  return img

### Real Thing

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

def read_image(filepath):
  """Retrieves image.
  Params:
  filepath - string filepath
  Returns:
  image - 3 x n x m matrix representation of image
  """
  image = cv2.imread(filepath, flags=cv2.IMREAD_COLOR) # image is in opencv format
  return image

def write_image(image, filepath):
  """Writes image.
  Params:
  image - image - 3 x n x m matrix representation of image
  filepath - string of target filepath
  Returns:
  None
  """
  cv2.imwrite(filepath, image)

def generate_locations(public_key_filepath, length, max_index):
  with open(public_key_filepath, 'r') as f:
    public_key = f.read()
  pubHash = hash(public_key)
  random.seed(pubHash)
  result = random.sample(range(max_index), length)
  return result

def decode_transformed_image(transformed_image, locations):
  """Retrieves encrypted message from image.
  Params:
  transformed_image - 3 x n x m matrix representation of image
  locations - list of locations for row-major indexed image
  Returns:
  encrypted_message - string
  """

  n = transformed_image.shape[0]
  m = transformed_image.shape[1]
  bitstring = "0b"
  for l in locations:
    bitstring = bitstring + str(transformed_image[l//(3*m)][l//3%m][l%3])
  bits = int(bitstring, 2)
  encrypted_message = bits.to_bytes((bits.bit_length() + 7) // 8, 'big').decode()
  return encrypted_message

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

def sender_job(message, source_image_filepath, target_image_filepath, public_key_filepath):
  encrypted_message = encrypt(message, public_key_filepath)

  image = read_image(source_image_filepath)
  message_length = 3 * image.shape[0] * image.shape[1]

  transformed_image = transform(image)
  locations = generate_locations(public_key_filepath, message_length, message_length)
  transformed_encoded_image = encode(encrypted_message, transformed_image, locations)
  encoded_image = inverse_transform(transformed_encoded_image)

  write_image(encoded_image, target_image_filepath)

def receiver_job(encoded_image_filepath, public_key_filepath, private_key_filepath, passphrase):
  encoded_image = read_image(encoded_image_filepath)
  message_length = 3 * encoded_image.shape[0] * encoded_image.shape[1]

  transformed_encoded_image = transform(encoded_image)
  locations = generate_locations(public_key_filepath, message_length, message_length)
  encrypted_message = decode_transformed_image(transformed_encoded_image, locations)

  message = decrypt(encrypted_message, private_key_filepath, passphrase)
  return message
