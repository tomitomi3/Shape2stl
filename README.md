<img src="image\image_shape2stl.PNG" width="70%">

Converting Japanese Kanazawa city boundaries to STL file.
This is based on ESRI Japan 全国市区町村データ.
https://www.esrij.com/products/japan-shp/

# Shape2stl

This Python code reads polygons from a shapefile, converts them to 3D, and converts them to an STL file. I created this python code for the purpose of making a Japanese city puzzle.

Shapeファイルからポリゴン抽出を行い、Z方向に押し出して、3Dプリンタで使用できるSTLファイルに変換します。

## usage

> python shape2stl.py [shapefile path] [shapeIndex] [scaleFactor] [z offset]

* [shapefile path]
  * This argument specifies the path to the shapefile (.shp format).
* [shapeIndex]
  * This argument specifies an index to select a particular shape.
* [scaleFactor]
  * This argument specifies the value used to scale the polygons. All polygons are normalized from 0 to 1.
* [z offset]
  * This argument specifies the thickness (Z-direction offset). This value is the length of the extrusion in the Z direction.

## Example using this code

金沢市と津幡町

<img src="image\print_kanazawa_tsubata.JPG" width="30%">
