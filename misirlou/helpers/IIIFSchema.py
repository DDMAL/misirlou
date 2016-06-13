from voluptuous import Schema, Required, Invalid, ALLOW_EXTRA
import urllib.parse


class ManifestSchema:
    VIEW_DIRS = ['left-to-right', 'right-to-left',
                 'top-to-bottom', 'bottom-to-top']
    VIEW_HINTS = ['individuals', 'paged', 'continuous']

    def validate(self, jdump,):
        """Validate a Manifest.

        :param jdump: Json dump of a IIIF2.0 Manifest
        :return: Any errors or None.
        """
        self.is_valid = None
        self.errors = []
        self.warnings = set()
        try:
            if self.STRICT:
                self.modified_manifest = jdump
                self.ManifestSchema(jdump)
            else:
                self.modified_manifest = self.ManifestSchema(jdump)
            self.is_valid = True
            self.warnings = list(self.warnings)
        except Exception as e:
            self.errors.append(str(e))
            self.is_valid = False

    def __init__(self, strict=False):
        """Create a ManifestSchema validator.

        :param strict: Set to True to disable heuristics and correction.
        """
        self.STRICT = strict
        self.warnings = set()
        self.errors = []
        self.is_valid = None
        self.modified_manifest = None

        # Sub-schema for services.
        if self.STRICT:
            self._Service = Schema(
                {
                    Required('@context'): self.uri,
                    '@id': self.uri,
                    'profile': self.service_profile,
                    'label': str
                },
                extra=ALLOW_EXTRA
            )
        else:
            self._Service = Schema(
                {
                    '@context': self.repeatable_string,
                    '@id': self.uri,
                    'profile': self.service_profile,
                    'label': str
                },
                extra=ALLOW_EXTRA
            )

        # Sub-schema for checking items in the metadata list.
        self._MetadataItem = Schema(
            {
                'label': self.str_or_val_lang,
                'value': self.str_or_val_lang
            }
        )

        # Sub-schema for lang-val pairs which can stand in for some stings as defined in 5.3.3
        self._LangValPairs = Schema(
            {
                '@language': self.repeatable_string,
                '@value': self.repeatable_string
            }
        )

        # Sub-schema for images. Do not require the redundant 'on' key in flexible mode.
        if self.STRICT:
            self._ImageSchema = Schema(
                {
                    "@id": self.http_uri,
                    Required('@type'): "oa:Annotation",
                    Required('motivation'): "sc:painting",
                    Required('resource'): self.image_resource,
                    Required("on"): self.http_uri
                }, extra=ALLOW_EXTRA
            )
        else:
            self._ImageSchema = Schema(
                {
                    "@id": self.http_uri,
                    Required('@type'): "oa:Annotation",
                    Required('motivation'): "sc:painting",
                    Required('resource'): self.image_resource,
                    "on": self.http_uri
                }, extra=ALLOW_EXTRA
            )

        # Sub-schema for image-resources.
        self._ImageResourceSchema = Schema(
            {
                Required('@id'): self.http_uri,
                '@type': 'dctypes:Image',
                "service": self.service
            }, extra=ALLOW_EXTRA
        )

        # Sub-schema for Canvases.
        self._CanvasSchema = Schema(
            {
                Required('@id'): self.http_uri,
                Required('@type'): 'sc:Canvas',
                Required('label'): self.str_or_val_lang,
                Required('height'): int if self.STRICT else self.str_or_int,
                Required('width'): int if self.STRICT else self.str_or_int,
                'images': self.images_in_canvas,
                'other_content': self.other_content
            },
            extra=ALLOW_EXTRA
        )

        # An embedded sequence must contain canvases.
        self._EmbSequenceSchema = Schema(
            {
                Required('@type'): 'sc:Sequence',
                '@id': self.http_uri,
                'label': self.str_or_val_lang,
                Required('canvases'): self.sequence_canvas_list
            },
            extra=ALLOW_EXTRA
        )

        # A linked sequence must have an @id and no canvases
        self._LinkedSequenceSchema = Schema(
            {
                Required('@type'): 'sc:Sequence',
                Required('@id'): self.http_uri,
                'canvases': self.not_allowed
            },
            extra=ALLOW_EXTRA
        )

        # Schema for validating manifests with flexible corrections.
        self.ManifestSchema = Schema(
            {
                # Descriptive properties
                Required('label'): self.str_or_val_lang,
                '@context': self.http_uri,
                'metadata': self.metadata_type,
                'description': self.str_or_val_lang,
                'thumbnail': self.uri_or_image_resource,

                # Rights and Licensing properties
                'attribution': self.str_or_val_lang,
                'logo': self.uri_or_image_resource,
                'license': self.repeatable_string,

                # Technical properties
                Required('@id'): self.http_uri,
                Required('@type'): 'sc:Manifest',
                'format': self.not_allowed,
                'height': self.not_allowed,
                'width': self.not_allowed,
                'viewingDirection': self.viewing_dir,
                'viewingHint': self.viewing_hint,

                # Linking properties
                'related': self.repeatable_uri,
                'service': self.service,
                'seeAlso': self.repeatable_uri,
                'within': self.repeatable_uri,
                'startCanvas': self.not_allowed,
                Required('sequences'): self.manifest_sequence_list
            },
            extra=ALLOW_EXTRA
        )

    def not_allowed(self, value):
        """Raise invalid as this key is not allowed in the context."""
        raise Invalid("Key is not allowed here.")

    def str_or_int(self, value):
        if isinstance(value, str):
            try:
                val = int(value)
                self.warnings.add("Replaced string with int on height/width key.")
                return val
            except ValueError:
                raise Invalid("Str_or_int: {}".format(value))
        if isinstance(value, int):
            return value
        raise Invalid("Str_or_int: {}".format(value))

    def str_or_val_lang(self, value):
        """Check value is str or lang/val pairs, else raise Invalid.

        Allows for repeated strings as per 5.3.2.
        """
        if isinstance(value, str):
            return value
        if isinstance(value, list):
            return [self.str_or_val_lang(val) for val in value]
        if isinstance(value, dict):
            return self._LangValPairs(value)
        raise Invalid("Str_or_val_lang: {}".format(value))

    def repeatable_string(self, value):
        """Allows for repeated strings as per 5.3.2."""
        if isinstance(value, str):
            return value
        if isinstance(value, list):
            for val in value:
                if not isinstance(val, str):
                    raise Invalid("Overly nested strings: {}".format(value))
            return value
        raise Invalid("repeatable_string: {}".format(value))

    def metadata_type(self, value):
        """General type check for metadata.

        Recurse into keys/values and checks that they are properly formatted.
        """
        if isinstance(value, list):
            return [self._MetadataItem(val) for val in value]
        raise Invalid("Metadata is malformed.")

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
        """Check value is URI type or raise Invalid.

        Allows for multiple URI representations, as per 5.3.1 of the
        Presentation API.
        """
        if isinstance(value, str):
            return self._string_uri(value, http)
        elif isinstance(value, dict):
            emb_uri = value.get('@id')
            if not emb_uri:
                raise Invalid("URI not found: {} ".format(value))
            return self._string_uri(emb_uri, http)
        else:
            raise Invalid("Can't parse URI: {}".format(value))



    def _string_uri(self, value, http=False):
        """Validate that value is a string that can be parsed as URI.

        This is the last stop on the recursive structure for URI checking.
        Should not actually be used in schema.
        """
        if not isinstance(value, str):
            raise Invalid("URI is not String: {]".format(value))
        try:
            pieces = urllib.parse.urlparse(value)
        except AttributeError as a:
            raise Invalid("URI is not valid: {}".format(value))
        if not all([pieces.scheme, pieces.netloc]):
            raise Invalid("URI is not valid: {}".format(value))
        if http and pieces.scheme not in ['http', 'https']:
            raise Invalid("URI must be http: {}".format(value))
        return value

    def uri_or_image_resource(self, value):
        """Check value is URI or image_resource or raise Invalid.

        This is to be applied to Thumbnails, Logos, and other fields
        that could be a URI or image resource.
        """
        if not self.STRICT and not value:
            # Null out the field if some falsey value was passed in.
            return None
        try:
            return self.repeatable_uri(value)
        except Invalid:
            return self.service(value)

    def service(self, value):
        """Validate against Service sub-schema."""
        if isinstance(value, str):
            return self.uri(value)
        elif isinstance(value, list):
            return [self.service(val) for val in value]
        else:
            return self._Service(value)

    def service_profile(self, value):
        """Profiles in services are a special case.

        The profile key can contain a uri, or a list with extra
        metadata and a uri in the first position.
        """
        if isinstance(value, list):
            return self.uri(value[0])
        else:
            return self.uri(value)

    def viewing_dir(self, value):
        """Validate against VIEW_DIRS list."""
        if value not in self.VIEW_DIRS:
            raise Invalid("viewingDirection: {}".format(value))
        return value

    def viewing_hint(self, value):
        """Validate against VIEW_HINTS list."""
        if value not in self.VIEW_HINTS:
            raise Invalid("viewingHint: {}".format(value))
        return value

    def manifest_sequence_list(self, value):
        """Validate sequence list for Manifest.

        Checks that exactly 1 sequence is embedded.
        """
        if not isinstance(value, list):
            raise Invalid("'sequences' must be a list")
        lst = [self._EmbSequenceSchema(value[0])]
        lst.extend([self._LinkedSequenceSchema(s) for s in value[1:]])
        return lst

    def sequence_canvas_list(self, value):
        """Validate canvas list for Sequence."""
        if not isinstance(value, list):
            raise Invalid("'canvases' must be a list")
        return [self._CanvasSchema(c) for c in value]

    def images_in_canvas(self, value):
        """Validate images list for Canvas"""
        if isinstance(value, list):
            return [self._ImageSchema(i) for i in value]
        if not value:
            return
        raise Invalid("'images' must be a list")

    def image_resource(self, value):
        """Validate image resources inside images list of Canvas"""
        if value['@type'] == "dctypes:Image":
            return self._ImageResourceSchema(value)
        if value['@type'] == 'oa:Choice':
            return self._ImageResourceSchema(value['default'])

    def other_content(self, value):
        if not isinstance(value, list):
            raise Invalid("other_content must be list!")
        return [self.uri(item['@id']) for item in value]
