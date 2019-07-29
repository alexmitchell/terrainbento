from __future__ import print_function

import os
import subprocess
import sys
import traceback

print('Using python: {prefix}'.format(prefix=sys.prefix))

repo_tag = os.environ.get('APPVEYOR_REPO_TAG', 'false')
tag_name = os.environ.get('APPVEYOR_REPO_TAG_NAME', '')
token = os.environ.get('TWINE_PASSWORD', 'NOT_A_TOKEN')

if repo_tag == 'true' and tag_name.startswith('v'):
    print('Uploading to PyPI')

    try:
        cmd = ' '.join(['twine', 'upload', '-u', 'katybarnhart', '-p', token,
                        'dist/*'])
        resp = subprocess.check_output(cmd)
    except subprocess.CalledProcessError:
        traceback.print_exc()
    else:
        print('OK')
else:
    print('Not a tagged release. Not deploying to PyPI.')
