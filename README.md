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

- Example image header:

`    <entry timestamp="1304429991.248683820" time="2011 05  3 13:39:51.248">
        <capture_time>1304429990.583357625</capture_time>
        <auvstate>
            <altitude>14.234</altitude>
            <depth>0.171272</depth>
            <heading>76.0199</heading>
            <lat>2456.5694N</lat>
            <lon>08027.7486W</lon>
            <pitch>-6.45996</pitch>
            <roll>3.38379</roll>
            <surge>-0.220703</surge>
        </auvstate>
        <features>
            <brightness>0</brightness>
            <exposure>1.18323</exposure>
            <gain>0.14809</gain>
            <gamma>1</gamma>
            <shutter>0.00112784</shutter>
            <tilt>3.75</tilt>
            <white-balance_bu>89</white-balance_bu>
            <white-balance_rv>80</white-balance_rv>
            <zoom>0</zoom>
        </features>
        <filename>/var/iac/images/201105031339/frame000020_0.jpg</filename>
        <jpeg_quality>90</jpeg_quality>
        <thread_id>-1290048624</thread_id>
    </entry>`

Authors:
---------------

The developer of the tool is Andrew W Hill (@andrewxhill)

* Based on work by Val Schmidt to build KML from transect data.
