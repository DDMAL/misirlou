from rest_framework.response import Response
from rest_framework import status
from rest_framework import generics

from misirlou.renderers import SinglePageAppRenderer


class SearchView(generics.GenericAPIView):
    renderer_classes = (SinglePageAppRenderer,)

    def get(self, request, *args, **kwargs):
        if request.GET.get('q'):
            return Response({'q': request.GET.get('q')})
        else:
            return Response({'error': 'Did not provide query (q).'},
                            status=status.HTTP_400_BAD_REQUEST)
