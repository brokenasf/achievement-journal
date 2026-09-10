import test from 'node:test';
import assert from 'node:assert/strict';
import {emptyState,validateState} from '../dist/model.js';
test('import rejects repeated evidence and excessive links',()=>{
 const state=emptyState();
 state.entries.quickdraw.evidence=['https://github.com/a/b','https://github.com/a/b'];
 assert.throws(()=>validateState(state),/Повторяющиеся/);
 state.entries.quickdraw.evidence=Array.from({length:101},(_,i)=>`https://github.com/a/b/issues/${i}`);
 assert.throws(()=>validateState(state));
});
test('import strips unknown properties and rejects missing entries',()=>{
 const state=emptyState();state.untrusted='not retained';
 assert.equal(validateState(state).untrusted,undefined);
 delete state.entries.yolo;
 assert.throws(()=>validateState(state));
 assert.throws(()=>validateState({version:1,entries:[]}));
});
