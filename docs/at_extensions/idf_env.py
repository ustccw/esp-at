# SPDX-FileCopyrightText: 2026 Espressif Systems (Shanghai) CO LTD
# SPDX-License-Identifier: Apache-2.0

import os
import subprocess
import sys

_DOCS_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_AT_ROOT = os.path.abspath(os.path.join(_DOCS_DIR, '..'))
_PREPARED = False


def _valid_idf_path(path):
    return path and os.path.isfile(os.path.join(path, 'tools', 'idf.py'))


def resolve_idf_path():
    env_idf_path = os.environ.get('IDF_PATH')
    if _valid_idf_path(env_idf_path):
        return os.path.realpath(env_idf_path)

    for candidate in (os.path.join(_AT_ROOT, 'esp-idf'), '/opt/esp/idf'):
        if _valid_idf_path(candidate):
            return os.path.realpath(candidate)

    raise RuntimeError(
        'Cannot find ESP-IDF for documentation build. '
        'Set IDF_PATH, use an image that ships esp-idf at /opt/esp/idf, or clone esp-idf into esp-at/esp-idf.'
    )


def export_idf_tools(idf_root):
    export_cmd = [
        sys.executable,
        os.path.join(idf_root, 'tools', 'idf_tools.py'),
        '--non-interactive',
        'export',
        '--format=key-value',
    ]
    try:
        output = subprocess.check_output(export_cmd, stderr=subprocess.STDOUT, text=True)
    except subprocess.CalledProcessError as exc:
        raise RuntimeError(
            'Failed to export ESP-IDF build tools from {}.\n'
            'Install the required tools first:\n'
            '  python {}/tools/idf_tools.py install\n'
            'Command output:\n{}'
            .format(idf_root, idf_root, exc.output)
        ) from exc

    for line in output.splitlines():
        if not line or '=' not in line:
            continue
        key, value = line.split('=', 1)
        if key == 'PATH':
            os.environ['PATH'] = value + os.pathsep + os.environ.get('PATH', '')
        else:
            os.environ[key] = value


def get_idf_python():
    idf_python_env = os.environ.get('IDF_PYTHON_ENV_PATH')
    if idf_python_env:
        idf_python = os.path.join(idf_python_env, 'bin', 'python')
        if os.path.isfile(idf_python):
            return idf_python
    return sys.executable


def prepare_idf_env():
    global _PREPARED
    if _PREPARED:
        return os.environ['IDF_PATH']

    idf_root = resolve_idf_path()
    os.environ['IDF_PATH'] = idf_root
    export_idf_tools(idf_root)
    _PREPARED = True
    return idf_root
