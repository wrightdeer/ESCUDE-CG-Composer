import os

from lsfInfo import LSFFile


def parse_lsf_files(dir_path):
    files = os.listdir(dir_path)
    valid_files = []
    invalid_files = []

    for file in files:
        if file.endswith(".lsf"):
            file_path = os.path.join(dir_path, file)
            try:
                lsf_file = LSFFile(file_path)
                keys = lsf_file.get_base_images_keys()
                print(lsf_file.get_name())
                print(lsf_file.get_base_images_keys())
                print(lsf_file.get_face_differences_keys())
                print(lsf_file.get_face_effects_keys())
                print(lsf_file.get_holy_light_keys())
                valid_files.append(file)
            except Exception as e:
                invalid_files.append(file)
                print(f"Error processing file {file}: {e}")

    print(f"Valid files: {valid_files}")
    print(f"Invalid files: {invalid_files}")


parse_lsf_files('data/ev_1')
