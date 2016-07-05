"""This module defines special handling for manifests from specific libraries.

All functions should return a ManifestSchema() instance to be used by the
validator.

These functions specify exceptions and corrections to be made during validation
and indexing based on the systematic faults of manifests hosted by specific libraries.
They do this by patching the ManifestSchema and ManifestImporter classes with
overriding behaviour before instantiating these newly patched classes and
returning them.

Functions which return ManifestSchemas should be named get_[netloc]_validator,
where [netloc] is the hostname of the library website. Function which return
ManifestImporters should be named get_[netloc]_importer.

If possible (e.g., if all that is required is adding/removing/modifying the
return value of a particular section), the original function should be called
and changes applied afterwards (see get_harvard_edu_validator()).

The patched function should, if possible, check that the error it is designed
to correct is still present before making modifications. This way, if the
library eventually corrects their manifests, re-importing will not result in
erroneous corrections.

Include a doc string for every over-ridden function explaining its purpose.
"""
from misirlou.helpers.manifest_utils.importer import ManifestImporter
from misirlou.helpers.manifest_utils.schema_validator import ManifestValidator, ImageResourceValidator, ValidatorError
from voluptuous import Schema, Required, ALLOW_EXTRA, Invalid


def get_harvard_edu_validator():
    class PatchedImageResourceValidator(ImageResourceValidator):

        # Append a context to the image services if none exist.
        def image_service_field(self, value):
            val = super().image_service_field(value)
            if not val.get('@context'):
                val['@context'] = 'http://library.stanford.edu/iiif/image-api/1.1/context.json'
                self._handle_warning("@context", "Applied library specific corrections. Added @context to images.")
            return val

        # Allow @type to be 'dcterms:Image'
        def image_resource_field(self, value):
            if value.get('@type') in "dctypes:Image":
                return self.ImageResourceSchema(value)
            if value.get('@type') == "dcterms:Image":
                self._handle_warning("@type", "Applied library specific corrections. Allowed 'dcterms:Image'.")
                value['@type'] = 'dctypes:Image'
                return self.ImageResourceSchema(value)
            if value.get('@type') == 'oa:Choice':
                return self.ImageResourceSchema(value['default'])
            raise Invalid("Image resource has unknown type: '{}'".format(value.get('@type')))

    class PatchedManifestValidator(FlexibleManifestValidator):

        # Allow the unkown top level context (since it doesn't seem to break things")
        def presentation_context_field(self, value):
            try:
                return super().presentation_context_field(value)
            except Invalid:
                self._handle_warning("@context", "Unknown context.")
                return value

    mv = PatchedManifestValidator()
    mv.ImageResourceValidator = PatchedImageResourceValidator
    return mv


def get_vatlib_it_validator():
    class PatchedImageResourceValidator(ImageResourceValidator):

        # Alter ImageSchema to not really check the 'on' key.
        def setup(self):
            super().setup()
            self.ImageSchema = Schema(
                {
                    "@id": self.http_uri_type,
                    Required('@type'): "oa:Annotation",
                    Required('motivation'): "sc:painting",
                    Required('resource'): self.image_resource_field,
                    "on": self.http_uri_type
                }, extra=ALLOW_EXTRA
            )

        def modify_validation_return(self, json_dict):
            if not json_dict.get('on'):
                self._handle_warning("on", "Applied library specific corrections. Key requirement ignored.")
            return json_dict

    mv = FlexibleManifestValidator()
    mv.ImageResourceValidator = PatchedImageResourceValidator
    return mv


def get_stanford_edu_validator():
    class PatchedManifestSchema(FlexibleManifestValidator):
        def image_resource(self, value):
            """Allow and correct 'dcterms:Image' in place of 'dctypes:Image'."""
            try:
                val = super().image_service(value)
            except Invalid:
                if value.get('@type') == "dcterms:Image":
                    val = self._ImageResourceSchema(value)
                    val['@type'] = "dctypes:Image"
                    self.warnings.add("Applied library specific corrections.")
                elif value.get('@type') == "oa:Choice":
                        val = self._ImageResourceSchema(value['default'])
                        val['@type'] = "dctypes:Image"
                        self.warnings.add("Applied library specific corrections.")
                else:
                    raise
            return val
    return PatchedManifestSchema()


