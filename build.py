#!/usr/bin/env python
#
# SPDX-FileCopyrightText: 2024-2025 Espressif Systems (Shanghai) CO LTD
# SPDX-License-Identifier: Apache-2.0

import os
import sys
import subprocess
import json

# color output on windows
if sys.platform == 'win32':
    from colorama import init

# preset environment variables
if sys.platform == 'win32':
    sys_cmd = 'set'
    sys_delimiter = ';'
else:
    sys_cmd = 'export'
    sys_delimiter = ':'

at_targets = ['esp32', 'esp32c2', 'esp32c3', 'esp32c5', 'esp32c6', 'esp32c61', 'esp32s2']
at_macro_pairs = []

def ESP_LOGI(x):
    print('\033[32m{}\033[0m'.format(x))

def ESP_LOGE(x):
    print('\033[31m{}\033[0m'.format(x))

def jihulab_repo_preprocess():
    print('Redirect repository to https://jihulab.com/esp-mirror/espressif')
    return 'https://jihulab.com/esp-mirror/espressif'

def jihulab_repo_postprocess(path, redirect_repo):
    pass

preset_origins = {
    'https://jihulab.com/esp-mirror/espressif/esp-at':{'preprocess': jihulab_repo_preprocess, 'postprocess': jihulab_repo_postprocess},
    'https://jihulab.com/esp-mirror/espressif/esp-at.git':{'preprocess': jihulab_repo_preprocess, 'postprocess': jihulab_repo_postprocess},
    'git@jihulab.com:esp-mirror/espressif/esp-at.git':{'preprocess': jihulab_repo_preprocess, 'postprocess': jihulab_repo_postprocess},
}

def at_sync_submodule(path, repo, branch, commit, redirect):
    at_origin = subprocess.check_output(['git', 'remote', '-v']).decode(encoding = 'utf-8').split()[1]

    new_clone = False
    if not os.path.exists(path):
        # clone repository
        if at_origin in preset_origins:
             if redirect == 1:
                repo = '/'.join([preset_origins[at_origin]['preprocess'](), os.path.basename(repo)])

        ESP_LOGI('Cloning into submodule:"{}" from "{}" (This may take some time)..'.format(path, repo))
        ret = subprocess.call('git clone -b {} {} {}'.format(branch, repo, path), shell = True)
        if ret:
            raise Exception('git clone failed')
        new_clone = True

    rev_parse_head = subprocess.check_output('cd {} && git rev-parse HEAD'.format(path), shell = True).decode(encoding='utf-8').strip()
    if rev_parse_head != commit:
        ESP_LOGI('Synchronizing submodule:"{}" from "{}" (This may take time)..'.format(path, repo))
        print('old commit: {}'.format(rev_parse_head))
        print('checkout commit: {}'.format(commit))
        cmd = 'cd {} && git fetch origin {}'.format(path, branch)
        ret = subprocess.call(cmd, shell = True)
        if ret:
            raise Exception('git fetch failed! Please manually run:\r\n{}'.format(cmd))
        cmd = 'cd {} && git merge origin/{} {}'.format(path, branch, branch)
        ret = subprocess.call(cmd, shell = True)
        if ret:
            raise Exception('git merge failed! Please manually run:\r\n{}'.format(cmd))
        cmd = 'cd {} && git checkout -q {}'.format(path, commit)
        ret = subprocess.call(cmd, shell = True)
        if ret:
            raise Exception('git checkout failed! Please manually run:\r\n{}'.format(cmd))

    if new_clone:
        # init submoules for cloned repository
        ret = subprocess.call('cd {} && git submodule init'.format(path), shell = True)
        if ret:
            raise Exception('git submodule init failed')

        if at_origin in preset_origins:
            # redirect esp-idf submodules if esp-idf itself is redirected (just redirect one-level submodules currently)
            if redirect and path == 'esp-idf':
                preset_origins[at_origin]['postprocess'](path, None)

    if rev_parse_head != commit or new_clone:
        cmd = 'cd {} && git submodule update --init --recursive'.format(path)
        ret = subprocess.call(cmd, shell = True)
        if ret:
            raise Exception('git submodule update failed! Please manually run:\r\n{}'.format(cmd))

