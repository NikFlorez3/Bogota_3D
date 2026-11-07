"""
Genera bogota_3d_completo.glb a partir del MDT 2025 (EPSG:9377), SIN Blender.

Se ejecuta con el Python de QGIS (trae GDAL y numpy):
  Menú Inicio > "OSGeo4W Shell" y ahí:

  python generar_glb_completo.py --src "RUTA\\mdt2025_bogota_20m.tif" --out "C:\\Users\\angel\\Documents\\Bogota_3D\\entrega_github\\bogota_3d_completo.glb"

--src puede ser:
  * un ráster (GeoTIFF u otro formato que lea GDAL), por ejemplo mdt2025_bogota_20m, o
  * una carpeta con los tiles GeoTIFF (se unen en un mosaico virtual).

Convenciones del GLB (las mismas del bogota_3d_continuo.glb que usa el visor):
  x =  E - 4.870.000       (Este)
  y =  elevación (m s.n.m.), sin exageración
  z = -(N - 2.046.000)     (-Z = Norte, convención glTF)
No modifica los datos de origen: solo los lee.
"""
import argparse, glob, json, os, struct, sys

import numpy as np

ORIGEN_E = 4870000.0
ORIGEN_N = 2046000.0


def leer_mdt(src, res, nodata_in):
    from osgeo import gdal
    gdal.UseExceptions()
    if os.path.isdir(src):
        tifs = sorted(glob.glob(os.path.join(src, "*.tif")) + glob.glob(os.path.join(src, "*.tiff")))
        if not tifs:
            sys.exit(f"No hay archivos .tif en {src}")
        print(f"Mosaico de {len(tifs)} tiles")
        src_ds = gdal.BuildVRT("/vsimem/mosaico.vrt", tifs, srcNodata=nodata_in, VRTNodata=nodata_in)
    else:
        src_ds = gdal.Open(src)
    srs = src_ds.GetProjection()
    if "9377" not in srs and "Origen" not in srs and "CTM12" not in srs:
        print("AVISO: el ráster no parece estar en EPSG:9377. Se reproyecta a EPSG:9377.")
    # Remuestreo a 'res' metros, promedio, en EPSG:9377
    ds = gdal.Warp("/vsimem/mdt_res.tif", src_ds, dstSRS="EPSG:9377", xRes=res, yRes=res,
                   resampleAlg="average", srcNodata=nodata_in, dstNodata=-9999, targetAlignedPixels=True)
    band = ds.GetRasterBand(1)
    z = band.ReadAsArray().astype(np.float64)
    gt = ds.GetGeoTransform()
    nd = band.GetNoDataValue()
    valid = np.isfinite(z) & (z > -1000) & (z < 9000)
    if nd is not None:
        valid &= z != nd
    return z, valid, gt


def construir_malla(z, valid, gt):
    h, w = z.shape
    filas, cols = np.nonzero(valid)
    idx = -np.ones((h, w), dtype=np.int64)
    idx[filas, cols] = np.arange(filas.size)
    E = gt[0] + (cols + 0.5) * gt[1] + (filas + 0.5) * gt[2]
    N = gt[3] + (cols + 0.5) * gt[4] + (filas + 0.5) * gt[5]
    pos = np.empty((filas.size, 3), dtype=np.float32)
    pos[:, 0] = E - ORIGEN_E
    pos[:, 1] = z[filas, cols]
    pos[:, 2] = -(N - ORIGEN_N)
    # Celdas 2x2: a=(r,c) b=(r,c+1) c=(r+1,c) d=(r+1,c+1). Dos triángulos por celda,
    # cada uno solo si sus 3 vértices tienen dato (NoData no se rellena).
    a, b = idx[:-1, :-1], idx[:-1, 1:]
    c, d = idx[1:, :-1], idx[1:, 1:]
    t1 = np.stack([a, c, b], -1).reshape(-1, 3)   # orientación con normal hacia +Y
    t2 = np.stack([b, c, d], -1).reshape(-1, 3)
    tri = np.concatenate([t1, t2])
    tri = tri[(tri >= 0).all(1)].astype(np.uint32)
    return pos, tri


