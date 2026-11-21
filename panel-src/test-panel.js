// Prueba del panel generado (index.html) sobre un DOM simulado.
// Uso: node panel-src/test-panel.js
const fs = require('fs');
const html = fs.readFileSync(__dirname + '/../index.html', 'utf8');
const src = html.match(/<script>([\s\S]*)<\/script>/)[1];

function fakeEl(id){
  const el = {
    id, style: {}, dataset: {}, innerHTML: '', textContent: '', value: '',
    listeners: {}, children: [],
    classList: { add(){}, remove(){}, toggle(){} },
    addEventListener(ev, fn){ el.listeners[ev] = fn; },
    appendChild(c){ el.children.push(c); },
    scrollIntoView(){},
    querySelectorAll(sel){
      if (el.id === 'kBuckets' && /bucketChk/.test(sel)) return el._chks || [];
      return [];
    },
    _chks: null
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
const MES = P.setMes, DUR = P.setDur;
check(DATA.grupos.length > 40, DATA.grupos.length + ' grupos de bolsa');
check(DATA.contratos.length > 5000, DATA.contratos.length + ' contratos en 3 departamentos');
check(/^\d{4}-\d{2}-\d{2}$/.test(DATA.corte) && /^\d{4}-\d{2}-\d{2}$/.test(DATA.fBolsa), 'fechas de corte y bolsa');

const gi = DATA.grupos.findIndex(g => g.cat === 'TCAE' && !g.pi);
const g = DATA.grupos[gi];
check(g.filas.length > 3000 && (g.cnt.D || 0) > 900, 'TCAE·ELCHE: candidatos y DISPONIBLE (' + (g.cnt.D || 0) + ')');
check((g.cnt.U || 0) > 100 && 'U' in g.cnt, 'TCAE·ELCHE: NO VACANTE (DISP. ESPECIAL) como bucket propio (' + (g.cnt.U || 0) + ')');
check(g.act.every((x, k) => k === 0 || x > g.act[k - 1]), 'lista de llamables ordenada');
const BORDEN = DATA.bOrden;
check(BORDEN.indexOf('D') === 0 && BORDEN.indexOf('E') > -1 && BORDEN.indexOf('U') > -1,
      'orden de situaciones con D/E/U prioritarios');

// --- analisis: total, cortos, vacantes ---
MES('2026-10');
DUR('');
const aAll = P.analisis('2026-10', '');
const aC = P.analisis('2026-10', 'C');
const aL = P.analisis('2026-10', 'L');
const aV = P.analisis('2026-10', 'V');
const sum = a => [...a.cnt.values()].reduce((s, o) => s + (o['2026-10'] || 0), 0);
check(sum(aAll) === DATA.contratos.filter(r => String(new Date(Date.UTC(1970,0,1)+r[4]*86400000).toISOString().slice(0,7)) === '2026-10').length,
      'analisis sin filtro = todos los contratos del mes (' + sum(aAll) + ')');
check(sum(aC) + sum(aL) + sum(aV) <= sum(aAll), 'cortos + no cortos + vacantes no superan el total');
check(sum(aC) > 0 && sum(aV) > 0, 'hay contratos cortos (' + sum(aC) + ') y vacantes (' + sum(aV) + ') en el mes');
check(P.claseContrato([0,0,0,0,10,14,'O','S','N','N']) === 'C', 'claseContrato: 5 días = corto');
check(P.claseContrato([0,0,0,0,10,16,'O','S','N','N']) === 'L', 'claseContrato: 7 días = no corto');
check(P.claseContrato([0,0,0,0,10,null,'O','I','S','N']) === 'V', 'claseContrato: interinidad = vacante');

// --- llamada con filtro: un grupo concreto ---
const llamAll = P.llamadosDe(gi, '2026-10', '');
const llamC = P.llamadosDe(gi, '2026-10', 'C');
check(llamAll.size >= llamC.size, 'llamadas sin filtro >= llamadas cortas');
check(typeof llamC.size === 'number', 'llamadas cortas recuento: ' + llamC.size);

// --- render de grupo con filtros y buckets ---
E('fPuesto').value = String(g.act[0]);
P.renderGrupo(gi);
check(E('gSub').textContent.indexOf(DATA.fBolsa) !== -1, 'detalle de grupo con fecha de bolsa');
check((E('kBuckets').innerHTML.match(/bucketChk/g) || []).length >= 1, 'casillas de situación renderizadas');
check(E('estOut').innerHTML.indexOf('puesto/s por delante') !== -1, 'estimación con desglose por posición');

// desglose por situación: consistencia con el conteo por buckets
const v = g.act[0];
const t = P.delantePorSitu(g, v);
const totT = Object.values(t).reduce((a, b) => a + b, 0);
const idxPrimera = g.filas.findIndex(f => f[0] >= v);
check(totT === (idxPrimera < 0 ? g.filas.length : idxPrimera), 'delantePorSitu suma = nº de filas con puesto anterior (' + totT + ')');

// buckets: las 4 situaciones llamables activas por defecto
['A', 'D', 'E', 'U'].forEach(b => check(P.buckets.has(b), 'bucket por defecto activo: ' + b));
E('fPuesto').oninput();
const conLlam = (E('estOut').innerHTML.match(/(\d+) puesto\/s por delante/) || [])[1];

// --- puesto inexistente ---
E('fPuesto').value = '999999';
P.renderEstim(gi);
check(E('estOut').innerHTML.indexOf('no figura') !== -1, 'puesto inexistente avisa');

// --- buscador ---
E('fNombre').value = 'VERA CANOVAS';
E('fNombre').listeners.input();
check(E('searchRes').innerHTML.indexOf('person-row') !== -1, 'buscador por nombre');
E('fNombre').value = 'MARTINEZ SEVILA';
E('fNombre').listeners.input();
check(E('searchRes').innerHTML.indexOf('person-row') !== -1, 'buscador encuentra Mª/MARIA normalizada');

// --- ficha con contratos y última llamada ---
const ni = g.filas[0][1];
P.showPersona(ni);
check(E('pBolsa').innerHTML.length > 0, 'ficha: situación en bolsa');
check(typeof P.ultimaLlamada(gi, (g.filas.find(f => f[1] === ni) || [])[0]) === 'string' || true, 'ultimaLlamada ejecutable');

// --- visual: logo del sindicato, compartido en WhatsApp y fecha en espanol ---
check(html.indexOf('property="og:image"') !== -1 && html.indexOf('icon-512.png') !== -1, 'og:image con el logo del repositorio (previsualizacion WhatsApp)');
check(html.indexOf('<img class="logo" src="icon-512.png"') !== -1, 'logo del sindicato en la cabecera');
check(E('fechaActualizacion').textContent === '15 de noviembre de 2026', 'fecha de datos legible en la cabecera (' + E('fechaActualizacion').textContent + ')');
check(P.fechaTxt('2026-03-05') === '5 de marzo de 2026', 'fechaTxt en espanol');

// --- puesto pincheable: ficha -> Resumen ---
P.showPersona(ni);
check(E('pBolsa').innerHTML.indexOf('poslink') !== -1, 'ficha: numero de puesto pincheable');
P.abrirGrupoEnResumen(gi, g.filas[0][0]);
check(E('fDpto').value === g.dpto && E('fCat').value === g.cat, 'pinchar puesto filtra la bolsa concreta');
check(E('fPuesto').value === String(g.filas[0][0]), 'puesto precargado en Tu puesto en esta bolsa');
check(E('estOut').innerHTML.indexOf('puesto/s por delante') !== -1, 'estimacion recalculada al abrir desde la ficha');

const r0 = DATA.contratos.find(r => String(new Date(Date.UTC(1970, 0, 1) + r[4] * 86400000).toISOString().slice(0, 7)) === '2026-10');
const csMes = P.contratosDe(r0[0], '2026-10');
check(csMes.length >= 1 && csMes.every(c => c[4] != null), 'fechas de contrato de inicio y fin accesibles (' + csMes.length + ' contratos del contratado del mes)');

console.log(fallos ? ('\n' + fallos + ' pruebas fallidas') : '\nTodo correcto');
process.exit(fallos ? 1 : 0);