def at_parse_idf_version(idf_ver_file, pairs):
    if not os.path.exists(idf_ver_file):
        ESP_LOGE('File does not exist: {}'.format(idf_ver_file))
        sys.exit(2)

    with open(idf_ver_file) as f:
        for line in f.readlines():
            index = line.strip().find('branch:')
            if index >= 0:
                branch = line[index + len('branch:'):].rstrip('\n')
                continue
            index = line.strip().find('commit:')
            if index >= 0:
                commit = line[index + len('commit:'):].rstrip('\n')
                continue
            index = line.strip().find('repository:')
            if index >= 0:
                repo = line[index + len('repository:'):].rstrip('\n')
                continue

    if len(branch) <= 0:
        sys.exit('ERROR: idf branch is not defined')
    if len(commit) <= 0:
        sys.exit('ERROR: idf commit is not defined')
    if len(repo) <= 0:
        sys.exit('ERROR: idf url is not defined')

    pairs.append(('esp-idf', repo, branch, commit, 1))

def at_parse_submodules(submodules_file, pairs):
    import configparser
    if not os.path.exists(submodules_file):
        return None
    config = configparser.ConfigParser()
    config.read(submodules_file)
    for item in config.sections():
        at_macro_pairs.append('AT_' + item.split()[1].strip('"').upper() + '_SUPPORT')
        pairs.append((config[item]['path'], config[item]['url'], config[item]['branch'], config[item]['commit'], 0))

def at_submodules_update(platform, module):
    config_dir = os.path.join(os.getcwd(), 'module_config', 'module_{}'.format(module.lower()))
    if not os.path.exists(config_dir):
        config_dir = os.path.join(os.getcwd(), 'module_config',  'module_{}_default'.format(platform.lower()))

    pairs = []
    ext_module_cfg = os.environ.get('AT_EXT_MODULE_CFG')
    if ext_module_cfg and os.path.exists(os.path.join(ext_module_cfg, 'IDF_VERSION')):
        idf_ver_file = os.path.join(ext_module_cfg, 'IDF_VERSION')
    else:
        idf_ver_file = os.path.join(config_dir, 'IDF_VERSION')
    at_parse_idf_version(idf_ver_file, pairs)

    try:
        if ext_module_cfg and os.path.exists(os.path.join(ext_module_cfg, 'submodules')):
            submodules_file = os.path.join(ext_module_cfg, 'submodules')
        else:
            submodules_file = os.path.join(config_dir, 'submodules')
        at_parse_submodules(submodules_file, pairs)
    except Exception as e:
        ESP_LOGE('Failed to parse submodules:"{}" ({})'.format(submodules_file, e))
        sys.exit(2)

    for path, repo, branch, commit, redirect in list(filter(None, pairs)):
        at_sync_submodule(path, repo, branch, commit, redirect)

    ESP_LOGI('submodules check completed for updates.')

def get_python():
    if sys.platform in ['win32', 'linux2']:
        return sys.executable
    return os.path.join(os.environ.get('IDF_PYTHON_ENV_PATH'), 'bin', 'python') if os.environ.get('IDF_PYTHON_ENV_PATH') else 'python'

def at_patch_external_if_config(chip):
    ext_module_cfg = os.environ.get('AT_EXT_MODULE_CFG')
    patch_dir = os.path.join(ext_module_cfg, 'patch') if ext_module_cfg and os.path.exists(os.path.join(ext_module_cfg, 'patch')) else None
    patch_tool = os.path.join(os.getcwd(), 'tools', 'patch.py')
    if patch_dir is not None and os.path.exists(patch_tool):
        cmd = f'{get_python()} {patch_tool} {patch_dir} {chip} before_sdkconfig'
        if subprocess.call(cmd, shell = True):
            raise Exception('apply external patches failed.')
        ESP_LOGI('external patches check completed for updates.')

