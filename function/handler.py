import tempfile
import os
from git import Repo
import json
import shutil
import toml
from .logs import MergeLogs

def handle(req):
    """handle a request to the function
    Args:
        req (str): request body
    """

    conf = read_conf()

    result_logs = MergeLogs("/tmp/result.log")

    try:

        with tempfile.TemporaryDirectory() as temp_dir_path, result_logs as logs_write:

            logs_write.add_log("New import")

            left_repo = Repo.clone_from(
                conf["leftRepo"], 
                os.path.join(temp_dir_path, conf["leftRepoName"]), 
                branch="master"
            )

            right_repo = Repo.clone_from(
                conf["rightRepo"], 
                os.path.join(temp_dir_path, conf["rightRepoName"]), 
                branch="master"
            )

            final_repo = Repo.clone_from(
                conf["finalRepo"].format(os.getenv("GITHUB_TOKEN", default="DEFAULT")), 
                os.path.join(temp_dir_path, conf["finalRepoName"]), 
                branch="master"
            )

            if final_repo.head.commit.message == f"Merge: {left_repo.head.commit.hexsha[:7]} / {right_repo.head.commit.hexsha[:7]}":

                logs_write.add_log("This commits have been already merged")

                return {
                    "error": True,
                    "message": "Merge for this commits already done"
                }

            logs_write.add_log(f"Core repo - commit: {left_repo.head.commit.hexsha[:7]}")
            logs_write.add_log(f"Internal repo - commit: {left_repo.head.commit.hexsha[:7]}")

            # Start by merge all the folder write in the config
            for folder in conf["folderToMerge"]:

                temp_folder = os.path.join(temp_dir_path, conf["finalRepoName"], folder)

                make_empty_dir(temp_folder)

                logs_write.add_log(f"Merge {folder} folder")

                resultCore = merge_folder(os.path.join(temp_dir_path, conf["leftRepoName"], folder), temp_folder)
                resultInternal = merge_folder(os.path.join(temp_dir_path, conf["rightRepoName"], folder), temp_folder)

                add_merge_result_to_log(logs_write, resultCore, resultInternal)

            # Merge all the config folder in config file
            for folder in conf["configFolderToSearch"]:

                temp_final_folder = os.path.join(temp_dir_path, conf["finalRepoName"], "config", folder)

                temp_left_folder = os.path.join(temp_dir_path, conf["leftRepoName"], "config", folder)
                temp_right_folder = os.path.join(temp_dir_path, conf["rightRepoName"], "config", folder)

                if not os.path.exists(temp_final_folder):
                
                    os.makedirs(temp_final_folder)

                # Merge all the file write in the config file
                for config in conf["configToMerge"]:

                    merge_left = toml.load(os.path.join(temp_left_folder, config))
                    merge_right = toml.load((os.path.join(temp_right_folder, config)))

                    with open(os.path.join(temp_final_folder, config), "w+") as f:

                        toml.dump(merge_config_menu_file(merge_left, merge_right), f)

            # Finaly commit the final result
            final_repo.git.add(A=True)
            final_repo.index.commit(f"Merge: {left_repo.head.commit.hexsha[:7]} / {right_repo.head.commit.hexsha[:7]}")
            final_repo.git.push('origin', "master")

            return {
                "error": False,
                "commitNumber": final_repo.head.commit.hexsha
            }
   
    except Exception as e:

        return {
            "error": True,
            "message": e
        }

    

    return req

def make_empty_dir(path: str):
    """Check if a folder exist
        If yes delete it
        If no do nothing
        Then create the folder
    """

    if os.path.exists(path):
                    
        shutil.rmtree(path)

    os.mkdir(path)

def add_merge_result_to_log(logs: MergeLogs, resultCore: dict, resultInternal: dict):

    logs.add_log(f"file merged: {resultCore['fileMerged'] + resultInternal['fileMerged']}")
    logs.add_log(f"Directory Created: {resultCore['directoryCreated'] + resultInternal['directoryCreated']}")
    logs.add_log("Conflict file:")

    for num, file in enumerate(resultInternal['conflictFile'], start=1):

        logs.add_log(f"    {num}. {file}")


def read_conf():

    with open(os.getenv("CONFIG_PATH", default="/opt/conf/config.json"), "r") as f:

        return json.load(f)

def merge_folder(root_src_dir, root_dst_dir):

    result = {
        "fileMerged": 0,
        "directoryCreated": 0,
        "conflictFile": []
    }

    for src_dir, dirs, files in os.walk(root_src_dir):
        dst_dir = src_dir.replace(root_src_dir, root_dst_dir, 1)
        if not os.path.exists(dst_dir):
            os.makedirs(dst_dir)
            result["directoryCreated"] = result["directoryCreated"] + 1

            # print("make dir", dst_dir)
        for file_ in files:
            src_file = os.path.join(src_dir, file_)
            dst_file = os.path.join(dst_dir, file_)

            if os.path.exists(dst_file):

                os.remove(dst_file)
                result["conflictFile"].append(dst_file)


            result["fileMerged"] = result["fileMerged"] + 1
            shutil.copy(src_file, dst_dir)

    return result

def merge_config_menu_file(dict1, dict2):
    
    dict3 = {**dict1, **dict2}

    for key, value in dict3.items():

        if key in dict1 and key in dict2:

               dict3[key] = dict1[key] + dict2[key]

    return dict3