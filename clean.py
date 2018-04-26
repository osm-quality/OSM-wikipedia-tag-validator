import shutil
import common

folder_for_removal = common.get_file_storage_location() + "/reload_querries"
try:
    shutil.rmtree(folder_for_removal)
except FileNotFoundError:
    print(folder_for_removal + " was not found")