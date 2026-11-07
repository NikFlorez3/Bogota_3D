# Bogotá 3D — Modelo Digital del Terreno 2025

## Objetivo
Visor web interactivo de un sector continuo del MDT 2025 generado a partir de cinco tiles seleccionados (0_2, 1_2, 2_2, 3_2, 4_2) que forman un sector desde los Cerros Orientales hasta el área urbana de Bogotá.

## Fuentes y Datos
- **Datos base**: MDT 2025, resolución 20 m/píxel
- **Entidad gestora**: IDECA / UAECD (MAGNA‑SIRGAS Origen Único Nacional, EPSG:9377)
- **Tiles utilizados**: 5 tiles MDT 2025 consecutivos que forman sector continuo
- **Generado por**: Blender 5.2.3 (Script `generar_continuo.py`)
- **Visor**: Three.js (import map jsDelivr)

## Sector Cubierto
- Cinco tiles consecutivos que forman un sector continuo
- Desde los Cerros Orientales hasta el área urbana de Bogotá
- Dimensión aproximada: 116 km (Y) × 60 km (X)
- Porcentaje de NoData por tile: tile 0_2 80.5%, resto 40‑46% (datos reales sin modificar)

## Herramientas Utilizadas
- **QGIS**: Procesamiento del DTM de Bogotá, generación de tiles
- **Blender 5.2.3**: Generación del modelo GLB continuo a partir de los 5 tiles
- **Three.js**: Visualización web del modelo GLB
- **OpenCode**: Entorno de desarrollo y asistencia

## Instrucciones para Ejecutar el Visor

1.  **Clonar o descargar** este repositorio o copiar los archivos a una carpeta local.
2.  Asegurarse de tener Python instalado.
3.  Ejecutar el siguiente comando en una terminal/consola:

   ```powershell
   cd C:\ruta\a\entrega_github
   python -m http.server 8000
   ```

4.  Abrir el navegador en `http://localhost:8000`
5.  El visor cargará el modelo `bogota_3d_continuo.glb` y mostrará el sector continuo.

## Controles del Visor
- **Arrastrar**: Girar la vista alrededor del terreno
- **Rueda del mouse**: Acercar y alejar
- **Clic derecho**: Desplazar el visor
- **Botón "Restablecer vista"**: Recuperar el encuadre inicial del sector
- **Botón "Vista superior":** Posicionar la cámara directamente encima mirando al terreno

## Limitaciones y Nota Importante
- **Solo sector**: Este modelo muestra el sector de cinco tiles MDT 2025 seleccionados. No representa toda la ciudad de Bogotá.
- **Datos NoData**: Los tiles contienen áreas con datos NoData (-9999). El modelo conserva estas elevaciones reales sin inventar datos.
- **Colores**: Se aplican colores según elevación (azul → verde → marrón → blanco) basándose en el rango aproximado 2267‑4161 m.
- **Sin datos originales modificados**: Los datos MDT 2025 originales no fueron alterados. El GLB fue generado a partir de los 5 tiles seleccionados.

## Estructura del Repositorio
```
entrega_github/
│
├── index.html          -- Visor web Three.js
├── bogota_3d_continuo.glb -- Modelo GLB continuo (18.37 MB)
├── .gitignore          -- Archivos y directorios excluidos del versionado
└── README.md           -- Este archivo
```

## Contacto / Proveniencia
Datos abiertos IDECA / UAECD. Proyecto desarrollado con OpenCode, QGIS y Blender.