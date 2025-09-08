import os.path

ACCEPTABLE_IMAGE_EXTENSIONS = ["jpg", "jpeg", "png", "webp", "bmp"]

def get_file_extension(file_name):
    return os.path.splitext(file_name)[1][1:]

def is_valid_image_extension(ext):
    return ext in ACCEPTABLE_IMAGE_EXTENSIONS

def is_valid_image(file_name):
    return is_valid_image_extension(get_file_extension(file_name))