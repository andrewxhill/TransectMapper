#!/usr/bin/env python

__doc__='''
Python script to extract the metadata from transect images stored in a directory and output KML+JSON
Andrew W. Hill
Vizzuality
2011

Modified from Val Scmidt's script read_imagemetadata.py
Val Schmidt
CCOM/UNH
CSHEL/UDEL
2010

Modified from Eggert's script xmlEXimage_unix.py
'''
import os
import sys
import glob
import PIL.Image
import xml.etree.ElementTree as etree
import xml.dom.minidom
import string as s
import scipy as sci
import scipy.io as sio
import json
from math import radians, sqrt, pow, tan, sin, cos, pi, log, atan, exp

CAMERA_FIELD_OF_VIEW = 54.0 #DEGREES OF HORIZONTAL
IMAGE_WIDTH = 800 #pixels
IMAGE_HEIGHT = 600 #pixels
#THE OFFSETS OF THE CAMERA FROM THE LOCATION OF MEASUREMENT INSTRUMENTS IN METERS (float)#
CAMERA_OFFSET_X = 1.3
CAMERA_OFFSET_Y = 0.0

def handlelat(input):
    ''' 
    Convert latitude as formatting in message to decimal degrees
    '''
    hem = input[-1]
    deg = input[0:2]
    minute = input[2:-1]
    if hem == 'S':
        return - (s.atof(deg)+s.atof(minute)/60)
    return s.atof(deg) + s.atof(minute)/60
        
def handlelon(input):
    ''' 
    Convert longitude as formatting in message to decimal degrees
    '''
    hem = input[-1]
    deg = input[0:3]
    minute = input[3:-1]
    if hem == 'W':
        return - (s.atof(deg)+s.atof(minute)/60)
    return s.atof(deg) + s.atof(minute)/60

######################################################################
def ConvertLatLon(data):
    hem = data[-1]
    if hem in ('E', 'N'):
        mul = 1.0
    else:
        mul = -1.0
    try:
        number = float(data[:-1])
    except:
        return None
    deg = int(number/100)
    minutes = number - deg*100
    #deg = float(nextChild.data[0:-8])
    return (deg + minutes / 60.0)  * mul

class KML():
    def __init__(self):
        self.head = """<?xml version="1.0" encoding="utf-8"?>
                        <kml xmlns="http://www.opengis.net/kml/2.2">"""
        self.document = """<Document>"""
        self.close = """</Document></kml>"""
        self.entries = []
        
    def output(self):
        out = self.head
        out += self.document 
        for i in self.entries:
            out+=i
        out+= self.close
        return out
    
    def addentry(self,entry):
        self.entries.append(entry)

