
# Copyright (c) 2014 Ahmed H. Ismail
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#     http://www.apache.org/licenses/LICENSE-2.0
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals

import re

from spdx import checksum
from spdx import document
from spdx import version
from spdx.parsers.builderexceptions import CardinalityError
from spdx.parsers.builderexceptions import OrderError
from spdx.parsers.builderexceptions import SPDXValueError
from spdx.parsers import tagvaluebuilders
from spdx.parsers import validations


class DocBuilder(object):
    VERS_STR_REGEX = re.compile(r'SPDX-(\d+)\.(\d+)', re.UNICODE)

    def __init__(self):
        # FIXME: this state does not make sense
        self.reset_document()

    def set_doc_version(self, doc, value):
        """
        Set the document version.
        Raise exceptions:
        - SPDXValueError if malformed value,
        - CardinalityError if already defined,
        """
        if not self.doc_version_set:
            self.doc_version_set = True
            m = self.VERS_STR_REGEX.match(value)
            if m is None:
                raise SPDXValueError('Document::Version')
            else:
                doc.version = version.Version(major=int(m.group(1)),
                                              minor=int(m.group(2)))
                return True
        else:
            raise CardinalityError('Document::Version')

    def set_doc_data_lic(self, doc, res):
        """
        Set the document data license.
        Raise exceptions:
        - SPDXValueError if malformed value,
        - CardinalityError if already defined.
        """
        if not self.doc_data_lics_set:
            self.doc_data_lics_set = True
            # TODO: what is this split?
            res_parts = res.split('/')
            if len(res_parts) != 0:
                identifier = res_parts[-1]
                doc.data_license = document.License.from_identifier(identifier)
            else:
                raise SPDXValueError('Document::License')
        else:
            raise CardinalityError('Document::License')

    def set_doc_name(self, doc, name):
        """
        Sets the document name, raises CardinalityError if already defined.
        """
        if not self.doc_name_set:
            doc.name = name
            self.doc_name_set = True
            return True
        else:
            raise CardinalityError('Document::Name')

    def set_doc_spdx_id(self, doc, doc_spdx_id_line):
        """Sets the document SPDX Identifier.
        Raises value error if malformed value, CardinalityError
        if already defined.
        """
        if not self.doc_spdx_id_set:
            if validations.validate_doc_spdx_id(doc_spdx_id_line):
                doc.spdx_id = doc_spdx_id_line
                self.doc_spdx_id_set = True
                return True
            else:
                raise SPDXValueError('Document::SPDXID')
        else:
            raise CardinalityError('Document::SPDXID')

    def set_doc_comment(self, doc, comment):
        """Sets document comment, Raises CardinalityError if
        comment already set.
        """
        if not self.doc_comment_set:
            self.doc_comment_set = True
            doc.comment = comment
        else:
            raise CardinalityError('Document::Comment')

    def set_doc_namespace(self, doc, namespace):
        """Sets the document namespace.
        Raise SPDXValueError if malformed value, CardinalityError
        if already defined.
        """
        if not self.doc_namespace_set:
            self.doc_namespace_set = True
            if validations.validate_doc_namespace(namespace):
                doc.namespace = namespace
                return True
            else:
                raise SPDXValueError('Document::Namespace')
        else:
            raise CardinalityError('Document::Comment')

    def reset_document(self):
        """
        Reset the internal state to allow building new document
        """
        # FIXME: this state does not make sense
        self.doc_version_set = False
        self.doc_comment_set = False
        self.doc_namespace_set = False
        self.doc_data_lics_set = False
        self.doc_name_set = False
        self.doc_spdx_id_set = False


class ExternalDocumentRefBuilder(tagvaluebuilders.ExternalDocumentRefBuilder):

    def set_chksum(self, doc, chk_sum):
        """
        Sets the external document reference's check sum, if not already set.
        chk_sum - The checksum value in the form of a string.
        """
        if chk_sum:
            doc.ext_document_references[-1].check_sum = checksum.Algorithm(
                'SHA1', chk_sum)
        else:
            raise SPDXValueError('ExternalDocumentRef::Checksum')


class EntityBuilder(tagvaluebuilders.EntityBuilder):

    def __init__(self):
        super(EntityBuilder, self).__init__()

    def create_entity(self, doc, value):
        if self.tool_re.match(value):
            return self.build_tool(doc, value)
        elif self.person_re.match(value):
            return self.build_person(doc, value)
        elif self.org_re.match(value):
            return self.build_org(doc, value)
        else:
            raise SPDXValueError('Entity')


class CreationInfoBuilder(tagvaluebuilders.CreationInfoBuilder):

    def __init__(self):
        super(CreationInfoBuilder, self).__init__()

    def set_creation_comment(self, doc, comment):
        """Sets creation comment, Raises CardinalityError if
        comment already set.
        Raises SPDXValueError if not free form text.
        """
        if not self.creation_comment_set:
            self.creation_comment_set = True
            doc.creation_info.comment = comment
            return True
        else:
            raise CardinalityError('CreationInfo::Comment')


