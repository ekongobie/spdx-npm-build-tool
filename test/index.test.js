const assert = require('assert');

describe('Tool Test', () => {
 it('Without arguments', () => {
        assert.equal(process.argv.length, 2);
    });
});