class GroundOverlay():
    def __init__(self, n, pitch, surge, altitude, latitude, longitude, roll, heading, f, draworder=1):
        self.n =  n
        self.pitch =  pitch
        self.surge =  surge
        self.altitude =  altitude
        self.latitude =  latitude
        self.longitude =  longitude
        self.roll =  roll
        self.heading =  heading
        self.rotation = -1 * self.heading if self.heading <=180 else 1*(360.0-self.heading)
        self.f = os.path.abspath(f)
        self.draworder = draworder
        
        #NOTE
        # - All locations are stored as offsets from the camera center in meters
        #   until it is reported at the end
        
        #TODO
        #   measure real depth of the aperature when image is taken
        
        
        #constants
        self.origin_x, self.origin_y = float(CAMERA_OFFSET_X), float(CAMERA_OFFSET_Y)
        
        self.field_of_view = float(CAMERA_FIELD_OF_VIEW)
        self.afield_of_view = radians(self.field_of_view)
        self.image_width_in_pixels = float(IMAGE_WIDTH)
        self.image_height_in_pixels = float(IMAGE_HEIGHT)
        
        #converted values
        self.aroll = radians(self.roll) #radians of roll
        self.apitch = radians(self.pitch) #radians of pitch
        self.aheading = radians(self.heading) #radians of heading
        self.mlat, self.mlon = self.LatLonToMeters(self.latitude,self.longitude)
        self.camera_height = self.altitude #in meters. TODO: might not be true
        
        self.image_center_offset = () #x, y in meters
        self.distance_to_center = None # in meters. new distance from camera to image center
        self.alt_to_distance()
        
        self.image_dimension_in_meters = () #w, h in meters
        self.fov_to_image_width()
        
        self.top_meters_from_origin = ()
        self.bottom_meters_from_origin = ()
        self.left_meters_from_origin = ()
        self.right_meters_from_origin = ()
        self.meter_offset_of_extents()
        
        #These coordinates are actually a step too far for Google Earth, as it wants an unrotated extent plus a rotation, this is extents after rotation
        self.top_coordinates = self.OffsetToLatLon(self.top_meters_from_origin[0], self.top_meters_from_origin[1])
        self.bottom_coordinates = self.OffsetToLatLon(self.bottom_meters_from_origin[0], self.bottom_meters_from_origin[1])
        self.left_coordinates = self.OffsetToLatLon(self.left_meters_from_origin[0], self.left_meters_from_origin[1])
        self.right_coordinates = self.OffsetToLatLon(self.right_meters_from_origin[0], self.right_meters_from_origin[1])
        
        #here we grab the dumbed down version for google earth
        self.bottom = self.origin_x + self.image_center_offset[0] + self.image_dimension_in_meters[0]/2
        self.right = self.origin_y + self.image_center_offset[1] - self.image_dimension_in_meters[1]/2
        
        self.top = self.origin_x + self.image_center_offset[0] - self.image_dimension_in_meters[0]/2
        self.left = self.origin_y + self.image_center_offset[1] + self.image_dimension_in_meters[1]/2
        
        self.south, self.east = self.OffsetToLatLon(self.bottom, self.right)
        self.north, self.west = self.OffsetToLatLon(self.top, self.left)
        
        self.json = {'rotated':{'top':    self.top_coordinates,
                                'bottom': self.bottom_coordinates,
                                'left': self.left_coordinates,
                                'right': self.right_coordinates,
                                'heading': self.heading
                               },
                     'unrotated':{'top': self.top,
                                  'bottom': self.bottom,
                                  'left': self.left,
                                  'right': self.right,
                                  'heading': self.heading,
                                  }
                    }
        
    def getkml(self):
        entry = """
        <GroundOverlay>
           <name>%s</name>
           <drawOrder>%s</drawOrder>
           <Icon>
              <href>%s</href>
           </Icon>
           <altitudeMode>clampToSeaFloor</altitudeMode>
           <LatLonBox>
              <north>%s</north>
              <south>%s</south>
              <east>%s</east>
              <west>%s</west>
              <rotation>%s</rotation>
           </LatLonBox>
        </GroundOverlay>
        """ % ( self.n, self.draworder, self.f, self.north, self.south, self.east, self.west, self.rotation )
        return entry
        
    def alt_to_distance(self):
        """Takes coords, altitude, roll, pitch, heading to determine where the 
               -  center : the latitude and longitude of the center of the image is
               -  distance : the meters of the verticy from aperature to center
        """
        #TODO
        #   - since Camera is actualy >1 meter ahead of the measurement device, we should actually
        #     calculate how pitch and roll change the altitude of the camera versus the measurement
        #     but we would need to know where the center of rotation for the sub is, blimey
        roll_offset_in_meters = tan(self.aroll) * self.camera_height
        pitch_offset_in_meters = tan(self.apitch) * self.camera_height
        radius_of_offset = sqrt(pow(roll_offset_in_meters,2) + pow(pitch_offset_in_meters,2))
        self.distance_to_center = sqrt( pow(radius_of_offset,2) + pow(self.camera_height,2))
        
        center_x = self.origin_x + radius_of_offset *  sin(self.aheading);
        center_y = self.origin_y + radius_of_offset * -cos(self.aheading);
        self.image_center_offset = (center_x,center_y)
        
    def fov_to_image_width(self):
        """Takes distance_to_center, field_of_view, and the image h/w ratio 
           to find the height/widht of the image in meters
        """
        width = 2.0 * (tan(self.afield_of_view/2) * self.distance_to_center)
        height = width * (self.image_height_in_pixels / self.image_width_in_pixels)
        
        self.image_dimension_in_meters = (width, height)
        
    def meter_offset_of_extents(self):
        """Taxes the offsets from origin(camera), the dimensions of the image, and the heading
           to find the top, bottom, left, and right extents of the image
        """
        
        top_x = (self.origin_x + self.image_center_offset[0]) + self.image_dimension_in_meters[1]/2 *  sin(self.aheading);
        top_y = (self.origin_y + self.image_center_offset[1]) + self.image_dimension_in_meters[1]/2 * -cos(self.aheading);
        
        bottom_x = (self.origin_x + self.image_center_offset[0]) + self.image_dimension_in_meters[1]/2 *  sin(self.aheading + pi);
        bottom_y = (self.origin_y + self.image_center_offset[1]) + self.image_dimension_in_meters[1]/2 * -cos(self.aheading + pi);
        
        left_x = (self.origin_x + self.image_center_offset[0]) + self.image_dimension_in_meters[0]/2 *  sin(self.aheading + 0.5*pi);
        left_y = (self.origin_y + self.image_center_offset[1]) + self.image_dimension_in_meters[0]/2 * -cos(self.aheading + 0.5*pi);
        
        right_x = (self.origin_x + self.image_center_offset[0]) + self.image_dimension_in_meters[0]/2 *  sin(self.aheading - 0.5*pi);
        right_y = (self.origin_y + self.image_center_offset[1]) + self.image_dimension_in_meters[0]/2 * -cos(self.aheading - 0.5*pi);
        
        
        self.top_meters_from_origin    = (top_x,top_y)
        self.bottom_meters_from_origin = (bottom_x,bottom_y)
        self.left_meters_from_origin   = (left_x,left_y)
        self.right_meters_from_origin  = (right_x,right_y)
    
    def LatLonToMeters(self, lat, lon):
        "Converts given lat/lon in WGS84 Datum to XY in Spherical Mercator EPSG:900913"

        shift = 2 * pi * 6378137 / 2.0
        
        mx = lon * shift / 180.0
        my = log( tan((90 + lat) * pi / 360.0 )) / (pi / 180.0)

        my = my * shift / 180.0
        return mx, my
        
    def OffsetToLatLon(self, mx, my ):
        "Converts XY point from Spherical Mercator EPSG:900913 to lat/lon in WGS84 Datum"
        mx = mx + self.mlat
        my = my + self.mlon
        
        shift = 2 * pi * 6378137 / 2.0
        
        lon = (mx / shift) * 180.0
        lat = (my / shift) * 180.0
        lat = 180 / pi * (2 * atan( exp( lat * pi / 180.0)) - pi / 2.0)
        return lat, lon
  
