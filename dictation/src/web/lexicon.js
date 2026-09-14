/* Lexicon workspace: local dictionary, study, objective practice and durable records. */
"use strict";
const $ = selector => document.querySelector(selector);
const TYPES = {recall:"回忆释义",meaning:"看词识义",reading:"看词写读音",production:"看释义回忆词语",listening:"听音识词",cloze:"例句填空",connection:"接续练习",usage:"近义辨析",collocation:"搭配辨析",order:"句子排序",context:"语境选择",writing:"造句 / 改写"};
const KIND = {word:"词汇",grammar:"语法"};
// Why a type cannot be practised yet. "Generated" is not "reviewed" (LEX-04).
const REASONS = {"review.required":"等待内容审核","review.withdrawn":"题目已撤回","review.stale":"审核记录与当前内容不符","review.reviewer_missing":"审核记录缺少审核人","review.hash_missing":"审核记录未标明覆盖内容","evidence.missing":"缺少来源证据","audio.unavailable":"没有可靠音源"};
const reasonText = codes => (codes||[]).map(code=>REASONS[code]||code).join("、");
const state = { token:"", online:false, packs:[], decks:[], users:[], pack:null, request:0, session:null, offlineSession:null, study:null, learn:null, busy:false, editor:null, planRefs:[], planUnits:[], practiceRefs:[], practiceUnits:[], detailReturn:"", activeView:"packs" };
const { renderInline, renderBlocks, renderConnection, plainText } = LexiconMarkup;
const node = (tag, text, cls) => { const n=document.createElement(tag); if(text!==undefined)n.textContent=String(text);if(cls)n.className=cls;return n; };
function button(text, action, cls="quiet-button") {const b=node("button",text,cls);b.type="button";b.addEventListener("click",()=>guard(b,action));return b;}
function clear(n){n.replaceChildren();return n;}
function notice(message,error=false){let n=$("#lex-status");n.textContent=message;n.classList.toggle("is-error",error);n.hidden=false;}
function toast(message,error=false){notice(message,error);let n=$("#lex-toast");if(!n){n=node("div",undefined,"lex-toast");n.id="lex-toast";n.setAttribute("role","status");document.body.append(n);}n.textContent=message;n.hidden=false;clearTimeout(toast.timer);toast.timer=setTimeout(()=>{n.hidden=true;},6500);}
async function guard(b, fn) {if(b?.disabled)return; if(b)b.disabled=true;try{await fn();}catch(e){toast(e.message||String(e),true);}finally{if(b)b.disabled=false;}}
const uid = () => "op_"+(crypto.randomUUID ? crypto.randomUUID().replaceAll("-","") : Date.now().toString(36)+Math.random().toString(36).slice(2));
function readLocal(key,fallback){try{return JSON.parse(localStorage.getItem(key))??fallback;}catch{return fallback;}}
function writeLocal(key,value){localStorage.setItem(key,JSON.stringify(value));}
async function token(){try{const r=await fetch("./api/session/bootstrap",{cache:"no-store"});if(!r.ok)return false;state.token=(await r.json()).token;state.online=Boolean(state.token);return state.online;}catch{state.online=false;return false;}}
async function api(path,options={},retried=false){
  let response;
  try{response=await fetch(path,{cache:"no-store",...options,headers:{Accept:"application/json","X-Dictation-Token":state.token,...(options.body?{"Content-Type":"application/json"}:{}),...(options.headers||{})}});}catch(e){state.online=false;throw e;}
  if(response.headers.get("X-Dictation-Offline")==="1"){state.online=false;throw new TypeError("本地服务未连接，使用已保存的离线数据。");}
  if(response.status===403&&!retried&&await token())return api(path,options,true);
  const text=await response.text();let data;try{data=text?JSON.parse(text):{};}catch{throw new Error("服务返回内容不可读，请重试。");}
  if(!response.ok||data.ok===false){const error=new Error(data.error||`请求失败（${response.status}）`);error.status=response.status;throw error;}
  state.online=true;return data;
}
const post = (path,body={},operationId) => api(path,{method:"POST",body:JSON.stringify(body),headers:operationId?{"X-Learning-Operation-Id":operationId}:{}});
async function sendSyncOperation(op){return api(op.path,{method:op.method,headers:{"X-Learning-Operation-Id":op.id},body:op.body==null?undefined:JSON.stringify(op.body)});}
function show(name){state.activeView=name;document.querySelectorAll(".lex-view").forEach(n=>{n.hidden=n.id!=="view-"+name;});const tabs={browse:["packs","pack","search","detail"],study:["study","learn"],plans:["plans"],practice:["practice","session"],records:["records"]};for(const [tab,names]of Object.entries(tabs)){const n=document.getElementById("lex-tab-"+tab);n.classList.toggle("is-active",names.includes(name));n.setAttribute("aria-current",names.includes(name)?"page":"false");}$("#lex-home-button").hidden=name==="packs";}
function navigate(hash){if(location.hash===hash)route();else location.hash=hash;}
function refOf(entry,pack){return entry.sourceRef||`lex:${pack.packId}#${entry.id}`;}
/* Japanese speech availability.
 *
 * Voices load asynchronously, so a check at page load sees an empty list and a check
 * after `speak()` returns proves nothing: `speechSynthesis.speak` resolves whether or
 * not anything was said. The state is tracked as it becomes known, and a listening
 * question is only offered once a Japanese voice is actually present (LEX-19, §11.3).
 */
const voice={state:"unknown",voice:null};
function refreshVoices(){
  if(!("speechSynthesis" in window)){voice.state="unsupported";return voice;}
  const voices=speechSynthesis.getVoices();
  if(!voices.length){voice.state="unknown";return voice;}
  voice.voice=voices.find(v=>v.lang.toLowerCase().startsWith("ja"))||null;
  voice.state=voice.voice?"available":"missing";
  return voice;
}
function audioAvailable(){return refreshVoices().state==="available";}
function audioReason(){
  return {unsupported:"当前浏览器没有语音合成能力",missing:"系统没有安装日语语音",
          unknown:"日语语音尚未就绪"}[refreshVoices().state]||"";
}
function speak(text){
  const status=refreshVoices();
  if(status.state==="unsupported")throw new Error("当前浏览器没有语音朗读能力。");
  if(status.state==="missing")throw new Error("请先在系统设置中安装日语语音。");
  if(status.state==="unknown")throw new Error("日语语音尚未就绪，请稍后再试。");
  speechSynthesis.cancel();
  const utterance=new SpeechSynthesisUtterance(plainText(text));
  utterance.lang="ja-JP";utterance.rate=.85;utterance.voice=status.voice;
  let spoke=false;
  utterance.onstart=()=>{spoke=true;};
  utterance.onerror=()=>toast("日语语音不可用，可继续其他题型。",true);
  // Nothing having started is not success; saying so beats a silent "played".
  utterance.onend=()=>{if(!spoke)toast("没有播放出声音，可改用其他题型。",true);};
  speechSynthesis.speak(utterance);
}
window.LexLookupHost={
  canLookup:()=>!document.querySelector("dialog[open]"),
  getSelectionContext:()=>({hostType:"lexicon",packSlug:state.pack?.slug||"",
    sourceRevision:state.pack?.contentRevision||"",view:state.activeView}),
};
function examples(list,target){for(const e of list||[]){const wrap=node("div",undefined,"lex-example");const ja=node("p",undefined,"lex-example-ja");renderInline(e.ja||"",ja);wrap.append(ja);if(e.reading&&e.readingSource)wrap.append(node("p",e.reading,"lex-example-reading"));if(e.zh)wrap.append(node("p",e.zh,"lex-example-zh"));if(e.en)wrap.append(node("p",e.en,"lex-example-en"));wrap.append(button("朗读例句",()=>speak(e.ja)));target.append(wrap);}}
function inline(text,tag="p",cls=""){const p=node(tag,undefined,cls);renderInline(text||"",p);return p;}
function personal(ref){return state.users.find(e=>e.sourceRef===ref&&!e.deleted);}
async function cacheUsers(){await LearningCardStore.writeRecords([{store:"lex-meta",value:{id:"users",items:state.users}}]);}
function renderCapabilities(capabilities,body){
  if(!capabilities?.byType)return;
  const ready=(capabilities.types||[]).map(t=>TYPES[t]||t);
  if(ready.length)body.append(node("p","可练题型："+ready.join("、"),"lex-notice"));
  const pending=(capabilities.pendingTypes||[]).map(t=>`${TYPES[t]||t}（${reasonText(capabilities.byType[t]?.reasonCodes)}）`);
  // Say why, rather than letting a type quietly vanish from the practice form.
  if(pending.length)body.append(node("p","暂不计入正式练习："+pending.join("；"),"lex-notice"));
}
function renderSensePicker(payload,body){
  const options=payload.options;const state0=payload.selection||{};
  const wrap=node("section",undefined,"lex-sense-picker");
  wrap.append(node("h2","选择表记、读音与义项"));
  if(state0.chosen&&!state0.resolved){
    // A rebuilt dictionary can change a sense key. Never swap the meaning silently.
    wrap.append(node("p","词典已更新，原先选择的义项在新版本中找不到了。请从下面重新确认；原显示内容仍然保留。","lex-notice"));
  }else if(!state0.chosen){
    wrap.append(node("p","尚未选择义项。选定后收藏与练习只使用该义项的释义。","lex-notice"));
  }
  const formSelect=node("select");formSelect.setAttribute("aria-label","表记");
  const readingSelect=node("select");readingSelect.setAttribute("aria-label","读音");
  const senseList=node("div",undefined,"lex-sense-options");
  const forms=options.writtenForms||[];
  for(const form of forms){const o=node("option",form.writtenForm||"（仅假名）");o.value=form.writtenForm;o.selected=form.writtenForm===state0.writtenForm;formSelect.append(o);}
  const drawReadings=()=>{
    const form=forms.find(f=>f.writtenForm===formSelect.value)||forms[0];
    clear(readingSelect);
    for(const reading of form?.readings||[]){const o=node("option",reading.reading);o.value=reading.reading;o.selected=reading.reading===state0.reading;readingSelect.append(o);}
    drawSenses();
  };
  const chosen=new Set((state0.senses||[]).map(s=>s.key));
  const drawSenses=()=>{
    const form=forms.find(f=>f.writtenForm===formSelect.value)||forms[0];
    const reading=(form?.readings||[]).find(r=>r.reading===readingSelect.value)||form?.readings?.[0];
    clear(senseList);
    // Only senses the dictionary allows for this spelling and reading are offered.
    for(const sense of reading?.senses||[]){
      const label=node("label",undefined,"lex-answer-choice");const box=node("input");box.type="checkbox";box.value=sense.key;box.checked=chosen.has(sense.key);
      box.addEventListener("change",()=>{if(box.checked)chosen.add(sense.key);else chosen.delete(sense.key);});
      label.append(box,node("span",sense.gloss.join("；")+(sense.notes?.length?`（${sense.notes.join("；")}）`:"")));
      senseList.append(label);
    }
    if(!(reading?.senses||[]).length)senseList.append(node("p","这个表记与读音的组合没有对应义项。","lex-notice"));
  };
  formSelect.addEventListener("change",drawReadings);
  readingSelect.addEventListener("change",drawSenses);
  drawReadings();
  wrap.append(formSelect,readingSelect,senseList);
  wrap.append(button("保存义项选择并收藏",async()=>{
    if(!chosen.size)throw new Error("请至少选择一个义项。");
    const keys=[...chosen].sort();
    const entSeq=payload.sourceRef.split("#")[1].split("/")[0];
    const selection={writtenForm:formSelect.value,reading:readingSelect.value,senseKeys:keys,
      dictionaryVersion:options.dictionaryVersion||""};
    const form=forms.find(f=>f.writtenForm===formSelect.value)||forms[0];
    const reading=(form?.readings||[]).find(r=>r.reading===readingSelect.value)||form?.readings?.[0];
    const picked=(reading?.senses||[]).filter(s=>chosen.has(s.key));
    // The reference carries the sense, so two senses of one entry stay two favourites.
    const ref=`dict:jmdict#${entSeq}/${keys[0]}`;
    await saveUser({...personal(ref),sourceRef:ref,headword:formSelect.value||readingSelect.value,
      reading:readingSelect.value,gloss:{en:picked.map(s=>s.gloss.join("; ")).join(" / ")},
      kind:"word",starred:true,selection,snapshot:{reading:readingSelect.value,senses:picked}});
    toast("已按所选义项收藏。");navigate(`#/dictionary/${encodeURIComponent(entSeq+"/"+keys[0])}`);
  },"primary-button"));
  body.append(wrap);
}
async function saveUser(item){const ts=new Date().toISOString();const saved={...item,updatedAt:ts};const index=state.users.findIndex(e=>e.sourceRef===item.sourceRef);const response=await LearningDataSync.mutate("PUT","./api/lexicon/user-entries",saved,{entityType:"lex-entry",entityKey:item.sourceRef});const result=response.result?.item||saved;if(index<0)state.users.push(result);else state.users[index]=result;await cacheUsers();
  broadcast({entityType:"lex-entry",id:item.sourceRef,version:result.version,operationId:response.operation?.id});return result;}
function broadcast(change={}){return LearningCards.announce({entityType:"vocab",...change});}
const STAGE_LABELS={queued:"准备中",download:"下载中",build:"建立索引",publish:"发布中",
  complete:"已完成",failed:"失败",cancelled:"已取消",interrupted:"已中断"};
