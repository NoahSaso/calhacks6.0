#!/usr/bin/env python3

from utils import *
from PIL import Image
import random
import pgpy
import cv2
import traceback
import time

# change to 1 if not compressing at all, super fast too
BIT_IDX = 3  # 0 = MSB, 7 = LSB

# use 7 bits for encrypted message chars because ASCII max value is 127 and encrypted_msg is ASCII-armored PGP message
ENCRYPTED_MESSAGE_CHAR_BITS = 7
zeroPadderEncrypted = makeZeroPadder(ENCRYPTED_MESSAGE_CHAR_BITS)

zeroPadderRGB = makeZeroPadder(8)  # 8 bits for rgb 255

def get_val(orig, b):
  bits = zeroPadderRGB(bin(orig)[2:])
  return int(bits[0:BIT_IDX] + str(b) + bits[BIT_IDX + 1:], 2)

def get_modified_bit(orig):
  bits = zeroPadderRGB(bin(orig)[2:])
  return bits[BIT_IDX]

"""
MAIN
"""

def sender_job(message, source_image_filepath, target_image_filepath, public_key_filepath):
  encrypted_message = encrypt(message, public_key_filepath)

  image = read_image(source_image_filepath)
  shape = image_shape(image)
  number_of_values = shape[0] * shape[1] * 3

  transformed_image = transform(image)
  random_location_generator = create_random_location_generator(public_key_filepath, number_of_values)

  try:
    transformed_encoded_image = encode(encrypted_message, transformed_image, random_location_generator)
  except Exception as e:
    traceback.print_exc()
    raise e

  encoded_image = inverse_transform(transformed_encoded_image)

  write_image(encoded_image, target_image_filepath)

def receiver_job(encoded_image_filepath, public_key_filepath, private_key_filepath, passphrase):
  encoded_image = read_image(encoded_image_filepath)
  shape = image_shape(encoded_image)
  number_of_values = shape[0] * shape[1] * 3

  transformed_encoded_image = transform(encoded_image)
  random_location_generator = create_random_location_generator(public_key_filepath, number_of_values)

  try:
    encrypted_message = decode_transformed_image(transformed_encoded_image, random_location_generator)
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

  return str(encrypted_message).encode('unicode_escape').decode('utf-8')

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
  print(encrypted_message.encode('utf-8').decode('unicode_escape'))
  msg = pgpy.PGPMessage.from_blob(encrypted_message.encode('utf-8').decode('unicode_escape')) # unescape string

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

