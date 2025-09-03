import os
import src.utils_recognition as u_rec

main_img = "./tests/img_test.jpg"
database_path = "./tests/db_images/"

u_rec._save_encodings_if_necessary(database_path)
database_encodings = u_rec.get_saved_encodings(database_path)

main_img_encoding = u_rec.get_face_encoding(main_img)
matches = []

for file_name, person_encoding in database_encodings.items():
    d, are_the_same_person = u_rec.comparison(main_img_encoding, person_encoding)
    if are_the_same_person:
        matches.append((os.path.join(database_path, file_name), d))

if matches:
    print("Matches found with {}: ".format(main_img))
    for file, distance in matches:
        print("  {}, distance = {}".format(file, distance))
else:
    print("No matches found")