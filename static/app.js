/**
 * Neon Odyssey — Character Sheet Generator
 * Frontend-only version for GitHub Pages
 *
 * Estructura:
 * - game_data.json  → datos del juego (cargados vía fetch)
 * - index.html      → formulario (generado dinámicamente)
 * - app.js          → lógica de UI, auto-calc, export/import, PDF
 * - styles.css      → estilos (4 temas)
 * - template.pdf    → plantilla PDF (para rellenar con pdf-lib)
 */

// ============================================================
// CONFIGURACIÓN
// ============================================================

const CONFIG = {
  // Ruta a los datos del juego (puede ajustarse para subdominios)
  gameDataPath: 'game_data.json',
  // Plantilla PDF (incluida en el repositorio)
  templatePdf: 'template.pdf',
  // Número de slots para las secciones dinámicas
  maxAttacks: 10,
  maxFactions: 12,
  maxMagicItems: 6,
  maxSpells: 32,
  // Nombre por defecto para exportación
  defaultCharName: 'Character',
  // Prefijo para archivos exportados
  exportPrefix: 'Neon_Odyssey',
  // Id del contenedor principal
  containerId: 'sheetContainer',
};

// ============================================================
// ESTADO DE LA APLICACIÓN
// ============================================================

const appState = {
  gameData: null,
  loaded: false,
  theme: localStorage.getItem('neonOdysseyTheme') || 'theme-neon',
  autoCalc: localStorage.getItem('neonOdysseyAutoCalc') !== '0',
  draftKey: 'neonOdysseyDraft',
};

// ============================================================
// UTILIDADES
// ============================================================

/**
 * Genera un identificador único
 * @returns {string} Identificador
 */
function generateId() {
  return 'id_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
}

/**
 * Sanitiza un string para uso seguro en HTML
 * @param {string} str - Cadena a sanitizar
 * @returns {string} Cadena segura
 */
function sanitizeHtml(str) {
  const div = document.createElement('div');
  div.textContent = str;
  return div.innerHTML;
}

/**
 * Escapa un valor para atributos HTML
 * @param {string} value - Valor a escapar
 * @returns {string} Valor escapado
 */
