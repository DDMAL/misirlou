from urllib import parse
import scorched
import ujson as json
import requests

from rest_framework.response import Response
from rest_framework.renderers import JSONRenderer, BrowsableAPIRenderer
from rest_framework import generics
from django.conf import settings
from rest_framework.reverse import reverse

from misirlou.renderers import SinglePageAppRenderer


class RootView(generics.GenericAPIView):
    renderer_classes = (SinglePageAppRenderer, JSONRenderer,
                        BrowsableAPIRenderer)

    def get(self, request, *args, **kwargs):
        results = {}
        if request.GET.get('q'):
            results['search'] = do_minimal_search(request)

        results['routes'] = {
            'manifests': reverse('manifest-list', request=request),
        }
        return Response(results)


class StatsView(generics.GenericAPIView):
    renderer_classes = (JSONRenderer,)

    def get(self, request, *args, **kwargs):
        """Return basic stats about the indexed data."""
        url = settings.SOLR_SERVER + "select?group=true&group.field=attribution&group.ngroups=true&q=*:*&wt=json&fl=id"
        resp = requests.get(url).json()
        num = resp['grouped']['attribution']['matches']
        atts = resp['grouped']['attribution']['ngroups']

        return Response({"manifests": num, "attributions": atts})


def do_minimal_search(request):
    page = request.GET.get('page')
    if page:
        start = ((int(page)-1)*10)
    else:
        start = 0

    solr_conn = scorched.SolrInterface(settings.SOLR_SERVER)
    response = solr_conn.query(request.GET.get('q'))\
        .set_requesthandler('/minimal')\
        .paginate(start=start).execute()

    return format_response(request, response)


def format_response(request, scorched_response, page_by=10):
    """Format response dict according to API
    :param request: django request object
    :param scorched_response: Scorched solr response object
    :return: dict with proper nesting and formatting for response
    """
    num_found = scorched_response.result.numFound
    params = scorched_response.params
    hl = scorched_response.highlighting
    q = params['q']
    documents = scorched_response.result.docs
    page = int(request.GET.get('page', 1))
    request_url = request.build_absolute_uri()

    if num_found % page_by:
        max_page = (num_found // page_by) + 1
    else:
        max_page = (num_found // page_by)

    scheme, netloc, path, query_string, fragment = parse.urlsplit(request_url)
    qs = parse.parse_qs(query_string)

    # Finding next page.
    if page < max_page:
        qs['page'] = page + 1
        query_string = parse.urlencode(qs, doseq=True)
        next_page = parse.urlunsplit((scheme, netloc, path, query_string, fragment))
    else:
        next_page = None

    # Finding previous page.
    if page > 1:
        qs['page'] = page - 1
        query_string = parse.urlencode(qs, doseq=True)
        prev_page = parse.urlunsplit((scheme, netloc, path, query_string, fragment))
    else:
        prev_page = None

    # Finding last page.
    qs['page'] = max_page
    query_string = parse.urlencode(qs, doseq=True)
    last_page = parse.urlunsplit((scheme, netloc, path, query_string, fragment))

    results = []
    for doc in documents:
        id = doc.get('id')
        result = {
            '@id': doc.get('remote_url'),
            'local_id': id,
            'label': doc.get('label'),
            'description': doc.get('description'),
            'attribution': doc.get('attribution'),
            'hits': []
        }

        thumbnail = doc.get('thumbnail')
        result['thumbnail'] = json.loads(thumbnail) if thumbnail else None
        logo = doc.get('logo')
        result['logo'] = json.loads(logo) if logo else None

        # Append highlights.
        highlights = hl.get(id)
        for k, v in highlights.items():
            values = v[0].split('[$M$]')
            hit = {
                'field': k,
                'parsed': [v for v in values]
            }
            result['hits'].append(hit)

        results.append(result)

    response = {
        '@id': request_url,
        'num_found': num_found,
        'q': q,
        'next': next_page,
        'prev': prev_page,
        'last': last_page,
        'results': results,
        'spellcheck': None
    }

    if scorched_response.spellcheck.get('collations'):
        response['spellcheck'] = scorched_response.spellcheck['collations'][1]

    return response
