import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import scoring from "../src/web/lexicon_scoring.js";
const cases=JSON.parse(fs.readFileSync(new URL("./fixtures/lexicon_scoring_cases.json",import.meta.url)));
for(const c of cases)test(`shared scoring: ${c.name}`,()=>{
 if(c.error)assert.throws(()=>scoring.score(c.question,c.answer,c.options));
 else {const r=scoring.score(c.question,c.answer,c.options);for(const [k,v] of Object.entries(c.expected))assert.deepEqual(r[k],v);}
});
