import test from 'node:test';
import assert from 'node:assert/strict';
import {emptyState} from '../dist/model.js';
import {readJournal,writeJournal,STORAGE_KEY} from '../dist/storage.js';
test('storage round trip',()=>{
  const values=new Map();
  const storage={getItem:k=>values.get(k),setItem:(k,v)=>values.set(k,v)};
  const state=emptyState();state.entries.yolo.confirmed=true;
  assert.equal(writeJournal(storage,state),true);
  assert.deepEqual(readJournal(storage),{state,blocked:false});
  assert.ok(values.has(STORAGE_KEY));
});
test('corrupt or inaccessible storage is not overwritten during load',()=>{
  let writes=0;
  const storage={getItem:()=>'{broken',setItem:()=>writes++};
  assert.equal(readJournal(storage).blocked,true);
  assert.equal(writes,0);
  assert.equal(readJournal({getItem:()=>{throw new Error('Denied');}}).blocked,true);
});
test('quota failure is reported as unsaved',()=>{
  assert.equal(writeJournal({setItem:()=>{throw new Error('Quota');}},emptyState()),false);
});
