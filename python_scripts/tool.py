import sys, os, logging
import argparse

import utils
import core
import helpers


def build_parser(args):
    arguments = {
        "project_path": args[0],
        "spdx_file_name": args[1],
        "tv": True if "--tv" in args else False,
        "rdf": True if "--rdf" in args else False,
        "res": True if "--res" in args else False,
    }
    return arguments


def create_spdx_document(args):
    deps = utils.get_dependencies(args)
    glob_to_skip = []
    file_types = "tv"
    deps_l = helpers.get_dependencies_file_paths(deps)
    all_identifiers = helpers.get_identifiers_for_paths(deps_l, glob_to_skip)
    # spdx_file = core.SPDXFile(
    #     args["project_path"], args["spdx_file_name"], all_identifiers, True, file_types
    # )
    # spdx_file.create_spdx_document()


def main(argv):
    arguments = argv[3:]
    args = build_parser(arguments)
    create_spdx_document(args)


main(sys.argv)
