import os, logging
from os.path import basename, dirname, isdir
import hashlib, io
import checksumdir
import utils

from spdx.document import ExternalDocumentRef, Document, License, ExtractedLicense
from spdx.checksum import Algorithm
from spdx.utils import SPDXNone, NoAssert
from spdx.version import Version
from spdx.package import Package
from spdx.creationinfo import Tool
from spdx.file import File


class SPDXFile(object):
    def __init__(
        self, path_or_file, output_file_name, id_scan_results, file_sum_info, doc_type
    ):
        self.is_file = utils.is_file(path_or_file)
        self.path_or_file = os.path.expanduser(path_or_file)
        self.file_to_scan = None
        if self.is_file:
            self.file_to_scan = path_or_file
            self.path_or_file = os.path.dirname(path_or_file)
        self.output_file_name = output_file_name + utils.FILE_SUFFIX
        self.id_scan_results = id_scan_results
        self.doc_type = doc_type
        self.output_file = None
        self.code_extra_params = utils.get_codebase_extra_params(self.path_or_file)
        self.full_file_path = None
        self.spdx_document = None

    def get_package_version(self):
        return utils.get_package_version(self.path_or_file)

    def get_package_verification_code(self):
        verificationcode = 0
        filelist = ""
        templist = []
        for item in self.id_scan_results:
            if not utils.should_skip_file(item["FileName"], self.output_file_name):
                templist.append(utils.get_file_hash(item["FileName"]))
        # sort the sha values
        templist.sort()
        for item in templist:
            filelist = "{0}{1}".format(filelist, item)
        verificationcode = hashlib.sha1(filelist.encode())
        return verificationcode.hexdigest()

    def get_package_checksum(self):
        sha1hash = None
        if not self.is_file:
            sha1hash = checksumdir.dirhash(self.path_or_file, "sha1")
        else:
            h = hashlib.sha1()
            # open file for reading in binary mode
            with open(self.file_to_scan, "rb") as file:
                # loop till the end of the file
                chunk = 0
                while chunk != b"":
                    # read only 1024 bytes at a time
                    chunk = file.read(1024)
                    h.update(chunk)
            # return the hex representation of digest
            sha1hash = h.hexdigest()
        return sha1hash

    def get_output_file(self):
        if utils.is_dir(self.path_or_file):
            self.full_file_path = os.path.join(
                self.path_or_file, self.output_file_name + ".spdx"
            )
            self.output_file = open(self.full_file_path, "wb+")
        else:
            file_dir = os.path.dirname(os.path.abspath(self.path_or_file))
            self.full_file_path = os.path.join(
                file_dir, self.output_file_name + ".spdx"
            )
            self.output_file = open(self.full_file_path, "wb+")

    def set_creation_info(self):
        ext_doc_ref = ExternalDocumentRef(
            self.code_extra_params["ext_doc_ref"],
            self.code_extra_params["tool_version"],
            Algorithm("SHA1", utils.get_file_hash(self.full_file_path or "")),
        )
        self.spdx_document.add_ext_document_reference(ext_doc_ref)
        self.spdx_document.comment = self.code_extra_params["notice"]
        if self.doc_type == utils.TAG_VALUE:
            self.spdx_document.creation_info.add_creator(
                Tool(
                    self.code_extra_params["tool_name"]
                    + " "
                    + self.code_extra_params["tool_version"]
                )
            )
            self.spdx_document.namespace = self.code_extra_params["notice"]
            self.spdx_document.name = self.code_extra_params["notice"]
        else:
            self.spdx_document.creation_info.add_creator(
                Tool(
                    self.code_extra_params["tool_name_rdf"]
                    + "."
                    + self.code_extra_params["tool_version"]
                )
            )
            self.spdx_document.namespace = self.code_extra_params["tool_name_rdf"]
            self.spdx_document.name = self.code_extra_params["tool_name_rdf"]
        self.spdx_document.creation_info.set_created_now()
        self.spdx_document.creation_info.comment = self.code_extra_params[
            "creator_comment"
        ]
        self.spdx_document.spdx_id = self.code_extra_params["doc_ref"]

    def set_package_info(self, package):
        # Use a set of unique copyrights for the package.
        package.name = basename(self.path_or_file)
        if self.path_or_file == ".":
            package.name = os.getcwd().split("/")[-1]
        if self.file_to_scan:
            package.name = "{0}/{1}".format(
                basename(self.path_or_file), basename(self.file_to_scan)
            )

        package.check_sum = Algorithm("SHA1", self.get_package_checksum())

        package.homepage = SPDXNone()
        package.verif_code = self.get_package_verification_code()

        package.source_info = SPDXNone()
        package.conc_lics = NoAssert()

        package.license_declared = NoAssert()
        package.cr_text = SPDXNone()

    def create_spdx_document(self):
        """
        Write identifier scan results as SPDX Tag/value or RDF.
        """
        logging.basicConfig(level=logging.INFO)
        logging.info("Creating spdx document")
        self.get_output_file()
        self.spdx_document = Document(
            version=Version(2, 1),
            data_license=License.from_identifier(
                self.code_extra_params["lic_identifier"]
            ),
        )
        self.set_creation_info()
        if isdir(self.path_or_file):
            input_path = self.path_or_file
        else:
            input_path = dirname(self.path_or_file)

        package = self.spdx_document.package = Package(
            download_location=NoAssert(), version=self.get_package_version()
        )
        self.set_package_info(package)
        all_files_have_no_license = True
        all_files_have_no_copyright = True
        file_license_list = []
        file_license_ids = []
        if utils.is_dir(self.path_or_file):
            for idx, file_data in enumerate(self.id_scan_results):
                file_data_instance = open(file_data["FileName"], "r")
                if not utils.should_skip_file(
                    file_data["FileName"], self.output_file_name
                ):
                    name = file_data["FileName"].replace(self.path_or_file, ".")
                    file_entry = File(
                        name=name,
                        chk_sum=Algorithm(
                            "SHA1", utils.get_file_hash(file_data["FileName"]) or ""
                        ),
                    )
                    spdx_license = None
                    if self.doc_type == utils.TAG_VALUE:
                        spdx_license = License.from_identifier(file_data["SPDXID"])
                    else:
                        licenseref_id = "SPDXID-Doc-Generator-" + file_data["SPDXID"]
                        file_license_ids.append(licenseref_id)
                        if licenseref_id in file_license_ids:
                            spdx_license = ExtractedLicense(licenseref_id)
                        spdx_license.name = NoAssert()
                        comment = "N/A"
                        spdx_license.comment = comment
                        text = NoAssert()
                        if not text:
                            text = comment
                        spdx_license.text = text
                        self.spdx_document.add_extr_lic(spdx_license)
                        package.add_lics_from_file(spdx_license)
                    file_entry.add_lics(spdx_license)
                    file_license_list.append(spdx_license)
                    file_entry.conc_lics = NoAssert()
                    file_entry.copyright = SPDXNone()
                    file_entry.spdx_id = self.code_extra_params["file_ref"].format(
                        idx + 1
                    )
                    package.add_file(file_entry)
            if self.doc_type == utils.TAG_VALUE:
                for spdx_license in list(set(file_license_list)):
                    package.add_lics_from_file(spdx_license)

        if len(package.files) == 0:
            if self.doc_type == utils.TAG_VALUE:
                self.output_file.write(
                    "# No results for package '{}'.\n".format(package.name)
                )
            else:
                self.output_file.write(
                    "<!-- No results for package '{}'. -->\n".format(package.name)
                )

        if self.doc_type == utils.TAG_VALUE:
            from spdx.writers.tagvalue import write_document  # NOQA
        else:
            from spdx.writers.rdf import write_document  # NOQA

        if package.files:
            spdx_output = io.StringIO()
            if self.doc_type == utils.TAG_VALUE:
                write_document(self.spdx_document, spdx_output, validate=False)
                logging.info("SPDX Tag-Value Document created successfully.")
            else:
                # spdx_output = io.BytesIO()
                write_document(self.spdx_document, spdx_output, validate=False)
                logging.info("SPDX RDF Document created successfully.")
            result = spdx_output.getvalue()
            if self.doc_type == utils.TAG_VALUE:
                result = result.encode("utf-8")
            self.output_file.write(result)
