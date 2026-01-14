# Taller Antiscraping: repositorio de materiales para oyentes

Este repositorio contiene todo lo que los asistentes puedan necesitar para el desarrollo del taller con instrucciones.

## Web Crawler

Contiene un Web Crawler propio hecho en python para los distintos propósitos del taller. Es un sólo archivo y debería poder ejecutarse tanto en consola como desde el plugin Python para Visual Studio Code. No requiere instalación de dependencias adicionales.

## Nepenthes

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