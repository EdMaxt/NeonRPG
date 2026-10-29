# Neon Odyssey Character Sheet Generator

> **NeonRPG** — Aplicación web que genera hojas de personaje en PDF para **Neon Odyssey**, variante de D&D (playtest **v0.1.1**).

[![Status](https://img.shields.io/badge/status-Development%20activa-orange)]()
[![Version](https://img.shields.io/badge/version-v0.1.1-blue)]()

## 📖 Descripción

App que toma los datos ingresados en un formulario web y los escribe directamente en los campos de un PDF template, generando una hoja de personaje lista para imprimir o usar digitalmente.

**Neon Odyssey** es una variante de D&D con un estilo visual cyberpunk/neon. La app permite crear personajes con:

- Sistema de clases, especies, subclases y hogares
- Proficiencias (lenguajes, armas, herramientas, feats)
- Salvos, habilidades y atributos
- Cálculo automático de AC, atributos, iniciativa, etc.
- Generación de PDF editable o aplanado (flattened)

## 🎯 Objetivo

Asumir un personaje de **Neon Odyssey** y generar una hoja de personaje en PDF, con un enfoque en:
- Usabilidad (formulario intuitivo, cálculos automáticos)
- Accesibilidad (4 temas visuales, diseño responsive)
- Funcionalidad (PDF editable y versión aplanada para imprimir)
- Mantenibilidad (documentación clara, tests, estructura modular)

## 📜 Derechos de Propiedad Intelectual

### 🛡 Dungeons & Dragons (D&D)
> © **Wizards of the Coast LLC**. All Rights Reserved.

- **Marco legal:** La campaña base de D&D 5e está protegida bajo el **OGL (Open Gaming License)** de Wizards of the Coast.
- **Qué está protegido:**
  - Personajes, clases, razas, armas, habilidades, hechizos, criaturas, magias, etc.
  - El nombre "Dungeons & Dragons", "D&D", "Wizards of the Coast", el dragón ampersand, y todos los demás nombres de productos.
- **Exenciones aplicables:**
  - El **OGL permite** el uso interno y comercial no masivo de la mecánica de juego (lo que constituye "sistema de juego funcional").
  - **No está permitido** usar los logotipos de Wizards of the Coast, indicar alianzas, ni vender versiones modificadas que puedan confundirse con la original.
- **Ley aplicable:** © 2024 Wizards of the Coast LLC. Todos los derechos reservados. Los personajes y sus apariencias distintivas son propiedad de Wizards of the Coast.

### 🌙 Neon Odyssey (Avantris Entertainment)
> © **Avantris Entertainment / Legends of Avantris**. All Rights Reserved.

- **Marco legal:** Neon Odyssey es un universo creativo (Space Opera) desarrollado por **Avantris Entertainment (Legends of Avantris)**.
- **Qué está protegido:**
  - Personajes, criaturas, mundos, antecedentes, escenas, arte, diseños, audio, música, texto escrito, contenido mediático, y otros materiales.
  - Los logotipos/trademarks: "Avantris", "Avantris LLC", "Legends of Avantris", "Neon Odyssey", "The Crooked Moon".
- **Guía de contenido para fans (resumen):**
  - El contenido **no comercial** creado por fans está permitido para su visualización dentro de la comunidad.
  - **No se permite** vender material que contenga IP de Avantris como parte de un negocio a gran escala sin permiso.
  - No se pueden usar los logotipos/trademarks de Avantris (incluyendo "Neon Odyssey") en productos similares a los de Avantris.
- **Nota legal:** El uso de la IP de Avantris es **a tu propio riesgo**. Avantris conserva el derecho de detener o restringir el uso de su IP en cualquier momento.

---

## ⚠️ Aviso Legal

> **ADVERTENCIA DE USO DE IP**  
> Este proyecto es **no oficial** y se basa en el marco del **OGL de D&D 5e** y en los **derechos de autor de Avantris Entertainment (Neon Odyssey)**.
>
> - El uso de la IP de Avantris es **a tu propio riesgo**.
> - No vendas versiones modificadas ni indices alianzas con Wizards of the Coast o Avantris.
> - Si eres dueño de los derechos de los materiales aquí mencionados, por favor contacta al autor.
> - Este proyecto es **sin fines de lucro** y es un trabajo independiente.

---

## 📚 Fuentes de referencia

| Fuente | URL |
|--------|-----|
| Wizards of the Coast | https://www.wizards.com/ |
| D&D Licensing | https://www.dungeonsanddragons.com/licensing/ |
| Avantris Entertainment (fan content guidelines) | https://avantris.com/en-gb/pages/fan-content-guidelines |
| GitHub DMCA - Wizards of the Coast | https://github.com/github/dmca/blob/master/2024/08/2024-08-07-wizards-of-the-coast.md |



Asumir un personaje de **Neon Odyssey** y generar una hoja de personaje en PDF, con un enfoque en:

- Usabilidad (formulario intuitivo, cálculos automáticos)
- Accesibilidad (4 temas visuales, diseño responsive)
- Funcionalidad (PDF editable y versión aplanada para imprimir/distributed)
- Mantenibilidad (documentación clara, tests, estructura modular)

## 🏗️ Stack

| Capacidad | Tecnología |
|-----------|------------|
| Backend | Python 3.14 + Flask |
| PDF | pypdf (llenado de formularios AcroForm), PyMuPDF (bake/flatten) |
| Frontend | HTML + CSS vanilla (sin frameworks) |
| Seguridad | Flask-WTF (CSRF), validación de input |
| Estilo | 4 temas visuales inspirados en el arte de los libros |
| Tests | pytest (40 tests) |
| Documentación | Obsidian (vault personal) |

## 📁 Estructura del repositorio

```
NeonCharacters/
├── app.py                     # Servidor Flask + endpoints PDF
├── template.pdf               # Hoja de personaje original (campos AcroForm)
├── game_data.json             # Datos del juego v0.1.1
├── requirements.txt           # Dependencias Python
├── CODE_REVIEW.md             # Reporte de code review
├── tests/test_app.py          # 40 tests unitarios
├── templates/
│   ├── index.html             # Formulario web con secciones colapsables
│   └── preview.html           # Vista previa del PDF (iframe + descargar)
├── static/
│   └── style.css              # Estilo cyberpunk + 4 temas
├── temp/                      # PDF de previsualización (runtime, gitignored)
├── assets/                    # 3 fondos de tema generados (Overdrive pendiente)
└── .gitignore                 # Archivos a ignorar
```

## 🚀 Instalación y Ejecución

```bash
cd "path/to/NeonCharacterSheet"
pip install -r requirements.txt
python app.py
```

El servidor corre en `http://localhost:5000`.

## ⚙️ Endpoints

| Endpoint | Método | Descripción |
|----------|--------|-------------|
| `/` | GET | Formulario principal |
| `/generate` | POST | Genera el PDF, guarda en `temp/`, muestra previsualización |
| `/preview/<filename>` | GET | Sirve el PDF en línea (para el iframe) |
| `/download/<filename>` | GET | Descarga el PDF con nombre personalizado |
| `/health` | GET | Health check |

### Formulario

- Checkbox `flattenPDF` → Generar PDF sin editar (aplanado) con PyMuPDF bake
- Todos los campos del PDF se llenan automáticamente

## 🔧 Funcionalidades

### 1. Serie PDF

- /generate: Llena el PDF con los campos del formulario (pypdf, campos AcroForm).
- /preview y /download: Manejan la previsualización y la descarga del PDF

### 2. Auto-calc

- Modifiers, Iniciativa, PB, Spell Attack/DC, HP Max (fórmulas de D&D 5e)
- Auto-calc Armor Class: tipo de armadura + DEX + escudo (+2)
- Auto-check saves/skills por clase

### 3. JSON Export/Import

- Exportar JSON: serialize all form fields to a downloadable .json file
- Importar JSON: load a .json file and populate all form fields
- Auto-save draft: persists across sessions via browser localStorage

### 4. Temas Visuales

- 4 temas: Neon Cyber, Cosmic Codex, Outrunner, Overdrive
- 3 imágenes de fondo validadas: Neon Cyber, Cosmic Codex, Outrunner
- Overdrive (imagen de fondo) pendiente

## 🧪 Tests

```bash
python -m pytest tests/ -v
```

40 tests conexos passing.

## 📝 Notas

- El PDF template es el archivo `Neon_Odyssey_Character_Sheet_v0.1_-_Form_Fillable.pdf` original
- Los campos se llenan con `pypdf` respetando la estructura AcroForm del PDF
- Los checkboxes del PDF usan `/Off` (desmarcado) y `/Yes` (marcado)
- Los campos de salvación son texto (`Save STR`) y la proficiencia es un checkbox aparte
- El flattering (Recorte/No editable PDF) usa PyMuPDF: llenar campos, `widget.update()`, `doc.bake(widgets=True, annots=True)`
- Verificar: `len(list(page.widgets())) == 0` en todas las páginas después de aplanado

## 🔗 Enlaces

- GitHub: https://github.com/EdMaxt/NeonRPG
- Obsidian Vault: `vault personal`

## 📜 Licencia

Proyecto personal / desarrollado con propósito. (v0.1.1)