def build_project(platform_name, module_name, silence, build_args):
    tool = os.path.join('esp-idf', 'tools', 'idf.py')
    exp_macro_cmd = ''
    for item in at_macro_pairs:
        exp_macro_cmd += '{} {}={} &&'.format(sys_cmd, item, item)
    exp_macro_cmd += '{} ESP_AT_PROJECT_PLATFORM=PLATFORM_{} &&'.format(sys_cmd, platform_name)
    exp_macro_cmd += '{} ESP_AT_MODULE_NAME={} &&'.format(sys_cmd, module_name)
    exp_macro_cmd += '{} ESP_AT_PROJECT_PATH={} &&'.format(sys_cmd, os.getcwd())
    exp_macro_cmd += '{} SILENCE={}'.format(sys_cmd, silence)

    compile_cmd = '{} {} -DIDF_TARGET={} {}'.format(get_python(), tool, platform_name.lower(), build_args)
    cmd = exp_macro_cmd + '&&' + compile_cmd
    ret = subprocess.call(cmd, shell = True)
    if ret:
        raise Exception('idf.py build failed')

    with open(os.path.join('build', 'flash_project_args'), 'r') as rd_f:
        with open(os.path.join('build', 'download.config'), 'w') as wr_f:
            data = rd_f.read().splitlines()
            wr_f.write(' '.join(data))

def get_param_data_info(source_file, sheet_name):
    import xlrd
    import csv
    filename, filetype = os.path.splitext(source_file)
    if filetype == '.csv':
        with open(source_file) as f:
            csv_data = csv.reader(f)
            param_data_list = list(csv_data)

    else:
        print('The file type is not supported.')
        exit()

    return param_data_list


def get_platform_and_module_lists():
    platform_lists = {}
    data_lists = get_param_data_info(
        os.path.join('components', 'customized_partitions', 'raw_data', 'factory_param', 'factory_param_data.csv'), 'Param_Data')

    headers = data_lists[0]

    nrows = len(data_lists)
    ncols = len(data_lists[0])
    platform_index = ncols
    module_name_index = ncols
    description_index = ncols
    for i in range(ncols):  # get platform index
        if headers[i] == 'platform':
            platform_index = i
            break

    for i in range(ncols):  # get module name index
        if headers[i] == 'module_name':
            module_name_index = i
            break

    for i in range(ncols):  # get description index
        if headers[i] == 'description':
            description_index = i
            break

    if platform_index == ncols:
        sys.exit('ERROR: Not found platform in header.')

    if module_name_index == ncols:
        sys.exit('ERROR: Not found module name in header.')

    if description_index == ncols:
        sys.exit('ERROR: Not found description in header.')

    for row in range(1, nrows):  # skip header
        data_list = data_lists[row]
        modules = []

        platform_name = data_list[platform_index].upper()
        module_name = data_list[module_name_index].upper()
        module_info = {'module_name': module_name, 'description': data_list[description_index]}
        if platform_name in platform_lists:
            platform_lists.fromkeys(platform_name, platform_lists[platform_name].append(module_info))
        else:
            platform_lists[platform_name] = [module_info]

    return platform_lists


