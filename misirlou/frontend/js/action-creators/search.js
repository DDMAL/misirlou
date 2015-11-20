import debounce from 'lodash.debounce';

import { PROCESSING, ERROR, SUCCESS } from '../async-status-record';
import { SEARCH_REQUEST_STATUS_CHANGE } from '../actions';

import * as Search from '../api/search';


const DEBOUNCE_INTERVAL = 500;


/**
 * Load the first page of search results, ensuring that requests are throttled and cached
 * results are not re-requested
 */
export function request({ query })
{
    return (dispatch, getState) => execRequest(query, dispatch, getState);
}

/**
 * Load the next page of search results for the given query. This is a no-op if the
 * query hasn't previously been requested or if it isn't in a success state.
 */
export function loadNextPage({ query })
{
    return (dispatch, getState) =>
    {
        const existing = getState().search.get(query);

        if (existing.status !== SUCCESS || !existing.value || existing.value.nextPage === null)
            return;

        dispatch(getSearchAction(PROCESSING, query));

        Search.loadPage(existing.value.nextPage).then(
            response => dispatch(getSearchAction(SUCCESS, query, { response })),
            error => dispatch(getSearchAction(ERROR, query, { error }))
        );
    };
}

const execRequest = debounce((query, dispatch, getState) =>
{
    const cached = getState().search.get(query);

    if (cached && cached.status !== ERROR)
        return;

    dispatch(getSearchAction(PROCESSING, query));

    Search.get(query).then(
        response => dispatch(getSearchAction(SUCCESS, query, { response })),
        error => dispatch(getSearchAction(ERROR, query, { error }))
    );
}, DEBOUNCE_INTERVAL);

/** Get a search status change action for the given status and query */
function getSearchAction(status, query, extra = null)
{
    return {
        type: SEARCH_REQUEST_STATUS_CHANGE,
        payload: {
            ...extra,
            status,
            query
        }
    };
}
