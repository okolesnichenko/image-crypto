import io
import sys

from PIL import Image, ImageDraw

import cipher
import utils


def expand_image(small_image):
    factor = 2
    px = small_image.load()
    width, height = small_image.size

    img = Image.new('RGB', (width * factor + 2, height * factor + 2), 'Black')
    pixels = img.load()
    for i in range(width):
        for j in range(height):
            pixels[factor * i, factor * j] = px[i, j]
            pixels[factor * i + 1, factor * j] = px[i, j]
            pixels[factor * i + 2, factor * j] = px[i, j]

            pixels[factor * i, factor * j + 1] = px[i, j]
            pixels[factor * i + 1, factor * j + 1] = px[i, j]
            pixels[factor * i + 2, factor * j + 1] = px[i, j]

            pixels[factor * i, factor * j + 2] = px[i, j]
            pixels[factor * i + 1, factor * j + 2] = px[i, j]
            pixels[factor * i + 2, factor * j + 2] = px[i, j]
    img = img.crop((0, 0, crop_width, crop_height))
    return img


def steganography_process(encrypted_fragment):
    conv = image.convert("RGBA").getdata()
    max_size = width * height * 3.0 / 8 / 1024

    v = utils.decompose(encrypted_fragment)
    while len(v) % 3:
        v.append(0)

    payload_size = len(v) / 8 / 1024.0
    print("Коэффициент эффективного использования: %.3f " % float(
        100 * crop_height * crop_width / (width * height)))
    if payload_size > max_size - 4:
        print("Cannot embed. File too large")
        sys.exit()

    steg_image = Image.new('RGBA', (width, height))
    data_img = steg_image.getdata()

    idx = 0
    for h in range(height):
        for w in range(width):
            (r, g, b, a) = conv.getpixel((w, h))
            if idx < len(v):
                r = utils.set_bit(r, 0, v[idx])
                g = utils.set_bit(g, 0, v[idx + 1])
                b = utils.set_bit(b, 0, v[idx + 2])
            data_img.putpixel((w, h), (r, g, b, a))
            idx = idx + 3

    steg_image.save(f"images/steg_{image_name}.png", "PNG")
    return steg_image


def get_final_image(decrypted_fragment):
    image_stream = io.BytesIO(decrypted_fragment)
    final_image = Image.open(image_stream)

    final_image = expand_image(final_image)

    x_start = int((width - crop_width) / 2)
    y_start = int((height - crop_height) / 2)

    image_copy = image.copy()
    position = (x_start, y_start)
    image_copy.paste(final_image, position)
    image_copy.save(f"images/pasted_{image_name}.{image_format}")

    return final_image


def get_encrypted_data(crypto_key, fragment_image):
    buf = io.BytesIO()
    fragment_image.save(buf, format='JPEG')
    byte_im = buf.getvalue()
    encrypt_fragment = cipher.encrypt_image(byte_im, crypto_key)
    return encrypt_fragment


def get_decrypted_data(cryptographic_key, extracting_data):
    decrypted_fragment = cipher.decrypt_image(extracting_data, cryptographic_key)
    return decrypted_fragment


def crop_image():
    # Координаты фрагмента
    x_start = int((width - crop_width) / 2)
    y_start = int((height - crop_height) / 2)
    x_stop = x_start + crop_width
    y_stop = y_start + crop_height

    fragment_image = image.crop((x_start, y_start, x_stop, y_stop))

    draw = ImageDraw.Draw(image)

    for x in range(x_start, x_stop):
        for y in range(y_start, y_stop):
            draw.point((x, y), (0, 0, 0))

    fragment_image.thumbnail((crop_width / 2, crop_height / 2), Image.ANTIALIAS)
    fragment_image.save(f"images/fragment_{image_name}.{image_format}", "JPEG")

    return fragment_image


def perform():
    compressed_fragment = crop_image()

    key_pbkdf2 = cipher.get_key_pbkdf2(key)

    encrypted_fragment = get_encrypted_data(key_pbkdf2, compressed_fragment)

    steg_image = steganography_process(encrypted_fragment)

    extracting_data = utils.extract(steg_image)
    # Дешифруем
    decrypted_fragment = get_decrypted_data(key_pbkdf2, extracting_data)

    get_final_image(decrypted_fragment)


if __name__ == '__main__':
    # оригинальное изображение
    #image_name = "fish_or_not"
    #image_format = "jpeg"
    image_name = "cat_or_dog"
    image_format = "jpg"

    image_path = f"./images/{image_name}.{image_format}"
    image = Image.open(image_path)
    # криптографический ключ
    key = "secret12"

    # расчет размера фрагмента
    croper_size = 5
    width, height = image.size
    crop_width = int(width / croper_size)
    crop_height = int(height / croper_size)

    # Основная часть
    perform()
