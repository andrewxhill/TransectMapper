What is transect2overlay.py
---------------

transect2overlay.py is a python script to extract metadata from every image in a directory of images and create a KML of groundoverlays and a JSON file describing all the images. Importantly, transect2overlay.py was designed to use the positioning of an underwater camera to calculate the real-world position of the image on the ground. 

Why?
---------------

In our case we had transects of images taken across the sea floor. If we just use the coordinates of the camera at the time of image capture as the coordinate of each image we run into a few problems. Things like the pitch and the roll, as well as the rise and fall of the camera over time drastically changes the relationship of the lens position to the image positoin. This script tries to take care of that.

How to use it
---------------
- Modify the transect2overlay.py file and change the field of view and image dimension parameters to match your particular case.

- Run it via command line like:

		$ python transect2overlay.py -d {dirname} -o {name}

where:

* dirname - the directory with images belonging to the same transect

optional:

* name  - the name of file you wish to store {name}.kml and {name}.json stored in the same directory as transect2overlay.py

- Example:

		$ python transect2overlay.py -d ../data/20110504/files/images/201105042046 -o newkml
        
Authors:
---------------

The developer of the tool is Andrew W Hill (@andrewxhill)

* Based on work by Val Schmidt to build KML from transect data.
