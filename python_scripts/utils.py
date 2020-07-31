import os, sys, logging
import hashlib
from distutils.sysconfig import get_python_lib

# filenames to ignore altogether, and not include in reports
IGNORE_FILENAMES = [".DS_Store", "INSTALLER"]

# extensions to report on, but skip scanning
SKIP_EXTENSIONS = [".gif", ".png", ".jpg", ".PNG", ".pdf", ".der", ".bin"]

# directories whose files should be reported on, but skip scanning
SKIP_DIRECTORIES = ["LICENSES", ".git"]

# directories whose files should not be reported on and not scanned
HIDE_DIRECTORIES = ["LICENSES", ".git"]

# Suffix used to guarantee uniqueness of spdx filename
FILE_SUFFIX = "spdx"

CODEBASE_EXTRA_PARAMS = {
    "header": "",
    "tool_name": "Python SPDX Build tool generator",
    "tool_name_rdf": "SPDX.Doc.Generator",
    "tool_version": "1.0",
    "notice": "SPDX Doc Generator",
    "creator_comment": "Created by SPDX Build tool generator",
    "ext_doc_ref": "SPDX-DOC-GENERATOR",
    "doc_ref": "SPDXRef-DOCUMENT",
    "file_ref": "SPDXRef-{0}",
    "lic_identifier": "CC0-1.0",
}

FILES_TO_EXCLUDE = ["VERSION", "LICENSE"]

# TAG VALUE or RDF
TAG_VALUE = "tv"
RDF = "rdf"


def is_dir(path):
    """
    Returns True if the path is that of a directory; and False otherwise
    """
    return os.path.isdir(path)


def is_file(path):
    """
    Returns True if the path is that of a file; and False otherwise
    """
    return os.path.isfile(path)


def get_file_hash(file_path):
    sha1sum = hashlib.sha1()
    with open(file_path, "rb") as source:
        block = source.read(2 ** 16)
        while len(block) != 0:
            sha1sum.update(block)
            block = source.read(2 ** 16)
    return sha1sum.hexdigest()


def should_skip_file(file_path, output_file):
    should_skip = False
    for item in FILES_TO_EXCLUDE:
        if item in file_path:
            should_skip = True
    if output_file in file_path:
        should_skip = True
    return should_skip


def get_codebase_extra_params(path_or_file):
    return CODEBASE_EXTRA_PARAMS


def get_package_file(dir_or_file, file_name):
    if is_dir(dir_or_file):
        version_file_path = os.path.join(dir_or_file, file_name)
        if os.path.exists(version_file_path):
            return version_file_path
    return None


def get_package_version(path_or_file):
    version_file = get_package_file(path_or_file, "VERSION")
    version_major = None
    version_minor = None
    if version_file:
        version_file_content = open(version_file, "r")
        for line in version_file_content:
            if "VERSION_MAJOR" in line:
                version_major = line.split("=")[1]
            if "VERSION_MINOR" in line:
                version_minor = line.split("=")[1]
        if version_major and version_minor:
            return "{0}.{1}".format(
                version_major.strip(" ").strip("\n"),
                version_minor.strip(" ").strip("\n"),
            )
    return None


def get_file_hash(file_path):
    sha1sum = hashlib.sha1()
    with open(file_path, "rb") as source:
        block = source.read(2 ** 16)
        while len(block) != 0:
            sha1sum.update(block)
            block = source.read(2 ** 16)
    return sha1sum.hexdigest()


def read(filename):
    """Return the contents of a file.

    :param filename: file path
    :type filename: :class:`str`
    :return: the file's content
    :rtype: :class:`str`
    """
    with open(filename) as f:
        return f.read()


def get_virtual_env_dir():
    if "VIRTUAL_ENV" in os.environ:
        return os.environ["VIRTUAL_ENV"]
    return None


def get_python_version():
    return sys.version[:3]


def get_dependencies(args):
    """
    Get python dependencies from virtualenv.
    If they are not available(user uses another virtualenv), download them to temp folder.
    """
    logging.basicConfig(level=logging.INFO)
    logging.info("Getting dependencies")
    project_path = os.path.expanduser(args["project_path"])
    reserved_python_names = args["res"]
    short_dep_list = os.listdir(get_python_lib())
    dep_list = [project_path]
    if not reserved_python_names:
        final_dep_list = []
        for item in short_dep_list:
            if not item.startswith("__") and not item.endswith("__"):
                final_dep_list.append(item)
        for item in final_dep_list:
            dep_list.append(os.path.join(get_python_lib(), item))
    else:
        for item in short_dep_list:
            dep_list.append(os.path.join(get_python_lib(), item))
    return dep_list
