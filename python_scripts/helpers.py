# SPDX-License-Identifier: Apache-2.0

import logging
import os
import utils


class ScanData(object):
    def __init__(self):
        self.filename = ""
        self.scanned = False
        self.skipReason = ""
        self.license = None
        self.lineno = -1

    def __str__(self):
        return self.license


def get_list_of_all_files_in_all_deps(dirName):
    """Returns a list of all paths for all files within topDir or its children."""
    # create a list of file and sub directories
    # names in the given directory
    listOfFile = os.listdir(dirName)
    allFiles = list()
    # Iterate over all the entries
    for entry in listOfFile:
        # Create full path
        fullPath = os.path.join(dirName, entry)
        # If entry is a directory then get the list of files in this directory
        if os.path.isdir(fullPath):
            if not entry in utils.HIDE_DIRECTORIES:
                allFiles = allFiles + getListOfFiles(fullPath)
        else:
            if not entry in utils.IGNORE_FILENAMES:
                allFiles.append(fullPath)

    return allFiles


def skip_directory(dir_list, filePath):
    for d in dir_list:
        sd = f"/{d}/"
        if sd in filePath:
            return (True, "skipped directory")


def should_skip_file(filePath, glob_to_skip):
    """Returns (True, "reason") if file should be skipped for scanning, (False, "") otherwise."""
    for item in glob_to_skip:
        if item.startswith("./") and item.endswith("/"):
            # if item is a directory
            dir_name1 = item.replace(item[:2], "")
            dir_name = dir_name1[:-1]
            mk = skip_directory([dir_name], filePath)
            if mk != None:
                return mk
        elif item.startswith("./") and not item.endswith("/"):
            file_name = item.replace(item[:1], "")
            if item in filePath:
                return (True, "skipped file name")
        elif item in filePath:
            return (True, "skipped file name")
    _, extension = os.path.splitext(filePath)
    if extension in utils.SKIP_EXTENSIONS:
        return (True, "skipped file extension")
    skip_directory(utils.SKIP_DIRECTORIES, filePath)
    return (False, "")


def get_dependencies_file_paths(dep_path_list):
    """
    Return a list of path strings for all the installed python package files
    given a dep_path_list list of directories path of installed python packages
    """
    logging.basicConfig(level=logging.INFO)
    logging.info("Getting dependencies file paths")
    dep_path_list1 = ["/home/philip/Desktop/tests/bitbake"]
    dep_file_list = []  # installed_files
    for item in dep_path_list:
        if os.path.isfile(item):
            dep_file_list.append(item)
        else:
            for (currentDir, _, filenames) in os.walk(item):
                for item in utils.HIDE_DIRECTORIES:
                    if item in currentDir:
                        continue  # Clear
                    else:
                        for filename in filenames:
                            filebasename, file_extension = os.path.splitext(filename)
                            if (
                                filename not in utils.IGNORE_FILENAMES
                                and file_extension not in utils.SKIP_EXTENSIONS
                            ):
                                p = os.path.join(currentDir, filename)  # current_dir
                                dep_file_list.append(p)
    return dep_file_list


def parseLineForIdentifier(line):
    """
    Return parsed SPDX expression if tag found in line, or None otherwise.
    """
    p = line.partition("SPDX-License-Identifier:")
    if p[2] == "":
        return None
    # strip away trailing comment marks and whitespace, if any
    identifier = p[2].strip()
    identifier = identifier.rstrip("/*")
    identifier = identifier.strip()
    return identifier


