<img src="image\image_shape2stl.PNG">

Converting Japanese Kanazawa city boundaries to STL file.
This is based on ESRI Japan 全国市区町村データ.
https://www.esrij.com/products/japan-shp/

# Shape2stl

This Python code reads polygons from a shapefile, converts them to 3D, and converts them to an STL file. I created this python code for the purpose of making a Japanese city puzzle.

## usage

> python shape2stl.py [shapefile path] [shapeIndex] [scaleFactor] [z offset]
