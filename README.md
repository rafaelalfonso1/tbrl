# The Business Research Lab — Sitio web

Sitio estático (HTML, CSS y JavaScript) para **Netlify**, con datos de mercado que se actualizan solos mediante **GitHub Actions**. No hay servidor ni base de datos que mantener.

## Estructura

```
public/                       ← lo que se publica (Netlify sirve esta carpeta)
  index.html                  Inicio
  investigacion.html          Biblioteca de investigación (descargas gratis y estudios premium)
  mercados.html               Inteligencia de mercado (USD/DOP, TPM, conversor, decisiones)
  datos.html                  Centro de datos: dashboards + descargas CSV/Excel
  js/config.js                ← EDITA: correo, teléfono, WhatsApp, LinkedIn, enlaces de pago
  data/research.json          ← EDITA: tus estudios
  data/markets.json           Datos de la página de mercados (se sincroniza solo)
  data/macro/fuente/          ← FUENTES de datos (ver abajo)
  data/macro/series.json      Generado automáticamente (no editar)
  data/macro/descargas/       CSV y Excel generados automáticamente (no editar)
  data/inmobiliario/          Dataset inmobiliario (CSV original, Excel y resumen.json)
  data/origen.json            Lo crea la automatización si el repo es público (no editar)
  downloads/                  PDF gratuitos
scripts/
  actualizar_datos.py         Descarga las fuentes oficiales (BCRD/DGII) y reconstruye todo
  construir_datos.py          Genera series.json, CSV, Excel y sincroniza markets.json
  construir_inmobiliario.py   Genera el Excel y el resumen del dataset inmobiliario
.github/workflows/actualizar-datos.yml   Programación automática
netlify.toml                  Configuración de Netlify (publica la carpeta public/)
```

## Puesta en marcha con actualización automática (una sola vez, ~15 minutos)

1. **Crea una cuenta en GitHub** (gratis) en github.com.
2. **Crea un repositorio** nuevo, por ejemplo `tbrl-sitio` (puede ser privado).
3. **Sube los archivos**: en el repositorio, *Add file → Upload files*, arrastra **todo el contenido** de esta carpeta (incluida la carpeta oculta `.github`) y confirma con *Commit changes*.
   - Si tu sistema oculta `.github`, crea el archivo a mano: *Add file → Create new file*, nombre `.github/workflows/actualizar-datos.yml`, y pega su contenido.
4. **Permite que la automatización guarde cambios**: *Settings → Actions → General → Workflow permissions →* marca **Read and write permissions** → *Save*.
5. **Conecta Netlify al repositorio**: en app.netlify.com, *Add new site → Import an existing project → GitHub* → elige el repositorio. Netlify detecta `netlify.toml` (carpeta `public`). *Deploy*.
6. **Primera carga de datos**: en GitHub, pestaña *Actions → Actualizar datos de mercado → Run workflow*. La primera vez descarga el histórico diario desde 2019 y crea la serie **semanal**. Revisa que termine en verde.

Desde ahí, de lunes a viernes a las 10:30 a. m. y 4:30 p. m. (hora de Santo Domingo) el sistema descarga la tasa del día del BCRD y la serie de la DGII, regenera los dashboards y las descargas, y Netlify publica la nueva versión sola.

> Si una fuente no responde o cambia de formato, el proceso **no borra nada**: conserva los datos anteriores y deja un aviso en el registro de *Actions*.

## Importante: créditos de Netlify (plan gratuito)

En el plan gratuito de Netlify cada **despliegue a producción consume 15 créditos** de 300 al mes; al agotarse, el sitio se pausa hasta el mes siguiente. Si cada actualización de datos redesplegara el sitio, se acabarían a mitad de mes.

Solución incluida: **haz público el repositorio** (*Settings → General → Danger Zone → Change visibility → Public*). La automatización lo detecta, crea `public/data/origen.json` y desde ese momento:
- el sitio lee los datos de mercado directo de GitHub (actualizados en ~5 minutos),
- las actualizaciones de datos se guardan con `[skip netlify]` y **no consumen créditos**,
- si GitHub no respondiera, el sitio usa automáticamente la última copia publicada.

Hacer público el repositorio no expone nada sensible: todo lo que contiene ya es visible en el propio sitio web (no hay contraseñas ni claves). Si prefieres mantenerlo privado, la alternativa es el plan Personal de Netlify (1,000 créditos/mes) o actualizar con menos frecuencia.

Revisa tu consumo en Netlify → *Billing → Usage*.

## Qué se actualiza solo y qué no

| Dato | Cómo se actualiza |
|---|---|
| Tipo de cambio del día (compra/venta) | Automático (PDF diario del BCRD) |
| Tipo de cambio diario, semanal y promedio mensual | Automático (serie de la DGII con datos del BCRD) |
| TPM e inflación interanual | **Manual, 1 minuto al mes**: edita `public/data/macro/fuente/indicadores_mensuales.csv` en GitHub y guarda. El sitio se reconstruye solo. |
| Tabla de decisiones de política y próxima reunión | Manual en `public/data/markets.json` (`decisions`, `nextMeeting...`) |

El BCRD no publica la TPM ni la inflación en un formato de máquina estable, por eso se dejan como edición manual. Alternativa: una tarea programada de Claude puede investigarlas y actualizarlas cada mes si conectas tu GitHub a Claude.

### Formato de `indicadores_mensuales.csv`