class PackageBuilder(tagvaluebuilders.PackageBuilder):

    def __init__(self):
        super(PackageBuilder, self).__init__()

    def set_pkg_chk_sum(self, doc, chk_sum):
        """Sets the package check sum, if not already set.
        chk_sum - A string
        Raises CardinalityError if already defined.
        Raises OrderError if no package previously defined.
        """
        self.assert_package_exists()
        if not self.package_chk_sum_set:
            self.package_chk_sum_set = True
            doc.package.check_sum = checksum.Algorithm('SHA1', chk_sum)
        else:
            raise CardinalityError('Package::CheckSum')

    def set_pkg_source_info(self, doc, text):
        """Sets the package's source information, if not already set.
        text - Free form text.
        Raises CardinalityError if already defined.
        Raises OrderError if no package previously defined.
        """
        self.assert_package_exists()
        if not self.package_source_info_set:
            self.package_source_info_set = True
            doc.package.source_info = text
            return True
        else:
            raise CardinalityError('Package::SourceInfo')

    def set_pkg_verif_code(self, doc, code):
        """Sets the package verification code, if not already set.
        code - A string.
        Raises CardinalityError if already defined.
        Raises OrderError if no package previously defined.
        """
        self.assert_package_exists()
        if not self.package_verif_set:
            self.package_verif_set = True
            doc.package.verif_code = code
        else:
            raise CardinalityError('Package::VerificationCode')

    def set_pkg_excl_file(self, doc, filename):
        """Sets the package's verification code excluded file.
        Raises OrderError if no package previously defined.
        """
        self.assert_package_exists()
        doc.package.add_exc_file(filename)

    def set_pkg_license_comment(self, doc, text):
        """Sets the package's license comment.
        Raises OrderError if no package previously defined.
        Raises CardinalityError if already set.
        """
        self.assert_package_exists()
        if not self.package_license_comment_set:
            self.package_license_comment_set = True
            doc.package.license_comment = text
            return True
        else:
            raise CardinalityError('Package::LicenseComment')

    def set_pkg_cr_text(self, doc, text):
        """Sets the package's license comment.
        Raises OrderError if no package previously defined.
        Raises CardinalityError if already set.
        """
        self.assert_package_exists()
        if not self.package_cr_text_set:
            self.package_cr_text_set = True
            doc.package.cr_text = text
        else:
            raise CardinalityError('Package::CopyrightText')

    def set_pkg_summary(self, doc, text):
        """Set's the package summary.
        Raises CardinalityError if summary already set.
        Raises OrderError if no package previously defined.
        """
        self.assert_package_exists()
        if not self.package_summary_set:
            self.package_summary_set = True
            doc.package.summary = text
        else:
            raise CardinalityError('Package::Summary')

    def set_pkg_desc(self, doc, text):
        """Set's the package's description.
        Raises CardinalityError if description already set.
        Raises OrderError if no package previously defined.
        """
        self.assert_package_exists()
        if not self.package_desc_set:
            self.package_desc_set = True
            doc.package.description = text
        else:
            raise CardinalityError('Package::Description')


class FileBuilder(tagvaluebuilders.FileBuilder):

    def __init__(self):
        super(FileBuilder, self).__init__()

    def set_file_chksum(self, doc, chk_sum):
        """Sets the file check sum, if not already set.
        chk_sum - A string
        Raises CardinalityError if already defined.
        Raises OrderError if no package previously defined.
        """
        if self.has_package(doc) and self.has_file(doc):
            if not self.file_chksum_set:
                self.file_chksum_set = True
                self.file(doc).chk_sum = checksum.Algorithm('SHA1', chk_sum)
                return True
            else:
                raise CardinalityError('File::CheckSum')
        else:
            raise OrderError('File::CheckSum')

    def set_file_license_comment(self, doc, text):
        """
        Raises OrderError if no package or file defined.
        Raises CardinalityError if more than one per file.
        """
        if self.has_package(doc) and self.has_file(doc):
            if not self.file_license_comment_set:
                self.file_license_comment_set = True
                self.file(doc).license_comment = text
                return True
            else:
                raise CardinalityError('File::LicenseComment')
        else:
            raise OrderError('File::LicenseComment')

    def set_file_copyright(self, doc, text):
        """Raises OrderError if no package or file defined.
        Raises CardinalityError if more than one.
        """
        if self.has_package(doc) and self.has_file(doc):
            if not self.file_copytext_set:
                self.file_copytext_set = True
                self.file(doc).copyright = text
                return True
            else:
                raise CardinalityError('File::CopyRight')
        else:
            raise OrderError('File::CopyRight')

    def set_file_comment(self, doc, text):
        """Raises OrderError if no package or no file defined.
        Raises CardinalityError if more than one comment set.
        """
        if self.has_package(doc) and self.has_file(doc):
            if not self.file_comment_set:
                self.file_comment_set = True
                self.file(doc).comment = text
                return True
            else:
                raise CardinalityError('File::Comment')
        else:
            raise OrderError('File::Comment')

    def set_file_notice(self, doc, text):
        """Raises OrderError if no package or file defined.
        Raises CardinalityError if more than one.
        """
        if self.has_package(doc) and self.has_file(doc):
            if not self.file_notice_set:
                self.file_notice_set = True
                self.file(doc).notice = tagvaluebuilders.str_from_text(text)
                return True
            else:
                raise CardinalityError('File::Notice')
        else:
            raise OrderError('File::Notice')


