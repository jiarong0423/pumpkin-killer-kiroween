const fs=require('fs'),R=require('path').join(__dirname,'..','..','..')+'/';
const html=fs.readFileSync(R+'index.html','utf8');
const en=JSON.parse(fs.readFileSync(R+'assets/i18n/en.json','utf8')),zh=JSON.parse(fs.readFileSync(R+'assets/i18n/zh-TW.json','utf8'));
const flat=(o,p='',out={})=>{for(const k in o){const v=o[k];if(v&&typeof v==='object')flat(v,p+k+'.',out);else out[p+k]=v;}return out;};
const E=flat(en),Z=flat(zh);
const used=new Set();
for(const m of html.matchAll(/["'`]((?:lobby|name)\.[A-Za-z0-9_.]+)["'`]/g))used.add(m[1]);
for(const m of html.matchAll(/data-i18n(?:-attr)?="([^"]+)"/g))m[1].split(';').forEach(p=>{const k=p.includes(':')?p.split(':')[1]:p;if(/^(lobby|name)\./.test(k))used.add(k)});
const miss=[...used].filter(k=>!(k in E)||!(k in Z)).map(k=>k+(k in E?'':' [en]')+(k in Z?'':' [zh]'));
console.log('used',used.size,'missing',miss);
const ek=Object.keys(E).filter(k=>/^(lobby|name)\./.test(k)),zk=Object.keys(Z).filter(k=>/^(lobby|name)\./.test(k));
console.log('en only',ek.filter(k=>!(k in Z)),'zh only',zk.filter(k=>!(k in E)));
// placeholder parity
const ph=s=>[...String(s).matchAll(/\{(\w+)\}/g)].map(m=>m[1]).sort().join(',');
console.log('placeholder mismatch',ek.filter(k=>k in Z&&ph(E[k])!==ph(Z[k])).map(k=>k+': '+ph(E[k])+' vs '+ph(Z[k])));
console.log('unused',ek.filter(k=>!used.has(k)));
