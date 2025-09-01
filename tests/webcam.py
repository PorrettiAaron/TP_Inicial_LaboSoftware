import cv2
import src.utils_recognition as u_rec

database_path = "./tests/db_images/"
u_rec._save_encodings_if_necessary(database_path)
saved_encodings = u_rec.get_saved_encodings(database_path)

def _quick_comparison(my_encoding):
    print("Looking for you in the database...")
    for file_name, other_encoding in saved_encodings.items():
        d, are_the_same = u_rec.comparison(my_encoding, other_encoding)
        if are_the_same:
            print("Match with {}. Distance = {}".format(file_name, d))
    print("--------------------")

video_capture = cv2.VideoCapture(0)

while True:
    ret, frame = video_capture.read()
    small_frame = cv2.resize(frame, (0,0), fx=0.25, fy=0.25)
    encoding = u_rec.get_face_encoding_from_opencv_frame(small_frame)
    if encoding is not None:
        _quick_comparison(encoding)
    cv2.imshow("Press q to quit", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

video_capture.release()
cv2.destroyAllWindows()