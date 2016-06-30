import urllib.parse
import pdb
from voluptuous import Schema, Required, Invalid, MultipleInvalid, ALLOW_EXTRA


class ValidatorWarning:
    """Warning that can hold an in-document path and a message."""
    def __init__(self, msg, path):
        self.msg = msg
        self.path = path

    def __str__(self):
        path = ' @ data[%s]' % ']['.join(map(repr, self.path)) \
            if self.path else ''
        output = "Warning: {}".format(self.msg)
        return output + path

    def __repr__(self):
        return "ValidatorWarning('{}', {})".format(self.msg, self.path)

    def __lt__(self, other):
        return len(self.path) < len(other.path)

    def __hash__(self):
        return hash(str(self))

    def __eq__(self, other):
        return str(self) == str(other)


class ValidatorError(Invalid):

    def __str__(self):
        path = ' @ data[%s]' % ']['.join(map(repr, self.path)) \
            if self.path else ''
        output = "Error: {}".format(self.msg)
        return output + path

    def __repr__(self):
        return "ValidatorError('{}', {})".format(self.msg, self.path)

    def __eq__(self, other):
        return str(self) == str(other)

    def __hash__(self):
        return hash(str(self))

    def __lt__(self, other):
        return len(self.path) < len(other.path)


class BaseValidatorMixin:

    def __init__(self):
        """You should NOT override ___init___. Override setup() instead."""
        self.raise_warnings = True
        self._errors = set()
        self.path = tuple()
        self.is_valid = None
        self.json = None
        self._ManifestValidator = None
        self._SequenceValidator = None
        self._ImageResourceValidator = None
        self._CanvasValidator = None
        self._LangValPairs = None
        self.setup()

    def setup(self):
        self._LangValPairs = Schema(
            {
                Required('@language'): self.repeatable_string,
                Required('@value'): self.repeatable_string
            }
        )

    @property
    def errors(self):
        errs = filter(lambda err: isinstance(err, ValidatorError), self._errors)
        return sorted(errs)

    @property
    def warnings(self):
        warns = filter(lambda warn: isinstance(warn, ValidatorWarning), self._errors)
        return sorted(warns)

    @property
    def SequenceValidator(self):
        return self._ManifestValidator._SequenceValidator

    @property
    def ImageResourceValidator(self):
        return self._ManifestValidator._ImageResourceValidator

    @property
    def CanvasValidator(self):
        return self._ManifestValidator._CanvasValidator

    @SequenceValidator.setter
    def SequenceValidator(self, value):
        self._ManifestValidator._SequenceValidator = value(self._ManifestValidator)

    @ImageResourceValidator.setter
    def ImageResourceValidator(self, value):
        self._ManifestValidator._ImageResourceValidator = value(self._ManifestValidator)

    @CanvasValidator.setter
    def CanvasValidator(self, value):
        self._ManifestValidator._CanvasValidator = value(self._ManifestValidator)

    def print_errors(self):
        for err in self.errors:
            print(err)

    def print_warnings(self):
        for warn in self.warnings:
            print(warn)

    def reset(self, path):
        """Reset the validator to handle a new chunk of data."""
        self.json = None
        self.is_valid = None
        self._errors = set()
        self.path = path

    def validate(self, json_dict, path=None, raise_warnings=None, **kwargs):
        """Public method to run validation."""
        if raise_warnings is not None:
            self.raise_warnings = raise_warnings

        if not path:
            path = tuple()
        self.reset(path)

        try:
            self.json = json_dict
            self._run_validation(**kwargs)
            self.is_valid = True
        except MultipleInvalid as e:
            # Cast all errors to comparable ones before returning.
            for err in e.errors:
                if isinstance(err, ValidatorWarning):
                    self._errors.add(err)
                elif isinstance(err, ValidatorError):
                    err.path = self.path + tuple(err.path)
                    self._errors.add(err)
                else:
                    err.path = self.path + tuple(err.path)
                    new_err = ValidatorError(err.msg, tuple(err.path))
                    self._errors.add(new_err)
        if self._errors:
            self.is_valid = False

    def _run_validation(self, **kwargs):
        raise NotImplemented

    def _handle_warning(self, field, msg):
        """Add a warning to the validator if warnings are being caught.

        :param field: The field the warning was raised on.
        :param msg: The message to associate with the warning.
        :return:
        """
        if self.raise_warnings:
            self._errors.add(ValidatorWarning(msg, self.path + (field,)))

    def _sub_validate(self, subschema, value, path, **kwargs):
        """Validate a field using another Validator.

        :param subschema: A BaseValidatorMixin implementing object.
        :param value (dict): The data to be validated.
        :param path (tuple): The path where the above data exists.
            Example: ('sequences', 'canvases') for the CanvasValidator.
        :param kwargs: Any keys to subschema._run_validation()
            - canvas_uri: String passed to ImageResourceValidator from
              CanvasValidator to ensure 'on' key is valid.
        """
        subschema.validate(value, path, **kwargs)
        if subschema._errors:
            self._errors = self._errors | subschema._errors
        return subschema.json

    # Field definitions #
    def optional(self, field, fn):
        """Wrap a function to make its value optional (null and '' allows)"""
        def new_fn(*args):
            if args[0] == "" or args[0] is None:
                self._handle_warning(field, "'{}' field should not be included if it is empty.".format(field))
                return args[0]
            return fn(*args)
        return new_fn

    def not_allowed(self, value):
        """Raise invalid as this key is not allowed in the context."""
        raise ValidatorError("Key is not allowed here.")

    def str_or_val_lang(self, value):
        """Check value is str or lang/val pairs, else raise ValidatorError.

        Allows for repeated strings as per 5.3.2.
        """
        if isinstance(value, str):
            return value
        if isinstance(value, list):
            return [self.str_or_val_lang(val) for val in value]
        if isinstance(value, dict):
            return self._LangValPairs(value)
        raise ValidatorError("Str_or_val_lang: {}".format(value))

    def repeatable_string(self, value):
        """Allows for repeated strings as per 5.3.2."""
        if isinstance(value, str):
            return value
        if isinstance(value, list):
            for val in value:
                if not isinstance(val, str):
                    raise ValidatorError("Overly nested strings: {}".format(value))
            return value
        raise ValidatorError("repeatable_string: {}".format(value))

    def repeatable_uri(self, value):
        """Allow single or repeating URIs.

        Based on 5.3.2 of Presentation API
        """
        if isinstance(value, list):
            return [self.uri(val) for val in value]
        else:
            return self.uri(value)

    def http_uri(self, value):
        """Allow single URI that MUST be http(s)

        Based on 5.3.2 of Presentation API
        """
        return self.uri(value, http=True)

    def uri(self, value, http=False):
        """Check value is URI type or raise ValidatorError.

        Allows for multiple URI representations, as per 5.3.1 of the
        Presentation API.
        """
        if isinstance(value, str):
            return self._string_uri(value, http)
        elif isinstance(value, dict):
            emb_uri = value.get('@id')
            if not emb_uri:
                raise ValidatorError("URI not found: {} ".format(value))
            return self._string_uri(emb_uri, http)
        else:
            raise ValidatorError("Can't parse URI: {}".format(value))

    def _string_uri(self, value, http=False):
        """Validate that value is a string that can be parsed as URI.

        This is the last stop on the recursive structure for URI checking.
        Should not actually be used in schema.
        """
        # Always raise invalid if the string field is not a string.
        if not isinstance(value, str):
            raise ValidatorError("URI is not String: {]".format(value))
        # Try to parse the url.
        try:
            pieces = urllib.parse.urlparse(value)
        except AttributeError as a:
            raise ValidatorError("URI is not valid: {}".format(value))
        if not all([pieces.scheme, pieces.netloc]):
            raise ValidatorError("URI is not valid: {}".format(value))
        if http and pieces.scheme not in ['http', 'https']:
            raise ValidatorError("URI must be http: {}".format(value))
        return value