class SnippetBuilder(tagvaluebuilders.SnippetBuilder):

    def __init__(self):
        super(SnippetBuilder, self).__init__()

    def set_snippet_lic_comment(self, doc, lic_comment):
        """Sets the snippet's license comment.
        Raises OrderError if no snippet previously defined.
        Raises CardinalityError if already set.
        """
        self.assert_snippet_exists()
        if not self.snippet_lic_comment_set:
            self.snippet_lic_comment_set = True
            doc.snippet[-1].license_comment = lic_comment
        else:
            CardinalityError('Snippet::licenseComments')

    def set_snippet_comment(self, doc, comment):
        """
        Sets general comments about the snippet.
        Raises OrderError if no snippet previously defined.
        Raises CardinalityError if comment already set.
        """
        self.assert_snippet_exists()
        if not self.snippet_comment_set:
            self.snippet_comment_set = True
            doc.snippet[-1].comment = comment
            return True
        else:
            raise CardinalityError('Snippet::comment')

    def set_snippet_copyright(self, doc, copyright):
        """Sets the snippet's copyright text.
        Raises OrderError if no snippet previously defined.
        Raises CardinalityError if already set.
        """
        self.assert_snippet_exists()
        if not self.snippet_copyright_set:
            self.snippet_copyright_set = True
            doc.snippet[-1].copyright = copyright
        else:
            raise CardinalityError('Snippet::copyrightText')


class ReviewBuilder(tagvaluebuilders.ReviewBuilder):

    def __init__(self):
        super(ReviewBuilder, self).__init__()

    def add_review_comment(self, doc, comment):
        """Sets the review comment. Raises CardinalityError if
        already set. OrderError if no reviewer defined before.
        """
        if len(doc.reviews) != 0:
            if not self.review_comment_set:
                self.review_comment_set = True
                doc.reviews[-1].comment = comment
                return True
            else:
                raise CardinalityError('ReviewComment')
        else:
            raise OrderError('ReviewComment')


class AnnotationBuilder(tagvaluebuilders.AnnotationBuilder):

    def __init__(self):
        super(AnnotationBuilder, self).__init__()

    def add_annotation_comment(self, doc, comment):
        """Sets the annotation comment. Raises CardinalityError if
        already set. OrderError if no annotator defined before.
        """
        if len(doc.annotations) != 0:
            if not self.annotation_comment_set:
                self.annotation_comment_set = True
                doc.annotations[-1].comment = comment
                return True
            else:
                raise CardinalityError('AnnotationComment')
        else:
            raise OrderError('AnnotationComment')

    def add_annotation_type(self, doc, annotation_type):
        """Sets the annotation type. Raises CardinalityError if
        already set. OrderError if no annotator defined before.
        """
        if len(doc.annotations) != 0:
            if not self.annotation_type_set:
                if annotation_type.endswith('annotationType_other'):
                    self.annotation_type_set = True
                    doc.annotations[-1].annotation_type = 'OTHER'
                    return True
                elif annotation_type.endswith('annotationType_review'):
                    self.annotation_type_set = True
                    doc.annotations[-1].annotation_type = 'REVIEW'
                    return True
                else:
                    raise SPDXValueError('Annotation::AnnotationType')
            else:
                raise CardinalityError('Annotation::AnnotationType')
        else:
            raise OrderError('Annotation::AnnotationType')


class Builder(DocBuilder, EntityBuilder, CreationInfoBuilder, PackageBuilder,
              FileBuilder, SnippetBuilder, ReviewBuilder, ExternalDocumentRefBuilder,
              AnnotationBuilder):

    def __init__(self):
        super(Builder, self).__init__()
        # FIXME: this state does not make sense
        self.reset()

    def reset(self):
        """Resets builder's state for building new documents.
        Must be called between usage with different documents.
        """
        # FIXME: this state does not make sense
        self.reset_creation_info()
        self.reset_document()
        self.reset_package()
        self.reset_file_stat()
        self.reset_reviews()
        self.reset_annotations()
