export const achievements = [
 {id:'quickdraw',name:'Quickdraw',icon:'↯',color:'peach',unit:'закрытых задач вовремя',tiers:[1],description:'Закрой issue или PR в течение 5 минут после открытия.',hint:'Сначала подготовь исправление, затем открой небольшую задачу.'},
 {id:'yolo',name:'YOLO',icon:'✌',color:'lilac',unit:'PR без review',tiers:[1],description:'Влей собственный PR без проверки кода другим участником.',hint:'Выбери небольшое проверенное изменение, разрешённое правилами проекта.'},
 {id:'pull-shark',name:'Pull Shark',icon:'≈',color:'blue',unit:'влитых PR',tiers:[2,16,128,1024],description:'Предлагай изменения, которые принимают в репозиторий.',hint:'Считаются влитые PR. Закрытие без слияния не равно принятию.'},
 {id:'pair-extraordinaire',name:'Pair Extraordinaire',icon:'♧',color:'pink',unit:'совместных PR',tiers:[1,10,24,48],description:'Сделай совместное изменение, которое попадёт во влитый PR.',hint:'Укажи реального соавтора в Co-authored-by и сохрани авторство при слиянии.'},
 {id:'galaxy-brain',name:'Galaxy Brain',icon:'✧',color:'purple',unit:'принятых ответов',tiers:[2,8,16,32],description:'Помогай людям в Discussions: ответы должны отметить как принятые.',hint:'Выбирай Discussions проектов. Главный форум GitHub Community не подходит.'},
 {id:'starstruck',name:'Starstruck',icon:'☆',color:'yellow',unit:'звёзд одного проекта',tiers:[16,128,512,4096],description:'Создай полезный репозиторий, который захотят сохранить другие.',hint:'Учитывай звёзды одного своего репозитория, а не сумму по всем проектам.'}
];
export const emptyState = () => ({version:1,entries:Object.fromEntries(achievements.map(a=>[a.id,{count:0,confirmed:false,evidence:[]}]))});
export function safeUrl(value) { const u = new URL(value); if(u.protocol!=='https:' || u.hostname!=='github.com' || u.username || u.password) throw new Error('Нужна ссылка https://github.com/…'); return u.href; }
export function validateState(data) {
 if(!data || Array.isArray(data) || data.version!==1 || !data.entries || Array.isArray(data.entries) || typeof data.entries!=='object') throw new Error('Неподдерживаемый формат журнала. Нужен экспорт версии 1.');
 const result=emptyState();
 for(const a of achievements){const e=data.entries[a.id]; if(!e || !Number.isSafeInteger(e.count) || e.count<0 || e.count>100000000 || typeof e.confirmed!=='boolean' || !Array.isArray(e.evidence) || e.evidence.length>100) throw new Error('Некорректная запись: '+a.name);
 const evidence=e.evidence.map(link=>{if(typeof link!=='string'||link.length>2048)throw new Error('Некорректная ссылка.');return safeUrl(link);});
 if(new Set(evidence).size!==evidence.length)throw new Error('Повторяющиеся ссылки: '+a.name);
 result.entries[a.id]={count:e.count,confirmed:e.confirmed,evidence}; }
 return result;
}
export function progress(a,count) {const level=a.tiers.filter(t=>count>=t).length;const target=a.tiers.find(t=>t>count)??a.tiers.at(-1);return {level,target,remaining:Math.max(0,target-count),percent:Math.min(100,count/target*100)};}
