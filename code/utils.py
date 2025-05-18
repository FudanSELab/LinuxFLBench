import json
import os

def deduplicate(dirs):
    # deduplicate and keep the order
    seen = set()
    seen_add = seen.add
    return [x for x in dirs if not (x in seen or seen_add(x))]


def read_jsonl_data(data_path):
    bugs = []
    with open(data_path, "r") as f:
        lines = f.readlines()
        for line in lines:
            # line = line.replace('\\', '')
            bug = json.loads(line)
            bugs.append(bug)
    return bugs


def write_jsonl_data(data, data_path):
    with open(data_path, "w") as f:
        for d in data:
            f.write(json.dumps(d) + "\n")



def formate_predicts(predicts, original_predicts=None):
    import ast

    if isinstance(predicts, str):
        predicts = predicts.split("[", 1)[1].rsplit("]", 1)[0]
        predicts = "[" + predicts + "]"
        predicts = ast.literal_eval(predicts)

    
    if original_predicts:
        for predict in original_predicts:
            if predict not in predicts:
                predicts.append(predict)

    return predicts

def formate_json_string(json_string):

    json_string = "{" + json_string.split("{")[1].split("}")[0] + "}"
    json_string = json.loads(json_string)
    return json_string


def filter_non_exist_files(predicts, root_path):
    """
    filter the non-exist file in the predicts
    :param predicts: the predicts
    :param root_path: the root path of the project
    :return: the filtered predicts
    """
    new_predicts = []
    for predict in predicts:
        if os.path.exists(os.path.join(root_path, predict)):
            new_predicts.append(predict)
    return new_predicts


def deduplicate(dirs):
    # deduplicate and keep the order
    seen = set()
    seen_add = seen.add
    return [x for x in dirs if not (x in seen or seen_add(x))]


########################################################################

# Extract file paths from emails
import jsonlines
import glob
import json
import re
import os
import shutil
import sys


# Regular expression for matching file paths
re_rule1=re.compile(r"([A-Za-z0-9_\-/]+[A-Za-z0-9_\-/]+\.[a-z]+)\s+")

linux_main_root_V0=['boot','drivers','fs','ibcs','include','init','ipc','kernel','lib','mm','net','tools','zBoot']
linux_main_root_V1=['Documentation','arch','drivers','fs','include','init','ipc','kernel','lib','mm','net','scripts']
linux_main_root_V2=['Documentation','arch','block','crypto','drivers','firmware','fs','include','init','ipc','kernel','lib','mm','net','samples','scripts','security','sound','tools','usr','virt']
linux_main_root_V3=['Documentation','arch','block','crypto','drivers','firmware','fs','include','init','ipc','kernel','lib','mm','net','samples','scripts','security','sound','tools','usr','virt']
linux_main_root_V4=['Documentation','LICENSES','arch','block','certs','crypto','drivers','firmware','fs','include','init','ipc','kernel','lib','mm','net','samples','scripts','security','sound','tools','usr','virt']
linux_main_root_V5=['Documentation','LICENSES','arch','block','certs','crypto','drivers','fs','include','init','io_uring','ipc','kernel','lib','mm','net','samples','scripts','security','sound','tools','usr','virt']
linux_main_root_V6=['Documentation','LICENSES','arch','block','certs','crypto','drivers','fs','include','init','io_uring','ipc','kernel','lib','mm','net','rust','samples','scripts','security','sound','tools','usr','virt']
linux_dic={'0':linux_main_root_V0,'1':linux_main_root_V1,'2':linux_main_root_V2,'3':linux_main_root_V3,'4':linux_main_root_V4,'5':linux_main_root_V5,'6':linux_main_root_V6}

illegal_suffix=['.old','.orig','.fixed']


# Due to some irregularities or special cases in emails, regular expressions cannot cover all scenarios, so we manually clean up special cases again
def normalize_file_path(file_path,norm_for_mail_dataset=False):
    each_file=file_path.split('/')
    if each_file[0].isdigit() or each_file[0]=='a' or each_file[0]=='b':
        file_path=file_path[2:]
    no_alpha=True
    for c in each_file[0]:
        if c.isalpha():
            no_alpha=False
            break
    # If the file name contains only numbers and symbols but no letters, it is obviously invalid and can be removed
    if no_alpha:
        each_file.pop(0)
        file_path=''
        for file in each_file:
            file_path+=file
            file_path+='/'
        file_path=file_path[:len(file_path)-1]
    '''It is not reasonable to directly judge whether the first file in the path is standard. For example, there are file paths like t/xxx.c.
    However, if the second file in the path has the same name as one in linux_main_root, then the first file in the path is likely dirty data.'''
    linux_main_root=[]
    for i in linux_dic.keys():
        for file_name in linux_dic[i]:
            linux_main_root.append(file_name)
    if len(each_file)>1:
        if each_file[0] in linux_main_root:
            for suffix in illegal_suffix:
                if file_path.endswith(suffix):
                    file_path=file_path[:len(file_path)-len(suffix)]
            if norm_for_mail_dataset:
                if not file_path.endswith('.c') and not file_path.endswith('.h'):
                    return ''
            return file_path
        if each_file[0] not in linux_main_root and each_file[1] in linux_main_root:
            each_file.pop(0)
            file_path = ''
            for file in each_file:
                file_path += file
                file_path += '/'
            file_path = file_path[:len(file_path) - 1]
        else:
            return ''
    else:
        return ''
    for suffix in illegal_suffix:
        if file_path.endswith(suffix):
            file_path=file_path[:len(file_path)-len(suffix)]
    if norm_for_mail_dataset:
        if not file_path.endswith('.c') and not file_path.endswith('.h'):
            return ''
    return file_path

# If you want to extract file paths for building a mail dataset, set norm_for_mail_dataset to True to ensure that files not ending with .c or .h are filtered out
def extract_filepath(content,norm_for_mail_dataset=False):
    filenames = set()
    lines = content.split('\n')
    for line in lines:
        paths=re.findall(re_rule1,line)
        if len(paths)!=0:
            for path in paths:
                if path.find('i2c-ip4xx.c')!=-1:
                    a=1
                file_path=normalize_file_path(path,norm_for_mail_dataset)
                if file_path!='':
                    filenames.add(file_path)
        # Handle lines starting with +++
        if line.startswith('+++'):
            path = line.split('+++', 1)[1].strip()
            # Split the path to remove possible prefixes (such as version directories)
            parts = path.split('/', 1)
            if len(parts) > 1:
                    filename = parts[1]
            else:
                    filename = parts[0]
            filename = filename.split(' ')[0]
            filename = filename.split('\t')[0]
            filename=normalize_file_path(filename,norm_for_mail_dataset)
            if filename!='':
                filenames.add(filename)
        # Handle file names in diffstat (format: filename | statistics)
        else:
            if '/' in line and "|" in line:
                parts = line.split('|', 1)
                filename_candidate = parts[0].strip()
                stat_part = parts[1].strip()
                # Check if the statistics part starts with a number to avoid misjudgment
                if '/' in filename_candidate and re.match(r'^\d+.*', stat_part):
                    filename_candidate=normalize_file_path(filename_candidate,norm_for_mail_dataset)
                    if filename_candidate!='':
                        filenames.add(filename_candidate)
    return sorted(filenames)