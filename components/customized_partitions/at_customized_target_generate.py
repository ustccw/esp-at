#!/usr/bin/env python
#
# SPDX-FileCopyrightText: 2024-2026 Espressif Systems (Shanghai) CO LTD
# SPDX-License-Identifier: Apache-2.0

import os
import argparse
import re
import sys

to_read_config_name = {}
to_write_partition = {}

def get_to_read_config_name(dependency_file, sdkconfig_file):
    with open(sdkconfig_file) as sdkconfig_f:
        sdkconfig = sdkconfig_f.read()
        with open(dependency_file) as f:
            for line in f.readlines():
                line_str = line.strip()
                line_str = re.sub(' +', ' ', line_str)
                if not line_str.startswith('#'):
                    str_list = line_str.split()
                    if (sdkconfig.find(''.join(['CONFIG_',str_list[0]])) != -1):
                        to_read_config_name.update({str_list[1] : ''})

def get_to_write_partition(partition_file):
    with open(partition_file) as f:
        for line in f.readlines():
            line_str = line.strip()
            line_str = re.sub(' +', '', line_str)
            if not line_str.startswith('#'):
                str_list = line_str.split(',')
                if str_list[0] in to_read_config_name:
                    offset = str_list[3]
                    size = str_list[4]
                    to_write_partition.update({str_list[0] : {'offset' : offset, 'size' : size}})

def _find_nvs_key_partition(sdkconfig_file, project_dir):
    """If CONFIG_NVS_ENCRYPTION is enabled, find the nvs_keys partition in the main partition table."""
    with open(sdkconfig_file) as f:
        sdkconfig = f.read()
    if 'CONFIG_NVS_ENCRYPTION=y' not in sdkconfig:
        return None

    # Read partition table path from sdkconfig
    m = re.search(r'CONFIG_PARTITION_TABLE_CUSTOM_FILENAME="([^"]+)"', sdkconfig)
    if not m:
        return None
    part_table_path = os.path.join(project_dir, m.group(1))
    if not os.path.isfile(part_table_path):
        return None

    # Parse partition table CSV to find the nvs_keys row
    with open(part_table_path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            cols = [c.strip() for c in line.split(',')]
            if len(cols) >= 5 and cols[2] == 'nvs_keys':
                return {'name': cols[0], 'offset': cols[3], 'size': cols[4]}
    return None

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--dependency_file', help='dependency')
    parser.add_argument('--sdkconfig_file', help='sdkconfig')
    parser.add_argument('--partition_file', help='at_customize.csv')
    parser.add_argument('--output_dir', default='output', help='the output bin directory')
    parser.add_argument('--flash_args_file', default='flash_args_file', help='the file to store flash args')
    parser.add_argument('--project_dir', default='', help='ESP-AT project root')
    args = parser.parse_args()
    sdkconfig_file = args.sdkconfig_file
    dependency_file = args.dependency_file
    partition_file = args.partition_file
    output_dir = args.output_dir
    flash_args_file = args.flash_args_file
    get_to_read_config_name(dependency_file, sdkconfig_file)
    get_to_write_partition(partition_file)

    if os.path.exists(output_dir) == False:
        os.mkdir(output_dir)

    # check fs_storage dependency
    if 'fs_storage' in to_read_config_name and 'fs_storage' not in to_write_partition:
        print('fs_storage is required in sdkconfig but not found in partition table. Please check the at_customize.csv')
        sys.exit(1)

    with open(flash_args_file, 'w+') as args_file:
        for partition in to_write_partition:
            args_file.write(''.join([to_write_partition[partition]['offset'], ' ']))
            args_file.write(''.join([os.path.join(output_dir, partition), ''.join(['.bin', ' '])]))
            args_file.write(''.join([to_write_partition[partition]['size'], '\r\n']))

    # NVS encryption: append nvs_key entry if CONFIG_NVS_ENCRYPTION is enabled
    project_dir = args.project_dir.strip() or os.path.abspath(
        os.path.join(os.path.dirname(partition_file), '..', '..'))
    nvs_key_info = _find_nvs_key_partition(sdkconfig_file, project_dir)
    if nvs_key_info:
        keys_bin = os.path.join(project_dir, 'module_config', 'flash_encryption', 'sample_encryption_keys.bin')
        if os.path.isfile(keys_bin):
            with open(flash_args_file, 'a') as args_file:
                args_file.write('{} {} {}\r\n'.format(
                    nvs_key_info['offset'], os.path.abspath(keys_bin), nvs_key_info['size']))
        else:
            print('Warning: NVS encryption enabled but key file not found: {}'.format(keys_bin))

if __name__ == '__main__':
    main()
