from misirlou.tests.mis_test import MisirlouTestSetup
from misirlou.tasks import *
from misirlou.helpers.IIIFImporter import WIPManifest
import uuid
import requests


class CeleryTaskTestCase(MisirlouTestSetup):
    """Run celery tasks as normal functions to test behaviour."""

    def test_import_single_manifest_success(self):
        rem_url = "http://localhost:8888/misirlou/tests/fixtures/manifest.json"
        data = requests.get(rem_url)
        imp_result = import_single_manifest(data.text, rem_url)
        status, imp_id, url, errors, warnings = imp_result
        self.assertTupleEqual((status, errors, warnings), (0, [], []))

    def test_import_single_manifest_fail(self):
        rem_url = "http://localhost:8888/misirlou/tests/fixtures/collection_top.json"
        data = requests.get(rem_url)
        imp_result = import_single_manifest(data.text, rem_url)
        status, imp_id, url, errors, warnings = imp_result
        expected = (-1, ["not a valid value for dictionary value @ data['@type']"], [])
        self.assertTupleEqual((status, errors, warnings), expected)

    def test_get_document(self):
        rem_url = "http://localhost:8888/misirlou/tests/fixtures/manifest.json"
        rem_data = get_document(rem_url)
        with open("misirlou/tests/fixtures/manifest.json") as f:
            local_data = f.read()
        self.assertEqual(rem_data, local_data)