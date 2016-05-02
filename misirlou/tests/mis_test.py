import scorched
from urllib.parse import urlparse, parse_qs

from django.conf import settings
from django.test import Client
from rest_framework.test import APITestCase


class MisirlouTestSetup(APITestCase):

    @classmethod
    def setUpClass(cls):
        settings.SOLR_SERVER = settings.SOLR_TEST
        cls.client = Client()
        cls.solr_con = scorched.SolrInterface(settings.SOLR_SERVER)

    @classmethod
    def tearDownClass(cls):
        pass

    def normalize_url(self, url):
        """Sort query parameters for json dict equality checks.

        Returns the given url, with all its query parameters sorted.
        """
        o = urlparse(url)
        qs = parse_qs(o.query)
        sqs = []
        for key in sorted(qs.keys()):
            for val in sorted(qs[key]):
                sqs.append(key+"="+val)
        sqs = "?" + "&".join(sqs)

        return o.scheme + "://" + o.netloc + o.path + o.params + sqs + o.fragment
