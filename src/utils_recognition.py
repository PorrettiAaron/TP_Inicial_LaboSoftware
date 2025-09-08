import face_recognition
import pickle
import os
import utils_files

class MultipleFacesDetectedException(Exception):
    def __init__(self):
        super().__init__("Se detectaron múltiples caras en la imagen actual, cuando se esperaba solo una")

ENCODINGS_FILE = ".already_computed_face_encodings.pkl"

ACCEPTABLE_IMAGE_EXTENSIONS = ["jpg", "jpeg", "png", "webp", "bmp"]

EUCLIDEAN_DISTANCE_TOLERANCE = 0.6

def get_encodings_file_path(database_path):
    return os.path.join(database_path, ENCODINGS_FILE)

def get_saved_encodings(database_path):
    _enc_file = get_encodings_file_path(database_path)
    if not os.path.exists(_enc_file):
        return {}
    try:
        with open(_enc_file, mode="rb") as f:
            return pickle.load(f)
    except EOFError:
        return {}

def _set_new_encodings(encodings, database_path):
    with open(get_encodings_file_path(database_path), mode="wb") as f:
            pickle.dump(encodings, f)

def _save_encodings_if_necessary(database_path):
    images = os.listdir(database_path)
    if not images:
        return
    encodings = get_saved_encodings(database_path)
    for image in images:
        if not utils_files.is_valid_image(image) or image in encodings:
            continue
        encodings[image] = get_face_encoding(os.path.join(database_path, image))
    _set_new_encodings(encodings, database_path)

def get_face_location(image):
    if image is None:
        return None
    if isinstance(image, str):
        image = face_recognition.load_image_file(image)
    face_locations = face_recognition.face_locations(image)
    if not face_locations:
        return None
    if len(face_locations) > 1:
        raise MultipleFacesDetectedException()
    return face_locations

def get_face_encoding(image, known_location=None):
    if image is None:
        return None
    if isinstance(image, str):
        image = face_recognition.load_image_file(image)
    faces = face_recognition.face_encodings(image, known_face_locations=known_location)
    if not faces:
        return None
    if len(faces) > 1:
        raise MultipleFacesDetectedException()
    return faces[0]

def _euclidean_distance(face1_encoding, face2_encoding):
    return face_recognition.face_distance([face1_encoding], face2_encoding)[0]

def comparison(face1_encoding, face2_encoding, tolerance=EUCLIDEAN_DISTANCE_TOLERANCE):
    euclidean_distance = _euclidean_distance(face1_encoding, face2_encoding)
    return euclidean_distance, euclidean_distance <= tolerance