def get_identifier_data(filePath, glob_to_skip, numLines=20):
    """
    Scans the specified file for the first SPDX-License-Identifier:
    tag in the file.

    Arguments:
        - filePath: path to file to scan.
        - numLines: number of lines to scan for an identifier before
                    giving up. If 0, will scan the entire file.
                    Defaults to 20.
    Returns: ScanData with (parsed identifier, line number) if found;
                           (None, -1) if not found.
    """
    # FIXME probably needs to be within a try block
    sd = ScanData()
    sd.filename = filePath
    (shouldSkip, reason) = should_skip_file(filePath, glob_to_skip)
    if shouldSkip:
        logging.debug(f"===> Skipping {filePath}")
        sd.scanned = False
        sd.skipReason = reason
        sd.license = "SKIPPED"
        sd.lineno = -1
        return {
            "FileName": filePath,
            "SPDXID": sd.license,
            "scanned": sd.scanned,
            "FileType": None,
            "FileChecksum": None,
        }

    # if we get here, we will scan the file
    sd.scanned = True
    logging.debug(f"Scanning {filePath}")
    with open(filePath, "r") as f:
        try:
            lineno = 0
            for line in f:
                lineno += 1
                if numLines > 0 and lineno > numLines:
                    break
                identifier = parseLineForIdentifier(line)
                if identifier is not None:
                    sd.license = identifier
                    sd.lineno = lineno
                    return {
                        "FileName": filePath,
                        "SPDXID": sd.license,
                        "scanned": sd.scanned,
                        "FileType": None,
                        "FileChecksum": None,
                    }
        except UnicodeDecodeError:
            # invalid UTF-8 content
            sd.scanned = False
            sd.skipReason = "encountered invalid UTF-8 content"
            sd.license = "SKIPPED"
            sd.lineno = -1
            return {
                "FileName": filePath,
                "SPDXID": sd.license,
                "scanned": sd.scanned,
                "FileType": None,
                "FileChecksum": None,
            }

    # if we get here, we didn't find an identifier
    sd.license = None
    sd.lineno = -1
    return {
        "FileName": filePath,
        "SPDXID": "NOASSERTION",
        "scanned": sd.scanned,
        "FileType": None,
        "FileChecksum": None,
    }


def get_identifiers_for_paths(paths, glob_to_skip, numLines=20):
    """
    Scans all specified files for the first SPDX-License-Identifier:
    tag in each file.

    Arguments:
        - paths: list of all file paths to scan.
        - numLines: number of lines to scan for an identifier before
                    giving up. If 0, will scan the entire file.
                    Defaults to 20.
    Returns: dict of {filename: ScanData} for each file in paths.
             ScanData is (parsed identifier, line number) if found;
                         (None, -1) if not found.
    """
    logging.basicConfig(level=logging.INFO)
    logging.info("Getting identifiers for paths")
    scan_metrics = {"with_id": 0, "without_id": 0, "skipped": 0, "total": len(paths)}
    results = []
    for filePath in paths:
        id_data = get_identifier_data(filePath, glob_to_skip, numLines)
        if id_data["SPDXID"] == "SKIPPED":
            scan_metrics["skipped"] = scan_metrics["skipped"] + 1
        if id_data["SPDXID"] == "NOASSERTION":
            scan_metrics["without_id"] = scan_metrics["without_id"] + 1
        if id_data["SPDXID"] != "SKIPPED" and id_data["SPDXID"] != "NOASSERTION":
            scan_metrics["with_id"] = scan_metrics["with_id"] + 1

        results.append(id_data)
    return results


def get_complete_time(function, args=tuple(), kwargs={}):
    """
    ----Decorator----
    Get real, user and system time
    """

    def wrappedMethod(*args, **kwargs):
        from time import time as timestamp
        from resource import getrusage as resource_usage, RUSAGE_SELF

        start_time, start_resources = timestamp(), resource_usage(RUSAGE_SELF)
        func = function(*args, **kwargs)
        end_resources, end_time = resource_usage(RUSAGE_SELF), timestamp()
        results = {
            "real": end_time - start_time,
            "sys": end_resources.ru_stime - start_resources.ru_stime,
            "user": end_resources.ru_utime - start_resources.ru_utime,
        }
        # print("Execution time for {0}".format(function.__name__))
        return func

    return wrappedMethod
