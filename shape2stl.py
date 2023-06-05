import sys
import geopandas as gpd
import mapbox_earcut as earcut
import numpy as np
import pymeshfix
import pyvista as pv
import trimesh
from stl import mesh
from shapely import geometry
from trimesh.exchange.stl import export_stl_ascii

# 一時STLファイル
TEMP_STL_FILE = "output.stl"

def NormalizePolygons(polygons, scaleFactor):
    # 飛び地対策、MultiPolygonの対策 面積が大きいものを採用する
    tgtPolygons = []
    for polygon in polygons:
        if isinstance(polygon, geometry.polygon.Polygon):
            target_poly = polygon
        elif isinstance(polygon, geometry.multipolygon.MultiPolygon):
            area_list = [(p.area, p) for p in polygon.geoms]
            area_list = sorted(area_list, key=lambda x: -x[0])
            largest_poly = area_list[0][1]
            target_poly = largest_poly

        # ポリゴン追加
        tgtPolygons.append(target_poly)

    # 正規化 全ポリゴンの頂点からの最大値を用いて正規化する。0～1の範囲にする。
    x_min_list = []
    y_min_list = []
    x_max_list = []
    y_max_list = []

    for p in tgtPolygons:
        tempX, tempY = p.exterior.xy
        x_min_list.append(np.min(np.array(tempX)))
        y_min_list.append(np.min(np.array(tempY)))
        x_max_list.append(np.max(np.array(tempX)))
        y_max_list.append(np.max(np.array(tempY)))

    x_min = np.min(x_min_list)
    x_max = np.max(x_max_list)
    y_min = np.min(y_min_list)
    y_max = np.max(y_max_list)

    # XとYの最大値と最小値の差のうち大きい値を取得
    max_range = max(x_max - x_min, y_max - y_min)

    # 任意倍率にしたポリゴンリスト
    scaledPolygons = []
    for polygon in tgtPolygons:
        # 頂点情報
        x, y = polygon.exterior.xy

        # 正規化
        x = np.array(x)
        y = np.array(y)
        normalizedX = (x - x_min) / max_range
        normalizedY = (y - y_min) / max_range

        # 任意倍率に設定
        scaledX = normalizedX * scaleFactor
        scaledY = normalizedY * scaleFactor

        # ポリゴンを作成 リストに追加
        scaledPolygon = geometry.Polygon(zip(scaledX, scaledY))
        scaledPolygons.append(scaledPolygon)

    return scaledPolygons

def CreateAndSaveSTL(scaledPolygons, shapeIndex, thickness):
    # 頂点情報
    x, y = scaledPolygons[shapeIndex].exterior.xy

    # 目安サイズ 外接する矩形サイズを出力
    x_min = np.min(x)
    x_max = np.max(x)
    y_min = np.min(y)
    y_max = np.max(y)
    rectangle_width = x_max - x_min
    rectangle_height = y_max - y_min
    print(f"width: {rectangle_width} mm, height: {rectangle_height} mm")

    # 頂点の数
    num_vertices = len(x)

    # ポリゴンの頂点を3Dに拡張
    vertices = np.zeros((num_vertices*2, 3))
    vertices[:num_vertices, 0] = x
    vertices[:num_vertices, 1] = y
    vertices[num_vertices:, 0] = x
    vertices[num_vertices:, 1] = y
    vertices[num_vertices:, 2] = thickness

    # 頂点情報を組み合わせた座標データ
    verts = np.column_stack((x, y))

    # mapbox_earcutを使用して非凸ポリゴンを三角形に分割
    rings = np.array([len(verts)])
    triangles = earcut.triangulate_float32(verts, rings)

    # 分割三角毎にreshape
    triangles = triangles.reshape(-1, 3)

    # 上面と下面の面を定義
    top_faces = []
    bottom_faces = []
    for t in triangles.tolist():
        top_faces.append([t[0], t[1], t[2]])
        bottom_faces.append([t[0] + num_vertices, t[1] +
                            num_vertices, t[2] + num_vertices])

    # 側面を定義
    side_faces = []
    for i in range(num_vertices):
        side_faces.append([i, (i+1) % num_vertices, i+num_vertices])
    for i in range(num_vertices):
        side_faces.append([(i+1) % num_vertices, (i+1) %
                          num_vertices+num_vertices, i+num_vertices])

    # 結合
    faces = top_faces + bottom_faces + side_faces

    # メッシュにする
    polygon_mesh = mesh.Mesh(np.zeros(len(faces), dtype=mesh.Mesh.dtype))
    for i, f in enumerate(faces):
        for j in range(3):
            polygon_mesh.vectors[i][j] = vertices[f[j], :]

    # STLファイル出力
    polygon_mesh.save(TEMP_STL_FILE)
    
    # 修復
    CleanSTL()
    
def ViewSTL():
    # STLファイルの読み込み
    tempMesh = pv.read(TEMP_STL_FILE)

    # メッシュの表示
    p = pv.Plotter()
    p.add_axes()
    p.add_mesh(tempMesh)
    p.add_mesh(tempMesh, style='wireframe', color='black')
    p.show()

def CleanSTL():
    # 比較用に出力
    readMeshPyVista = pv.read(TEMP_STL_FILE)
    readMeshPyVista.save("output_raw.stl", binary=False)
    
    # メッシュの不整合を修復
    loadMesh = trimesh.load_mesh(TEMP_STL_FILE)
    
    # メッシュの法線が外を向いているかなど fix_winding, fix_inversionが実行
    trimesh.repair.fix_normals(loadMesh)
    with open(TEMP_STL_FILE, 'w') as f:
        f.write(export_stl_ascii(loadMesh))  # 比較用にASCII形式で出力

    # pymeshfixで修復
    pymeshfix.clean_from_file(TEMP_STL_FILE, TEMP_STL_FILE)

if __name__ == "__main__":
    if len(sys.argv) == 5:
        shapefilePath = sys.argv[1]
        shapeIndex = int(sys.argv[2])
        scaleFactor = int(sys.argv[3])
        zOffset = int(sys.argv[4])
        print("exist arguments")
    else:
        # debug
        # 国土数値情報 行政区域データ https://nlftp.mlit.go.jp/ksj/gml/datalist/KsjTmplt-N03-v3_1.html (accessed 2023.06.06)
        shapefilePath = r".\N03-20230101_17_GML\N03-23_17_230101.shp" 
        shapeIndex = 0
        scaleFactor = 200  # 読み込んだShapeの全体長を決める
        zOffset = 5
        print("debug")

    # shape to stl    
    shapeData = gpd.read_file(shapefilePath, encoding='cp932')

    # 国土数値情報 行政区域データを使う場合 行政区域コードでディゾルブしてポリゴンをマージ
    shapeDataDissolved = shapeData.dissolve(by='N03_007')
    # shapeDataDissolved.to_file("output.shp")  # 保存
    print(shapeDataDissolved["N03_004"])  # 市区町村名列
    
    polygons = shapeDataDissolved.geometry.values
    scaledPolygons = NormalizePolygons(polygons, scaleFactor)
    CreateAndSaveSTL(scaledPolygons, shapeIndex, zOffset)
    ViewSTL()