function describeJob(job){
  const stage=STAGE_LABELS[job.stage]||job.stage||"";
  const size=job.bytes?` · 已下载 ${Math.round(job.bytes/1048576)} MB`:"";
  const entries=job.entriesProcessed?` · 已导入 ${job.entriesProcessed.toLocaleString()} 词目`:"";
  return `${stage}${size}${entries}${job.message?" · "+job.message:""}`;
}
let dictionaryTimer=null;
function watchDictionaryJob(){
  clearInterval(dictionaryTimer);
  let polls=0;
  const tick=async()=>{
    let job;
    try{job=(await api("./api/dictionary/install")).job;}catch{clearInterval(dictionaryTimer);return;}
    $("#dictionary-cancel").hidden=job.status!=="running";
    $("#lex-search-scope").textContent=describeJob(job);
    if(job.status==="running"){
      // Running out of polls says nothing about the job. Reporting "已更新" here is the
      // claim this replaces (§9.4).
      if(++polls>120){clearInterval(dictionaryTimer);
        $("#lex-search-scope").textContent=describeJob(job)+" · 仍在处理，可稍后重新进入此页面查看。";}
      return;
    }
    clearInterval(dictionaryTimer);
    await refresh();
    const failed=job.status==="failed";
    toast(failed?job.message:job.status==="cancelled"?"已取消安装，原词典未改变。"
      :job.status==="interrupted"?job.message:"词典已更新。",failed||job.status==="interrupted");
  };
  dictionaryTimer=setInterval(tick,3000);
  tick();
}
async function refresh(){
  const results=await Promise.allSettled([api("./api/lexicon/packs"),api("./api/decks"),api("./api/lexicon/user-entries?includeDeleted=1"),api("./api/dictionary/status")]);
  if(results[0].status==="fulfilled")state.packs=results[0].value.packs||[];
  if(results[1].status==="fulfilled"){state.decks=results[1].value.decks||[];writeLocal("dictation-lexicon-decks:v2",state.decks);}
  if(results[2].status==="fulfilled"){const remote=results[2].value.items||[];state.users=LearningDataSync.mergeItems(state.users,remote,{entityType:"lex-entry",keyOf:i=>i.sourceRef});await cacheUsers();}
  if(results[3].status==="fulfilled"){
    const d=results[3].value;
    $("#lex-search-scope").textContent=d.available
      ?`本地 JMdict ${Number(d.entries).toLocaleString()} 词目 · 教材与个人条目 · 英文词典释义与中文学习释义分别展示`
        +(d.degraded?` · ${d.degradedReason}`:"")
      :"尚未安装词典；当前可搜索教材与个人条目。";
    $("#dictionary-cancel").hidden=d.job?.status!=="running";
    // An install left running by a previous session is still that session's job; pick it
    // back up rather than reporting nothing is happening.
    if(d.job?.status==="running")watchDictionaryJob();
    else if(d.job?.status==="interrupted")$("#lex-search-scope").textContent=describeJob(d.job);
  }
  renderPacks();renderOptions();
}
function renderOptions(){
  for(const selector of ["#plan-pack","#practice-pack"]){const select=$(selector);const old=[...select.selectedOptions].map(o=>o.value);clear(select);if(selector==="#practice-pack"){const o=node("option","全部内容包");o.value="";select.append(o);}for(const pack of state.packs.filter(p=>!p.broken)){const o=node("option",`${pack.level==="ungraded"?"未分级":pack.level} · ${pack.title}`);o.value=pack.slug;o.selected=old.includes(pack.slug);select.append(o);}if(selector==="#plan-pack"&&!select.selectedOptions.length&&select.options.length)select.options[0].selected=true;}
  const select=clear($("#study-deck"));const all=node("option","全部计划与个人卡片");all.value="";select.append(all);for(const deck of state.decks){const o=node("option",`${deck.name} · ${deck.progress?.due||0} 到期`);o.value=deck.id;select.append(o);}const active=new URLSearchParams(location.hash.split("?")[1]||"").get("deck");select.value=active||"";
}
function renderPacks(){
  const list=clear($("#lex-pack-list"));const kind=$("#search-kind").value;const level=$("#search-level").value;const packs=state.packs.filter(p=>(!kind||p.kind===kind)&&(!level||p.level===level));$("#lex-empty").hidden=packs.length>0;$("#lex-empty-note").textContent="当前筛选没有可用内容。可安装内容包，或在学习记录中建立个人条目。";
  for(const p of packs){const li=node("li",undefined,"lex-pack-card");li.append(node("p",`${p.level==="ungraded"?"未分级":p.level} · ${KIND[p.kind]||p.kind}`,"lex-pack-meta"),node("h2",p.title),node("p",`${p.entryCount||0} 条 · ${p.unitCount||0} 个单元`));if(p.broken)li.append(node("p","内容未通过质量审计，暂不可学习。","lex-notice is-error"));else{if(p.quality?.warnings)li.append(node("p",`${p.quality.warnings} 项内容待核对；可用题型按条目决定。`,"lex-notice"));const actions=node("div",undefined,"lex-pack-actions");actions.append(button("浏览",()=>navigate("#/pack/"+encodeURIComponent(p.slug)),"primary-button"),button("建立计划",()=>planFor(p.slug)),button("练习",()=>practiceFor({pack:p.slug})));li.append(actions);}list.append(li);}
  $("#level-switch").hidden=true;
}
let searchTimer=null;
function scheduleQuery(){
  // Debounced, and never during composition: querying half-typed kana would also tear
  // down the IME candidate window (§9.3). Stale responses are already dropped by the
  // request generation in `route()`.
  clearTimeout(searchTimer);
  searchTimer=setTimeout(()=>{if($("#lex-search-input").value.trim())queryRoute();},250);
}
function highlight(text,needle,target){
  const value=String(text??"");
  const at=needle?value.toLowerCase().indexOf(needle.toLowerCase()):-1;
  if(at<0){target.append(node("span",value));return target;}
  target.append(node("span",value.slice(0,at)),node("mark",value.slice(at,at+needle.length)),
                node("span",value.slice(at+needle.length)));
  return target;
}
function queryRoute(){clearTimeout(searchTimer);const p=new URLSearchParams();p.set("q",$("#lex-search-input").value.trim());for(const key of ["kind","level","scope"])if($("#search-"+key).value)p.set(key,$("#search-"+key).value);if($("#search-starred").checked)p.set("starred","1");navigate("#/search?"+p);}
/* ---------------------------------------------------------------------------
 * Offline reads from the service worker's pack cache.
 *
 * With the local service stopped, a fully cached pack is still a complete copy of
 * its content, so browsing, searching and opening an entry all remain answerable.
 * The previous offline path only ran `JSON.stringify(personalEntry).includes(q)`
 * and reported that as the whole search (LEX-17, §8.3).
 * ------------------------------------------------------------------------- */
