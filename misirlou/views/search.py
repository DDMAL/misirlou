from rest_framework.response import Response
from rest_framework.renderers import JSONRenderer
from rest_framework.renderers import BrowsableAPIRenderer
from rest_framework import status
from rest_framework import generics

from misirlou.renderers import SinglePageAppRenderer
from django.conf import settings
import scorched

class SearchView(generics.GenericAPIView):
    renderer_classes = (SinglePageAppRenderer, JSONRenderer,
                        BrowsableAPIRenderer)

    def get(self, request, *args, **kwargs):
        if not request.GET.get('q'):
            return Response({'error': 'Did not provide query (q).'},
                            status=status.HTTP_400_BAD_REQUEST)
        solr_conn = scorched.SolrInterface(settings.SOLR_SERVER)
        response = solr_conn.query(request.GET.get('q')).execute()
        results = {'results': response.result.docs}
        return Response(results, content_type="charset=utf-8")