class ManifestValidator(BaseValidatorMixin):
    PRESENTATION_API_URI = "http://iiif.io/api/presentation/2/context.json"
    IMAGE_API_1 = "http://library.stanford.edu/iiif/image-api/1.1/context.json"
    IMAGE_API_2 = "http://iiif.io/api/image/2/context.json"

    VIEW_DIRS = ['left-to-right', 'right-to-left',
                 'top-to-bottom', 'bottom-to-top']
    VIEW_HINTS = ['individuals', 'paged', 'continuous']

    def __init__(self):
        """You should not override ___init___. Override setup() instead."""
        super().__init__()
        self._ManifestValidator = self
        self.ManifestSchema = None
        self.MetadataItemSchema = None
        self.setup()

    def setup(self):
        self._ImageResourceValidator = ImageResourceValidator(self)
        self._CanvasValidator = CanvasValidator(self)
        self._SequenceValidator = SequenceValidator(self)

        # Schema for validating manifests with flexible corrections.
        self.ManifestSchema = Schema(
            {
                # Descriptive properties
                Required('label'): self.label_field,
                '@context': self.presentation_context_field,
                'metadata': self.metadata_field,

                'description': self.description_field,
                'thumbnail': self.thumbnail_field,

                # Rights and Licensing properties
                'attribution': self.optional('attribution', self.str_or_val_lang),
                'logo': self.optional('logo', self.repeatable_uri),
                'license': self.optional('license', self.repeatable_string),

                # Technical properties
                Required('@id'): self.http_uri,
                Required('@type'): 'sc:Manifest',
                'format': self.not_allowed,
                'height': self.not_allowed,
                'width': self.not_allowed,
                'viewingDirection': self.viewing_dir,
                'viewingHint': self.viewing_hint,

                # Linking properties
                'related': self.optional('related', self.repeatable_uri),
                'service': self.optional('service', self.repeatable_uri),
                'seeAlso': self.optional('seeAlso', self.repeatable_uri),
                'within': self.optional('within', self.repeatable_uri),
                'startCanvas': self.not_allowed,
                Required('sequences'): self.sequences_field
            },
            extra=ALLOW_EXTRA
        )
        self.MetadataItemSchema = Schema(
            {
                'label': self.str_or_val_lang,
                'value': self.str_or_val_lang
            }
        )

    def _run_validation(self, **kwargs):
        return self.ManifestSchema(self.json)

    def label_field(self, value):
        """Labels can be multi-value strings per 2.1-4.3"""
        return self.str_or_val_lang(value)

    def presentation_context_field(self, value):
        if isinstance(value, str):
            if not value == self.PRESENTATION_API_URI:
                raise ValidatorError("'@context' must be set to {}".format(self.PRESENTATION_API_URI))
        if isinstance(value, list):
            if self.PRESENTATION_API_URI not in value:
                raise ValidatorError("'@context' must be set to {}".format(self.PRESENTATION_API_URI))
        return value

    def description_field(self, value):
        return self.str_or_val_lang(value)

    def metadata_field(self, value):
        """General type check for metadata.

        Recurse into keys/values and checks that they are properly formatted.
        """
        if isinstance(value, list):
            return [self.MetadataItemSchema(val) for val in value]
        raise ValidatorError("Metadata key MUST be a list.")

    def thumbnail_field(self, value):
        if isinstance(value, str):
            self._handle_warning("thumbnail", "Thumbnail SHOULD be IIIF image service.")
            return self.uri(value)
        if isinstance(value, dict):
            path = self.path + ("thumbnail",)
            return self._sub_validate(self.ImageResourceValidator, value, path)

        # TODO complete this function.

    def viewing_dir(self, value):
        """Validate against VIEW_DIRS list."""
        if value not in self.VIEW_DIRS:
            raise ValidatorError("viewingDirection: {}".format(value))
        return value

    def viewing_hint(self, value):
        """Validate against VIEW_HINTS list."""
        if value not in self.VIEW_HINTS:
            raise ValidatorError("viewingHint: {}".format(value))
        return value

    def sequences_field(self, value):
        """Validate sequence list for Manifest.

        Checks that exactly 1 sequence is embedded.
        """
        path = self.path + ("sequences", )
        return self._sub_validate(self.SequenceValidator, value, path)