const LEXICON_CACHE="dictation-lexicon-packs-v1";
function cacheUrl(kind,slug){return new URL(`__lexicon_cache__/${kind}/${encodeURIComponent(slug)}`,location.href).toString();}
async function readCachedJson(slug){
  if(!globalThis.caches)return null;
  try{
    const cache=await caches.open(LEXICON_CACHE);
    const pointer=await cache.match(cacheUrl("pointer",slug));
    if(!pointer)return null;
    const {dataKey}=await pointer.json();
    if(!dataKey)return null;
    const stored=await cache.match(dataKey);
    return stored?await stored.json():null;
  }catch{return null;}
}
async function cachedPackList(){
  const payload=await readCachedJson("packs");
  return Array.isArray(payload?.packs)?payload.packs:[];
}
async function cachedPacks(){
  const packs=[];
  for(const summary of await cachedPackList()){
    const payload=await readCachedJson(summary.slug);
    if(payload?.pack)packs.push(payload.pack);
  }
  return packs;
}
async function cachedEntry(slug,entryId){
  const payload=await readCachedJson(slug);
  const pack=payload?.pack;
  if(!pack)return null;
  const entry=(pack.entries||[]).find(item=>item.id===entryId);
  return entry?{pack,entry}:null;
}
function matchesEntry(entry,needle){
  const parts=[entry.headword,entry.snapshot?.reading,entry.dictRef?.reading,
    entry.gloss?.zh,entry.gloss?.en,entry.grammar?.notes,
    ...(entry.examples||[]).flatMap(e=>[e.ja,e.zh,e.en])];
  return parts.some(part=>String(part||"").toLowerCase().includes(needle));
}
async function offlineSearch(query){
  const needle=String(query||"").trim().toLowerCase();
  const sources=[];const results=[];
  if(!needle)return {results:[],total:0,totalRelation:"eq",hasMore:false,nextCursor:null,
    availableSources:[],notes:["请输入查询内容。"]};
  const packs=await cachedPacks();
  if(packs.length)sources.push("packs");
  for(const pack of packs)for(const entry of pack.entries||[]){
    if(!matchesEntry(entry,needle))continue;
    results.push({id:entry.id,sourceRef:`lex:${pack.packId}#${entry.id}`,packSlug:pack.slug||pack.packId,
      packTitle:pack.title,kind:entry.kind,level:entry.level||"",headword:entry.headword,
      reading:entry.snapshot?.reading||entry.dictRef?.reading||"",gloss:entry.gloss||{},
      unitId:entry.unitId||"",score:45,matchField:"已缓存内容包"});
  }
  const mine=state.users.filter(item=>!item.deleted);
  if(mine.length)sources.push("personal");
  for(const entry of mine){
    if(entry.sourceRef.startsWith("lex:")&&results.some(r=>r.sourceRef===entry.sourceRef))continue;
    if(!matchesEntry(entry,needle)&&!String(entry.note||"").toLowerCase().includes(needle))continue;
    results.push({...entry,id:entry.sourceRef,score:40,matchField:"个人条目/笔记"});
  }
  results.sort((a,b)=>a.score-b.score||String(a.sourceRef).localeCompare(String(b.sourceRef)));
  for(const item of results)item.starred=Boolean(personal(item.sourceRef)?.starred);
  return {results,total:results.length,totalRelation:"eq",hasMore:false,nextCursor:null,
    availableSources:sources,
    // Say what was searched. Claiming a complete result from a partial cache is the
    // failure this replaces.
    notes:[packs.length?`本地服务不可用：已查询 ${packs.length} 个缓存内容包与个人条目。`
      :"本地服务不可用，且没有缓存的内容包：仅查询个人条目。"]};
}
async function search(p,request){show("search");const q=p.get("q")||"";$("#lex-search-input").value=q;for(const key of ["kind","level","scope"])$("#search-"+key).value=p.get(key)||(key==="scope"?"all":"");$("#search-starred").checked=p.get("starred")==="1";const list=clear($("#search-list"));$("#search-meta").textContent="正在查询…";p.set("limit","30");let payload;
  try{payload=await api("./api/lexicon/search?"+p);}
  catch(e){
    if(e.status===409){
      // The index moved under the cursor. Keep the query, restart from the first page.
      const restart=new URLSearchParams(p);restart.delete("cursor");restart.delete("trail");
      toast("内容索引已更新，已回到第一页。",true);navigate("#/search?"+restart);return;
    }
    if(e.status)throw e;
    payload=await offlineSearch(q);
    toast("本地服务不可用："+payload.notes[0],true);
  }
  if(request!==state.request)return;
  const shown=payload.total??payload.results.length;
  const counted=payload.totalRelation==="gte"?`至少 ${shown}`:`${shown}`;
  const sources=(payload.availableSources||[]).map(name=>({packs:"教材",dictionary:"词典",personal:"个人条目"})[name]||name);
  // Say which sources actually answered, and never present a lower bound as a total.
  $("#search-meta").textContent=`“${q}” · ${counted} 条结果`
    +(sources.length?` · 来源：${sources.join("、")}`:"")
    +(payload.notes?.length?` · ${payload.notes.join(" ")}`:"");
  for(const r of payload.results){const li=node("li",undefined,"lex-entry");li.append(inline(r.headword,"h2","lex-headword"));if(r.reading)li.append(highlight(r.reading,q,node("p",undefined,"lex-example-reading")));li.append(highlight(r.gloss?.zh||r.gloss?.en||"暂无释义",q,node("p")));li.append(node("p",`${r.packTitle||r.source||"个人条目"} · ${r.matchField||"匹配"}${r.chain?.length?" · "+r.chain.join(" → "):""}`,"lex-entry-source"));li.append(button("查看详情",()=>openRef(r.sourceRef,r.packSlug)),button(r.starred?"已收藏":"收藏",async()=>{await saveUser({...personal(r.sourceRef),sourceRef:r.sourceRef,headword:r.headword,reading:r.reading||"",gloss:r.gloss||{},kind:r.kind||"word",starred:!r.starred});search(p,state.request);}));list.append(li);}
  if(!payload.results.length)list.append(node("li","没有匹配结果。试试取消等级限制、查询原形或安装词典。","lex-empty"));
  const paging=node("li",undefined,"lex-pack-actions");
  // Cursors are opaque, so "previous" walks a trail kept in the URL rather than
  // subtracting a page size that no longer means anything (§9.1).
  const trail=(p.get("trail")||"").split(",").filter(Boolean);
  if(trail.length)paging.append(button("上一页",()=>{const back=[...trail];const previous=back.pop();const next=new URLSearchParams(p);if(previous==="0")next.delete("cursor");else next.set("cursor",previous);if(back.length)next.set("trail",back.join(","));else next.delete("trail");navigate("#/search?"+next);}));
  if(payload.hasMore&&payload.nextCursor)paging.append(button("下一页",()=>{const next=new URLSearchParams(p);next.set("trail",[...trail,p.get("cursor")||"0"].join(","));next.set("cursor",payload.nextCursor);navigate("#/search?"+next);}));
  list.append(paging);
  if(q){const history=[q,...readLocal("dictation-lex-search-history",[]).filter(x=>x!==q)].slice(0,8);writeLocal("dictation-lex-search-history",history);renderHistory();}
}
function renderHistory(){const n=clear($("#search-history"));for(const q of readLocal("dictation-lex-search-history",[]))n.append(button(q,()=>{$("#lex-search-input").value=q;queryRoute();}));if(n.childNodes.length)n.append(button("清空历史",()=>{localStorage.removeItem("dictation-lex-search-history");renderHistory();}));}
function openRef(ref,slug){state.detailReturn=location.hash;if(ref.startsWith("dict:"))navigate("#/dictionary/"+encodeURIComponent(ref.split("#")[1]));else if(ref.startsWith("user:"))navigate("#/personal/"+encodeURIComponent(ref));else{const [pack,id]=ref.slice(4).split("#");const found=state.packs.find(p=>p.packId===pack);navigate(`#/entry/${encodeURIComponent(slug||found?.slug||pack)}/${encodeURIComponent(id)}`);}}
async function openPack(slug,unitId,entryId,request){
  const {pack}=await api("./api/lexicon/packs/"+encodeURIComponent(slug));if(request!==state.request)return;state.pack=pack;show("pack");$("#pack-heading").textContent=pack.title;$("#pack-meta").textContent=`${KIND[pack.kind]} · ${pack.entryCount} 条 · ${pack.unitCount} 个单元`;const stale=pack.publication?.staleReports||[];
  $("#pack-quality").hidden=!pack.quality?.warnings&&!stale.length;
  // A report describing a different build is a fact about this pack, not a detail.
  $("#pack-quality").textContent=`${pack.quality?.warnings||0} 项待核对，缺项会在条目中显示。`
    +(stale.length?` 制作报告与当前版本不一致（${stale.join("、")}），需重新装配后发布。`:"");$("#pack-rights").hidden=true;
  const packActions=node("div",undefined,"lex-pack-actions");
  packActions.append(
    button("学习整个内容包",()=>navigate(`#/learn/${encodeURIComponent(slug)}`),"primary-button"),
    button("练习整个内容包",()=>practiceFor({pack:slug})),
    button("加入学习计划",()=>planFor(slug)));
  $("#pack-meta").after(packActions);
  const units=pack.units||[];const unit=units.find(u=>u.unitId===unitId)||units[0];const rail=clear($("#unit-rail"));for(const u of units){const b=button(`${u.label||u.unitId} · ${u.entryIds.length}`,()=>navigate(`#/pack/${encodeURIComponent(slug)}/${encodeURIComponent(u.unitId)}`),"lex-unit-tab");b.classList.toggle("is-active",u===unit);rail.append(b);}
  $("#unit-title").textContent=unit?.title?`${unit.label} · ${unit.title}`:unit?.label||"";const list=clear($("#entry-list"));if(!unit)return;
  const actions=node("li",undefined,"lex-pack-actions");
  actions.append(
    button("开始学习本单元",()=>navigate(`#/learn/${encodeURIComponent(slug)}/${encodeURIComponent(unit.unitId)}`),"primary-button"),
    button("练习本单元",()=>practiceFor({pack:slug,units:[unit.unitId]})),
    // The old 「学习本单元」 went here, which is a plan form, not studying.
    button("加入学习计划",()=>planFor(slug,[],[unit.unitId])));
  list.append(actions);
  for(const id of unit.entryIds){const e=pack.entries.find(e=>e.id===id);if(!e)continue;const li=node("li",undefined,"lex-entry");li.id="entry-"+e.id;li.append(inline(e.headword,"h3","lex-headword"));const reading=e.snapshot?.reading||e.dictRef?.reading;if(reading)li.append(node("p",reading,"lex-example-reading"));li.append(inline(e.gloss?.zh||e.gloss?.en||"中文释义待补充"));for(const c of e.grammar?.connection||[])renderConnection(c,li);examples((e.examples||[]).slice(0,1),li);li.append(button("详情 / 学习 / 笔记",()=>openRef(refOf(e,pack),slug)));list.append(li);}
  if(entryId)document.getElementById("entry-"+entryId)?.scrollIntoView({block:"center"});
}
async function detail(kind,parts,request){
  let payload;let offline=false;
  if(kind==="entry"){
    try{payload=await api(`./api/lexicon/entries/${encodeURIComponent(parts[1])}/${encodeURIComponent(parts[2])}`);}
    catch(e){
      if(e.status)throw e;
      // A cached pack is a complete copy of its content, so the entry is answerable
      // from it rather than the page reporting a dead end (LEX-17, §8.3).
      const found=await cachedEntry(parts[1],parts[2]);
      if(!found)throw new Error("本地服务不可用，且该内容包尚未缓存，无法离线查看此条目。");
      const saved=personal(`lex:${found.pack.packId}#${found.entry.id}`);
      const offlineRelated=[];
      for(const conf of (found.entry.grammar?.confusables||[])){
        const ref=typeof conf==="string"?conf:conf?.sourceRef;
        if(!ref||!ref.startsWith("lex:")||!ref.includes("#"))continue;
        const [pId,eId]=ref.slice(4).split("#");
        if(pId===found.pack.packId){
          const relE=found.pack.entries.find(x=>x.id===eId);
          if(relE){
            offlineRelated.push({
              sourceRef:ref,packSlug:parts[1],entryId:eId,headword:relE.headword,gloss:relE.gloss||{},
              ...(typeof conf==="object"?{relationType:conf.relationType,contrast:conf.contrast,scenario:conf.scenario}:{})
            });
          }
        }
      }
      payload={entry:found.entry,sourceRef:`lex:${found.pack.packId}#${found.entry.id}`,
        packSlug:parts[1],packTitle:found.pack.title,personal:saved||null,contexts:[],related:offlineRelated};
      offline=true;
    }
  }
  else if(kind==="dictionary")payload=await api("./api/dictionary/entries/"+encodeURIComponent(parts[1]));
  else{const e=personal(parts[1]);if(!e)throw new Error("个人条目不存在。");payload={entry:e,sourceRef:e.sourceRef,personal:e};}
  if(request!==state.request)return;
  show("detail");const e=payload.entry;const ref=payload.sourceRef;$("#detail-heading").textContent=plainText(e.headword);const body=clear($("#detail-body"));const reading=e.reading||e.snapshot?.reading||e.dictRef?.reading||"";if(reading)body.append(node("p",reading,"lex-example-reading"));const pos=e.pos||e.snapshot?.pos;if(pos?.length)body.append(node("p",pos.join(" · ")));body.append(inline(e.gloss?.zh||"中文释义待补充","p","lex-gloss"));if(e.gloss?.en)body.append(node("p",e.gloss.en,"lex-gloss is-secondary"));
  if(e.senses){
    if(payload.options)renderSensePicker(payload,body);
    for(const sense of e.senses){const div=node("article",undefined,"lex-example");div.append(node("h3",sense.gloss.join("；")));if(sense.notes?.length)div.append(node("p",sense.notes.join("；"),"lex-notice"));const restrictions=[...(sense.writtenRestrictions||[]),...(sense.readingRestrictions||[])];if(restrictions.length)div.append(node("p","适用形式："+restrictions.join("、")));body.append(div);}
    const attribution=node("p","JMdict © James William Breen and EDRDG · ","lex-entry-source");const link=node("a","来源与许可（CC BY-SA 4.0）");link.href="https://www.edrdg.org/edrdg/licence.html";link.target="_blank";link.rel="noopener";attribution.append(link);body.append(attribution);}
  if(e.grammar){body.append(node("h2","接续与用法"));for(const c of e.grammar.connection||[])renderConnection(c,body);renderBlocks(e.grammar.notes||"",body);}
  examples(e.examples,body);if(payload.capabilities?.missing?.length)body.append(node("p","待补充："+payload.capabilities.missing.join("、"),"lex-notice"));
  renderCapabilities(payload.capabilities,body);
  if(offline)body.append(node("p","离线查看：来自已缓存的内容包，题型资格与收藏语境需要连接本地服务后才完整。","lex-notice"));
  const saved=personal(ref)||payload.personal;const base={...saved,sourceRef:ref,headword:e.headword,reading,gloss:e.gloss||{},kind:e.kind||"word",level:e.level||"",examples:e.examples||[]};const actions=node("div",undefined,"lex-pack-actions");actions.append(button("朗读",()=>speak(reading||e.headword)),button(saved?.starred?"取消收藏":"收藏",async()=>{await saveUser({...base,starred:!saved?.starred});route();}),button("笔记与标签",()=>editUser(base)),button("立即练习",async()=>{if(ref.startsWith("dict:"))await saveUser({...base,starred:true});practiceFor({refs:[ref]});}),button("加入复习",async()=>{
    if(!ref.startsWith("lex:"))await saveUser({...base,starred:true});
    const result=await post("./api/lexicon/introduce",{sourceRefs:[ref],promptTypes:["recall"]});
    if(!result.count)throw new Error("这一条没有可用的复习卡片（可能缺读音或例句，或此前被删除过）。");
    await LearningCardStore.putMany(result.items);
    broadcast({id:result.items[0].id,reason:"introduce"});
    toast("已加入复习，可在今日背诵里看到。");
  }),button("加入学习计划",()=>{
    if(ref.startsWith("lex:"))planFor(payload.packSlug,[ref]);
    else practiceFor({refs:[ref],types:["recall","reading"]});
  }));body.append(actions);
  if(saved?.note){body.append(node("h2","个人笔记"),node("p",saved.note,"lex-personal-note"));}if(saved?.tags?.length)body.append(node("p",saved.tags.join(" · ")));
  if(payload.related?.length){
    body.append(node("h2","相近语法与辨析"));
    for(const r of payload.related){
      const card=node("div",undefined,"lex-plan-card");
      card.append(node("h3",r.headword));
      if(r.gloss?.zh)card.append(node("p",r.gloss.zh));
      if(r.relationType)card.append(node("p",`关系：${r.relationType==="nuance_contrast"?"语感/语义辨析":r.relationType==="usage_difference"?"用法/接续区别":r.relationType}`,"lex-review-meta"));
      if(r.contrast)card.append(node("p",`对比辨析：${r.contrast}`));
      if(r.scenario)card.append(node("p",`典型场景：${r.scenario}`,"lex-notice"));
      card.append(button("查看该条目",()=>openRef(r.sourceRef,r.packSlug)));
      body.append(card);
    }
  }
  if(payload.contexts?.length){body.append(node("h2","收藏时的语境"));for(const c of payload.contexts)body.append(node("p",c.text||c.sourceText||""));}
}
function planFor(slug,refs=[],units=[]){state.planRefs=refs;state.planUnits=units;saveScope();navigate("#/plans");setTimeout(()=>{for(const o of $("#plan-pack").options)o.selected=o.value===slug;$("#plan-name").value=state.packs.find(p=>p.slug===slug)?.title||"";$("#plan-status").textContent=refs.length?`已选 ${refs.length} 个条目`:units.length?"已选择当前单元":"";},0);}
const PROMPT_LABELS={recall:"识义",production:"看释义回忆词语",reading:"看词写读音",cloze:"例句填空",usage:"近义辨析"};
function renderPlans(){
  const list=clear($("#plan-list"));
  if(!state.decks.length)list.append(node("p","还没有计划。选择内容包后即可建立。","lex-empty"));
  for(const d of state.decks){
    const c=node("article",undefined,"lex-plan-card");const p=d.progress||{};const settings=d.settings||{};
    c.append(node("h2",d.name+(settings.paused?"（已暂停）":"")),
      node("p",`已投放 ${p.entriesIntroduced??p.introduced}/${p.entryTotal??p.total} 条 · ${p.due||0} 到期 · ${p.mature||0} 张成熟卡 · 每日 ${d.dailyNew} ${settings.quotaUnit==="entry"?"条目":"卡片（旧计划）"}`),
      node("p",`学习日 ${d.learningDay||"—"}（${d.studyTimezone}） · 方向 ${(settings.promptTypes||[]).map(t=>PROMPT_LABELS[t]||t).join("、")||"推荐"} · 新条目${settings.autoInclude===false?"不自动加入":"自动加入"}`,"lex-review-meta"));
    const actions=node("div",undefined,"lex-pack-actions");
    actions.append(
      button("开始学习",()=>navigate("#/study?deck="+encodeURIComponent(d.id)),"primary-button"),
      button(settings.paused?"恢复计划":"暂停计划",()=>patchPlan(d.id,{paused:!settings.paused})),
      button("编辑计划",()=>editPlan(d)),
      button("删除计划",async()=>{if(!confirm(`删除“${d.name}”？已学卡片与复习历史会保留。`))return;await api("./api/decks/"+d.id,{method:"DELETE"});await refresh();renderPlans();}));
    c.append(actions);list.append(c);
  }
}
async function patchPlan(id,body){
  await api("./api/decks/"+id,{method:"PATCH",body:JSON.stringify(body)});
  await refresh();renderPlans();
}
function editPlan(deck){
  const settings=deck.settings||{};
  $("#plan-editor-heading").textContent=`编辑「${deck.name}」`;
  $("#plan-edit-name").value=deck.name;
  $("#plan-edit-daily").value=deck.dailyNew;
  $("#plan-edit-quota").value=settings.quotaUnit||"card";
  $("#plan-edit-order").value=deck.orderMode;
  $("#plan-edit-timezone").value=deck.studyTimezone||"";
  $("#plan-edit-auto-include").checked=settings.autoInclude!==false;
  $("#plan-edit-paused").checked=Boolean(settings.paused);
  const packs=clear($("#plan-edit-pack"));
  for(const pack of state.packs.filter(item=>!item.broken)){
    const option=node("option",`${pack.level==="ungraded"?"未分级":pack.level} · ${pack.title}`);
    option.value=pack.slug;option.selected=(settings.packSlugs||[deck.packId]).includes(pack.slug);
    packs.append(option);
  }
  const prompts=clear($("#plan-edit-prompts"));
  for(const [value,label] of Object.entries(PROMPT_LABELS)){
    const option=node("option",label);option.value=value;
    option.selected=(settings.promptTypes||[]).includes(value);
    prompts.append(option);
  }
  state.editingPlan=deck.id;
  $("#plan-editor").showModal();
}
async function savePlanEdit(event){
  event.preventDefault();
  await guard(event.submitter,async()=>{
    const body={
      name:$("#plan-edit-name").value.trim(),
      dailyNew:Number($("#plan-edit-daily").value),
      quotaUnit:$("#plan-edit-quota").value,
      orderMode:$("#plan-edit-order").value,
      studyTimezone:$("#plan-edit-timezone").value.trim()||Intl.DateTimeFormat().resolvedOptions().timeZone||"UTC",
      autoInclude:$("#plan-edit-auto-include").checked,
      paused:$("#plan-edit-paused").checked,
      packSlugs:[...$("#plan-edit-pack").selectedOptions].map(o=>o.value),
      promptTypes:[...$("#plan-edit-prompts").selectedOptions].map(o=>o.value),
    };
    // The whole edit is one request, so a rejected direction cannot leave the scope
    // changed and the rest of the plan untouched (§7.3).
    await patchPlan(state.editingPlan,body);
    $("#plan-editor").close();
    toast("已保存。改动从下一个学习日生效；当日批次保持不变。");
  });
}
async function createPlan(event){event.preventDefault();await guard(event.submitter,async()=>{
  const packSlugs=[...$("#plan-pack").selectedOptions].map(o=>o.value);
  const payload={packSlugs,name:$("#plan-name").value.trim(),dailyNew:Number($("#plan-daily").value),
    orderMode:$("#plan-order").value,
    studyTimezone:$("#plan-timezone").value.trim()||Intl.DateTimeFormat().resolvedOptions().timeZone||"UTC",
    quotaUnit:"entry",sourceRefs:state.planRefs,unitIds:state.planUnits,
    autoInclude:$("#plan-auto-include").checked,
    promptTypes:$("#plan-prompts").value.split(",").filter(Boolean)};
  await post("./api/decks",payload);clearScope();
  await refresh();renderPlans();$("#plan-status").textContent="计划已创建。";});}
