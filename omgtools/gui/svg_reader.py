#!/usr/bin/python

from ..environment import Environment
from ..basics.shape import Circle, Rectangle

import numpy as np
from xml.etree.ElementTree import ElementTree
import re
import sys, os
from matplotlib import pyplot as plt

class SVGReader(object):
    def __init__(self):
        # Load xml-tree
        self.ns = 'http://www.w3.org/2000/svg' # XML namespace
        self.et = ElementTree()
        self.svgpath = None

    def init(self, data):
        self.data = data
        self.tree = self.et.parse(data)
        if (self.tree.get('width')[-2:] in ['mm', 'px']):  # units millimeter or pixels
            viewbox = self.tree.get('viewBox').split(' ')
            xmin, ymin, xmax, ymax = viewbox
            if (self.tree.get('width')[-2:] is 'mm'):
                self.width_px = float(xmax) - float(xmin)
                self.height_px = float(ymax) - float(ymin)
                # self.width_mm = float(self.tree.get('width')[:-2])  # not necessary, can be obtained from meter_to_pixel and px
                # self.height_mm = float(self.tree.get('height')[:-2])
                self.meter_to_pixel = self.width_px/float(self.tree.get('width')[:-2])
            else: # units px
                self.width_px = float(xmax) - float(xmin)
                self.height_px = float(ymax) - float(ymin)
        else:
            # if no unit mentioned, it is px
            self.width_px = float(self.tree.get('width'))  # get width from svg
            self.height_px = float(self.tree.get('height'))  # get height from svg
        self.obstacles = []

    def convert_path_to_points(self):
        
        # Find svg-paths, describing the shapes
        try:
            self.svgpath = self.tree.findall("{%s}path" %self.ns)  # Search for the word path in the outer branch of the SVG-file.
            if not self.svgpath:
                self.svgpath = self.tree.find("{%s}g" %self.ns).findall("{%s}path" %self.ns)  # If not yet found, search for the word path in the next branch
            if not self.svgpath:
                self.svgpath = self.tree.find("{%s}g" %self.ns).find("{%s}g" %self.ns).findall("{%s}path" %self.ns)  # If not yet found, search for the word path in the next branch
        except:  # error occured, e.g. no <g/> found, this is possible when you only have basic shapes
            print 'No shapes found which are described by a path, probably you only have basic shapes'
            return
        if not self.svgpath:  # no path found, this is possible when you only have basic shapes
            print 'No shapes found which are described by a path, probably you only have basic shapes'
            return

        self.n_paths = len(self.svgpath)  # number of paths which build up the figure

        #Initialize output file
        counter = 0
        # Loop over paths
        while counter < self.n_paths:
            lines = re.findall('[MCmc][\s.,0-9-]+', self.svgpath[counter].get('d')) # look for all MCmc with a number behind it, line runs until a space or minus sign is found
            points = []
            for line in lines:
                if line:
                    # line [0] contains Mx,y, the startpoint
                    test1=line[1:].replace(","," ")  # replace comma by: space 
                    test2 = test1.replace("-"," -")  # replace minus sign by: space minus 
                    test3 = test2.replace("c"," c ")  # replace c by: space c space
                    newpoints = np.array(map(eval, test3.strip().split(' ')))  # splits the line at each space, to create separate points
                    if line[0] == 'c':  # lower case c means relative coordinates, upper case C is absolute coordinates
                        newpoints[0:6:2] = newpoints[0:6:2] + points[-2]  # relative to absolute coordinates for x
                        newpoints[1:6:2] = newpoints[1:6:2] + points[-1]  # relative to absolute coordinates for y
                    # for the first line (Mx,y) there is no 'c', so the starting point (x,y) is added to points in the first iteration
                    points.extend(newpoints)  # add newpoints to points
            counter += 1
            # Save points to file
            f = open("environment.txt", "a")
            f.write( "path_"+ str(counter) + "="+ str(np.array(points)) + "\n" )
            f.close() 

    def convert_basic_shapes(self):
        
        # Code for basic shapes <circle> and <rect>

        # Find svg-paths, describing the shapes
        try:
            self.rectangles = self.tree.findall("{%s}rect" %self.ns)  # Search for the word rect in the outer branch of the SVG-file.
            if not self.rectangles:
                self.rectangles = self.tree.find("{%s}g" %self.ns).findall("{%s}rect" %self.ns)  # If not yet found, search for the word rect in the next branch
            if not self.rectangles:
                self.rectangles = self.tree.find("{%s}g" %self.ns).find("{%s}g" %self.ns).findall("{%s}rect" %self.ns)  # If not yet found, search for the word rect in the next branch
            self.n_rect = len(self.rectangles)  # number of paths which build up the figure
            if self.n_rect == 0:
                print 'No rectangles found'
        except:
            print 'No shapes found which are described by a rect'


        # Find svg-paths, describing the shapes
        try:
            self.circles = self.tree.findall("{%s}circle" %self.ns)  # Search for the word circ in the outer branch of the SVG-file.
            if not self.circles:
                self.circles = self.tree.find("{%s}g" %self.ns).findall("{%s}circle" %self.ns)  # If not yet found, search for the word circ in the next branch
            if not self.circles:
                self.circles = self.tree.find("{%s}g" %self.ns).find("{%s}g" %self.ns).findall("{%s}circle" %self.ns)  # If not yet found, search for the word circ in the next branch
            self.n_circ = len(self.circles)  # number of paths which build up the figure
            if self.n_circ == 0:
                print 'No circles found'
        except:
            print 'No shapes found which are described by a circle'

        for rectangle in self.rectangles:
            obstacle = {}
            obstacle['shape'] = 'rectangle'
            pos = [float(rectangle.get('x')), float(rectangle.get('y'))]  # Note: [x,y] is the top left corner
            # axis are placed in the top left corner and point to the right(x) and downward(y)
            obstacle['pos'] = [pos[0]+float(rectangle.get('width'))*0.5, pos[1]+float(rectangle.get('height'))*0.5]
            obstacle['width'] = float(rectangle.get('width'))
            obstacle['height'] = float(rectangle.get('height'))
            obstacle['velocity'] = [0, 0]
            obstacle['bounce'] = False
            self.obstacles.append(obstacle)

        for circle in self.circles:
            obstacle = {}
            obstacle['shape'] = 'circle'
            obstacle['pos'] = [float(circle.get('cx')), float(circle.get('cy'))]  # Note: [x,y] is the top left corner
            obstacle['radius'] = float(circle.get('r'))
            obstacle['velocity'] = [0, 0]
            obstacle['bounce'] = False
            self.obstacles.append(obstacle)

        # Code for Bezier expression
        # how represent a circle in bezier?
        # for rectangle check on straight lines --> is control point on line between start and end?

    def convert_lines(self):
        # Code for basic shapes <line> and <polyline>

        # Find svg-polylines
        # example: <polyline fill="none" stroke="#333333" stroke-width="10" points="25.41,40.983 25.41,258.197 414.754,258.197 "/>
        try: 
            self.polylines = self.tree.findall("{%s}polyline" %self.ns)  # Search for the word circ in the outer branch of the SVG-file.
            if not self.polylines:
                self.polylines = self.tree.find("{%s}g" %self.ns).findall("{%s}polyline" %self.ns)  # If not yet found, search for the word circ in the next branch
            if not self.polylines:
                self.polylines = self.tree.find("{%s}g" %self.ns).find("{%s}g" %self.ns).findall("{%s}polyline" %self.ns)  # If not yet found, search for the word circ in the next branch
            self.n_polylines = len(self.polylines)  # number of paths which build up the figure
            if self.n_polylines == 0:
                print 'No polylines found'
        except:
            print 'No shapes found which are described by a polyline'

        # Find svg-lines
        # example: <line fill="none" stroke="#333333" stroke-width="10" x1="25.41" y1="174.59" x2="69.672" y2="174.59"/>
        try: 
            self.lines = self.tree.findall("{%s}line" %self.ns)  # Search for the word line in the outer branch of the SVG-file.
            if not self.lines:
                self.lines = self.tree.find("{%s}g" %self.ns).findall("{%s}line" %self.ns)  # If not yet found, search for the word line in the next branch
            if not self.lines:
                self.lines = self.tree.find("{%s}g" %self.ns).find("{%s}g" %self.ns).findall("{%s}line" %self.ns)  # If not yet found, search for the word line in the next branch
            self.n_lines = len(self.lines)  # number of paths which build up the figure
            if self.n_lines == 0:
                print 'No lines found'
        except:
            print 'No shapes found which are described by a line'

        for polyline in self.polylines:
            try:
                stroke_width = float(polyline.get('stroke-width'))  # stroke-width given as basic element
            except:  # stroke-width wrapped in style element
                style = polyline.get('style').split(';')
                for element in style:
                    if 'stroke-width' in element:
                        stroke_width = float(element.split(':')[1])
            vertices = polyline.get('points').split(' ')
            vertices[:] = (v for v in vertices if v != '')  # remove all empty strings
            vertices = np.array(map(eval, vertices))  # gives array of arrays [[x,y],[],...]
            vertices += self.transform

            # make rectangle of each vertex couple
            for l in range(len(vertices)-1):
                obstacle = {}
                obstacle['shape'] = 'rectangle'
                obstacle['velocity'] = [0, 0]
                obstacle['bounce'] = False

                # Note: to avoid explicitly checking if the line goes from
                # left to right / right to left
                # bottom to top / top to bottom
                # we use w and h separate from obstacle width and height
                line = np.array(vertices[l+1]) - np.array(vertices[l])
                if line[0] == 0:  # vertical line
                    obstacle['width'] =  stroke_width
                    obstacle['height'] = abs(line[1])
                    h = line[1]
                    w = cmp(h,0)*stroke_width  # give stroke_width same sign as h
                elif line[1] == 0:  # horizontal line
                    obstacle['width'] = abs(line[0])
                    obstacle['height'] = stroke_width
                    w = line[0]
                    h = cmp(w,0)*stroke_width  # give stroke_width same sign as w
                else:
                    raise RuntimeError('Diagonal lines are not yet supported')
                obstacle['pos'] = [vertices[l][0] + w*0.5, vertices[l][1] + h*0.5]
                self.obstacles.append(obstacle)

        for line in self.lines:
            obstacle = {}
            obstacle['shape'] = 'rectangle'
            obstacle['velocity'] = [0, 0]
            obstacle['bounce'] = False

            try:
                stroke_width = float(line.get('stroke-width'))  # stroke-width given as basic element
            except:  # stroke-width wrapped in style element
                style = line.get('style').split(';')
                for element in style:
                    if 'stroke-width' in element:
                        stroke_width = float(element.split(':')[1])
            x1, y1 = float(line.get('x1')), float(line.get('y1'))
            x2, y2 = float(line.get('x2')), float(line.get('y2'))
            # add transform
            x1 += self.transform[0]
            y1 += self.transform[1]
            x2 += self.transform[0]
            y2 += self.transform[1]
            if x1 == x2:  # vertical line
                obstacle['width'] =  stroke_width
                obstacle['height'] = abs(y2-y1)
                h = y2-y1  # signed value
                w = cmp(h,0)*stroke_width
            elif y1 == y2:  # horizontal line
                obstacle['width'] = abs(x2-x1)
                obstacle['height'] = stroke_width
                w = x2-x1  # signed value
                h = cmp(w,0)*stroke_width
            else:
                raise RuntimeError('Diagonal lines are not yet supported')

            # don't use width and height since then you have to check if x1 > x2 etc,
            # to decide if the line goes from left to right or the other way around
            obstacle['pos'] = [x1 + w*0.5, y1 + h*0.5]
            self.obstacles.append(obstacle)


    def reconstruct(self, file):
        points = []
        with open(file, "r") as f:
            for line in f:
                for word in line.split(' '):
                    if (word != ', ' and word != ',  ' and word != '' and word != ' '):
                        points.append(word)
        f.close() 
        newpoints = []
        for point in points:
            if point[-1:] == '\n':
                point = point[:-1]
            if point[-1:] == ']':
                point = point[:-1]
            if point[0] != 'p':
                newpoints.append(point)
        x = []
        y = []
        for i in range(0,len(newpoints),2):
            x.append(newpoints[i])
            y.append(newpoints[i+1])
        
        plt.plot(x,y)
        plt.show()

    def build_environment(self):

        self.convert_basic_shapes()  # gives self.rects and self.circs 
        self.convert_path_to_points()  # completes self.rects and self.circs with shapes defined by path
        # if you found some paths, call function to transform them to an obstacle
        # e.g. rectangle or circle and place add it to self.obstacles

        # now self.obstacles is filled

# if __name__ == '__main__':

#     args = sys.argv
#     args[0] = args[0].replace("/",os.sep)
#     data = args[1]

#     reader = SVGReader()
#     reader.init(data)
#     # reader.reconstruct(data)
#     # reader.convert_path_to_points(data)
#     reader.build_environment()