class SequenceValidator(BaseValidatorMixin):
    def __init__(self, manifest_validator):
        """You should not override ___init___. Override setup() instead."""
        super().__init__()
        self._ManifestValidator = manifest_validator
        self.EmbSequenceSchema = None
        self.LinkedSequenceSchema = None
        self.setup()

    def setup(self):

        # An embedded sequence must contain canvases.
        self.EmbSequenceSchema = Schema(
            {
                Required('@type'): 'sc:Sequence',
                '@id': self.http_uri,
                'label': self.str_or_val_lang,
                Required('canvases'): self.canvas_list
            },
            extra=ALLOW_EXTRA
        )

        # A linked sequence must have an @id and no canvases
        self.LinkedSequenceSchema = Schema(
            {
                Required('@type'): 'sc:Sequence',
                Required('@id'): self.http_uri,
                'canvases': self.not_allowed
            },
            extra=ALLOW_EXTRA
        )

    def _run_validation(self, **kwargs):
        return self._validate_sequence()

    def _validate_sequence(self):
        value = self.json
        if not isinstance(value, list):
            raise ValidatorError("'sequences' must be a list.")
        lst = [self.EmbSequenceSchema(value[0])]
        lst.extend([self.LinkedSequenceSchema(s) for s in value[1:]])
        return lst

    def canvas_list(self, value):
        """Validate canvas list for Sequence."""
        if not isinstance(value, list):
            raise ValidatorError("'canvases' must be a list")
        path = self.path + ("canvases", )
        return [self._sub_validate(self.CanvasValidator, c, path) for c in value]


