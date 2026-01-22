# Taller Antiscraping: repositorio de materiales para oyentes

Este repositorio contiene todo lo que los asistentes puedan necesitar para el desarrollo del taller con instrucciones.

## Cloudflare Turnstile

Demo de cloudflare turnstile para probar con crawlers, scrapers y agentes de IA
https://cloudflareturnstile.onrender.com

Comet Browser: https://www.perplexity.ai/comet
Browser OS: https://www.browseros.com/

## FireCrawl

Es un crawler web online para observar el contenido obtenido.
https://www.firecrawl.dev/

## Web Crawler

Contiene un Web Crawler propio hecho en python para los distintos propósitos del taller. Es un sólo archivo y debería poder ejecutarse tanto en consola como desde el plugin Python para Visual Studio Code. No requiere instalación de dependencias adicionales.

Para el propósito del taller, el crawler preguntará antes de la url si se quiere buscar un llms.txt dentro de la url proporcionada. Si se está probando Nepenthes o Iocaine, es importante seleccionar "N"

## Web de cafetería para test con asistentes de IA

Comet Browser: https://www.perplexity.ai/comet
Browser OS: https://www.browseros.com/

Entrar en el enlace con comet o browserOS
https://abelgd.github.io/cafe-laesquina/

## Nepenthes

### La web del autor
https://zadzmo.org/code/nepenthes/

### Instrucciones

Contiene un archivo .zip con todo lo necesario para arrancar un pequeño servidor web con una muestra de las capacidades de Nepenthes.

Para arrancarlo, basta con situarse dentro de la carpeta descomprimida con la terminal y ejecutar docker compose up --build

```bash
  docker compose up --build
```
o en su defecto

```bash
  docker compose build
  docker compose up
```
Si se hacen cambios a la configuración, es posible que haya que ejecutar

```bash
  docker compose down --v
```
Y después volver a ejecutar los comandos de arranque