######################################################################
# Code that runs when this is this file is executed directly
######################################################################
if __name__ == '__main__':
    
    from optparse import OptionParser
    parser = OptionParser()
    parser.add_option("-d", "--directory",
                  action="store", type="string", dest="directory")
    parser.add_option("-o", "--output",
                  action="store", type="string", dest="outname", default="output")
    (options, args) = parser.parse_args()
    directory = options.directory
    outname = options.outname
    filenames = []
    filenames.extend(glob.glob(directory + '/*.jpg'))
    N = filenames.__len__();
    
    # Set up data stuctures
    # entry attribute:
    camera = {}
    camera['entrytime'] = sci.zeros((N,1),'double')

    # auvstate
    camera['lat'] = sci.zeros((N,1),'double')
    camera['lon'] = sci.zeros((N,1),'double')
    camera['altitude'] = sci.zeros((N,1),'double')
    camera['depth'] = sci.zeros((N,1),'double')
    camera['heading'] = sci.zeros((N,1),'double')
    camera['pitch'] = sci.zeros((N,1),'double')
    camera['roll'] = sci.zeros((N,1),'double')
    camera['surge'] = sci.zeros((N,1),'double')
    # capturetime
    camera['capture_time'] = sci.zeros((N,1),'double')
    # filename
    camera['filename'] = []
    # features
    camera['brightness'] = sci.zeros((N,1),'double')
    camera['exposure'] = sci.zeros((N,1),'double')
    camera['gain'] = sci.zeros((N,1),'double')
    camera['gamma'] = sci.zeros((N,1),'double')
    camera['shutter'] = sci.zeros((N,1),'double')
    camera['white_balance_bu'] = sci.zeros((N,1),'double')
    camera['white_balance_rv'] = sci.zeros((N,1),'double')
    # jpeg quality
    camera['jpeg_quality'] = sci.zeros((N,1),'double')
    camera['thread_id'] = sci.zeros((N,1),'double')

    # Initialize values to nans
    for key in camera.keys():
        if key is not 'filename':
            camera[key].fill(sci.nan)

    newnames = {'lat':'latitude',
                'lon':'longitude'}

            
    i = 0
    newdat = {}
    drawOrder = 100
    do = -1
    kml = KML()
    
    for f in filenames:
        out = {}
        n = f.split('/')[-1].replace('frame','').split('.')[0]
        n = int(n.split('_')[0])
        out['n'] = n
        #print "Reading file: " + f
        # Get the xml data in the header using PIL
        imagefile = PIL.Image.open(f)
        entry = imagefile.app['COM'].replace("white-balance","white_balance")
        # Parse it into a python object using ElementTree
        try:
            tree = etree.fromstring(entry)                
            tree_entries = tree.getchildren()
        except:
            print "Error reading header: " + f
            i = i+1
            continue

        for e in tree_entries:
            params = e.getiterator()

            for p in params:
                
                if camera.has_key(p.tag):
                    if p.tag in ['lat','lon']:
                        if p.tag == 'lat':
                            orig = handlelat(p.text)
                            out['latitude'] = orig
                        else: 
                            orig = handlelon(p.text)
                            out['longitude'] = orig
                    out[p.tag] = p.text
        
        e = GroundOverlay(n, float(out['pitch']), float(out['surge']), float(out['altitude']), float(out['latitude']), float(out['longitude']), float(out['roll']), float(out['heading']), f, draworder=drawOrder)
        if do == 0:
            drawOrder = 99
            do=1
        elif do == 1:
            drawOrder = 99
            do=2
        else:
            drawOrder = 100
            do = 0
        kml.addentry(e.getkml())
        out['overlay'] = e.json
        newdat[n] = out
        i=i+1
    kml_doc = kml.output()
    open(outname+'.kml',"w+").write(kml_doc)
    
    # rename stuff that needs renameing.    
    for key in camera.keys():
        if key not in newnames.keys():
            continue
        camera[newnames[key]] = camera[key]
        del camera[key]
        
    o = open(outname+".json", "w+")
    json.dump(newdat,o)





