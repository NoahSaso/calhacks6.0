message = 'hello, how are you?'
source_image_filepath = './styles/pooh.png'
target_image_filepath = 'test_1.png'
public_key_filepath = 'test_pub.asc'
encrypted_message = encrypt(message, public_key_filepath)
image = read_image(source_image_filepath)
shape = image_shape(image)
message_length = 3 * shape[0] * shape[1]

transformed_image = transform(image)

locations = generate_locations(public_key_filepath, message_length, message_length)
transformed_encoded_image = encode(encrypted_message, transformed_image, locations)
encoded_image = inverse_transform(transformed_encoded_image)

transformed_encoded_image2 = transform(encoded_image)
#dif = np.subtract(transformed_encoded_image, transformed_encoded_image2)
#ri, gi, bi = cv2.split(dif)
#summ = cv2.countNonZero(ri) + cv2.countNonZero(gi) + cv2.countNonZero(bi)
#print(summ)
encrypted_message = decode_transformed_image(transformed_encoded_image2, locations)

#decrypt(encrypted_message, 'test_priv.asc', 'ImNaza')
