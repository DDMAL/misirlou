import React, { PropTypes } from 'react';
import { locationShape } from 'react-router';
import CSSTransitionGroup from 'react-addons-css-transition-group';

import SearchResource from '../../resources/search-resource';
import updateSearch from './search-update-decorator';

@updateSearch
export default class SearchInput extends React.Component
{
    static propTypes = {
        // Optional
        className: PropTypes.string,

        // From updateSearch
        loadQuery: PropTypes.func.isRequired,
        loadPitchQuery: PropTypes.func.isRequired,
        search: PropTypes.shape({
            current: PropTypes.instanceOf(SearchResource).isRequired,
            stale: PropTypes.instanceOf(SearchResource).isRequired
        }).isRequired,
        location: locationShape.isRequired,
        stats: PropTypes.shape({
            attributions: PropTypes.number.isRequired,
            manifests: PropTypes.number.isRequired
        })
    };

    state = {
        pitchSearchShown: this.props.location.query.m ? true : false
    };

    _onPitchBtnClick()
    {
        // Remove the pitch search terms if hiding the pitch search input
        if (this.state.pitchSearchShown)
        {
            const fakeEvent = { target: { value: '' } };
            this.props.loadPitchQuery(fakeEvent);
        }

        this.setState({ pitchSearchShown: !this.state.pitchSearchShown });
    }

    _getStatsDisplay()
    {
        let statDisplay;
        if (this.props.stats)
        {
            statDisplay = (
                <span className="text-muted">
                        Search {this.props.stats.manifests} documents from {this.props.stats.attributions} sources.
                </span>);
        }
        return statDisplay
    }

    render()
    {
        const inputWidth = this.state.pitchSearchShown ? '400px' : '600px';
        const pitchBtnText = this.state.pitchSearchShown ? '<< Pitch Search (Experimental)' : '>> Pitch Search (Experimental)';

        return (
            <form onSubmit={e => e.preventDefault()} className={this.props.className}>
                <div className="search-input form-group">
                    <div>
                        <input type="search" name="q" placeholder="Search"
                               className="form-control search-input__input"
                               value={this.props.search.current.query}
                               onChange={this.props.loadQuery}
                               style={{width: inputWidth, transition: 'width 300ms'}}/>
                        <CSSTransitionGroup transitionName="input-anim"
                                            transitionEnterTimeout={200}
                                            transitionLeaveTimeout={200}>
                            {this.state.pitchSearchShown && (
                                <input type="search" name="m" placeholder="Pitch Search"
                                       className='form-control search-input__input'
                                       value={this.props.search.current.pitchQuery}
                                       onChange={this.props.loadPitchQuery}/>
                            )}
                        </CSSTransitionGroup>
                    </div>
                    <div className="row">
                        <div className="col-xs-6" style={{textAlign: "left"}}>
                            <span className="search-input__stat-display">{this._getStatsDisplay()}</span>
                        </div>
                        <div className="col-xs-6" style={{textAlign: "right"}}>
                            <CSSTransitionGroup transitionName="pitchBtn-anim"
                                                transitionEnterTimeout={200}
                                                transitionLeaveTimeout={10}>
                                {/* Use a key to create a new label every time the pitch input is shown.
                                    That way the animation always triggers */}
                                <label key={inputWidth} className="search-input__pitch-btn" onClick={() => this._onPitchBtnClick()}>
                                    {pitchBtnText}
                                </label>
                            </CSSTransitionGroup>
                        </div>

                    </div>

                </div>
            </form>
        );
    }
}
