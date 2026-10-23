const fs=require('fs'),vm=require('vm'),assert=require('assert');
const source=fs.readFileSync('device_login/index.html','utf8').split('<script>')[1].split('</script>')[0];
const data=new Map();
const storage={getItem:k=>data.get(k)||null,setItem:(k,v)=>data.set(k,v),removeItem:k=>data.delete(k)};
function browser(store=storage){
 const messages=[],parent={postMessage:m=>messages.push(m)};let handler;
 const window={parent,addEventListener:(name,fn)=>handler=fn};
 vm.runInNewContext(source,{window,localStorage:store});
 return {render(command,source=parent){handler({source,data:{type:'streamlit:render',args:{command}}})},values:()=>messages.filter(m=>m.type==='streamlit:setComponentValue').map(m=>m.value)};
}
let tab=browser();tab.render({action:'read',revision:'1'});assert.equal(tab.values().at(-1).token,'');
tab.render({action:'save',token:'signed-token',revision:'2'});assert.equal(tab.values().at(-1).token,'signed-token');
tab.render({action:'save',token:'signed-token',revision:'2'});assert.equal(tab.values().length,2);
tab=browser();tab.render({action:'read',revision:'3'});assert.equal(tab.values().at(-1).token,'signed-token');
tab.render({action:'clear',revision:'4'},{});assert.equal(tab.values().length,1); // foreign messages ignored
tab.render({action:'clear',revision:'5'});assert.equal(tab.values().at(-1).token,'');assert.equal(data.size,0);
const blocked=browser({getItem(){throw Error('blocked')}});blocked.render({action:'read',revision:'6'});assert(blocked.values()[0].error);
console.log('Browser storage: persistence, deletion, acknowledgement, message isolation, blocked-storage fallback PASS');