def choose_project_config():
    info = {}
    info_lists = get_platform_and_module_lists()
    platform_lists = list(info_lists.keys())
    module_info_file = os.path.join('build', 'module_info.json')
    if os.path.exists(module_info_file):
        with open(module_info_file, 'r') as f:
            info = json.load(f)
            if not 'platform' in info or not 'module' in info or not 'silence' in info:
                sys.exit('"{}" configuration error, please delete and reconfigure it'.format(module_info_file))
            platform_name = info['platform']
            module_name = info['module']

            if not platform_name in info_lists:
                sys.exit('"{}" configuration error, please delete and reconfigure it'.format(module_info_file))

            # get module_info
            found = False
            for index, module in enumerate(info_lists[platform_name]):
                if module_name == module['module_name']:
                    found = True
                    break

            if not found:
                sys.exit('"{}" configuration error, please delete and reconfigure it'.format(module_info_file))

            if info['silence'] != 0 and info['silence'] != 1:
                sys.exit('"{}" configuration error, please delete and reconfigure it'.format(module_info_file))

            return platform_name.replace('PLATFORM_', ''), module_name, info['silence']

    print('Platform name:')
    for i, platform in enumerate(platform_lists):
        print('{}. {}'.format(i + 1, platform))

    try:
        platform_index = raw_input('choose(range[1,{}]):'.format(i + 1))
    except NameError:
        platform_index = input('choose(range[1,{}]):'.format(i + 1))

    if (not platform_index.isdigit()) or (int(platform_index) - 1 > i):
        sys.exit('Invalid index')

    print('\r\nModule name:')
    platform_name = platform_lists[int(platform_index) - 1]
    info['platform'] = platform_name

    for i, module in enumerate(info_lists[platform_name]):
        if len(module['description']) > 0:
            print('{}. {}\t(Firmware description: {})'.format(i + 1, module['module_name'], module['description']))
        else:
            print('{}. {}'.format(i + 1, module['module_name']))
    try:
        module_index = raw_input('choose(range[1,{}]):'.format(i + 1))
    except NameError:
        module_index = input('choose(range[1,{}]):'.format(i + 1))

    if (not module_index.isdigit()) or (int(module_index) - 1 > i):
        sys.exit('Invalid index')

    module_name = info_lists[platform_name][int(module_index) - 1]['module_name']
    module = info_lists[platform_name][int(module_index) - 1]
    info['module'] = module_name
    info['description'] = module['description']

    print('\r\nEnable silence mode to remove some logs and reduce the firmware size?')
    print('0. No')
    print('1. Yes')
    try:
        silence_index = raw_input('choose(range[0,1]):')
    except NameError:
        silence_index = input('choose(range[0,1]):')

    if not silence_index.isdigit():
        sys.exit('Invalid index')

    if int(silence_index) == 0:
        info['silence'] = 0
    elif int(silence_index) == 1:
        info['silence'] = 1
    else:
        sys.exit('Invalid index')

    res = json.dumps(info)
    if not os.path.exists('build'):
        os.mkdir('build')

    with open(module_info_file, 'w+') as f:
        f.write(res)

    if os.path.exists('sdkconfig'):
        os.remove('sdkconfig')

    return platform_name.replace('PLATFORM_', ''), module_name, info['silence']

def setup_env_variables():
    ESP_LOGI('Ready to set up environment variables..')
    print('sys.platform is {}'.format(sys.platform))

    # set IDF_PATH
    idf_path=os.path.join(os.getcwd(), 'esp-idf')
    os.environ['IDF_PATH']=idf_path

    # get ESP-IDF environment variables
    export_str = ''
    if sys.platform != 'linux2':
        cmd = '{} {} export --format=key-value'.format(sys.executable, os.path.join('esp-idf', 'tools', 'idf_tools.py'))
        try:
            export_str = subprocess.check_output(cmd, shell=True).decode('utf-8')
        except Exception as e:
            print('Not found the environment installed by "install" command, and using the default system environment')

    if export_str:
        # extract each idf env variables and set them to system env variables
        for line in export_str.splitlines():
            key, value = line.split('=', 1)
            if key == 'PATH':
                value = value + sys_delimiter + os.environ.get('PATH')
            os.environ[key] = value

    print('PATH is {}'.format(os.environ.get('PATH')))
    print('IDF_PYTHON_ENV_PATH is {}'.format(os.environ.get('IDF_PYTHON_ENV_PATH')))

def install_compilation_env(target):
    # set up ESP-IDF tools
    ESP_LOGI('Ready to set up ESP-IDF tools..')
    cmd = '{} {} install-python-env'.format(sys.executable, os.path.join('esp-idf', 'tools', 'idf_tools.py'))
    ret = subprocess.call(cmd, shell = True)
    if ret:
        raise Exception('set up ESP-IDF python-env failed')
    cmd = '{} {} install --targets {}'.format(sys.executable, os.path.join('esp-idf', 'tools', 'idf_tools.py'), target)
    ret = subprocess.call(cmd, shell = True)
    if ret:
        raise Exception('set up ESP-IDF toolchains failed')

    # set up environment variables
    setup_env_variables()

    # install ESP-AT python packages
    ESP_LOGI('Ready to install ESP-AT python packages..')
    if sys.platform == 'win32':
        py_env_path = sys.executable
    else:
        py_env_path = os.path.join(os.environ.get('IDF_PYTHON_ENV_PATH'), 'bin', 'python')
    cmd = '{} -m pip install -r requirements.txt'.format(py_env_path)
    ret = subprocess.call(cmd, shell = True)
    if ret:
        raise Exception('install ESP-AT python packages failed!')

    print('\r\nAll done! You can now run:\r\n\r\n  {}build.py build\r\n'.format('python ' if sys.platform == 'win32' else './'))