/* ---------------------------------------------------------------------------
 * 学习：first exposure, in order.
 *
 * 「今日背诵」only ever shows cards a plan has already introduced and that are due, so
 * with no plan it is empty; 「学习本单元」went to the plan form. Reading through a unit
 * therefore meant opening each of its entries by hand, one at a time.
 *
 * This walks a chosen set of entries in order, shows each one in full, and lets the
 * learner decide per entry whether it enters the review queue. It creates cards through
 * the same adapter the plan uses, so a card learned here and a card served by a plan are
 * one card — it is not a second review system.
 * ------------------------------------------------------------------------- */
const LEARN_DIRECTIONS=[["recall","看词想义"],["production","看义想词"],["reading","看词写读音"],["cloze","例句填空"]];
function learnKey(scope){return "learn:"+scope;}

async function loadLearn(slug,unitId,request){
  show("learn");
  $("#learn-summary").textContent="正在准备学习内容…";
  const {pack}=await api("./api/lexicon/packs/"+encodeURIComponent(slug));
  if(request!==state.request)return;
  const unit=(pack.units||[]).find(u=>u.unitId===unitId);
  const ids=unit?unit.entryIds:(pack.entries||[]).map(e=>e.id);
  const entries=ids.map(id=>(pack.entries||[]).find(e=>e.id===id)).filter(Boolean);
  if(!entries.length)throw new Error("这个范围里没有条目。");

  const scope=`${slug}/${unitId||"all"}`;
  const saved=await LearningCardStore.getRecord("lex-sessions",learnKey(scope));
  // Resuming matters: a 22-entry unit is not one sitting.
  const index=saved&&saved.total===entries.length?Math.min(saved.index||0,entries.length):0;
  state.learn={scope,slug,unitId:unitId||"",packId:pack.packId,packTitle:pack.title,
    label:unit?(unit.label||unit.unitId):pack.title,entries,index,total:entries.length,
    revealed:false,introduced:saved?.introduced||[],skipped:saved?.skipped||[],
    directions:saved?.directions||["recall"],cover:Boolean(saved?.cover)};
  const select=clear($("#learn-directions"));
  for(const [value,label] of LEARN_DIRECTIONS){
    const option=node("option",label);option.value=value;
    option.selected=state.learn.directions.includes(value);
    select.append(option);
  }
  $("#learn-cover").checked=state.learn.cover;
  renderLearn();
}

async function saveLearn(){
  const l=state.learn;
  if(!l)return;
  await LearningCardStore.saveSession({id:learnKey(l.scope),scope:l.scope,index:l.index,
    total:l.total,introduced:l.introduced,skipped:l.skipped,directions:l.directions,cover:l.cover});
}

function renderLearn(){
  const l=state.learn;
  if(!l)return;
  $("#learn-heading").textContent=`学习 · ${l.label}`;
  $("#learn-summary").textContent=`${l.packTitle} · 顺序过一遍；决定加入复习的条目会进入今日背诵。`;
  const stats=clear($("#learn-progress"));
  for(const [n,label] of [[l.index,"已处理"],[l.introduced.length,"已加入复习"],
                          [Math.max(0,l.total-l.index),"剩余"]]){
    const cell=node("div",undefined,"lex-progress-stat");
    cell.append(node("strong",n),node("span",label));stats.append(cell);
  }
  const done=l.index>=l.total;
  $("#learn-card").hidden=done;
  $("#learn-empty").hidden=!done;
  if(done){
    $("#learn-empty-copy").textContent=`本组 ${l.total} 条已处理：加入复习 ${l.introduced.length} 条，跳过 ${l.skipped.length} 条。`;
    const actions=clear($("#learn-empty-actions"));
    if(l.introduced.length)actions.append(button("去今日背诵",()=>navigate("#/study"),"primary-button"));
    actions.append(button("练习本组",()=>practiceFor({pack:l.slug,units:l.unitId?[l.unitId]:[]})),
      button("从头再学一遍",async()=>{l.index=0;l.revealed=false;await saveLearn();renderLearn();}),
      button("返回单元",()=>navigate(`#/pack/${encodeURIComponent(l.slug)}${l.unitId?"/"+encodeURIComponent(l.unitId):""}`)));
    return;
  }

  const entry=l.entries[l.index];
  const ref=`lex:${l.packId}#${entry.id}`;
  const reading=entry.snapshot?.reading||entry.dictRef?.reading||"";
  $("#learn-meta").textContent=`${l.index+1}/${l.total} · ${KIND[entry.kind]||"词汇"}${entry.level&&entry.level!=="ungraded"?" · "+entry.level:""}`;

  const front=clear($("#learn-front"));
  front.append(inline(entry.headword,"h2","lex-card-primary"));
  if(reading)front.append(node("p",reading,"lex-example-reading"));

  const body=clear($("#learn-body"));
  const covered=l.cover&&!l.revealed;
  $("#learn-reveal").hidden=!covered;
  body.hidden=covered;
  if(!covered){
    body.append(inline(entry.gloss?.zh||entry.gloss?.en||"中文释义待补充","p","lex-gloss"));
    if(entry.gloss?.zh&&entry.gloss?.en)body.append(node("p",entry.gloss.en,"lex-gloss is-secondary"));
    const pos=entry.snapshot?.pos;
    if(pos?.length)body.append(node("p",pos.join(" · "),"lex-review-meta"));
    for(const connection of entry.grammar?.connection||[])renderConnection(connection,body);
    if(entry.grammar?.notes)renderBlocks(entry.grammar.notes,body);
    examples(entry.examples,body);
    const saved=personal(ref);
    if(saved?.note)body.append(node("p",saved.note,"lex-personal-note"));
  }

  const actions=clear($("#learn-actions"));
  if(reading||entry.headword)actions.append(button("朗读",()=>speak(reading||entry.headword)));
  actions.append(button("加入复习，下一条",()=>guard(null,()=>advanceLearn(entry,ref,true)),"primary-button"));
  actions.append(button("已会，跳过",()=>guard(null,()=>advanceLearn(entry,ref,false))));
  actions.append(button(personal(ref)?.starred?"取消收藏":"收藏",async()=>{
    const saved=personal(ref);
    await saveUser({...saved,sourceRef:ref,headword:entry.headword,reading,gloss:entry.gloss||{},
      kind:entry.kind,level:entry.level||"",examples:entry.examples||[],starred:!saved?.starred});
    renderLearn();
  }));
  actions.append(button("笔记",()=>editUser({...personal(ref),sourceRef:ref,headword:entry.headword,
    reading,gloss:entry.gloss||{},kind:entry.kind,level:entry.level||""})));
  actions.append(button("看完整详情",()=>openRef(ref,l.slug)));
  if(l.index>0)actions.append(button("上一条",async()=>{
    l.index-=1;l.revealed=false;await saveLearn();renderLearn();
  }));
}

async function advanceLearn(entry,ref,introduce){
  const l=state.learn;
  if(introduce){
    const directions=[...$("#learn-directions").selectedOptions].map(o=>o.value);
    l.directions=directions.length?directions:["recall"];
    const result=await post("./api/lexicon/introduce",
      {sourceRefs:[ref],promptTypes:l.directions});
    if(result.count){
      await LearningCardStore.putMany(result.items);
      if(!l.introduced.includes(ref))l.introduced.push(ref);
      broadcast({id:result.items[0].id,reason:"introduce"});
    }else{
      // Say why nothing was created rather than looking like it worked.
      const reason=(result.skipped||[])[0]?.reason==="no-direction"
        ? "这一条在所选方向上没有可用卡片（可能缺读音或例句）。"
        : "这一条没有加入复习（可能此前被删除过）。";
      toast(reason,true);
    }
  }else if(!l.skipped.includes(ref))l.skipped.push(ref);
  l.index+=1;l.revealed=false;
  await saveLearn();renderLearn();
}

