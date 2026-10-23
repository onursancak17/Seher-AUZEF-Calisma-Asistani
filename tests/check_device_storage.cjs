const fs=require('fs'),vm=require('vm'),assert=require('assert');
const source=fs.readFileSync('device_login/index.html','utf8').split('<script>')[1].split('</script>')[0];
const storage=()=>{const data=new Map();return {getItem:k=>data.get(k)||null,setItem:(k,v)=>data.set(k,v),removeItem:k=>data.delete(k)}};
const blocked={getItem(){throw Error('blocked')},setItem(){throw Error('blocked')},removeItem(){throw Error('blocked')}};
function cookies(deny=false){
 const jar=new Map();return Object.defineProperty({},'cookie',{
 get(){return [...jar].map(([k,v])=>k+'='+v).join('; ')},
 set(s){if(deny)return;const [kv,...opts]=s.split('; '),[k,v]=kv.split('=');if(opts.includes('Max-Age=0'))jar.delete(k);else jar.set(k,v)}
 });
}
function browser(hostStore,doc,frameStore=blocked){
 const messages=[],parent={document:doc,localStorage:hostStore,location:{protocol:'https:'},postMessage:m=>messages.push(m)};let handler;
 const window={parent,localStorage:frameStore,addEventListener:(name,fn)=>handler=fn};
 vm.runInNewContext(source,{window});
 return {render(command,sender=parent){handler({source:sender,data:{type:'streamlit:render',args:{command}}})},last:()=>messages.filter(m=>m.type==='streamlit:setComponentValue').at(-1)?.value,values:()=>messages.filter(m=>m.type==='streamlit:setComponentValue')};
}
const appStore=storage(),doc=cookies();let tab=browser(appStore,doc);
tab.render({action:'read',revision:'1'});assert.equal(tab.last().token,'');
tab.render({action:'save',token:'signed-token',revision:'2'});assert(!tab.last().error);assert(doc.cookie.includes('signed-token'));
tab.render({action:'save',token:'signed-token',revision:'2'});assert.equal(tab.values().length,2);
tab=browser(appStore,doc);tab.render({action:'read',revision:'3'});assert.equal(tab.last().token,'signed-token');
tab.render({action:'clear',revision:'4'},{});assert.equal(tab.values().length,1);
tab.render({action:'clear',revision:'5'});assert.equal(tab.last().token,'');assert.equal(doc.cookie,'');assert.equal(appStore.getItem('seher_auzef_remembered_login_v1'),null);
const cookieOnly=cookies();let fallback=browser(blocked,cookieOnly);
fallback.render({action:'save',token:'cookie-token',revision:'6'});assert(!fallback.last().error);
fallback=browser(blocked,cookieOnly);fallback.render({action:'read',revision:'7'});assert.equal(fallback.last().token,'cookie-token');
const denied=browser(blocked,cookies(true));denied.render({action:'save',token:'unsaved',revision:'8'});assert(denied.last().error);
const legacy=storage();legacy.setItem('seher_auzef_remembered_login_v1','legacy-token');
const migrated=browser(storage(),cookies(),legacy);migrated.render({action:'read',revision:'9'});assert.equal(migrated.last().token,'legacy-token');
migrated.render({action:'clear',revision:'10'});assert.equal(legacy.getItem('seher_auzef_remembered_login_v1'),null);
console.log('Storage: blocked iframe, first-party persistence, refresh, cookie-only fallback, logout, migration, failed writes PASS');