function escapeAttr(value) {
  return String(value)
    .replace(/&/g, '&amp;')
    .replace(/"/g, '&quot;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;');
}

/**
 * Genera un ID único para un campo del formulario
 * @param {string} base - Prefijo base
 * @returns {string} ID único
 */
function fieldId(base) {
  return `${base}_${generateId()}`;
}

// ============================================================
// CARGA DE DATOS
// ============================================================

/**
 * Carga los datos del juego desde game_data.json
 */
async function loadGameData() {
  try {
    appState.gameData = await fetch(CONFIG.gameDataPath)
      .then(response => {
        if (!response.ok) {
          throw new Error(`Error HTTP: ${response.status}`);
        }
        return response.json();
      })
      .catch(error => {
        console.error('Error cargando game_data.json:', error);
        showError('No se pudieron cargar los datos del juego. Verifica que game_data.json esté en la misma carpeta.');
        return null;
      });

    if (appState.gameData) {
      appState.loaded = true;
      initializeForm();
      loadDraft();
      setupEventListeners();
      calculateInitialStats();
      console.log('Game data loaded:', appState.gameData);
    }
  } catch (error) {
    console.error('Error cargando datos:', error);
    showError('Error inesperado al cargar los datos del juego.');
  }
}

/**
 * Inicializa el formulario una vez que los datos están cargados
 */
function initializeForm() {
  const data = appState.gameData;

  // Llena las opciones dinámicas (Class, Species, Homeworld, Armor Type)
  populateSelects(data);
  populateFeats(data);
  populateWeaponProficiencies(data);
  populateToolProficiencies(data);
  populateLanguageGroups(data);
  populateLifestyle(data);

  // Genera los slots dinámicos (ataques, facciones, objetos mágicos, hechizos)
  generateAttackSlots();
  generateFactionSlots(data);
  generateMagicItemSlots(data);
  generateSpellSlots(data);

  // Configura el submenú de subcases
  setupSubclassDropdown(data);

  // Filtro de feats por homeworld
  setupFeatsFilter();

  // Establece el tema inicial
  setTheme(appState.theme);

  // Aplica el cálculo inicial
  if (appState.autoCalc) {
    AutoCalc.recalc();
  }
}

/**
 * Carga el borrador guardado
 */
function loadDraft() {
  const saved = localStorage.getItem(appState.draftKey);
  if (!saved) return;

  try {
    const data = JSON.parse(saved);
    if (typeof data !== 'object' || data === null) return;

    const form = document.getElementById('sheetForm');
    if (!form) return;

    // Resetea todos los checkboxes y multi-selects
    form.querySelectorAll('input[type="checkbox"]').forEach(cb => { cb.checked = false; });
    form.querySelectorAll('select[multiple]').forEach(sel => {
      Array.from(sel.options).forEach(o => { o.selected = false; });
    });

    // Restaura los valores
    for (const [key, value] of Object.entries(data)) {
      const elements = form.querySelectorAll(`[name="${escapeAttr(key)}"]`);
      if (!elements.length) continue;
      const values = Array.isArray(value) ? value : [value];
      elements.forEach(el => {
        if (el.type === 'checkbox') {
          el.checked = values.includes(el.value);
        } else if (el.tagName === 'SELECT' && el.multiple) {
          Array.from(el.options).forEach(opt => {
            opt.selected = values.includes(opt.value);
          });
        } else {
          el.value = values[0];
        }
      });
    }

    // Actualiza paneles dinámicos
    if (typeof updateSubclasses === 'function') updateSubclasses();
    if (typeof filterFeats === 'function') filterFeats();

  } catch (e) {
    console.error('Error cargando borrador:', e);
  }
}

/**
 * Guarda el borrador en localStorage
 */
function saveDraft() {
  const form = document.getElementById('sheetForm');
  if (!form) return;

  const data = {};
  // Checkboxes agrupados por nombre
  form.querySelectorAll('input[type="checkbox"]').forEach(cb => {
    if (!cb.checked || !cb.name) return;
    if (!data[cb.name]) data[cb.name] = [];
    data[cb.name].push(cb.value);
  });
  // Campos de valor único
  form.querySelectorAll('input:not([type="checkbox"]), select:not([multiple]), textarea').forEach(el => {
    if (el.name) data[el.name] = el.value;
  });
  // Multi-selects
  form.querySelectorAll('select[multiple]').forEach(el => {
    if (el.name) data[el.name] = Array.from(el.selectedOptions).map(o => o.value).filter(Boolean);
  });

  localStorage.setItem(appState.draftKey, JSON.stringify(data));
}

/**
 * Configura los listeners del formulario
 */
function setupEventListeners() {
  const form = document.getElementById('sheetForm');
  if (!form) return;

  // Auto-calc toggle
  const autoCalcToggle = document.getElementById('autocalcToggle');
  if (autoCalcToggle) {
    autoCalcToggle.checked = appState.autoCalc;
    autoCalcToggle.addEventListener('change', () => {
      appState.autoCalc = autoCalcToggle.checked;
      localStorage.setItem('neonOdysseyAutoCalc', appState.autoCalc ? '1' : '0');
      AutoCalc.recalc();
    });
  }

  // Recalcula cuando hay cambios relevantes
  const recalculateCallback = () => AutoCalc.recalc();
  form.addEventListener('input', debounce(recalculateCallback, 150));

  // Cambio de clase
  const classSelect = document.getElementById('classSelect');
  if (classSelect) {
    classSelect.addEventListener('change', () => {
      applyClassProficiencies();
      AutoCalc.recalc();
      filterFeats();
    });
  }

  // Cambio de tipo de armadura
  const armorSel = document.getElementById('armorTypeSelect');
  if (armorSel) armorSel.addEventListener('change', AutoCalc.recalc);

  // Cambio de escudo
  const shieldCb = document.getElementById('shieldCheck');
  if (shieldCb) shieldCb.addEventListener('change', AutoCalc.recalc);

  // Cambio de homeworld
  const homeworldSelect = document.getElementById('homeworldSelect');
  if (homeworldSelect) {
    homeworldSelect.addEventListener('change', filterFeats);
    filterFeats();
  }

  // Cambio de subcase
  const subclassSelect = document.getElementById('subclassSelect');
  if (subclassSelect) {
    subclassSelect.addEventListener('change', AutoCalc.recalc);
  }

  // Validación en tiempo real
  form.addEventListener('input', validateFields);
  form.addEventListener('blur', validateFields, true);

  // Auto-guardar borrador
  form.addEventListener('input', debounce(saveDraft, 300));

  // Redirección de navegación suave
  document.querySelectorAll('.sticky-nav a').forEach(link => {
    link.addEventListener('click', function(e) {
      e.preventDefault();
      const targetId = this.getAttribute('href');
      const target = document.querySelector(targetId);
      if (target) {
        target.scrollIntoView({ behavior: 'smooth', block: 'start' });
        if (!target.hasAttribute('open')) {
          target.setAttribute('open', '');
        }
      }
    });
  });
}

// ============================================================
// TEMA Y ESTILOS
// ============================================================

/**
 * Cambia el tema de la aplicación
 * @param {string} themeName - Nombre del tema
 */
function setTheme(themeName) {
  document.body.className = themeName;
  localStorage.setItem('neonOdysseyTheme', themeName);
}

// ============================================================
// POBLADO DE SELECTS Y CHECKBOXES
// ============================================================

/**
 * Llena los selects de clase, especie, planeta e tipo de armadura
 * @param {object} data - Datos del juego
 */
function populateSelects(data) {
  const classSelect = document.getElementById('classSelect');
  const subclassSelect = document.getElementById('subclassSelect');
  const speciesSelect = document.getElementById('speciesSelect');
  const homeworldSelect = document.getElementById('homeworldSelect');
  const armorTypeSelect = document.getElementById('armorTypeSelect');

  if (classSelect) {
    classSelect.innerHTML = '<option value="">— Seleccionar —</option>';
    (data.classes || []).forEach(c => {
      const opt = document.createElement('option');
      opt.value = c.name;
      opt.textContent = c.name;
      classSelect.appendChild(opt);
    });
  }

  if (subclassSelect) {
    subclassSelect.innerHTML = '<option value="">— Seleccionar clase primero —</option>';
  }

  if (speciesSelect) {
    speciesSelect.innerHTML = '<option value="">— Seleccionar —</option>';
    (data.species || []).forEach(s => {
      const opt = document.createElement('option');
      opt.value = s.name;
      opt.textContent = s.name;
      speciesSelect.appendChild(opt);
    });
  }

  if (homeworldSelect) {
    homeworldSelect.innerHTML = '<option value="">— Seleccionar —</option>';
    (data.worlds || []).forEach(w => {
      const opt = document.createElement('option');
      opt.value = w.name;
      const tagText = (w.tags || []).join(', ');
      opt.textContent = `${w.name} (${tagText})`;
      homeworldSelect.appendChild(opt);
    });
  }

  if (armorTypeSelect) {
    armorTypeSelect.innerHTML = '<option value="">— Seleccionar —</option>';
    (data.armorTypes || []).forEach(a => {
      const opt = document.createElement('option');
      opt.value = a.name;
      opt.textContent = a.name;
      armorTypeSelect.appendChild(opt);
    });
  }
}

/**
 * Llena el selector de feats
 * @param {object} data - Datos del juego
 */
function populateFeats(data) {
  const featsContainer = document.querySelector('.field-block:has(.field-label:contains("Feats and Professions"))');
  if (!featsContainer) return;

  const checkboxTable = featsContainer.querySelector('.checkbox-table');
  if (!checkboxTable) return;

  checkboxTable.innerHTML = '';
  (data.homeworldFeats || []).forEach(feat => {
    const label = document.createElement('label');
    label.className = 'checkbox-label';
    label.title = feat.prerequisite || '';
    const cb = document.createElement('input');
    cb.type = 'checkbox';
    cb.name = 'Feats and Professions';
    cb.value = feat.name;
    const span = document.createElement('span');
    span.className = 'cb-text';
    span.textContent = feat.name;
    label.appendChild(cb);
    label.appendChild(span);
    checkboxTable.appendChild(label);
  });
}

/**
 * Llena las opciones de competencia de armas
 * @param {object} data - Datos del juego
 */
function populateWeaponProficiencies(data) {
  const weaponGroups = [
    { title: 'Simple Melee', key: 'simple_melee' },
    { title: 'Simple Ranged', key: 'simple_ranged' },
    { title: 'Martial Melee', key: 'martial_melee' },
    { title: 'Martial Ranged', key: 'martial_ranged' },
  ];

  const container = document.querySelector('.field-block:has(.field-label:contains("Weapon Proficiencies"))');
  if (!container) return;

  const checkboxTable = container.querySelector('.checkbox-table');
  if (!checkboxTable) return;

  weaponGroups.forEach(group => {
    const h5 = document.createElement('h5');
    h5.textContent = group.title;
    checkboxTable.appendChild(h5);

    const div = document.createElement('div');
    div.className = 'weapon-group';

    const weapons = (data.weapons && data.weapons[group.key]) || [];
    weapons.forEach(wpn => {
      const label = document.createElement('label');
      label.className = 'checkbox-label';
      const cb = document.createElement('input');
      cb.type = 'checkbox';
      cb.name = 'Weapon Proficiencies';
      cb.value = wpn;
      const span = document.createElement('span');
      span.className = 'cb-text';
      span.textContent = wpn;
      label.appendChild(cb);
      label.appendChild(span);
      div.appendChild(label);
    });

    checkboxTable.appendChild(div);
  });
}

/**
 * Llena las opciones de competencia de herramientas
 * @param {object} data - Datos del juego
 */
function populateToolProficiencies(data) {
  const container = document.querySelector('.field-block:has(.field-label:contains("Tool Proficiencies"))');
  if (!container) return;

  const checkboxTable = container.querySelector('.checkbox-table');
  if (!checkboxTable) return;

  const tools = (data.tools || []);
  checkboxTable.innerHTML = '';
  tools.forEach(tool => {
    const label = document.createElement('label');
    label.className = 'checkbox-label';
    const cb = document.createElement('input');
    cb.type = 'checkbox';
    cb.name = 'Tool Proficiencies';
    cb.value = tool;
    const span = document.createElement('span');
    span.className = 'cb-text';
    span.textContent = tool;
    label.appendChild(cb);
    label.appendChild(span);
    checkboxTable.appendChild(label);
  });
}

/**
 * Llena las grupos de idiomas
 * @param {object} data - Datos del juego
 */
function populateLanguageGroups(data) {
  const container = document.querySelector('.field-block:has(.field-label:contains("Languages"))');
  if (!container) return;

  const checkboxTable = container.querySelector('.checkbox-table');
  if (!checkboxTable) return;

  const languageGroups = data.languageGroups || [];
  languageGroups.forEach(group => {
    const h5 = document.createElement('h5');
    h5.textContent = group.name || 'Languages';
    checkboxTable.appendChild(h5);

    const div = document.createElement('div');
    div.className = 'weapon-group';

    (group.languages || []).forEach(lang => {
      const label = document.createElement('label');
      label.className = 'checkbox-label';
      const cb = document.createElement('input');
      cb.type = 'checkbox';
      cb.name = 'Languages';
      cb.value = lang;
      const span = document.createElement('span');
      span.className = 'cb-text';
      span.textContent = lang;
      label.appendChild(cb);
      label.appendChild(span);
      div.appendChild(label);
    });

    checkboxTable.appendChild(div);
  });
}

/**
 * Llena las opciones de estilo de vida
 * @param {object} data - Datos del juego
 */
function populateLifestyle(data) {
  const select = document.querySelector('select[name="Lifestyle"]');
  if (!select) return;

  select.innerHTML = '<option value="">— Seleccionar —</option>';
  (data.lifestyles || []).forEach(ls => {
    const opt = document.createElement('option');
    opt.value = ls;
    opt.textContent = ls;
    select.appendChild(opt);
  });
}

// ============================================================
// GENERACIÓN DE SLOTS DINÁMICOS
// ============================================================

/**
 * Genera los slots de ataques
 */
function generateAttackSlots() {
  const container = document.getElementById('attacks-container');
  if (!container) return;

  container.innerHTML = '';
  for (let i = 0; i < CONFIG.maxAttacks; i++) {
    const suffix = i === 0 ? '' : ` ${i}`;
    const suffix1 = i === 0 ? ' 1' : ` ${i+1}`;
    const row = document.createElement('div');
    row.className = 'attack-row';
    row.innerHTML = `
      <div class="grid-4">
        <label>Name<input type="text" name="Attack Name${suffix}" placeholder="Nombre"></label>
        <label>Bonus<input type="text" name="Attack Bonus${suffix}" placeholder="+0"></label>
        <label>Damage<input type="text" name="Attack Damage${suffix}" placeholder="1d8"></label>
        <label>Notes<input type="text" name="Attack Notes${suffix}" placeholder="Notas"></label>
      </div>
    `;
    container.appendChild(row);
  }
}

/**
 * Genera los slots de facciones
 * @param {object} data - Datos del juego
 */
function generateFactionSlots(data) {
  const container = document.getElementById('factions-container');
  if (!container) return;

  container.innerHTML = '';
  const datalist = document.createElement('datalist');
  datalist.id = 'factionList';
  (data.factions || []).forEach(f => {
    const opt = document.createElement('option');
    opt.value = f;
    datalist.appendChild(opt);
  });
  container.appendChild(datalist);

  for (let i = 0; i < CONFIG.maxFactions; i++) {
    const suffix = i === 0 ? '' : ` ${i}`;
    const row = document.createElement('div');
    row.className = 'faction-row';
    row.innerHTML = `
      <div class="grid-2">
        <label>Faction Name<input type="text" name="Faction${suffix}" list="factionList" placeholder="Facción"></label>
        <label>Score<input type="number" name="Faction Score${suffix}" placeholder="0"></label>
      </div>
    `;
    container.appendChild(row);
  }
}

/**
 * Genera los slots de objetos mágicos
 * @param {object} data - Datos del juego
 */
function generateMagicItemSlots(data) {
  const container = document.getElementById('magic-items-container');
  if (!container) return;

  container.innerHTML = '';
  for (let i = 0; i < CONFIG.maxMagicItems; i++) {
    const suffix = i === 0 ? '' : ` ${i}`;
    const suffix1 = i === 0 ? ' 1' : ` ${i+1}`;
    const row = document.createElement('label');
    row.innerHTML = `
      Magic Item ${i+1}<input type="text" name="Magic Item${suffix}" placeholder="Objeto mágico">
    `;
    container.appendChild(row);
  }
}

/**
 * Genera los slots de hechizos
 */
function generateSpellSlots() {
  const container = document.getElementById('spells-container');
  if (!container) return;

  container.innerHTML = '';
  for (let i = 0; i < CONFIG.maxSpells; i++) {
    const suffix = i === 0 ? ' 1' : ` ${i+1}`;
    const row = document.createElement('div');
    row.className = 'spell-row';
    row.innerHTML = `
      <h5>Spell ${i+1}</h5>
      <div class="grid-4">
        <label>Name<input type="text" name="Spell Name${suffix}" placeholder="Nombre"></label>
        <label>Level<input type="text" name="Spell Level${suffix}" placeholder="0"></label>
        <label>Casting Time<input type="text" name="Spell Casting Time${suffix}" placeholder="1 action"></label>
        <label>Range<input type="text" name="Spell Range${suffix}" placeholder="60 ft"></label>
        <label>Features<input type="text" name="Spell Features${suffix}" placeholder="Efectos"></label>
        <label>School<input type="text" name="Spell School${suffix}" placeholder="Evocación"></label>
        <label>Notes<input type="text" name="Spell Notes${suffix}" placeholder="Notas"></label>
        <label>Page<input type="text" name="Spell Page${suffix}" placeholder="Pág."></label>
      </div>
    `;
    container.appendChild(row);
  }
}

// ============================================================
// SUBCASE DROPDOWN
// ============================================================

/**
 * Configura el dropdown de subcases
 * @param {object} data - Datos del juego
 */
function setupSubclassDropdown(data) {
  const classSelect = document.getElementById('classSelect');
  const subclassSelect = document.getElementById('subclassSelect');

  if (!classSelect || !subclassSelect) return;

  const subclasses = data.subclasses || {};

  function updateSubclasses() {
    const selectedClass = classSelect.value;
    subclassSelect.innerHTML = '<option value="">— Seleccionar —</option>';
    if (selectedClass && subclasses[selectedClass]) {
      subclasses[selectedClass].forEach(sub => {
        const opt = document.createElement('option');
        opt.value = sub;
        opt.textContent = sub;
        subclassSelect.appendChild(opt);
      });
    } else {
      subclassSelect.innerHTML = '<option value="">— Seleccionar clase primero —</option>';
    }
  }

  classSelect.addEventListener('change', updateSubclasses);
  updateSubclasses();
}

// ============================================================
// FILTRO DE FEATS POR HOMEWORLD
// ============================================================

/**
 * Configura el filtro de feats por homeworld
 */
function setupFeatsFilter() {
  const homeworldSelect = document.getElementById('homeworldSelect');
  if (!homeworldSelect) return;

  const homeworldInfo = document.getElementById('homeworldInfo');
  const featsContainer = document.querySelector('.field-block:has(.field-label:contains("Feats and Professions"))');
  if (!featsContainer) return;

  function parsePrerequisite(prereq) {
    const parts = prereq.split(/\s+(?:or|,)\s+/i);
    const tags = [];
    for (const p of parts) {
      const tag = p.replace(/homeworld/i, '').trim();
      if (tag) tags.push(tag);
    }
    return tags;
  }

  function matchesHomeworld(prereq, homeworldTags) {
    const featTags = parsePrerequisite(prereq);
    return featTags.some(tag => homeworldTags.includes(tag));
  }

  function filterFeats() {
    const selected = homeworldSelect.value;
    if (!selected) {
      featsContainer.querySelectorAll('.checkbox-label').forEach(el => {
        el.style.display = '';
      });
      if (homeworldInfo) {
        homeworldInfo.innerHTML = '<span class="hw-detail">Filtro de feats: — Seleccionar —</span>';
      }
      return;
    }

    const worlds = appState.gameData?.worlds || [];
    const w = worlds.find(x => x.name === selected);
    if (!w) return;

    const homeworldTags = w.tags || [];
    const featLabels = featsContainer.querySelectorAll('.checkbox-label');
    let visibleCount = 0;

    featLabels.forEach(el => {
      const prereq = el.title || '';
      const matches = matchesHomeworld(prereq, homeworldTags);
      el.style.display = matches ? '' : 'none';
      if (matches) visibleCount++;
    });

    if (homeworldInfo) {
      let html = `<strong>${sanitizeHtml(w.name)}</strong>\n`;
      html += `<span class="hw-tags">${sanitizeHtml((w.tags || []).join(' · '))}</span>\n`;
      html += `<span class="hw-detail">Homeworld of: ${sanitizeHtml(w.homeworld_of || '')}</span>\n`;
      if (w.faction) {
        html += `<span class="hw-detail">Faction: ${sanitizeHtml(w.faction)}</span>\n`;
      }
      html += `<span class="hw-detail">Feats visibles: ${visibleCount} de ${featLabels.length}</span>`;
      homeworldInfo.innerHTML = html;
      homeworldInfo.classList.add('visible');
    }
  }

  homeworldSelect.addEventListener('change', filterFeats);
  filterFeats();
}

// ============================================================
// AUTO-CÁLCULO
// ============================================================

/**
 * Calcula las estadísticas iniciales
 */
function calculateInitialStats() {
  const levelEl = document.querySelector('[name="Level"]');
  if (!levelEl) return;

  const level = parseInt(levelEl.value, 10) || 1;
  const pbEl = document.getElementById('profBonusValue');
  if (pbEl) {
    const pb = AutoCalc.proficiency(level);
    pbEl.textContent = '+' + pb;
  }
}

// ============================================================
// VALIDACIÓN
// ============================================================

/**
 * Valida los campos en tiempo real
 * @param {Event} e - Evento
 */
function validateFields(e) {
  const field = e.target;
  if (field.tagName === 'INPUT' || field.tagName === 'TEXTAREA') {
    if (field.hasAttribute('required') && field.value.trim() === '') {
      field.classList.add('invalid');
      field.classList.remove('valid');
    } else if (field.value.trim() !== '') {
      field.classList.add('valid');
      field.classList.remove('invalid');
    } else {
      field.classList.remove('valid', 'invalid');
    }
  }
}

// ============================================================
// AUTO-GUARDADO (DEBOUNCE)
// ============================================================

/**
 * Crea un decorador de debounce
 * @param {Function} func - Función a debocear
 * @param {number} wait - Tiempo de espera en ms
 * @returns {Function} Función debounceada
 */
function debounce(func, wait) {
  let timeout;
  return function(...args) {
    clearTimeout(timeout);
    timeout = setTimeout(() => func.apply(this, args), wait);
  };
}

// ============================================================
// EXPORTACIÓN / IMPORTACIÓN DE JSON
// ============================================================

/**
 * Exporta el personaje como archivo JSON
 */
function exportCharacter() {
  const form = document.getElementById('sheetForm');
  if (!form) return;

  const data = {};
  const formData = new FormData(form);
  for (const [key, value] of formData.entries()) {
    const checkbox = form.querySelector(`[name="${escapeAttr(key)}"]`);
    if (checkbox && checkbox.type === 'checkbox') {
      data[key] = checkbox.checked;
    } else {
      data[key] = value;
    }
  }

  const charName = form.querySelector('[name="Character Name"]')?.value || CONFIG.defaultCharName;
  const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `${charName.replace(/[^a-zA-Z0-9_-]/g, '_')}_${CONFIG.exportPrefix}.json`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
  showToast(`Personaje exportado: ${a.download}`);
}

/**
 * Importa un personaje desde un archivo JSON
 * @param {File} file - Archivo a importar
 */
function importCharacter(file) {
  const reader = new FileReader();
  reader.onload = function(e) {
    try {
      const data = JSON.parse(e.target.result);
      if (typeof data !== 'object' || data === null) {
        throw new Error('El archivo no contiene datos JSON válidos.');
      }

      const form = document.getElementById('sheetForm');
      for (const [key, value] of Object.entries(data)) {
        const checkbox = form.querySelector(`[name="${escapeAttr(key)}"]`);
        if (checkbox && checkbox.type === 'checkbox') {
          checkbox.checked = !!value;
        } else if (checkbox) {
          checkbox.value = value;
        } else {
          const input = form.querySelector(`[name="${escapeAttr(key)}"]`);
          if (input) {
            input.value = value;
          }
        }
      }

      showToast('Personaje importado correctamente.');
      AutoCalc.recalc();
    } catch (err) {
      showToast('Error al importar: ' + err.message);
    }
  };
  reader.readAsText(file);
}

/**
 * Muestra un toast de notificación
 * @param {string} message - Mensaje a mostrar
 */
function showToast(message) {
  let toast = document.getElementById('toast');
  if (!toast) {
    toast = document.createElement('div');
    toast.id = 'toast';
    toast.style.cssText = `
      position:fixed;bottom:20px;left:50%;transform:translateX(-50%);
      background:var(--accent);color:#000;padding:10px 20px;border-radius:6px;
      font-size:0.9rem;z-index:9999;box-shadow:0 2px 8px rgba(0,0,0,0.3);
    `;
    document.body.appendChild(toast);
  }
  toast.textContent = message;
  toast.style.opacity = '1';
  setTimeout(() => {
    toast.style.opacity = '0';
    setTimeout(() => toast.remove(), 300);
  }, 3000);
}

// ============================================================
// GENERACIÓN DE PDF (CLIENT-SIDE)
// ============================================================

// Nota: La generación de PDF con pdf-lib se debe incluir
// en un archivo aparte o hacer referencia a una CDN.
// Ver PDFGeneration.js para la implementación completa.

// ============================================================
// INICIALIZACIÓN
// ============================================================

// Carga los datos del juego al iniciar
loadGameData();