async function loadStudy(deck=""){
  show("study");$("#study-deck").value=deck;$("#study-summary").textContent="正在载入待学内容…";
  const id="study:"+deck;const cached=await LearningCardStore.getRecord("lex-sessions",id);let items,warnings=[],learningDay="";
  try{const result=await post("./api/lexicon/today",{deck});items=result.items;warnings=result.warnings||[];learningDay=result.learningDay||"";
    if(result.pausedHeld)warnings.push(`${result.pausedHeld} 张卡属于已暂停的计划，本日不投放。`);
    await LearningCardStore.putMany(items);}catch(e){if(e.status)throw e;items=(await LearningCardStore.due()).filter(c=>!deck||(c.deckIds||[]).includes(deck));warnings=["本地服务不可用：使用已缓存卡片。"];learningDay=cached?.day||"";}
  // The plan's own timezone decides the learning day; the browser locale must not, or a
  // session in progress is dropped when the two disagree across midnight (§7.3).
  const day=learningDay||new Date().toLocaleDateString("en-CA");const saved=cached?.day===day?cached:null;const byId=new Map(items.map(c=>[c.id,c]));const remaining=saved?saved.items.slice(saved.index).filter(i=>i.round>0||byId.has(i.card.id)):[];const seen=new Set(remaining.map(i=>i.card.id));for(const card of items)if(!seen.has(card.id))remaining.push({card,round:0,revealed:false});
  state.study={id,day,items:remaining,index:0,deck};await LearningCardStore.saveSession(state.study);$("#study-summary").textContent=warnings.join(" ")||"到期复习优先，新条目随后。重来和困难会在本轮再次出现。";$("#lex-due-badge").textContent=items.length?`(${items.length})`:"";renderStudy();
}
function renderStudy(){
  const study=state.study;const entry=study?.items[study.index];$("#review-card").hidden=!entry;$("#study-empty").hidden=Boolean(entry);const stats=clear($("#study-progress"));for(const [n,label] of [[study?.index||0,"本轮已处理"],[Math.max(0,(study?.items.length||0)-(study?.index||0)),"剩余任务"]]){const c=node("div",undefined,"lex-progress-stat");c.append(node("strong",n),node("span",label));stats.append(c);}
  if(!entry){
    const nothingYet=!(study?.items||[]).length&&!state.decks.length;
    $("#study-empty-title").textContent=nothingYet?"还没有要复习的内容":"当前队列已完成";
    $("#study-empty-copy").textContent=nothingYet
      ?"先去内容包里学一个单元：学过的条目会进入这里等待复习。也可以建立学习计划，让它每天自动投放。"
      :"可以再学一个新单元、开始专项练习，或在学习计划中安排新条目。";
    const actions=clear($("#study-empty-actions"));
    actions.append(button("去学一个单元",()=>navigate(""),"primary-button"),
      button("专项练习",()=>navigate("#/practice/new")),
      button("学习计划",()=>navigate("#/plans")));
    return;
  }
  const card=entry.card;const payload=card.cardPayload||{};const template=payload.template||{};const prompt=clear($("#review-prompt"));const answer=clear($("#review-answer"));$("#review-meta").textContent=`${study.index+1}/${study.items.length} · ${KIND[card.entryKind]||"词汇"} · ${entry.round?"本轮巩固，不重复推进长期次数":TYPES[card.promptType]||"回忆"}`;
  // A card created by a reading / cloze / choice exercise keeps its question. Reviewing
  // it as a plain flip card would quietly drop the direction it was learned in (LEX-01).
  const snapshot=payload.exercise||template.exercise;
  const exercise=snapshot?.mode&&snapshot.mode!=="self"&&!(card.promptType==="cloze"&&template.markedJa)?snapshot:null;
  if(exercise){renderStudyExercise(entry,card,exercise,prompt,answer);return;}
  if(card.promptType==="cloze"&&template.markedJa)renderInline(template.markedJa,prompt,{cloze:"hide"});else prompt.append(inline(card.promptType==="production"?card.meaning:card.term,"p","lex-card-primary"));answer.append(inline(card.term,"h2"));if(card.reading)answer.append(node("p",card.reading,"lex-example-reading"));answer.append(inline(card.meaning||"来源释义待补充"));for(const c of payload.grammar?.connection||[])renderConnection(c,answer);examples(payload.examples,answer);if(card.note)answer.append(node("p",card.note,"lex-personal-note"));answer.append(button("朗读",()=>speak(card.reading||card.term)),button("暂停此卡",async()=>{await LearningDataSync.mutate("PATCH","./api/vocab/"+card.id,{reviewSuspended:true},{entityType:"vocab",entityKey:card.id});await LearningCardStore.put({...card,reviewSuspended:true});study.index++;await LearningCardStore.saveSession(study);renderStudy();
    broadcast({id:card.id,version:card.reviewVersion,reason:"suspend"});}));
  $("#review-answer").hidden=!entry.revealed;$("#review-grades").hidden=!entry.revealed;$("#review-reveal").hidden=entry.revealed;
  document.querySelectorAll("#review-grades [data-grade]").forEach(b=>{const schedule=SrsScheduler.schedule(card,b.dataset.grade,new Date().toISOString());b.textContent=({again:"重来",hard:"困难",good:"记得",easy:"简单"})[b.dataset.grade]+` · ${schedule.srsInterval} 天`;});
}
function renderStudyExercise(entry,card,q,prompt,answer){
  $("#review-reveal").hidden=true;$("#review-grades").hidden=true;
  prompt.append(inline(q.prompt,"p","lex-card-primary"));
  if(q.type==="listening")prompt.append(button("播放题目（合成语音）",()=>speak(q.speech||q.reading||card.reading||card.term),"primary-button"));
  if(entry.result){
    // The graded state is part of the session, so a refresh returns to the feedback
    // rather than silently skipping past it (§10.2).
    const labels={correct:"独立答对",wrong:"这题需要再练",assisted:"借助提示或蒙对，稍后再练"};
    answer.append(node("h2",labels[entry.result.classification]||"已保存"),inline(card.term,"p","lex-card-primary"));
    if(entry.result.referenceAnswer)answer.append(node("p","参考答案："+formatAnswer(entry.result.referenceAnswer)));
    answer.append(node("p",entry.result.explanation||""));
    for(const choice of entry.result.choices||[])answer.append(node("p",`${choice.label}：${choice.rationale}`));
    examples(card.cardPayload?.examples,answer);
    answer.append(button("记录并继续",()=>gradeStudy(entry.result.suggestedGrade),"primary-button"));
    answer.hidden=false;return;
  }
  const form=node("form",undefined,"lex-answer-form");let control;const order=[];
  if(q.mode==="choice"){
    for(const [index,choice] of (q.choices||[]).entries()){const label=node("label",undefined,"lex-answer-choice");const radio=node("input");radio.type="radio";radio.name="study-answer";radio.value=choice.id;radio.required=true;label.append(radio,node("span",`${index+1}. ${choice.label}`));form.append(label);}
  }else if(q.mode==="order"){
    const available=node("div",undefined,"lex-pack-actions");const selected=node("div",undefined,"lex-order-answer");selected.setAttribute("aria-label","已排列片段");
    const draw=()=>{clear(available);clear(selected);for(const token of q.tokens||[])if(!order.includes(token.id))available.append(button(token.label,()=>{order.push(token.id);draw();}));for(const [index,id] of order.entries()){const token=q.tokens.find(t=>t.id===id);const wrap=node("span",undefined,"lex-order-token");wrap.append(node("span",token.label),button("←",()=>{if(index){[order[index-1],order[index]]=[order[index],order[index-1]];draw();}}),button("移除",()=>{order.splice(index,1);draw();}));selected.append(wrap);}};
    draw();form.append(available,selected);
  }else{
    control=node("textarea");control.rows=2;control.maxLength=4000;control.required=true;control.setAttribute("aria-label","你的答案");control.placeholder=q.blankCount>1?"多个空按顺序用 / 分隔":"输入答案";form.append(control);setTimeout(()=>control.focus(),0);
  }
  const submit=node("button","提交答案","primary-button");submit.type="submit";form.append(submit);
  if(entry.hinted)form.append(node("p","参考答案："+formatAnswer(q.referenceAnswer||q.acceptedAnswers||""),"lex-notice"));
  else form.append(button("看答案（本次记为借助提示）",async()=>{entry.hinted=true;await LearningCardStore.saveSession(state.study);renderStudy();}));
  form.append(button("暂停此卡",()=>suspendStudyCard(card)));
  form.addEventListener("submit",event=>{
    event.preventDefault();if(event.isComposing)return;
    const picked=form.querySelector("input[name=study-answer]:checked");
    const value=q.mode==="choice"?picked?.value:q.mode==="order"?order:control?.value||"";
    guard(null,async()=>{
      entry.result=LexiconScoring.score(q,value,{hinted:Boolean(entry.hinted)});
      entry.answer=value;entry.revealed=true;
      await LearningCardStore.saveSession(state.study);renderStudy();
    });
  });
  form.addEventListener("keydown",e=>{if(e.isComposing||e.keyCode===229)return;if(e.key==="Enter"&&!e.shiftKey&&q.mode!=="order"){e.preventDefault();form.requestSubmit();}});
  prompt.append(form);
  answer.hidden=true;
}
async function suspendStudyCard(card){
  await LearningDataSync.mutate("PATCH","./api/vocab/"+card.id,{reviewSuspended:true},{entityType:"vocab",entityKey:card.id});
  await LearningCardStore.put({...card,reviewSuspended:true});
  state.study.index++;await LearningCardStore.saveSession(state.study);renderStudy();
  broadcast({id:card.id,version:card.reviewVersion,reason:"suspend"});
}
async function gradeStudy(grade){if(state.busy)return;state.busy=true;try{
  const study=state.study;const item=study.items[study.index];if(!item?.revealed)return;let card=item.card;
  if(item.round===0){
    const reviewedAt=new Date().toISOString();const predicted=SrsScheduler.schedule(card,grade,reviewedAt);
    let response;
    try{
      // `reviewVersion` moves only for scheduling changes, so a content refresh cannot
      // manufacture a conflict while a real concurrent grade still does (LEX-03).
      response=await LearningDataSync.mutate("POST","./api/vocab/review",
        {vocabId:card.id,grade,reviewedAt,expectedReviewVersion:card.reviewVersion},
        {entityType:"vocab-review",entityKey:card.id,clearTombstone:false});
    }catch(error){
      // The server rejected it. Writing the local prediction anyway would show a
      // schedule that does not exist, so reload the card and let the learner retry.
      await reloadStudyCard(item);
      renderStudy();
      throw error;
    }
    card={...(response.result?.item||predicted),deckIds:card.deckIds||[]};await LearningCardStore.put(card);
  }
  study.index++;
  if(["again","hard"].includes(grade)&&item.round<2)study.items.splice(Math.min(study.items.length,study.index+3),0,{card,round:item.round+1,revealed:false});
  await LearningCardStore.saveSession(study);renderStudy();
  broadcast({id:card.id,version:card.reviewVersion,reason:"review"});
}finally{state.busy=false;}}
async function reloadStudyCard(item){
  item.revealed=false;delete item.result;delete item.answer;delete item.hinted;
  try{const {items}=await api("./api/vocab");await LearningCardStore.putMany(items);
    const fresh=items.find(card=>card.id===item.card.id);
    if(fresh)item.card={...fresh,deckIds:item.card.deckIds||[]};
    else state.study.items.splice(state.study.items.indexOf(item),1);
  }catch{/* offline: the local copy stays, the operation stays queued */}
  await LearningCardStore.saveSession(state.study);
}
const SCOPE_KEY="dictation-lex-scope:v1";
function saveScope(){
  // The selected range used to live only in memory, so a reload silently widened a
  // targeted practice back to everything (§11.3).
  writeLocal(SCOPE_KEY,{practiceRefs:state.practiceRefs,practiceUnits:state.practiceUnits,
    planRefs:state.planRefs,planUnits:state.planUnits,at:Date.now()});
}
function restoreScope(){
  const saved=readLocal(SCOPE_KEY,null);
  if(!saved||Date.now()-Number(saved.at||0)>86400000)return;
  state.practiceRefs=saved.practiceRefs||[];state.practiceUnits=saved.practiceUnits||[];
  state.planRefs=saved.planRefs||[];state.planUnits=saved.planUnits||[];
}
function clearScope(){state.practiceRefs=[];state.practiceUnits=[];state.planRefs=[];state.planUnits=[];saveScope();}
function describeScope(){
  const refs=state.practiceRefs.length;const units=state.practiceUnits.length;
  $("#practice-status").textContent=refs?`已选 ${refs} 个条目（刷新后仍保留）`
    :units?"范围：所选单元（刷新后仍保留）":"";
}
function practiceFor({pack="",refs=[],units=[],types=[]}={}){
  state.practiceRefs=refs;state.practiceUnits=units;saveScope();
  navigate("#/practice/new");
  setTimeout(()=>{$("#practice-pack").value=pack;
    if(types.length)document.querySelectorAll("#practice-types input").forEach(n=>{n.checked=types.includes(n.value)&&!n.disabled;});
    describeScope();},0);
}
async function createPractice(event){event.preventDefault();await guard(event.submitter,async()=>{const pack=$("#practice-pack").value;const types=[...document.querySelectorAll("#practice-types input:checked")].map(n=>n.value);if(!types.length)throw new Error("请至少选择一种题型。");const payload={kind:$("#practice-kind").value,packSlugs:pack?[pack]:[],sourceRefs:state.practiceRefs,unitIds:state.practiceUnits,scope:$("#practice-scope").value,count:Number($("#practice-count").value),feedback:$("#practice-feedback").value,review:$("#practice-review").checked,includeDrafts:$("#practice-drafts").checked,types};let session;
    try{({session}=await post("./api/lexicon/sessions",payload,uid()));}
    catch(error){
      // A type with nothing reviewed is not a dead end: offer the draft path instead.
      if(!$("#practice-drafts").checked&&/未审核/.test(error.message||"")
         &&confirm(error.message+"\n\n现在就用未审核题目练习？")){
        $("#practice-drafts").checked=true;
        ({session}=await post("./api/lexicon/sessions",{...payload,includeDrafts:true},uid()));
      }else throw error;
    }
    await LearningCardStore.saveSession(session);clearScope();navigate("#/practice/"+session.id);});}