def encode(encrypted_msg, img, random_location_generator):
  '''
  encrypted_msg: encrypted message
  img: cv img
  random_location_generator: generator function that spits out a unique location each time
  '''
  # converts the message into 1's and zeros.
  bin_encrypted_msg = ''.join([zeroPadderEncrypted(bin(ord(c))[2:]) for c in encrypted_msg]) #"100100101001001"

  shape = image_shape(img)
  cols = shape[1]

  for i, l in enumerate(random_location_generator):
    bit = int(bin_encrypted_msg[i % len(bin_encrypted_msg)])
    row = l // (3 * cols)
    col = (l // 3) % cols
    val = l % 3

    pixel_loc = (row, col)

    pixel = get_pixel(img, pixel_loc)
    pixel[val] = get_val(pixel[val], bit)
    set_pixel(img, pixel_loc, pixel)
  return img

def find_all(s, sub):
  start = 0
  while True:
    start = s.find(sub, start)
    if start == -1: return
    yield start
    start += len(sub) # use start += 1 to find overlapping matches

def decode_transformed_image(transformed_image, random_location_generator):
  encoded_bits = ''

  shape = image_shape(transformed_image)
  cols = shape[1]

  for l in random_location_generator:
    row = l // (3 * cols)
    col = (l // 3) % cols

    val = get_pixel(transformed_image, (row, col))[l % 3]
    encoded_bits += get_modified_bit(val)

  bitstrings = [''.join(bitstring) for bitstring in zip(*[iter(encoded_bits)] * ENCRYPTED_MESSAGE_CHAR_BITS)]
  ascii_from_encoded_bits = ''.join([chr(int(bitstring, 2)) for bitstring in bitstrings])

  ### BASED ON KNOWING PGP EXISTS
  all_idxs = list(find_all(ascii_from_encoded_bits, 'BEGIN PGP'))
  diffs_in_idx = [all_idxs[i + 1] - all_idxs[i] for i in range(len(all_idxs) - 1)]
  print(diffs_in_idx)
  encrypted_message_length = min(diffs_in_idx)
  print(encrypted_message_length)

  ### BASED ON FINDING SIMILAR SEQUENCES:

  # max_run_len_found = None
  # diffs_btw_max_run_size = []

  # MIN_LENGTH = 500

  # min_run = 10
  # max_run = 11
  # len_data = len(ascii_from_encoded_bits)
  # for run_len in range(min_run, max_run):
  #   i = 0
  #   while i < len_data - run_len * 2:
  #     run1 = ascii_from_encoded_bits[i:i + run_len]
  #     j = i + run_len + MIN_LENGTH
  #     while j < len_data - run_len:
  #       run2 = ascii_from_encoded_bits[j: j + run_len]
  #       print(run1, run2)
  #       if run1 == run2:
  #         print(run_len, run1)
  #         if not max_run_len_found or run_len > max_run_len_found:
  #           max_run_len_found = run_len
  #           diffs_btw_max_run_size = []
  #         else:
  #           diffs_btw_max_run_size.append(j - i)
  #           print(j - i)
  #         j += run_len
  #       else:
  #         j += 1
  #     i += 1

  # print(max_run_len_found)
  # print(diffs_btw_max_run_size)

  # encrypted_message_length = max(diffs_btw_max_run_size)

  # exit(1)

  ### BASED ON A PREFIX:

  # zip(*[iter(l)]*n) = [(first n elements of l), (second n elements of l), ...]
  # if list length not divisible by n, will ignore excess values at end:
  ## if l = [1, 2, 3, 4, 5] and n = 2, output = [(1, 2), (3, 4)]
  # bitstrings = [''.join(bitstring) for bitstring in zip(*[iter(encoded_bits)] * ENCRYPTED_MESSAGE_CHAR_BITS)]
  # ascii_from_encoded_bits = [chr(int(bitstring, 2)) for bitstring in bitstrings]

  # idxs_of_prefix = [i for i, x in enumerate(ascii_from_encoded_bits) if x == PREFIX]
  # diffs_in_idx_of_prefix = [idxs_of_prefix[i + 1] - idxs_of_prefix[i] for i in range(len(idxs_of_prefix) - 1)]

  # encrypted_message_length = max(diffs_in_idx_of_prefix)

  # floor divide because end contains start of another repetition that makes this not divide evenly
  duplicates = len(bitstrings) // encrypted_message_length
  extra_data_length = len(bitstrings) % encrypted_message_length

  encrypted_message = ''
  for i in range(encrypted_message_length):
    bitstring_dupes = [bitstrings[j * encrypted_message_length + i] for j in range(duplicates)]

    # use extra data if we've encoded up to this part of the message
    if i < extra_data_length:
      bitstring_dupes += [bitstrings[duplicates * encrypted_message_length + i]]

    bitstr = ''
    for j in range(ENCRYPTED_MESSAGE_CHAR_BITS):
      bit_dupes = [dup[j] for dup in bitstring_dupes]
      bit = max(bit_dupes, key=bit_dupes.count)
      bitstr += bit
    encrypted_message += chr(int(bitstr, 2))

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

def create_random_location_generator(public_key_filepath, number_of_values):
  with open(public_key_filepath, 'rb') as f:
    public_key = f.read()
  public_key_hash = hashing_function_that_goddamn_works_correctly(public_key)
  random.seed(public_key_hash)
  return sample_gen(number_of_values)

# https://stackoverflow.com/a/18994897
def sample_gen(n):#, forbid):
  state = dict()
  # track = dict()
  # for i, o in enumerate(forbid):
  #   x = track.get(o, o)
  #   t = state.get(n - i - 1, n - i - 1)
  #   state[x] = t
  #   track[t] = x
  #   state.pop(n - i - 1, None)
  #   track.pop(o, None)
  # del track
  for remaining in range(n, 0, -1):  #- len(forbid), 0, -1):
    i = random.randrange(remaining)
    yield state.get(i, i)
    state[i] = state.get(remaining - 1, remaining - 1)
    state.pop(remaining - 1, None)

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