class CanvasValidator(BaseValidatorMixin):
    def __init__(self, manifest_validator):
        """You should not override ___init___. Override setup() instead."""
        super().__init__()

        self._ManifestValidator = manifest_validator
        self.CanvasSchema = None
        self.setup()

    def setup(self):
        self.CanvasSchema = Schema(
            {
                Required('@id'): self.http_uri,
                Required('@type'): 'sc:Canvas',
                Required('label'): self.str_or_val_lang,
                Required('height'): int,
                Required('width'): int,
                'images': self.images_field,
                'other_content': self.other_content_field
            },
            extra=ALLOW_EXTRA
        )

    def _run_validation(self, **kwargs):
        self.canvas_uri = self.json['@id']
        return self.CanvasSchema(self.json)

    def images_field(self, value):
        if isinstance(value, list):
            path = self.path + ("images",)
            return [self._sub_validate(self.ImageResourceValidator, i, path, canvas_uri=self.canvas_uri) for i in value]
        if not value:
            return
        raise ValidatorError("'images' must be a list")

    def other_content_field(self, value):
        if not isinstance(value, list):
            raise ValidatorError("other_content must be list!")
        return [self.uri(item['@id']) for item in value]


class ImageResourceValidator(BaseValidatorMixin):

    def __init__(self, manifest_validator):
        """You should not override ___init___. Override setup() instead."""
        super().__init__()

        self._ManifestValidator = manifest_validator
        self.ImageSchema = None
        self.ImageResourceSchema = None
        self.ServiceSchema = None
        self.canvas_uri = None
        self.setup()

    def setup(self):
        self.ImageSchema = Schema(
            {
                "@id": self.http_uri,
                Required('@type'): "oa:Annotation",
                Required('motivation'): "sc:painting",
                Required('resource'): self.image_resource,
                Required("on"): self.on_field
            }, extra=ALLOW_EXTRA
        )
        self.ImageResourceSchema = Schema(
            {
                Required('@id'): self.http_uri,
                '@type': self.resource_type_field,
                "service": self.image_service
            }, extra=ALLOW_EXTRA
        )

        self.ServiceSchema = Schema(
            {
                '@context': self.repeatable_string,
                '@id': self.uri,
                'profile': self.service_profile,
                'label': str
            },
            extra=ALLOW_EXTRA
        )

    def _run_validation(self, canvas_uri=None, **kwargs):
        self.canvas_uri = canvas_uri
        return self.ImageSchema(self.json)

    def id_field(self, value):
        pass

    def on_field(self, value):
        if value == self.canvas_uri:
            raise ValidatorError("'on' must reference the canvas URI.")
        return value

    def resource_type_field(self, value):
        if value != 'dctypes:Image':
            self._handle_warning("@type", "'@type' field SHOULD be dctypes:Image")
        return value

    def image_resource(self, value):
        """Validate image resources inside images list of Canvas"""
        if value.get('@type') == "dctypes:Image":
            return self.ImageResourceSchema(value)
        if value.get('@type') == 'oa:Choice':
            return self.ImageResourceSchema(value['default'])
        raise ValidatorError("Image resource has unknown type: '{}'".format(value))

    def image_service(self, value):
        """Validate against Service sub-schema."""
        if isinstance(value, str):
            return self.uri(value)
        elif isinstance(value, list):
            return [self.service(val) for val in value]
        else:
            return self.ServiceSchema(value)

    def service(self, value):
        """Validate against Service sub-schema."""
        if isinstance(value, str):
            return self.uri(value)
        elif isinstance(value, list):
            return [self.service(val) for val in value]
        else:
            return self.ServiceSchema(value)

    def service_profile(self, value):
        """Profiles in services are a special case.

        The profile key can contain a uri, or a list with extra
        metadata and a uri in the first position.
        """
        if isinstance(value, list):
            return self.uri(value[0])
        else:
            return self.uri(value)

if __name__ == "__main__":
    import requests
    import IPython
    man = requests.get("http://dev-cantus.simssa.ca/manuscript/133/manifest.json").json()
    mv = ManifestValidator()

    IPython.embed()