async function pendingOperations(){return (await LearningCardStore.listRecords("lex-operations")).filter(o=>o.status!=="archived").sort((a,b)=>a.createdAt.localeCompare(b.createdAt)||a.sequence-b.sequence);}
function mergeSession(remote,cached){
  if(!cached)return remote;
  if(cached.offlineQuestions)remote.offlineQuestions=cached.offlineQuestions;
  const pendingKeys=new Set(remote.state.queue.slice(remote.state.cursor).map(t=>draftKey(t.itemId,t.round)));
  remote.drafts=Object.fromEntries(Object.entries(cached.drafts||{}).filter(([key])=>pendingKeys.has(key)));
  if(cached.pendingFeedback&&remote.version===cached.version)remote.pendingFeedback=cached.pendingFeedback;
  return remote;
}
async function loadSession(id){
  let session;const cached=await LearningCardStore.getRecord("lex-sessions",id);
  const pending=(await pendingOperations()).some(o=>o.sessionId===id);
  if(pending&&cached)session=cached;
  else{try{session=mergeSession((await api("./api/lexicon/sessions/"+id)).session,cached);await LearningCardStore.saveSession(session);}
    catch(e){if(!cached||e.status)throw e;session=cached;}}
  state.session=session;show("session");
  if(["completed","completed_with_skips"].includes(session.status)){await displayReport(id);return;}
  renderSession();
}
function questionFor(session,itemId){const publicQ=session.items.find(q=>q.id===itemId);return !state.online&&session.offlineQuestions?session.offlineQuestions.find(q=>q.id===itemId)||publicQ:publicQ;}
function draftKey(itemId,round){return `${itemId}:${round}`;}
let draftTimer=null;
function saveDraft(session,key,patch){
  // Debounced so typing does not write on every keystroke; `pagehide` fills the gap.
  session.drafts={...(session.drafts||{}),[key]:{...(session.drafts?.[key]||{}),...patch}};
  clearTimeout(draftTimer);
  draftTimer=setTimeout(()=>{LearningCardStore.saveSession(session).catch(e=>toast("草稿保存失败："+e.message,true));},400);
}
function flushDraft(){
  clearTimeout(draftTimer);
  if(state.session)LearningCardStore.saveSession(state.session).catch(()=>{});
}
function renderSession(){
  const s=state.session;const body=clear($("#session-body"));const queued=s.state.queue[s.state.cursor];
  // A refresh must return to unread feedback rather than skipping silently past it.
  if(s.pendingFeedback){
    const shown=s.items.find(item=>item.id===s.pendingFeedback.itemId)||s.pendingFeedback.question;
    if(shown){renderFeedback(s.pendingFeedback.result,shown);return;}
    delete s.pendingFeedback;
  }$("#session-heading").textContent=`专项练习 · ${s.state.cursor}/${s.state.queue.length}`;$("#session-status").textContent=(state.online?"":"离线练习 · 结果将在重连后核验。 ")+(s.state.requested>s.items.length?`所选范围有 ${s.items.length} 道合格题目，已按实际数量组题。`:"");
  if(!queued){
    const answered=new Set((s.attempts||[]).filter(a=>a.result?a.result.skipped===false:true).map(a=>a.itemId));
    const outstanding=(s.state.skipped||[]).filter(id=>!answered.has(id));
    body.append(node("h2",outstanding.length?"本组还有跳过的题":"本组题目已作答"));
    if(outstanding.length){
      // Skipping is not answering, so the summary must not read as "all done" (§10.2).
      body.append(node("p",`${outstanding.length} 道题被跳过，尚未作答。`,"lex-notice"));
      body.append(button("回到跳过的题",()=>resumeSkipped(outstanding),"primary-button"),
                  button("就此结束（记为未完成）",()=>finishSession(true)));
    }else body.append(button("提交并查看报告",()=>finishSession(),"primary-button"));
    return;
  }
  const q=questionFor(s,queued.itemId);let full=s.offlineQuestions?.find(item=>item.id===q.id);body.append(node("p",`${KIND[q.kind]} · ${TYPES[q.type]||q.type}${queued.round?" · 本轮重练":""}`,"lex-review-meta"),inline(q.prompt,"p","lex-card-primary"));
  if(q.draft||q.qualified===false)body.append(node("p",q.draftReason||"未审核题目：不计入正式正确率，不推进长期复习。","lex-notice"));
  if(q.type==="listening")body.append(button("播放题目（合成语音）",()=>speak(q.speech||full?.speech||full?.reading||""),"primary-button"));
  const form=node("form");form.className="lex-answer-form";let control;const key=draftKey(q.id,queued.round);const draft=s.drafts?.[key]||{};let order=[...(draft.order||[])];let selfRevealed=false;const start=performance.now();
  if(q.mode==="choice"){for(const [i,c]of(q.choices||[]).entries()){const label=node("label",undefined,"lex-answer-choice");const radio=node("input");radio.type="radio";radio.name="answer";radio.value=c.id;radio.required=true;radio.checked=draft.choice===c.id;radio.addEventListener("change",()=>saveDraft(s,key,{choice:c.id}));label.append(radio,node("span",`${i+1}. ${c.label}`));form.append(label);}}
  else if(q.mode==="order"){
    const available=node("div",undefined,"lex-pack-actions");const selected=node("div",undefined,"lex-order-answer");selected.setAttribute("aria-label","已排列片段");const draw=()=>{saveDraft(s,key,{order:[...order]});clear(available);clear(selected);for(const t of q.tokens||[])if(!order.includes(t.id))available.append(button(t.label,()=>{order.push(t.id);draw();}));for(const [i,id]of order.entries()){const t=(q.tokens||[]).find(t=>t.id===id);if(!t)continue;const wrap=node("span",undefined,"lex-order-token");wrap.append(node("span",t.label),button("←",()=>{if(i){[order[i-1],order[i]]=[order[i],order[i-1]];draw();}}),button("移除",()=>{order.splice(i,1);draw();}));selected.append(wrap);}};draw();form.append(available,selected);
  }else if(q.mode!=="self"||q.type==="writing"||q.type==="production"){control=node("textarea");control.rows=q.type==="writing"?4:2;control.maxLength=4000;control.required=q.mode!=="self";control.setAttribute("aria-label","你的答案");control.placeholder=q.blankCount>1?"多个空按顺序用 / 分隔":"输入答案";control.value=draft.text||"";control.addEventListener("input",()=>saveDraft(s,key,{text:control.value}));form.append(control);setTimeout(()=>control.focus(),0);}
  const guessed=node("input");guessed.type="checkbox";guessed.checked=Boolean(draft.guessed);guessed.addEventListener("change",()=>saveDraft(s,key,{guessed:guessed.checked}));const guessedLabel=node("label");guessedLabel.append(guessed,node("span","这题是蒙的 / 不确定"));form.append(guessedLabel);
  async function reveal(){
    let answer;const key=`${q.id}:${queued.round}`;
    // The hint has to be part of the replayable event chain: preparing offline, taking a
    // hint online, then answering offline must rebuild the same version order (§8.2).
    const operation={id:uid(),sessionId:s.id,action:"reveal",body:{itemId:q.id,round:queued.round},createdAt:new Date().toISOString(),sequence:Date.now(),status:"pending"};
    const pending=structuredClone({...s,offlineQuestions:undefined});
    if(!pending.state.exposed.includes(key))pending.state.exposed.push(key);
    if(s.offlineQuestions)pending.offlineQuestions=s.offlineQuestions;
    await LearningCardStore.saveOperation(pending,operation);
    if(state.online){
      try{const r=await post(`./api/lexicon/sessions/${s.id}/reveal`,{itemId:q.id,round:queued.round},operation.id);answer=r.question;s.version=r.version;
        if(!s.state.exposed.includes(key))s.state.exposed.push(key);
        await LearningCardStore.writeRecords([{store:"lex-sessions",value:s},{store:"lex-operations",id:operation.id,remove:true}]);
      }catch(error){
        if(error.status){await LearningCardStore.writeRecords([{store:"lex-operations",id:operation.id,remove:true}]);throw error;}
        if(!full)throw new Error("尚未准备该题的离线答案。");
        answer=full;if(!s.state.exposed.includes(key))s.state.exposed.push(key);
      }
    }else{
      if(!full){await LearningCardStore.writeRecords([{store:"lex-operations",id:operation.id,remove:true}]);throw new Error("尚未准备该题的离线答案。");}
      answer=full;if(!s.state.exposed.includes(key))s.state.exposed.push(key);
    }
    await LearningCardStore.saveSession(s);const div=node("div",undefined,"lex-feedback");div.append(node("p",formatAnswer(answer.referenceAnswer||answer.acceptedAnswers||answer.meaning||"")),node("p",answer.explanation||""));form.append(div);selfRevealed=true;}
  if(q.mode==="self"){
    const revealButton=button("显示参考答案",async()=>{await reveal();revealButton.hidden=true;grades.hidden=false;},"primary-button");const grades=node("div",undefined,"lex-grade-row");grades.hidden=true;for(const [grade,label]of Object.entries({again:"重来",hard:"困难",good:"记得",easy:"简单"}))grades.append(button(label,()=>submitAnswer({grade,text:control?.value||""}),"quiet-button"));form.append(revealButton,grades);
  }else{
    const submit=node("button","提交答案","primary-button");submit.type="submit";form.append(submit);if(s.config.feedback!=="end")form.append(button("查看提示 / 答案",reveal));
  }
  form.append(button("跳过并稍后重试",()=>submitAnswer(null,true)));
  async function submitAnswer(answer,skipped=false){full=s.offlineQuestions?.find(item=>item.id===q.id)||full;if(state.busy)return;if((await pendingOperations()).some(op=>op.sessionId===s.id)&&!s.offlineQuestions)throw new Error("此会话有待确认的提交，请先同步记录。");state.busy=true;form.querySelectorAll("button,input,textarea").forEach(n=>n.disabled=true);try{
      const payload={itemId:q.id,round:queued.round,answer,skipped,guessed:guessed.checked,hinted:q.mode!=="self"&&s.state.exposed.includes(`${q.id}:${queued.round}`),version:s.version,reviewedAt:new Date().toISOString(),elapsedMs:Math.min(4*3600000,Math.round(performance.now()-start))};
      const operation={id:uid(),sessionId:s.id,action:"answer",body:payload,createdAt:new Date().toISOString(),sequence:Date.now(),status:"pending"};
      // Persist the answer and its operation id before the request leaves. A write the
      // service applied but never acknowledged is then replayed under the same id and
      // recognised as a duplicate, instead of being scored twice (LEX-05, §8.1).
      const held=structuredClone({...s,offlineQuestions:undefined});
      if(s.offlineQuestions)held.offlineQuestions=s.offlineQuestions;
      await LearningCardStore.saveOperation(held,operation);
      let response;let settled=true;
      try{
        if(!state.online)throw new TypeError("offline");
        response=await post(`./api/lexicon/sessions/${s.id}/answers`,payload,operation.id);
      }catch(e){
        if(e.status&&![408,429].includes(e.status)&&e.status<500){
          // The service decided; replaying cannot change that. The answer stays on
          // screen and the operation leaves the queue rather than blocking the rest.
          await LearningCardStore.writeRecords([{store:"lex-operations",id:operation.id,remove:true}]);
          throw e;
        }
        if(!full){throw new Error("未收到提交回执，答案及操作已保存。请同步记录确认结果后继续。");}
        const result=LexiconScoring.score(full,answer,payload);
        const updated=structuredClone(held);updated.version++;updated.state.cursor++;
        updated.state.skipped=updated.state.skipped||[];
        if(result.skipped){if(!updated.state.skipped.includes(q.id))updated.state.skipped.push(q.id);}
        else updated.state.skipped=updated.state.skipped.filter(id=>id!==q.id);
        if(updated.config.feedback!=="end"&&(result.needsRetry||result.skipped)&&queued.round<2)updated.state.queue.splice(Math.min(updated.state.queue.length,updated.state.cursor+3),0,{itemId:q.id,round:queued.round+1});
        updated.attempts.push({itemId:q.id,round:queued.round,answer,result:{...result,elapsedMs:payload.elapsedMs},createdAt:payload.reviewedAt});
        await LearningCardStore.saveOperation(updated,operation);
        response={session:updated,result:updated.config.feedback==="end"?{saved:true}:result};settled=false;
      }
      if(s.offlineQuestions)response.session.offlineQuestions=s.offlineQuestions;
      state.session=response.session;
      const drafts={...(s.drafts||{})};delete drafts[key];state.session.drafts=drafts;
      // The feedback screen is a stage of the session, not a transient view: a reload
      // during it must come back to it instead of jumping to the next question (§10.2).
      state.session.pendingFeedback=response.result.saved?null:{itemId:q.id,round:queued.round,result:response.result,question:q};
      if(!state.session.pendingFeedback)delete state.session.pendingFeedback;
      // Applying the receipt and clearing the pending marker is one transaction: a crash
      // between them would otherwise replay an answer the server already recorded.
      await LearningCardStore.writeRecords(settled
        ?[{store:"lex-sessions",value:state.session},{store:"lex-operations",id:operation.id,remove:true}]
        :[{store:"lex-sessions",value:state.session}]);
      if(response.result.saved)renderSession();else renderFeedback(response.result,q);
    }finally{state.busy=false;form.querySelectorAll("button,input,textarea").forEach(n=>n.disabled=false);}}
  form.addEventListener("submit",event=>{event.preventDefault();if(event.isComposing)return;const selected=form.querySelector("input[name=answer]:checked");const answer=q.mode==="choice"?selected?.value:q.mode==="order"?order:control?.value||"";guard(null,()=>submitAnswer(answer));});form.addEventListener("keydown",e=>{if(e.isComposing||e.keyCode===229)return;if(e.key==="Enter"&&!e.shiftKey&&q.mode!=="self"&&q.mode!=="order"){e.preventDefault();form.requestSubmit();}});body.append(form);
}
function formatAnswer(answer){if(Array.isArray(answer))return answer.map(a=>Array.isArray(a)?a.join(" / "):a).join("；");return String(answer??"");}
async function dismissFeedback(){
  if(state.session?.pendingFeedback){delete state.session.pendingFeedback;await LearningCardStore.saveSession(state.session);}
  renderSession();
}
function renderFeedback(result,q){const body=clear($("#session-body"));const labels={correct:"独立答对",wrong:"这题需要再练",assisted:"借助提示或蒙对，稍后再练",self_assessed:"已记录自评",skipped:"已跳过"};body.append(node("h2",labels[result.classification]||"已保存"),node("p",result.headword||""));if(result.referenceAnswer)body.append(node("p","参考答案："+formatAnswer(result.referenceAnswer),"lex-card-primary"));body.append(node("p",result.explanation||""));for(const c of result.choices||[])body.append(node("p",`${c.label}：${c.rationale}`));examples(result.examples,body);if(result.draft)body.append(node("p",result.draftNotice||"未审核题目，不计入正式正确率或长期复习。","lex-notice"));if(result.srsConflict)body.append(node("p",result.srsConflict,"lex-notice"));if(result.nextReviewAt)body.append(node("p","下次复习："+new Date(result.nextReviewAt).toLocaleString()));body.append(button("下一题",dismissFeedback,"primary-button"),button("查看条目",()=>openRef(q.sourceRef,q.packSlug)),button("反馈题目问题",async()=>{const message=prompt("请说明题目或答案的问题：");if(message?.trim()){await post(`./api/lexicon/sessions/${state.session.id}/feedback`,{itemId:q.id,message});toast("已记录问题，作答历史保留。");}}));}
async function prepareOffline(){const s=state.session;const response=await api(`./api/lexicon/sessions/${s.id}/offline`);s.offlineQuestions=response.session.items;s.offlinePrepared=true;await LearningCardStore.saveSession(s);toast(`已保存 ${s.items.length} 道题及判题数据，可在本地服务关闭后继续。`);}
async function resumeSkipped(itemIds){
  const s=state.session,body={itemIds};
  const operation={id:uid(),sessionId:s.id,action:"resume-skipped",body,createdAt:new Date().toISOString(),sequence:Date.now(),status:"pending"};
  const previous=await pendingOperations();
  await LearningCardStore.saveOperation(s,operation);
  let session;
  try{
    if(!state.online||previous.some(o=>o.sessionId===s.id))throw new TypeError("offline");
    ({session}=await post(`./api/lexicon/sessions/${s.id}/resume-skipped`,body,operation.id));
  }catch(error){
    if(error.status){await LearningCardStore.writeRecords([{store:"lex-operations",id:operation.id,remove:true}]);throw error;}
    if(!s.offlineQuestions)throw new Error("重排请求已保存，请连接本地服务后同步。");
    session=structuredClone(s);
    const pending=new Set(session.state.queue.slice(session.state.cursor).map(t=>t.itemId));
    for(const id of itemIds)if(!pending.has(id)){
      const round=1+Math.max(-1,...session.state.queue.filter(t=>t.itemId===id).map(t=>t.round));
      session.state.queue.push({itemId:id,round});
    }
    session.version++;
    await LearningCardStore.saveOperation(session,operation);
    state.session=session;renderSession();return;
  }
  state.session=mergeSession(session,s);
  await LearningCardStore.writeRecords([{store:"lex-sessions",value:state.session},{store:"lex-operations",id:operation.id,remove:true}]);renderSession();
}
async function finishSession(acceptSkipped=false){
  const s=state.session;const body={acceptSkipped};
  if(!state.online||(await pendingOperations()).some(op=>op.sessionId===s.id)){
    const answered=new Set((s.attempts||[]).filter(a=>a.result&&!a.result.skipped).map(a=>a.itemId));
    const outstanding=(s.state.skipped||[]).filter(id=>!answered.has(id));
    const updated={...s,status:outstanding.length?"completed_with_skips":"completed",provisional:true};
    const operation={id:uid(),sessionId:s.id,action:"submit",body,createdAt:new Date().toISOString(),sequence:Date.now(),status:"pending"};
    await LearningCardStore.saveOperation(updated,operation);state.session=updated;displayLocalReport(updated);return;
  }
  const {report}=await post(`./api/lexicon/sessions/${s.id}/submit`,body);
  state.session.status=report.status||"completed";state.session.report=report;
  await LearningCardStore.saveSession(state.session);renderReport(report);broadcast();
}
async function displayReport(id){try{const {report}=await api(`./api/lexicon/sessions/${id}/report`);renderReport(report);}catch(e){const cached=await LearningCardStore.getRecord("lex-sessions",id);if(cached?.report)renderReport(cached.report);else if(cached?.offlineQuestions)displayLocalReport(cached);else throw e;}}
function displayLocalReport(s){
  const attempts=s.attempts||[];const valid=attempts.filter(a=>a.result&&!byDraft(a));
  function byDraft(a){return a.validity==="draft"||a.result.draft||(s.offlineQuestions||s.items||[]).find(q=>q.id===a.itemId)?.qualified===false;}
  const first=valid.filter(a=>a.round===0);
  const answered=valid.filter((a,i)=>!a.result.skipped&&!valid.slice(0,i).some(b=>b.itemId===a.itemId&&!b.result.skipped));
  const objective=answered.filter(a=>a.result.correct!==null);
  const correct=objective.filter(a=>a.result.classification==="correct").length;
  const answeredIds=new Set(answered.map(a=>a.itemId));
  const skipped=first.filter(a=>a.result.skipped&&!answeredIds.has(a.itemId));
  const items=s.offlineQuestions||s.items||[];
  const byItem=new Map(items.map(q=>[q.id,q]));
  renderReport({sessionId:s.id,provisional:true,status:s.status,items,attempts,summary:{
    // Entries are counted by sourceRef: one entry practised in two directions is one
    // entry, and counting itemIds would inflate it (§10.4).
    entries:new Set(answered.map(a=>byItem.get(a.itemId)?.sourceRef||a.itemId)).size,
    processed:first.length,answered:answered.length,objectiveCount:objective.length,
    accuracy:objective.length?Math.round(1000*correct/objective.length)/10:null,
    draft:attempts.filter(byDraft).length,
    assisted:answered.filter(a=>a.result.classification==="assisted").length,
    selfAssessed:answered.filter(a=>a.result.classification==="self_assessed").length,
    skipped:skipped.length,remaining:skipped.length,complete:!skipped.length,
    retries:attempts.length-first.length,
    elapsedMs:attempts.reduce((n,a)=>n+(a.result?.elapsedMs||0),0)}});
}
function renderReport(report){show("session");$("#session-heading").textContent="练习报告";
  const incomplete=report.summary.complete===false||report.status==="completed_with_skips";
  $("#session-status").textContent=(report.provisional?"离线暂定报告，重连后会按服务器保存的题目核验。":"首次作答与巩固重练分别记录。")+(incomplete?` 本组以未完成结束，还有 ${report.summary.remaining??report.summary.skipped} 道题没有作答。`:"");
  const body=clear($("#session-body"));const s=report.summary;if(s.draft)body.append(node("p",`${s.draft} 次未审核题作答，不计入正式正确率与长期复习。`,"lex-notice"));
  body.append(node("p",`作答 ${s.answered} 题${s.processed!==undefined&&s.processed!==s.answered?`（处理 ${s.processed} 题）`:""} · ${s.entries} 个条目 · 首次客观正确率 ${s.accuracy===null?"暂无数据":s.accuracy+"%"} · 辅助完成 ${s.assisted} · 自评 ${s.selfAssessed??0} · 跳过未答 ${s.skipped} · 重练 ${s.retries}`));const wrongRefs=new Set();for(const a of report.attempts.filter(a=>a.round===0)){const q=report.items.find(q=>q.id===a.itemId);if(!q||!a.result)continue;if(a.result.needsRetry||a.result.skipped)wrongRefs.add(q.sourceRef);const details=node("details",undefined,"lex-report-item");details.append(node("summary",`${a.result.classification==="correct"?"✓":a.result.classification==="self_assessed"?"自评":"待巩固"} ${q.headword||TYPES[q.type]}`),inline(q.prompt),node("p","你的答案："+formatAnswer(typeof a.answer==="object"&&!Array.isArray(a.answer)?a.answer?.text||a.answer?.grade:a.answer)),node("p",a.result.explanation||q.explanation||""));for(const c of a.result.choices||[])details.append(node("p",`${c.label}：${c.rationale}`));details.append(button("回到条目",()=>openRef(q.sourceRef,q.packSlug)));body.append(details);}body.append(button("查看学习记录",()=>navigate("#/records")));if(wrongRefs.size)body.append(button("复练薄弱条目",()=>practiceFor({refs:[...wrongRefs]}),"primary-button"));}
