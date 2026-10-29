# Neon Odyssey Character Sheet Generator

> **NeonRPG** — Aplicación web que genera hojas de personaje en PDF para **Neon Odyssey**, variante de D&D (playtest **v0.1.1**).

> [![Status](https://img.shields.io/badge/status-Development%20activa-orange)]()
> [![Version](https://img.shields.io/badge/version-v0.1.1-blue)]()

<h2 id="quick-nav">📋 Quick Nav</h2>

| Sección | Descripción |
|---------|-------------|
| 🎯 Objetivo | Objetivos del proyecto |
| 📜 Derechos IP | Derechos de autor y marco legal |
| ⚠️ Aviso Legal | Advertencias legales |
| 🏗️ Stack | Tecnologías utilizadas |
| 🚀 GitHub Pages | Guía de despliegue |

<p align="center">
  <img src="static/assets/Neon Rain in the Cyberpunk City.png" alt="Neon Odyssey Background" width="100%" style="margin-bottom:12px;">
  <h1 align="center">Neon Odyssey Character Sheet Generator</h1>
  <p align="center">
    <sub><strong>NeonRPG</strong> — Aplicación web que genera hojas de personaje en PDF para <strong>Neon Odyssey</strong>, variante de D&D (playtest <strong>v0.1.1</strong>).</sub><br>
    <sub>Hospedada en <a href="https://EdMaxt.github.io/NeonRPG/">EdMaxt.github.io/NeonRPG</a></sub>
  </p>



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

## 📁 Estructura del repositorio (versión GitHub Pages)

```
NeonCharacters/
├── game_data.json             # Datos del juego v0.1.1
├── template.pdf               # Plantilla PDF (campos AcroForm) para rellenar en browser
├── README.md                  # Documentación
├── static/
│   ├── app.js                 # Lógica frontend: generación de slots, auto-calc, export/import JSON
│   ├── style.css              # Estilo cyberpunk + 4 temas
│   ├── assets/                # 3 imágenes de fondo generadas
│   └── template.pdf           # Copia de la plantilla (para preview)
├── templates/
│   ├── index.html             # Formulario web (frontend completo)
│   └── preview.html           # Vista previa del PDF
└── .gitignore                 # Ignora borradores temporales
```

> **Nota:** GitHub Pages solo sirve archivos estáticos (HTML/CSS/JS). No se puede ejecutar Python/Flask directamente.

## 🚀 Despliegue en GitHub Pages

1. Empuja todos los archivos al repositorio
2. Ve a **Settings → Pages** en GitHub
3. Source: **Deploy from a branch** → `main` (o `gh-pages`)
4. La aplicación estará disponible en `https://<tu-usuario>.github.io/<tu-repo>/`

## 📋 Modo de uso

1. Abre la URL de GitHub Pages
2. Rellena el formulario (clase, especie, habilidades, ataques, etc.)
3. Usa **Exportar JSON** para guardar el estado
4. Usa **Importar JSON** para cargar un estado anterior
5. Los cálculos automáticos se actualizan en tiempo real (AC, atributos, iniciativa, PB, etc.)
6. Descarga la **plantilla PDF** (`template.pdf`) y rellénala en cualquier viewer PDF
7. Usa la plantilla rellena para imprimir o usar digitalmente

---

## 📜 Derechos de Propiedad Intelectual — Resumen

> **Wizards of the Coast LLC**  
> © 2024. Todos los derechos reservados.  
> "Dungeons & Dragons", "D&D", y el símbolo del dragón son propiedad de Wizards of the Coast LLC.

> **Avantris Entertainment / Legends of Avantris**  
> © 2024. Todos los derechos reservados.  
> "Neon Odyssey", "Avantris", "Legends of Avantris" y "The Crooked Moon" son propiedad de Avantris Entertainment.

> **Aviso importante:**  
> Este proyecto es **no oficial** y **sin fines de lucro**. Es un trabajo independiente que utiliza el **OGL de D&D 5e** y los materiales de **Avantris Entertainment** únicamente a efectos de fan content y educación.  
> El uso de la IP de Avantris es **a tu propio riesgo**. Avantris conserva el derecho de detener o restringir el uso de su IP en cualquier tiempo.  
> Si eres dueño de los derechos de los materiales aquí mencionados, por favor contacta al autor para solicitar la remoción o licencia.

---

*Neon Odyssey Character Sheet Generator v0.1.1 — Hecho con ❤️ por Ed (Zelda).*
