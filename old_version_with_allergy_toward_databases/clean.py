import shutil
import common

folder_for_removal = common.reload_queries_location()
try:
    shutil.rmtree(folder_for_removal)
except FileNotFoundError:
    print(folder_for_removal + " was not found")

folder_for_removal = common.found_errors_storage_location()
try:
    shutil.rmtree(folder_for_removal)
except FileNotFoundError:
    print(folder_for_removal + " was not found")
