import os
import random


def create_tmp_dir(prefix: str = None):
    prefix = prefix or ''

    dir_path = os.path.join('/tmp', prefix, str(random.random())[2:8])
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)
    return dir_path


def get_file_dir(file_abspath: str, *relative_paths) -> str:
    """example: get_file_dir(__file__, '..', '..',...)"""

    return os.path.abspath(os.path.join(
        *[os.path.dirname(file_abspath)] + list(relative_paths)
    ))
