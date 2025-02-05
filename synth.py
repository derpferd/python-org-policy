# Copyright 2020 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import re

import synthtool as s
import synthtool.gcp as gcp
from synthtool import tmp
from synthtool.languages import python
from synthtool.sources import git


gapic = gcp.GAPICBazel()
common = gcp.CommonTemplates()

versions = ["v2"]  # this package also has v1 protos, see below for note

# ----------------------------------------------------------------------------
# Generate orgpolicy GAPIC layer
# ----------------------------------------------------------------------------
for version in versions:
    library = gapic.py_library(
        service="orgpolicy",
        version=version,
        bazel_target=f"//google/cloud/orgpolicy/{version}:orgpolicy-{version}-py",
    )
    s.move(library, excludes=["setup.py", "README.rst", "docs/index.rst"])

# Rename to google-cloud-org-policy
# TODO: use bazel option to rename package
s.replace(
    "google/cloud/**/*",
    "google-cloud-orgpolicy",
    "google-cloud-org-policy"
)

# ----------------------------------------------------------------------------
#  Add templated files
# ----------------------------------------------------------------------------

# coverage is 97 to exclude orgpolicy/v1 code
templated_files = common.py_library(microgenerator=True, cov_level=95)
s.move(
    templated_files, excludes=[".coveragerc",]
)

# NOTE: This library also has legacy pb2.py files for "v1"
# in google/cloud/orgpolicy/v1
# v1 only has messages (no service or RPCs).
# v1 protos can be refreshed by running
# `nox -s generate_protos`. See the noxfile.py.

# Append generate_protos  nox session
s.replace(
    "noxfile.py",
    """(@nox\.session.+?
def lint\(.+?)""",
    '''@nox.session(python="3.8")
def generate_protos(session):
    """Generates the protos using protoc.

    Some notes on the `google` directory:
    1. The `_pb2.py` files are produced by protoc.
    2. The .proto files are non-functional but are left in the repository
       to make it easier to understand diffs.
    3. The `google` directory also has `__init__.py` files to create proper modules.
       If a new subdirectory is added, you will need to create more `__init__.py`
       files.

    NOTE: This is a hack and only runnable locally. You will need to have
    the api-common-protos repo cloned. This should be migrated to use
    bazel in the future.
    """
    session.install("grpcio-tools")
    protos = [str(p) for p in (Path(".").glob("google/**/*.proto"))]

    session.run(
        "python",
        "-m",
        "grpc_tools.protoc",
        "--proto_path=../api-common-protos",
        "--proto_path=.",
        "--python_out=.",
        *protos,
    )

\g<1>''',
)
s.shell.run(["nox", "-s", "blacken"], hide_output=False)