def install_prerequisites():
    # install ESP-IDF prerequisites
    ESP_LOGI('Ready to install ESP-IDF prerequisites..')
    cmd = ''
    if sys.platform == 'linux':
        cmd = 'sudo apt-get install git wget flex bison gperf python3 python3-pip python3-venv python3-setuptools cmake ninja-build ccache libffi-dev libssl-dev dfu-util libusb-1.0-0'
    elif sys.platform == 'darwin':
        cmd = 'sudo easy_install pip && brew install cmake ninja dfu-util ccache python3'
    elif sys.platform == 'win32':
        print('Windows Installer Download has already installed all prerequisites.')
    elif sys.platform == 'linux2':
        print('GitLab CI has already installed all prerequisites.')
    else:
        raise Exception('unsupported platform: {} till now.'.format(sys.platform))

    if not os.environ.get('HAS_IDF_PREREQUISITES'):
        ret = subprocess.call(cmd, shell = True)
        if ret:
            raise Exception('install prerequisites failed! Please manually run:\r\n{}'.format(cmd))

    # install ESP-AT prerequisites
    ESP_LOGI('Ready to install ESP-AT prerequisites..')
    cmd = '{} -m pip install -r requirements.txt'.format(sys.executable)
    ret = subprocess.call(cmd, shell = True)
    if ret:
        raise Exception('install ESP-AT prerequisites failed!')

def get_doc_target():
    command = ['git', 'rev-parse', '--abbrev-ref', 'HEAD']
    try:
        result = subprocess.check_output(command).decode().strip()
    except Exception as e:
        raise Exception('cannot fetch the branch name: {}'.format(e))
    if not result.startswith('release'):
        return 'latest'
    return result.replace('/', '-')

"""
TODOs:
  1. optimise ESP-IDF clone and version update workflow
  2. optimise ESP-AT and ESP-IDF tools/packages install workflow
  3. remove workaround for windows
"""
def main():
    if sys.platform == 'win32':
        init(autoreset=True)
    argv = sys.argv[1:]

    # unset IDF_PATH
    if os.environ.get('IDF_PATH'):
        os.environ['IDF_PATH']=''

    # install prerequisites
    if (len(argv) == 1 and sys.argv[1] == 'install'):
        install_prerequisites()

    platform_name, module_name, silence = choose_project_config()
    if platform_name.lower() in at_targets:
        ESP_LOGI('Platform name:{}\tModule name:{}\tSilence:{}'.format(platform_name, module_name, silence))
    else:
        ESP_LOGE('Unsupported platform: <{}> till now.'.format(platform_name))
        sys.exit(2)

    at_submodules_update(platform_name, module_name)

    if (len(argv) == 1 and sys.argv[1] == 'install'):
        # install tools and packages only after esp-idf cloned
        install_compilation_env(platform_name.lower())
        sys.exit(0)
    elif len(argv) == 0:
        ESP_LOGE('Incorrect usage, please refer to https://docs.espressif.com/projects/esp-at/en/{}/{}/Compile_and_Develop/How_to_clone_project_and_compile_it.html for more details.'.format(get_doc_target(), platform_name.lower()))
        sys.exit(0)

    setup_env_variables()

    # apply possible external patches to source code
    at_patch_external_if_config(platform_name.lower())

    build_args = ' '.join(argv)
    build_project(platform_name, module_name, silence, build_args)

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        ESP_LOGE('A fatal error occurred: {}'.format(e))
        sys.exit(2)
