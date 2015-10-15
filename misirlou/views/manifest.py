import uuid
import json

from django.conf import settings

from misirlou.models import Manifest
from misirlou.serializers import ManifestSerializer

from rest_framework import generics
from rest_framework.renderers import JSONRenderer, BrowsableAPIRenderer
from rest_framework.response import Response
from rest_framework import status
from rest_framework.reverse import reverse

from misirlou.renderers import SinglePageAppRenderer
from misirlou.tasks import create_manifest


class ManifestImportError(Exception):
    def __init__(self, message, **kwargs):
        self.message = message
        self.data = kwargs


class ManifestDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Manifest.objects.all()
    serializer_class = ManifestSerializer
    renderer_classes = (SinglePageAppRenderer, JSONRenderer,
                        BrowsableAPIRenderer)


class ManifestList(generics.ListCreateAPIView):
    queryset = Manifest.objects.all()
    serializer_class = ManifestSerializer

    def post(self, request, *args, **kwargs):
        if request.META.get('CONTENT_TYPE') != 'application/json':
            remote_url = request.POST.get('remote_url')
        else:
            encoding = request.encoding or settings.DEFAULT_CHARSET
            j_dump = json.loads(request.body.decode(encoding))

            if isinstance(j_dump, dict):
                remote_url = j_dump.get('remote_url')
            else:
                remote_url = None

        if not remote_url:
            return Response(
                {'error': 'Did not provide remote_url.'},
                status=status.HTTP_400_BAD_REQUEST)

        shared_id = str(uuid.uuid4())
        create_manifest.apply_async(args=[remote_url, shared_id],
                                    task_id=shared_id)
        status_url = reverse('status', request=request, args=[shared_id])
        return Response({'status': status_url}, status.HTTP_202_ACCEPTED)