def escribir_glb(path, pos, tri):
    pos_b = pos.tobytes()
    idx_b = tri.reshape(-1).tobytes()
    pad = lambda b, ch=b"\x00": b + ch * ((4 - len(b) % 4) % 4)
    bin_data = pad(pos_b) + pad(idx_b)
    gltf = {
        "asset": {"version": "2.0", "generator": "generar_glb_completo.py"},
        "scene": 0,
        "scenes": [{"nodes": [0]}],
        "nodes": [{"mesh": 0, "name": "MDT_2025_Bogota_completo"}],
        "meshes": [{"name": "MDT_2025_Bogota_completo",
                    "primitives": [{"attributes": {"POSITION": 0}, "indices": 1, "material": 0, "mode": 4}]}],
        "materials": [{"name": "Terreno", "doubleSided": True,
                       "pbrMetallicRoughness": {"baseColorFactor": [0.667, 0.792, 0.627, 1.0],
                                                "metallicFactor": 0.0, "roughnessFactor": 1.0}}],
        "buffers": [{"byteLength": len(bin_data)}],
        "bufferViews": [
            {"buffer": 0, "byteOffset": 0, "byteLength": len(pos_b), "target": 34962},
            {"buffer": 0, "byteOffset": len(pad(pos_b)), "byteLength": len(idx_b), "target": 34963},
        ],
        "accessors": [
            {"bufferView": 0, "componentType": 5126, "count": int(pos.shape[0]), "type": "VEC3",
             "min": pos.min(0).astype(float).tolist(), "max": pos.max(0).astype(float).tolist()},
            {"bufferView": 1, "componentType": 5125, "count": int(tri.size), "type": "SCALAR"},
        ],
    }
    json_b = pad(json.dumps(gltf, separators=(",", ":")).encode("utf-8"), b" ")
    total = 12 + 8 + len(json_b) + 8 + len(bin_data)
    with open(path, "wb") as f:
        f.write(struct.pack("<III", 0x46546C67, 2, total))
        f.write(struct.pack("<II", len(json_b), 0x4E4F534A)); f.write(json_b)
        f.write(struct.pack("<II", len(bin_data), 0x004E4942)); f.write(bin_data)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--src", required=True, help="Ráster del MDT o carpeta con tiles GeoTIFF")
    ap.add_argument("--out", required=True, help="Ruta del GLB a crear")
    ap.add_argument("--res", type=float, default=40.0, help="Resolución de la malla en metros (por defecto 40)")
    ap.add_argument("--nodata", type=float, default=-9999.0, help="Valor NoData de origen (por defecto -9999)")
    a = ap.parse_args()

    if os.path.abspath(a.out).lower().endswith("bogota_3d_continuo.glb"):
        sys.exit("No sobrescribas bogota_3d_continuo.glb; usa otro nombre de salida.")

    z, valid, gt = leer_mdt(a.src, a.res, a.nodata)
    print(f"Grilla {z.shape[1]} x {z.shape[0]} a {a.res:.0f} m; celdas con dato: {int(valid.sum()):,}")
    if not valid.any():
        sys.exit("El ráster no tiene datos válidos.")
    pos, tri = construir_malla(z, valid, gt)
    escribir_glb(a.out, pos, tri)

    mn, mx = pos.min(0), pos.max(0)
    print(f"Vértices: {pos.shape[0]:,}   Triángulos: {tri.shape[0]:,}")
    print(f"Bounding box  X: {mn[0]:.0f} a {mx[0]:.0f}   Y (elev): {mn[1]:.1f} a {mx[1]:.1f}   Z: {mn[2]:.0f} a {mx[2]:.0f}")
    print(f"Equivale a    E: {ORIGEN_E+mn[0]:.0f} a {ORIGEN_E+mx[0]:.0f}   N: {ORIGEN_N-mx[2]:.0f} a {ORIGEN_N-mn[2]:.0f}")
    print(f"Archivo: {a.out}  ({os.path.getsize(a.out)/1048576:.1f} MB)")
    if os.path.getsize(a.out) > 40 * 1048576:
        print("Supera 40 MB: vuelve a correrlo con --res 50")


if __name__ == "__main__":
    main()
