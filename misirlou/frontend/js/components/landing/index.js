import React, { PropTypes } from 'react';
import CSSTransitionGroup from 'react-addons-css-transition-group';
import { locationShape } from 'react-router';
import { connect } from 'react-redux';
import { createSelector } from 'reselect';

import Navbar from './navbar';
import Footer from './footer';
import * as ManifestActions from '../../action-creators/manifest';
import ManifestResource from '../../resources/manifest-resource';
import ManifestDisplay from '../manifest-detail/manifest-display';
import SearchResults from '../search/search-results';
import ManifestCascade from './manifest-cascade/index';

import './landing-page.scss';
import './propagate-height.scss';


const TRANSITION_SETTINGS = {
    transitionName: {
        enter: 'recent-uploads--enter',
        leave: 'recent-uploads--leave'
    },
    transitionEnterTimeout: 400,
    transitionLeaveTimeout: 250
};

const manifestRequestSelector = createSelector(
    state => state.manifests,
    (_, props) => props.params.manifestId,
    (manifests, id) => ({ manifestRequest: manifests.get(id) })
);

/**
 * Render the landing page, which features a search function and a cascade of
 * recently uploaded manifests.
 */
@connect(manifestRequestSelector)
export default class LandingPage extends React.Component
{

    static propTypes = {
        params: PropTypes.shape({
            manifestId: PropTypes.string
        }).isRequired,

        location: locationShape,
        routes: PropTypes.array.isRequired,

        dispatch: PropTypes.func.isRequired,
        manifestRequest: PropTypes.instanceOf(ManifestResource)
    };

    componentDidMount()
    {
        console.log(this.props.manifestId);
        // Load the manifest if it isn't already loaded
        if (this.props.params.manifestId && !this.manifestRequest)
            this._loadManifest(this.props.params.manifestId);
    }

    componentWillReceiveProps(nextProps)
    {
        if (nextProps.params.manifestId && nextProps.params.manifestId !== this.props.params.manifestId)
            this._loadManifest(nextProps.params.manifestId);
    }

    _loadManifest(id, text)
    {
        this.props.dispatch(ManifestActions.request({id}));
    }

    render()
    {
        let children;
        if (this.props.location.query.q || this.props.params.manifestId)
            children = this._renderResults();
        else
            children = this._renderLanding();

        return (
            <div className="propagate-height propagate-height--root">
                <Navbar location={this.props.location} />
                {children}
                <Footer />
            </div>
        );
    }

    _renderLanding()
    {
        return (
            <div className="container">
                <CSSTransitionGroup {...TRANSITION_SETTINGS}>
                    {!this.props.location.query.q && (
                        <section key="recent-section">
                            <header className="page-header">
                                <h2>Recently uploaded</h2>
                            </header>
                            <ManifestCascade />
                        </section>
                    )}
                </CSSTransitionGroup>
            </div>
        );
    }

    _renderResults()
    {
        let rightPanel = this._renderManifest();
        return (
            <div className="manifest-detail propagate-height propagate-height--row">
                <div className="search-results--container">
                    <SearchResults location={this.props.location} />
                </div>
                {rightPanel}
            </div>
        );
    }

    _renderManifest()
    {
        if (this.props.params.manifestId)
            return <ManifestDisplay manifestRequest={this.props.manifestRequest} />;
        else
        {
            return <div className="manifest-detail__click-helper">
                <h5>Click on a Manifest to View it Here</h5>
            </div>;
        }
    }
}
