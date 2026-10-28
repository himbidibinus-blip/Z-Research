'use strict';
const assert=require('node:assert/strict');
const fs=require('node:fs');
const Citation=require('../app/static/citation09.js');
const UI=fs.readFileSync('app/static/studio09.js','utf8');
const refs=[
{id:'smith',authors:'Smith, John',title:'Study A',year:2025,venue:'Journal A'},
{id:'doe',authors:'Doe, Jane',title:'Study B',year:2026,venue:'Journal B'}];
function render(body,style='ieee') {return Citation.renderDocument(body,style,refs)}
assert.equal(Citation.token('doe'),'[@ref:doe]');
assert.deepEqual(Citation.citedIds('[@ref:doe] and [@ref:smith] and [@ref:doe]'),['doe','smith']);
const first=render('First [@ref:doe]; second [@ref:smith]; again [@ref:doe]. [@bibliography]');
assert.match(first.text,/First \[1\]; second \[2\]; again \[1\]/);
assert.match(first.bibliography,/^\[1\].*Doe/m);
assert.match(first.bibliography,/^\[2\].*Smith/m);
assert.equal(first.text.match(/References\n/g).length,1);
const removeSmith=render('First [@ref:doe]. [@bibliography]');
assert.ok(removeSmith.text.includes('First [1].'));
assert.equal(removeSmith.text.includes('[2]'),false);
assert.equal(removeSmith.text.includes('Smith'),false);
const reordered=render('First [@ref:smith] then [@ref:doe]');
assert.ok(reordered.text.includes('First [1] then [2]'));
assert.ok(reordered.bibliography.indexOf('Smith')<reordered.bibliography.indexOf('Doe'));
const apa=render('Cite [@ref:doe] and [@ref:smith]','apa');
assert.ok(apa.text.includes('(Doe, 2026)'));
assert.ok(apa.text.includes('(Smith, 2025)'));
const unknown=render('Unknown [@ref:missing]');
assert.deepEqual(unknown.missing,['missing']);
assert.ok(unknown.text.includes('MISSING SOURCE'));
assert.ok(render('Legacy [2] only').legacyNumeric);
assert.equal(render('Modern [@ref:doe]').legacyNumeric,false);
assert.match(UI,/versions\/\$\{d\.id\}\/restore/);
assert.match(UI,/state\.referenceSelections\[key\]=new Set\(out\.reference_ids\)/);
assert.match(UI,/state\.currentCitationStyle=out\.citation_style/);
assert.match(UI,/insertCitation\('\\n\\n\[@bibliography\]/);
console.log('PASS 20 v0.9.2 citation and revision invariants');