def get_archivelab_org_validator():
    class PatchedManifestSchema(FlexibleManifestValidator):
        def __init__(self):
            """Allow and correct 'type' instead of '@type' in images."""
            super().__init__()
            self._ImageSchema = Schema(
                {
                    "@id": self.http_uri,
                    '@type': "oa:Annotation",
                    'type': "oa:Annotation",
                    Required('motivation'): "sc:painting",
                    Required('resource'): self.image_resource,
                    "on": self.http_uri
                }, extra=ALLOW_EXTRA
            )
        def images_in_canvas(self, value):
            """Replace 'type' with '@type' in saved document."""
            val = super().images_in_canvas(value)
            for v in (v for v in val if v.get('type')):
                self.warnings.add("Applied library specific corrections.")
                v['@type'] = v['type']
                del v['type']
            return val
    return PatchedManifestSchema()


def get_archivelab_org_importer():
    class PatchedManifestImporter(ManifestImporter):
        def _default_thumbnail_finder(self):
            """The internet archive thumbnail are enormous."""
            tn = self.json.get("thumbnail")
            if tn and isinstance(tn, str):
                return super()._default_thumbnail_finder(force_IIIF=True, index=0)
            else:
                return super()._default_thumbnail_finder()
    return PatchedManifestImporter


def get_gallica_bnf_fr_validator():
    class PatchedManifestSchema(FlexibleManifestValidator):
        def __init__(self):
            """Allow language key to not appear in some LangVal pairs."""
            super().__init__()
            self._LangValPairs = Schema(
                {
                    '@language': self.repeatable_string,
                    Required('@value'): self.repeatable_string
                }
            )

        def metadata_type(self, value):
            """Correct any metadata entries missing a language key in lang-val pairs."""
            values = super().metadata_type(value)
            for value in values:
                v = value.get('value')
                if isinstance(v, list) and not all(vsub.get("@language") for vsub in v):
                    value['value'] = "; ".join((vsub.get("@value") for vsub in v))
            return values

    return PatchedManifestSchema()


def get_gallica_bnf_fr_importer():
    class PatchedManifestImporter(ManifestImporter):
        def _default_thumbnail_finder(self, force_IIIF=True):
            """The gallica thumbnails are very low res, so force it to pull out image."""
            return super()._default_thumbnail_finder(force_IIIF=True)
    return PatchedManifestImporter


def get_wdl_org_validator():
    class PatchedManifestSchema(FlexibleManifestValidator):
        def image_resource(self, value):
            """Allow and correct 'dcterms:Image' in place of 'dctypes:Image'."""
            try:
                val = super().image_service(value)
            except Invalid:
                if value.get('@type') == "dcterms:Image":
                    val = self._ImageResourceSchema(value)
                    val['@type'] = "dctypes:Image"
                    self.warnings.add("Applied library specific corrections.")
                elif value.get('@type') == "oa:Choice":
                    val = self._ImageResourceSchema(value['default'])
                    val['@type'] = "dctypes:Image"
                    self.warnings.add("Applied library specific corrections.")
                else:
                    raise
            return val
    return PatchedManifestSchema()

    # TODO Handle the keys that get missed in metadata.


class FlexibleManifestValidator(ManifestValidator):
    def str_or_int(self, value):
        if isinstance(value, str):
            try:
                val = int(value)
                self._handle_warning("height/width", "Replaced string with int on height/width key.")
                return val
            except ValueError:
                raise ValidatorError("Str_or_int: {}".format(value))
        if isinstance(value, int):
            return value
        raise ValidatorError("Str_or_int: {}".format(value))

    def setup(self):
        super().setup()
        self.raise_warnings = False
        self.CanvasValidator.CanvasSchema = Schema(
                {
                    Required('@id'): self.http_uri_type,
                    Required('@type'): 'sc:Canvas',
                    Required('label'): self.str_or_val_lang_type,
                    Required('height'): self.str_or_int,
                    Required('width'): self.str_or_int,
                    'images': self.CanvasValidator.images_field,
                    'other_content': self.CanvasValidator.other_content_field
                },
                extra=ALLOW_EXTRA
            )