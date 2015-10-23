import React, { PropTypes } from 'react';
import { ReduxRouter } from 'redux-react-router';
import { Provider } from 'react-redux';
import { Router, Route } from 'react-router';
import constProp from '../utils/const-prop';

import Search from './search/index';
import ManifestDetail from './manifest-detail/index';
import ManifestUpload from './manifest-upload/index';

export default class Root extends React.Component
{
    @constProp
    static get propTypes()
    {
        return {
            store: PropTypes.instanceOf(Object).isRequired
        };
    }

    render()
    {
        return (
            <div className="container">
                <Provider store={this.props.store}>
                    <ReduxRouter>
                        <Router>
                            <Route path="/search" component={Search}/>
                            <Route path="/manifests/upload" component={ManifestUpload}/>
                            <Route path="/manifests/:uuid" component={ManifestDetail}/>
                        </Router>
                    </ReduxRouter>
                </Provider>
            </div>
        );
    }
}

export const __hotReload = true;
