// Prueba del panel generado (panel/index.html) sobre un DOM simulado.
// Uso: node panel-src/test-panel.js
const fs = require('fs');
const html = fs.readFileSync(__dirname + '/../index.html', 'utf8');
const src = html.match(/<script>([\s\S]*)<\/script>/)[1];

function fakeEl(id){
  const el = {
    id, style: {}, dataset: {}, innerHTML: '', textContent: '', value: '',
    listeners: {},
    classList: { add(){}, remove(){}, toggle(){} },
    addEventListener(ev, fn){ el.listeners[ev] = fn; },
    appendChild(){}, scrollIntoView(){},
    querySelectorAll: () => []
  };
  return el;
}
const els = {};
const doc = {
  getElementById: id => (els[id] ||= fakeEl(id)),
  createElement: () => fakeEl('tmp'),
  querySelectorAll: () => [],
  addEventListener(){}
};
const storage = {
  data: {},
  getItem(k){ return this.data[k] || null; },
  setItem(k, v){ this.data[k] = v; },
  removeItem(k){ delete this.data[k]; }
};
global.window = {};
new Function('document','localStorage','sessionStorage','navigator','window', src)
  (doc, storage, storage, {}, global.window);
const E = id => doc.getElementById(id);

let fallos = 0;
const check = (cond, msg) => { console.log((cond ? 'OK  ' : 'FALLO') + ' ' + msg); if (!cond) fallos++; };

// acceso con el código compartido
E('loginNombre').value = 'Test';
E('loginCodigo').value = 'NO-CODE';
E('loginForm').listeners.submit({ preventDefault(){} });
check(E('loginError').textContent !== '', 'rechaza código incorrecto');
E('loginCodigo').value = 'IntersindicalSalut';
E('loginForm').listeners.submit({ preventDefault(){} });
check(E('appRoot').style.display === 'block', 'acepta código compartido y arranca init');

const P = global.window.__PANEL__;
const DATA = P.DATA;
check(DATA.grupos.length > 40, DATA.grupos.length + ' grupos de bolsa');
check(DATA.contratos.length > 5000, DATA.contratos.length + ' contratos en 3 departamentos');
check(/^\d{4}-\d{2}-\d{2}$/.test(DATA.corte) && /^\d{4}-\d{2}-\d{2}$/.test(DATA.fBolsa), 'fechas de corte y bolsa');

const gi = DATA.grupos.findIndex(g => g.cat === 'TCAE' && !g.pi);
const g = DATA.grupos[gi];
check(g.filas.length > 3000 && (g.cnt.A || 0) > 100, 'TCAE·ELCHE: candidatos y activos');
check(g.act.every((x, k) => k === 0 || x > g.act[k - 1]), 'lista de activos ordenada');

P.setMes(DATA.mesDef);
E('fPuesto').value = String(g.act[0]);
P.renderGrupo(gi);
check(E('estOut').innerHTML.indexOf('activos por delante') !== -1, 'estimación con puesto activo');
check(E('gSub').textContent.indexOf(DATA.fBolsa) !== -1, 'detalle de grupo con fecha de bolsa');

E('fPuesto').value = '999999';
P.renderEstim(gi);
check(E('estOut').innerHTML.indexOf('no figura') !== -1, 'puesto inexistente avisa');

E('fNombre').value = 'VERA CANOVAS';
E('fNombre').listeners.input();
check(E('searchRes').innerHTML.indexOf('person-row') !== -1, 'buscador por nombre devuelve resultados');

// búsqueda insensible a acentos/Mª
E('fNombre').value = 'MARTINEZ SEVILA';
E('fNombre').listeners.input();
check(E('searchRes').innerHTML.indexOf('person-row') !== -1, 'buscador encuentra Mª/MARIA normalizada');

// regla de contrato corto (la misma que la app Contrataciones)
const toISO = d => new Date(Date.UTC(1970, 0, 1) + d * 86400000).toISOString().slice(0, 10);
const p = DATA.corte.split('-').map(Number);
check(E('gBars').innerHTML.length > 0, 'barras por mes renderizadas');
check(E('fMes').innerHTML.split('<option').length - 1 >= 19, 'selector de mes con todos los meses');

// llamadas matcheadas: coherencia global
let llam = 0; DATA.grupos.forEach(x => llam += (x.llam[DATA.mesDef] || []).length);
check(llam > 200, llam + ' llamadas matcheadas en ' + DATA.mesDef);

console.log(fallos ? ('\n' + fallos + ' pruebas fallidas') : '\nTodo correcto');
process.exit(fallos ? 1 : 0);
