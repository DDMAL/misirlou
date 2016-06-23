import React, { PropTypes } from 'react';

export default function SpellingCorrection({ correction })
{
    // iterate over two strings as whitespace delimited list,
    // bold any corrections that were applied in the collation.
    const before = correction[0].split();
    const after = correction[1].split();
    let res = [];
    for (let i = 0; i < before.length; i++)
    {
        if (after[i] !== before[i])
            res.push(<strong>{after[i]}</strong>);
        else
            res.push(<span>{after[i]}</span>);
    }
    return (
    <div className="text-muted">
        Showing results for {res}
    </div>
    );
}

SpellingCorrection.propTypes = {
    correction: PropTypes.arrayOf(PropTypes.string)
};
