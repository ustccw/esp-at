# SPDX-FileCopyrightText: 2026 Espressif Systems (Shanghai) CO LTD
# SPDX-License-Identifier: Apache-2.0

import json
import os
import shutil
import subprocess

from esp_docs.idf_extensions.build_system import project_path as dummy_project_path

from at_extensions.idf_env import get_idf_python, prepare_idf_env


class AtIdfBuilder:
    def __init__(self) -> None:
        self.project_description = {}

    def _run_idf_py(self, idf_py, args, cmake_build_dir):
        result = subprocess.run(idf_py + args, env=os.environ.copy(), text=True, capture_output=True)
        if result.returncode == 0:
            return

        details = '\n'.join(part for part in [result.stdout, result.stderr] if part and part.strip()).strip()
        target = args[-1] if 'set-target' in args else 'unknown'
        raise RuntimeError(
            'Dummy ESP-IDF project setup failed for target {} (exit code {}).\n'
            'Install tools with: python $IDF_PATH/tools/idf_tools.py install\n'
            '{}'
            .format(target, result.returncode, details)
        )

    def generate_idf_info(self, app, config):
        os.environ['IDF_DOC_BUILD'] = 'y'

        if not app.config.idf_target:
            raise RuntimeError(
                'A valid target is needed to build ESP-AT docs. '
                'Please re-run build-docs with a target specified, e.g: build-docs -t esp32'
            )

        build_dir = os.path.dirname(app.doctreedir.rstrip(os.sep))
        cmake_build_dir = os.path.join(build_dir, 'build_dummy_project')
        idf_path = prepare_idf_env()
        idf_py = [
            get_idf_python(),
            os.path.join(idf_path, 'tools', 'idf.py'),
            '-B',
            cmake_build_dir,
            '-C',
            dummy_project_path,
            '-D',
            'SDKCONFIG={}'.format(os.path.join(build_dir, 'dummy_project_sdkconfig')),
        ]

        shutil.rmtree(cmake_build_dir, ignore_errors=True)
        print('Starting dummy IDF project for ESP-AT docs (IDF_PATH={})...'.format(idf_path))
        self._run_idf_py(idf_py, ['--preview', 'set-target', app.config.idf_target], cmake_build_dir)
        self._run_idf_py(idf_py, ['reconfigure'], cmake_build_dir)

        with open(os.path.join(cmake_build_dir, 'project_description.json')) as f:
            self.project_description = json.load(f)

        if self.project_description['target'] != app.config.idf_target:
            raise RuntimeError(
                'Dummy IDF project target mismatch: expected {}, got {}.'
                .format(app.config.idf_target, self.project_description['target'])
            )

        app.emit('project-build-info', self.project_description)
        return []


at_idf_builder = AtIdfBuilder()


def setup(app):
    try:
        build_dir = os.environ['BUILDDIR']
    except KeyError:
        build_dir = os.path.dirname(app.doctreedir.rstrip(os.sep))

    for directory in (build_dir, os.path.join(build_dir, 'inc')):
        try:
            os.mkdir(directory)
        except OSError:
            pass

    app.add_event('project-build-info')
    app.connect('config-inited', at_idf_builder.generate_idf_info)

    return {'parallel_read_safe': True, 'parallel_write_safe': True, 'version': '0.1'}