```
fecha,tpm,inflacion_interanual
2026-10,5.5,
2026-11,5.5,4.98     ← agrega una fila por mes; deja vacío lo que aún no se publica
```

## Centro de datos

- Cada serie tiene su dashboard (último dato, variación mensual y anual, gráfico con 1A/3A/5A/Todo, tabla) y botones **CSV** y **Excel**.
- *Descargar todo* entrega un Excel con hoja «Léeme», hoja con todas las series mensuales y una hoja por serie, más la tasa diaria.
- Para agregar una serie nueva (remesas, reservas, IMAE…): añade su CSV en `data/macro/fuente/` y una entrada en `construir_datos.py` (lista `series`).

## Publicar sin GitHub (sin automatización)

Netlify → *Add new site → Deploy manually* y arrastra la carpeta **`public`**. Los datos quedarán fijos hasta que vuelvas a subirla. Para regenerar los datos a mano: `pip install -r scripts/requirements.txt` y `python scripts/actualizar_datos.py`.

## Leads de los formularios

Los formularios **no se guardan en GitHub ni en el sitio**: los recibe y almacena **Netlify Forms**.

**Requisito (una sola vez):** Netlify → tu sitio → **Forms → Enable form detection** y luego **Deploys → Trigger deploy → Deploy project**. En sitios nuevos viene desactivado; sin esto los formularios fallan con «Algo salió mal» (las descargas gratuitas se entregan igual, pero no se registra el lead).

- Verlos: Netlify → tu sitio → **Forms**. Hay una lista por formulario: `contact` (contacto), `newsletter` (Monthly Pulse), `free-download` (descargas gratuitas, incluye qué estudio se descargó) y `study-waitlist` (lista de espera de estudios premium).
- Exportarlos: dentro de cada formulario, **Download as CSV**.
- Recibirlos por correo: *Project configuration → Notifications → Emails and webhooks → Form submission notifications → Add notification*, con tu correo.
- Spam: los sospechosos van a la pestaña *Spam*; revísala de vez en cuando.
- Llevarlos a una hoja o CRM: Zapier o Make (disparador «New form submission» de Netlify → Google Sheets, Mailchimp, HubSpot…).
- En los planes por créditos los envíos de formularios son gratuitos e ilimitados.

## Cómo actualizar el sitio (contenido, estudios, textos)

1. Recibe el paquete de actualización (zip) y descomprímelo. Contiene **solo los archivos que cambian**, en la misma estructura de carpetas.
2. En GitHub, abre tu repositorio → **Add file → Upload files**.
3. Arrastra **todo el contenido** de la carpeta descomprimida (incluida `.github` si viene) a la ventana. GitHub reemplaza los archivos con el mismo nombre y deja intactos los demás (incluidos los datos que se actualizan solos).
4. Escribe un mensaje (p. ej. «Nuevos estudios inmobiliarios») y pulsa **Commit changes**.
5. Netlify despliega solo en 1–2 minutos: compruébalo en Netlify → **Deploys** (debe decir *Published*).
6. Abre el sitio con Ctrl+F5 (Cmd+Shift+R en Mac) para ver la versión nueva sin caché.

Reglas para no romper nada:
- **Nunca subas** `public/data/markets.json` ni la carpeta `public/data/macro/` desde una copia vieja: los mantiene la automatización.
- Sube todos los cambios de una vez (un solo *commit* = un solo despliegue = 15 créditos).
- Cambios pequeños de texto: abre el archivo en GitHub, pulsa el lápiz (**Edit**), corrige y **Commit changes**.

### Agregar un estudio tú mismo

1. Sube el PDF a `public/downloads/` (*Add file → Upload files* dentro de esa carpeta).
2. Edita `public/data/research.json` y copia un bloque existente: cambia `id`, `title`, `category`, `date`, `pages`, `summary` y `downloadUrl` (`downloads/nombre-del-archivo.pdf`). Para que salga en el inicio, `"featured": true`.
3. Commit. Los estudios destacados y más recientes aparecen primero.

## Antes del lanzamiento

- [ ] `public/js/config.js`: correo real, teléfono, WhatsApp y LinkedIn.
- [ ] Precios de membresías en `index.html` (busca `US$149`) y enlaces de pago en `config.js`.
- [ ] Sustituye los estudios de ejemplo de `public/data/research.json`.
- [ ] Si tu dominio no es `thebusinessresearchlab.com`, cámbialo en `sitemap.xml`, `robots.txt` y las etiquetas `canonical`.

## Investigación de pago (sin backend)

**Nunca pongas PDF de pago en `public/`**: todo lo que está ahí es público. Usa Lemon Squeezy, Gumroad o Payhip (alojan el archivo y lo entregan tras el pago) y pega el enlace en `checkoutUrl` del estudio. Para membresías recurrentes, Stripe Payment Links en `config.js → plans`.

## Vista previa local

```
cd public && python3 -m http.server
```
Abre http://localhost:8000.

## Marca (según «TBRL — Línea gráfica»)

Navy `#2C4856` · Terracota `#B35231` (sobre navy `#C15C28`, solo línea/forma) · Crema `#F7F4EB` · Navy profundo `#1E3340` · Blush `#E2A38D` · Arena `#CDBB98`. Tipografía Manrope (alojada en `assets/fonts/`). Logo en `assets/img/logo-symbol.svg` y `logo-symbol-light.svg` (recreaciones SVG; sustitúyelas por los originales del diseñador si los tienes).
