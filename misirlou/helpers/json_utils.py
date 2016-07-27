def parse_lang_value(value, lang="en"):
    """Parse a value with preference for specified language.

    If the value is a dictionary, return either a @value key
    or a @id key (these are the 'values' of the two patterns
    used by IIIF documents).

    If the value is a list, go through its members, keeping
    track of those values in our preferred language and those
    that are not. Then, return the most preferred item (the
    first value in the correct language, or the first found
    value)
    """
    if isinstance(value, dict):
        val = value.get("@value")
        id = value.get("@id")
        return value if value else id
    if isinstance(value, list):
        prefered = []
        wrong = []
        for v in value:
            if isinstance(v, dict):
                l = v.get("@language")
                if l == lang:
                    prefered.append(v.get("@value"))
                else:
                    wrong.append(v.get("@value"))
                    wrong.append(v.get("@id"))
            if isinstance(v, str):
                wrong.append(v)
        for p in filter(None, prefered):
            return p
        for w in filter(None, wrong):
            return w
    if isinstance(value, str):
        return value


def get_metadata_value(metadata, key, ignore_case=True):
    """Get an item from the metadata list.

    Ignores case by default.
    """
    if ignore_case:
        key = key.lower()

    if not metadata:
        return None

    for m in metadata:
        label = parse_lang_value(m.get("label"))
        label = label.lower() if ignore_case else label
        if label == key:
            return m.get("value")
    return None