async function syncPractice(){
  if(!await token())throw new Error("本地服务未连接，离线记录已保留。");await LearningDataSync.flush();const pending=await pendingOperations();let sent=0;const blocked=new Set();
  for(const op of pending){if(blocked.has(op.sessionId))continue;try{const payload={operations:[op]};const response=await post("./api/lexicon/sync",payload);const r=response.results[0];if(["applied","duplicate"].includes(r.status)){await LearningCardStore.writeRecords([{store:"lex-operations",id:op.id,remove:true}]);sent++;}else{op.status=r.status;op.message=r.message;await LearningCardStore.writeRecords([{store:"lex-operations",value:op}]);blocked.add(op.sessionId);}}catch(e){if(!e.status)throw e;op.status="conflict";op.message=e.message;await LearningCardStore.writeRecords([{store:"lex-operations",value:op}]);blocked.add(op.sessionId);}}
  for(const id of new Set(pending.map(o=>o.sessionId)))if(!blocked.has(id)){const remote=(await api("./api/lexicon/sessions/"+id)).session;const cached=await LearningCardStore.getRecord("lex-sessions",id);mergeSession(remote,cached);await LearningCardStore.saveSession(remote);}
  const {items}=await api("./api/vocab");await LearningCardStore.putMany(items);if(!LearningDataSync.pendingCount()){const ids=new Set(items.map(i=>i.id));const old=await LearningCardStore.all();const deletes=old.filter(i=>!ids.has(i.id)).map(i=>({store:"review-cards",id:i.id,remove:true}));if(deletes.length)await LearningCardStore.writeRecords(deletes);}
  await refresh();toast(`同步完成：${sent} 项练习事件${blocked.size?`，${blocked.size} 组有冲突待处理`:""}。`);return blocked.size;
}
async function renderRecords(focusRef){show("records");let stats={},sessions=[],mistakes=[];try{const r=await Promise.all([api("./api/lexicon/stats"),api("./api/lexicon/sessions"),api("./api/lexicon/mistakes")]);stats=r[0];sessions=r[1].sessions;mistakes=r[2].items;await LearningCardStore.writeRecords([{store:"lex-meta",value:{id:"records",stats,sessions,mistakes}}]);}catch(e){if(e.status)throw e;const cache=await LearningCardStore.getRecord("lex-meta","records");if(cache){({stats,sessions,mistakes}=cache);}const local=await LearningCardStore.listRecords("lex-sessions");for(const s of local)if(s.id.startsWith("ls_")&&!sessions.some(i=>i.id===s.id))sessions.unshift(s);}
  const statsNode=clear($("#records-stats"));for(const [value,label]of [[stats.totalAttempts||0,"首次作答"],[stats.unresolved||0,"待巩固方向"],[Object.keys(stats.days||{}).length,"练习天数"]]){const c=node("div",undefined,"lex-progress-stat");c.append(node("strong",value),node("span",label));statsNode.append(c);}for(const g of stats.groups||[]){const c=node("div",undefined,"lex-progress-stat");c.append(node("strong",g.accuracy===null?"—":g.accuracy+"%"),node("span",`${KIND[g.kind]} · ${TYPES[g.type]} · ${g.answered} 次`));statsNode.append(c);}
  const syncList=clear($("#records-sync-list"));const operations=await pendingOperations();if(!operations.length)syncList.append(node("p","没有待同步的练习事件。"));for(const op of operations){const p=node("article",undefined,"lex-plan-card");p.append(node("p",`${op.status==="pending"?"等待同步":"需要处理"} · ${op.message||op.sessionId}`),button("重试同步",async()=>{await syncPractice();await renderRecords();}));if(op.status!=="pending")p.append(button("保留本地记录，采用服务端进度",async()=>{if(!confirm("本地作答会留在归档中；本会话后续待同步操作将归档，页面载入服务器状态。"))return;const group=operations.filter(o=>o.sessionId===op.sessionId);await LearningCardStore.writeRecords(group.map(o=>({store:"lex-operations",value:{...o,status:"archived"}})));const remote=(await api("./api/lexicon/sessions/"+op.sessionId)).session;const local=await LearningCardStore.getRecord("lex-sessions",op.sessionId);await LearningCardStore.writeRecords([{store:"lex-meta",value:{id:"conflict:"+uid(),session:local}},{store:"lex-sessions",value:remote}]);await renderRecords();}));syncList.append(p);}
  const list=clear($("#records-sessions"));if(!sessions.length)list.append(node("p","还没有练习记录。"));for(const s of sessions){const c=node("article",undefined,"lex-plan-card");c.append(node("p",`${s.status==="completed"?"已完成":"进行中"} · ${new Date(s.createdAt||s.updatedAt).toLocaleString()} · ${s.state?.cursor||0}/${s.state?.queue?.length||0}`),button(s.status==="completed"?"查看报告":"继续练习",()=>navigate("#/practice/"+s.id)));list.append(c);}
  const wrong=clear($("#records-mistakes"));for(const m of mistakes){const c=node("article",undefined,"lex-plan-card");c.dataset.sourceRef=m.sourceRef;c.append(node("h3",`${m.headword||"条目"} · ${TYPES[m.type]||m.type}`),node("p",`${m.resolved?"已巩固":"待巩固"} · 首次不可靠回忆 ${m.wrongCount} 次 · 独立答对连续 ${m.cleanStreak} 次`),button("复练",()=>practiceFor({refs:[m.sourceRef],types:[m.type]})),button("条目详情",()=>openRef(m.sourceRef)));wrong.append(c);}if(!mistakes.length)wrong.append(node("p","目前没有错题。"));
  const users=clear($("#records-entries"));for(const e of state.users.filter(e=>!e.deleted)){const c=node("article",undefined,"lex-plan-card");c.dataset.sourceRef=e.sourceRef;c.append(node("h3",e.headword||e.sourceRef),node("p",e.gloss?.zh||e.gloss?.en||""),node("p",e.note||""),button("编辑",()=>editUser(e)),button("学习",()=>practiceFor({refs:[e.sourceRef],types:["recall","reading"]})),button("删除个人收藏",async()=>{if(!confirm("删除这条个人收藏与笔记？教材正文和已有作答历史会保留。"))return;await saveUser({...e,deleted:true});await renderRecords();}));users.append(c);}if(!users.childNodes.length)users.append(node("p","在词条详情中收藏，或新增个人条目。"));
  if(focusRef){
    setTimeout(()=>{
      const all=Array.from(document.querySelectorAll("[data-source-ref]")).filter(el=>el.dataset.sourceRef===focusRef);
      if(all.length){
        all.forEach(el=>el.classList.add("is-focused"));
        all[0].scrollIntoView({behavior:"smooth",block:"center"});
      }
    },50);
  }
}
function editUser(entry=null){state.editor=entry;$("#editor-headword").value=entry?.headword||"";$("#editor-reading").value=entry?.reading||"";$("#editor-meaning").value=entry?.gloss?.zh||"";$("#editor-note").value=entry?.note||"";$("#editor-tags").value=(entry?.tags||[]).join(", ");$("#editor-kind").value=entry?.kind||"word";$("#editor-starred").checked=entry?.starred!==false;$("#editor-status").textContent="";$("#lex-editor").showModal();$("#editor-headword").focus();}
async function saveEditor(event){event.preventDefault();await guard(event.submitter,async()=>{const old=state.editor||{};await saveUser({...old,sourceRef:old.sourceRef||"user:"+uid(),headword:$("#editor-headword").value.trim(),reading:$("#editor-reading").value.trim(),gloss:{...old.gloss,zh:$("#editor-meaning").value.trim()},note:$("#editor-note").value,tags:$("#editor-tags").value.split(/[,，]/).map(s=>s.trim()).filter(Boolean),kind:$("#editor-kind").value,starred:$("#editor-starred").checked});$("#lex-editor").close();toast("个人资料已保存。");route();});}
function downloadJson(name,data){const url=URL.createObjectURL(new Blob([JSON.stringify(data,null,2)],{type:"application/json"}));const a=node("a");a.href=url;a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);}
function parseCsv(text){const rows=[];let row=[],value="",quoted=false;for(let i=0;i<text.length;i++){const c=text[i];if(c==='"'){if(quoted&&text[i+1]==='"'){value+='"';i++;}else quoted=!quoted;}else if(c===','&&!quoted){row.push(value);value="";}else if((c==='\n'||c==='\r')&&!quoted){if(c==='\r'&&text[i+1]==='\n')i++;row.push(value);if(row.some(Boolean))rows.push(row);row=[];value="";}else value+=c;}if(quoted)throw new Error("CSV 引号未闭合。");row.push(value);if(row.some(Boolean))rows.push(row);const headings=(rows.shift()||[]).map(s=>s.trim().toLowerCase());return rows.map(values=>{const r=Object.fromEntries(headings.map((k,i)=>[k,values[i]||""]));return {headword:r.headword||r.term||r["单词"]||r["词语"],reading:r.reading||r["读音"]||"",gloss:{zh:r.meaning||r["释义"]||""},note:r.note||r["笔记"]||"",kind:r.kind||"word",starred:true};});}
async function importFile(file){
  if(!file)return;
  if(file.size>20*1024*1024)throw new Error("文件不能超过 20 MB。");
  const text=await file.text();
  const isCsv=file.name.toLowerCase().endsWith(".csv");
  const data=isCsv?{entries:parseCsv(text)}:JSON.parse(text);
  // Accept a bare array, a v1 file (`items`) and a v2 backup (`entries` + `contexts`).
  const body=Array.isArray(data)
    ?{entries:data}
    :{schemaVersion:data.schemaVersion,entries:data.entries||data.items,
      contexts:data.contexts,learning:data.learning};
  const preview=await post("./api/lexicon/import",{...body,preview:true});
  if(preview.errors.length)throw new Error(preview.errors.map(e=>`第 ${e.row} 行：${e.error}`).join("；"));
  const lines=[`新增 ${preview.added.length} 条 · 更新 ${preview.updated.length} 条`];
  if(preview.contexts)lines.push(`收藏语境 ${preview.contexts} 条`);
  if(preview.duplicates.length)lines.push(`文件内重复 ${preview.duplicates.length} 条（只导入第一条）`);
  if(preview.conflicts.length)lines.push(`${preview.conflicts.length} 条比本地更旧，将覆盖本地内容`);
  if(preview.unresolvedReferences.length)lines.push(`${preview.unresolvedReferences.length} 条引用的内容包本机没有安装，条目仍会保留`);
  if(preview.includesLearning)lines.push("文件含学习记录；本次只恢复个人条目与语境");
  if(!confirm(`导入预览\n${lines.join("\n")}\n\n确认导入？`))return;
  const result=await post("./api/lexicon/import",{...body,entries:preview.ready,preview:false});
  await refresh();
  toast(`已导入 ${result.count} 条个人条目、${result.contexts} 条语境。`);
  navigate("#/records");
}
async function route(){const request=++state.request;const [path,query=""]=location.hash.replace(/^#/,"").split("?");const parts=path.split("/").filter(Boolean).map(decodeURIComponent);const params=new URLSearchParams(query);
if(params.get("return"))state.detailReturn=params.get("return");
try{if(parts[0]==="search")await search(params,request);
else if(parts[0]==="pack"&&parts[1])await openPack(parts[1],parts[2],params.get("entry"),request);
else if(["entry","dictionary","personal"].includes(parts[0]))await detail(parts[0],parts,request);
else if(parts[0]==="learn"&&parts[1])await loadLearn(parts[1],parts[2]||"",request);
else if(parts[0]==="study")await loadStudy(params.get("deck")||"");
else if(parts[0]==="plans"){show("plans");renderPlans();}
else if(parts[0]==="practice"&&parts[1]&&parts[1]!=="new")await loadSession(parts[1]);
else if(parts[0]==="practice"){
  const pRefs=params.get("refs")?params.get("refs").split(",").map(s=>s.trim()).filter(Boolean):null;
  const pUnits=params.get("units")?params.get("units").split(",").map(s=>s.trim()).filter(Boolean):null;
  const pTypes=params.get("types")?params.get("types").split(",").map(s=>s.trim()).filter(Boolean):null;
  const pPack=params.get("pack");
  if(pRefs!==null)state.practiceRefs=pRefs;
  if(pUnits!==null)state.practiceUnits=pUnits;
  if(pRefs!==null||pUnits!==null)saveScope();
  show("practice");
  if(pPack)$("#practice-pack").value=pPack;
  if(pTypes&&pTypes.length){
    document.querySelectorAll("#practice-types input").forEach(n=>{
      n.checked=pTypes.includes(n.value)&&!n.disabled;
    });
  }
  describeScope();
}
else if(parts[0]==="records")await renderRecords(params.get("focus")||params.get("ref"));
else{show("packs");renderPacks();}
}catch(e){toast(e.message||"页面载入失败",true);if(parts[0]==="study"){$("#study-summary").textContent="队列读取失败，原任务已保留，请重试。";$("#study-empty").hidden=true;}}
}
function bind(){
  const nav={"#lex-tab-browse":"","#lex-tab-study":"#/study","#lex-tab-plans":"#/plans","#lex-tab-practice":"#/practice/new","#lex-tab-records":"#/records","#lex-home-button":"","#pack-back":"","#search-back":""};for(const [id,hash]of Object.entries(nav))$(id).addEventListener("click",()=>navigate(hash));
  $("#detail-back").addEventListener("click",()=>{
    const ret=state.detailReturn||"";
    if(ret.startsWith("http://")||ret.startsWith("https://")||ret.startsWith("./")||ret.startsWith("/")||ret.includes(".html")){
      location.assign(ret);
    }else{
      navigate(ret);
    }
  });$("#lex-search-form").addEventListener("submit",e=>{e.preventDefault();queryRoute();});
  for(const id of ["#search-kind","#search-level"])$(id).addEventListener("change",()=>{if(state.activeView==="search")queryRoute();else renderPacks();});
  for(const id of ["#search-scope","#search-starred"])$(id).addEventListener("change",()=>{if(state.activeView==="search")queryRoute();});
  let composing=false;
  $("#lex-search-input").addEventListener("compositionstart",()=>{composing=true;});
  $("#lex-search-input").addEventListener("compositionend",()=>{composing=false;if(state.activeView==="search")scheduleQuery();});
  $("#lex-search-input").addEventListener("input",e=>{if(!composing&&!e.isComposing&&state.activeView==="search")scheduleQuery();});
  $("#plan-form").addEventListener("submit",createPlan);
  $("#plan-editor-form").addEventListener("submit",savePlanEdit);
  $("#plan-edit-cancel").addEventListener("click",()=>$("#plan-editor").close());$("#practice-form").addEventListener("submit",createPractice);$("#lex-editor-form").addEventListener("submit",saveEditor);$("#editor-cancel").addEventListener("click",()=>$("#lex-editor").close());
  $("#study-load").addEventListener("click",()=>guard($("#study-load"),()=>navigate("#/study?deck="+encodeURIComponent($("#study-deck").value))));$("#study-deck").addEventListener("change",()=>navigate("#/study?deck="+encodeURIComponent($("#study-deck").value)));
  $("#learn-back").addEventListener("click",()=>{
    const l=state.learn;
    navigate(l?`#/pack/${encodeURIComponent(l.slug)}${l.unitId?"/"+encodeURIComponent(l.unitId):""}`:"");
  });
  $("#learn-reveal").addEventListener("click",()=>guard($("#learn-reveal"),async()=>{
    state.learn.revealed=true;await saveLearn();renderLearn();
  }));
  $("#learn-cover").addEventListener("change",async()=>{
    state.learn.cover=$("#learn-cover").checked;state.learn.revealed=false;
    await saveLearn();renderLearn();
  });
  $("#learn-directions").addEventListener("change",async()=>{
    const chosen=[...$("#learn-directions").selectedOptions].map(o=>o.value);
    state.learn.directions=chosen.length?chosen:["recall"];await saveLearn();
  });
  $("#review-reveal").addEventListener("click",()=>guard($("#review-reveal"),async()=>{const item=state.study?.items[state.study.index];if(item){item.revealed=true;await LearningCardStore.saveSession(state.study);renderStudy();}}));document.querySelectorAll("#review-grades [data-grade]").forEach(b=>b.addEventListener("click",()=>guard(b,()=>gradeStudy(b.dataset.grade))));
  $("#session-offline").addEventListener("click",()=>guard($("#session-offline"),prepareOffline));$("#session-exit").addEventListener("click",()=>guard($("#session-exit"),async()=>{clearTimeout(draftTimer);if(state.session)await LearningCardStore.saveSession(state.session);navigate("#/records");}));$("#records-sync").addEventListener("click",()=>guard($("#records-sync"),async()=>{await syncPractice();await renderRecords();}));$("#user-add").addEventListener("click",()=>editUser());$("#user-export").addEventListener("click",()=>guard($("#user-export"),async()=>{
    // Exported from the service, not from `state.users`: the page's copy has no
    // contexts, so a round trip through it silently dropped every saved sentence.
    const full=$("#user-export-learning")?.checked;
    const payload=await api("./api/lexicon/export"+(full?"?learning=1":""));
    downloadJson(full?"dictation-learning-backup.json":"dictation-personal-entries.json",payload);
    toast(`已导出 ${payload.entries.length} 条条目、${(payload.contexts||[]).reduce((n,c)=>n+c.contexts.length,0)} 条语境${full?"，含学习记录":""}。`);
  }));$("#user-import").addEventListener("change",e=>guard(null,()=>importFile(e.target.files[0])));
  $("#dictionary-install").addEventListener("click",()=>guard($("#dictionary-install"),async()=>{
    const started=await post("./api/dictionary/install");
    toast(started.job.message||"词典更新任务已开始。");
    watchDictionaryJob();
  }));
  $("#dictionary-cancel").addEventListener("click",()=>guard($("#dictionary-cancel"),async()=>{
    const result=await post("./api/dictionary/install/cancel");
    toast(result.job.message||"已请求取消。");
  }));
  const types=$("#practice-types");for(const [value,label]of Object.entries(TYPES)){const wrap=node("label");const checkbox=node("input");checkbox.type="checkbox";checkbox.value=value;checkbox.checked=["reading","meaning","cloze","connection"].includes(value);wrap.append(checkbox,node("span",label));types.append(wrap);}
  restoreScope();
  LearningCards.migrateLegacyStorage().catch(()=>{});
  let pendingRefresh=null;
  LearningCards.subscribe(change=>{
    // A change this page just made is already on screen; everyone else's is not.
    if(change.origin==="self")return;
    clearTimeout(pendingRefresh);
    pendingRefresh=setTimeout(()=>{guard(null,async()=>{await refresh();if(state.activeView==="study")await loadStudy($("#study-deck").value||"");});},400);
  });
  window.addEventListener("hashchange",route);window.addEventListener("online",()=>guard(null,async()=>{await syncPractice();}));window.addEventListener("offline",()=>{notice("互联网已断开；本地服务运行时仍可学习。");});
  // The debounce can still be in flight when the tab goes away; write the draft then.
  window.addEventListener("pagehide",flushDraft);
  document.addEventListener("visibilitychange",()=>{if(document.visibilityState==="hidden")flushDraft();});
  document.addEventListener("keydown",e=>{if(e.isComposing||e.keyCode===229||e.ctrlKey||e.metaKey||e.altKey||["INPUT","TEXTAREA","SELECT"].includes(document.activeElement?.tagName)||$("#lex-editor").open)return;if(state.activeView==="learn"){
      if(e.code==="Space"){e.preventDefault();if(!$("#learn-reveal").hidden)$("#learn-reveal").click();return;}
      const learn=state.learn;const entry=learn?.entries[learn.index];
      if(!entry)return;
      const ref=`lex:${learn.packId}#${entry.id}`;
      if(e.key==="1"||e.key==="ArrowRight"){e.preventDefault();guard(null,()=>advanceLearn(entry,ref,true));}
      if(e.key==="2"){e.preventDefault();guard(null,()=>advanceLearn(entry,ref,false));}
      if(e.key==="ArrowLeft"&&learn.index>0){e.preventDefault();guard(null,async()=>{learn.index-=1;learn.revealed=false;await saveLearn();renderLearn();});}
    }else if(state.activeView==="study"){if(e.code==="Space"){e.preventDefault();if(!$("#review-reveal").hidden)$("#review-reveal").click();}const grade={"1":"again","2":"hard","3":"good","4":"easy"}[e.key];if(grade&&!$("#review-grades").hidden)guard(null,()=>gradeStudy(grade));}else if(state.activeView==="session"&&/^[1-9]$/.test(e.key)){const radios=$("#session-body").querySelectorAll('input[name="answer"]');if(radios[Number(e.key)-1]){radios[Number(e.key)-1].checked=true;radios[Number(e.key)-1].dispatchEvent(new Event("change",{bubbles:true}));}}});
}
async function boot(){
  bind();state.decks=readLocal("dictation-lexicon-decks:v2",[]);try{state.users=(await LearningCardStore.getRecord("lex-meta","users"))?.items||[];}catch(e){toast(e.message,true);}renderHistory();await token();LearningDataSync.configure({sender:sendSyncOperation,isOnline:()=>state.online});if(state.online)await LearningDataSync.flush();await refresh();await route();
  if("serviceWorker" in navigator)navigator.serviceWorker.register("./sw.js").catch(()=>{});
}
boot().catch(e=>toast(e.message,true));
