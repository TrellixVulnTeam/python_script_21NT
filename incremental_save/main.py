import json
import sys
import os
import shutil


# CONFIG_FILE = os.path.normpath(os.path.expanduser("~/.pysync"))
import tarfile

CONFIG_FILE = os.path.normpath(os.path.expanduser("~/Cours/Scripting/python_script/incremental_save/config.json"))


def raise_error(message, return_code=1):
    print(message)
    sys.exit(return_code)


def arguments_exists(args):
    return bool(args)


def arguments_are_valid(args):
    return len(args) == 2


def standardize_argument_input(args):
    dest_path, archive_name = os.path.split(args[1])
    return {
        "src_path": os.path.abspath(args[0]) + os.sep,
        "dest_path": os.path.abspath(dest_path) + os.sep,
        "archive_name": archive_name
    }


def load_json(json_path):
    try:
        with open(json_path, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        raise_error(f"Aucun fichier {json_path} trouvé")
    except json.JSONDecodeError:
        raise_error("Json invalide")


def json_is_valid(json_dict):
    return "src_path" in json_dict and "dest_path" in json_dict


def standardize_json_input(json_dict):
    return standardize_argument_input([json_dict["src_path"], json_dict["dest_path"]])


def input_data_is_valid(input_data):
    return os.path.isdir(input_data["src_path"]) and input_data["archive_name"]


def safe_extract_targz(dest_path, archive_name, src_path):
    """
    Extrait l'archive <archive_name> du dossier <dest_path> et renvoi le path du dossier ainsi poduit.
    Si l'archive n'existe pas, renvoi fait comme si l'archive ne contenait qu'un dossier vide
    """
    if os.path.isfile(dest_path + archive_name):
        with tarfile.open(dest_path + archive_name, "r:gz") as archive:
            def is_within_directory(directory, target):
                
                abs_directory = os.path.abspath(directory)
                abs_target = os.path.abspath(target)
            
                prefix = os.path.commonprefix([abs_directory, abs_target])
                
                return prefix == abs_directory
            
            def safe_extract(tar, path=".", members=None, *, numeric_owner=False):
            
                for member in tar.getmembers():
                    member_path = os.path.join(path, member.name)
                    if not is_within_directory(path, member_path):
                        raise Exception("Attempted Path Traversal in Tar File")
            
                tar.extractall(path, members, numeric_owner=numeric_owner) 
                
            
            safe_extract(archive, dest_path)
            basename = os.path.commonpath(archive.getnames())
        os.remove(data["dest_path"] + data["archive_name"])
    else:
        basename = src_path.split(os.sep)[-2]
        os.makedirs(os.path.join(dest_path, basename), 0o700, True)
    return os.path.join(dest_path, basename)


def rlistdir(path='.'):
    files_list = []
    for directory, sub_dir, files in os.walk(path):
        for file in files:
            files_list.append(os.path.join(directory, file))
    return files_list


def del_root(path, root):
    # print(path, root)
    path = os.path.normpath(path)
    root = os.path.normpath(root) + os.sep
    assert root in path
    assert root[-1] == os.sep
    rep = path[len(root):]
    # print(root + rep)
    # print(path)
    assert root + rep == path
    return rep


def move_item_in_list(liste: list, obj, index):
    liste.remove(obj)
    liste.insert(index, obj)
    return liste


def process_file_info(src_files, dest_files, dest_path):
    # todo: file_cmp
    for src_file, dest_file in zip(src_files, dest_files):
        if dest_file:
            os.makedirs(os.path.split(dest_file)[0], 0o700, exist_ok=True)
        if not src_file:
            print(src_file, "Supprimé")
            os.remove(dest_file)
        elif not dest_file:
            print(src_file, "Nouveau")
            shutil.copyfile(src_file, os.path.join(dest_path, os.path.split(src_file)[1]))
        elif os.path.getmtime(src_file) >= os.path.getmtime(dest_file):
            print(src_file, "Modifié")
            shutil.copyfile(src_file, dest_file)
        elif not (src_file and dest_file):
            raise SyntaxError


def zip_file_list(src_files, dest_files, src_path, untared_root):
    for i in range(max(len(src_files), len(dest_files))):
        if i >= len(src_files):
            src_files.append(None)
            continue
        if i >= len(dest_files):
            dest_files.append(None)
            continue
        src_file = del_root(src_files[i], src_path)
        dest_file = del_root(dest_files[i], untared_root)
        if src_file != dest_file:
            if os.path.join(untared_root, src_file) in dest_files:
                dest_files = move_item_in_list(dest_files, os.path.join(untared_root, src_file), i)
            else:
                dest_files.insert(i, None)
    return src_files, dest_files


if __name__ == '__main__':

    arguments = sys.argv[1:]

    if arguments:
        if not arguments_are_valid(arguments):
            raise_error("Arguments invalides")
        data = standardize_argument_input(arguments)
    else:
        json_conf = load_json(CONFIG_FILE)
        if not json_is_valid(json_conf):
            raise_error("Json invalide")
        data = standardize_json_input(json_conf)

    if not input_data_is_valid(data):
        raise_error(f"Données invalides\t:\t{data}")

    os.makedirs(data["dest_path"], 0o700, True)
    if not os.path.isdir(data["src_path"]):
        raise_error(f"La source {data['src_path']} n'existe pas ou n'est pas un dossier")

    untared_dir = safe_extract_targz(**data)
    print("kyhtf", untared_dir)
    print(data["src_path"])

    src_files, dest_files = zip_file_list(rlistdir(data["src_path"]), rlistdir(untared_dir), data["src_path"], untared_dir)

    process_file_info(src_files, dest_files, untared_dir)

    print("Synchronisation effectuée avec succès !", data)
