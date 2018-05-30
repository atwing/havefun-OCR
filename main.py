#!/usr/local/bin/python3
# -*- coding: utf-8 -*-
"""
OCR algorithm to read text from images/screenshots; for Empires & Puzzles war lists. To process multiple images use this bash script: "for i in {<number-range>}; do python3 main.py <path-to-images>/$i.png; done"
"""

"""
Tested with screenshot size: 1080 × 1920, PNG
Area of interest read with GIMP: 130, 560, 810, 830
Sub-margins x-axis splitting lines in name, number, name: 501, 578

TODO:
#- send tesseract output to excel sheet
#- use blue/red colored text to differentiate offense and defense
#- divide lines to three units: name, number, name
#    - read three units separately
(- accept folder as input to do OCR on image batch; conflicting with intermediate screen grabs for analysis during war)
- split function: prompt user if class UNKNOWN
"""

### Imports
import os
import sys
import cv2
import pdb
import numpy as np
import time
import csv
import argparse
os.environ["TESSDATA_PREFIX"] = "/opt/local/share/"
sys.path.insert(0, 'modules')

import pytesser

### Global variables
LEFT_CROP = 130 # left edge for image cropping 
RIGHT_CROP = 940
TOP_CROP = 560 # top edge for image cropping
# WIDTH_CROP = 810 # width for image cropping
HEIGHT_CROP = 49 # height of a line
LEFT_CUT_CROP = 501 # sub-margin after first name per line
RIGHT_CUT_CROP = 578 # sub-margin before second name per line

NUM_LINES = 17 # number of lines to read

# boundaries for filtering enemy AND ally colors
LBOUND_H = 0
LBOUND_S = 0
LBOUND_V = 50
UBOUND_H = 255
UBOUND_S = 100
UBOUND_V = 255
# boundaries for filtering ally color
COLOR_ALLIES = [104,56,240] # colors of text used for allies: 205,24,94; 209,21,94; 214,21,90 (!!! scale: 0-360, 0-100, 0-100)
RANGE_HUE = 10 # interval for color range: COLOR_ALLIES +/- RANGES
RANGE_SAT = 10
RANGE_VAL = 20

HIT_CLASS1 = "ALLY"
HIT_CLASS2 = "ENEMY"

# parser for command-line options, argument, subcommands
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("-w", "--write", help="Clear output file and write with new data. If not set, new data will be appended without clearing.",
                    action="store_true") #value True is assigned if option is specified
parser.add_argument("-s", "--split", help="Split output into two files based on hit class",
                    action="store_true")
parser.add_argument("input_image", help="Image file for text extraction",
                type=str)
args = parser.parse_args()

PATH_TO_OUTPUT = os.path.split(args.input_image)[0] + '/'

# Class declarations

### Function declarations

def crop(img, x, y, width, height):
    """ crops image down to relevant area
        img: nparray format
    """
    
    crop_img = img[y:y+height, x:x+width]
    # cv2.imshow("cropped", crop_img)
    # cv2.waitKey(0)
    return crop_img

def filter_color(img, lb_h, lb_s, lb_v, ub_h, ub_s, ub_v):
    """ filters a range of colors in HSV format
        img: nparray format
    """
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

    # define color range to filter
    l_bound = np.array([lb_h, lb_s, lb_v]) # hue, saturation, value
    u_bound = np.array([ub_h, ub_s, ub_v])

    mask = cv2.inRange(hsv,l_bound, u_bound)
    mask = cv2.bitwise_not(mask)
    res = cv2.bitwise_and(img, img, mask = mask)

    filter_img = mask
    return filter_img

def OCRreadline(img, *args):
    """ read line using OCR, separate with commas
        img: contains single line
    """

    left_edge = 0 # start from left edge
    top_edge = 0 # static!
    res_str = ""
    hit_class = ""
    nList = len(args)
    line_str = []
    i = 1

    for arg in args:
        width = arg
        # pdb.set_trace()
        sub_cropped_img = crop(img, left_edge, top_edge, width, img.shape[1])

        # extract relevant pixels based on color
        masked_img = filter_color(sub_cropped_img, LBOUND_H, LBOUND_S, LBOUND_V, UBOUND_H, UBOUND_S, UBOUND_V)
        # extract only one color group, e.g. allies
        lb_h = COLOR_ALLIES[0]-RANGE_HUE if COLOR_ALLIES[0]-RANGE_HUE>=0 else 0
        lb_s = COLOR_ALLIES[1]-RANGE_SAT if COLOR_ALLIES[1]-RANGE_SAT>=0 else 0
        lb_v = COLOR_ALLIES[2]-RANGE_VAL if COLOR_ALLIES[2]-RANGE_VAL>=0 else 0
        ub_h = COLOR_ALLIES[0]+RANGE_HUE if COLOR_ALLIES[0]+RANGE_HUE<=179 else 179
        ub_s = COLOR_ALLIES[1]+RANGE_SAT if COLOR_ALLIES[1]+RANGE_SAT<=255 else 255
        ub_v = COLOR_ALLIES[2]+RANGE_VAL if COLOR_ALLIES[2]+RANGE_VAL<=255 else 255
        # print(lb_h, lb_s, lb_v, ub_h, ub_s, ub_v)
        masked_img_single = filter_color(sub_cropped_img, lb_h, lb_s, lb_v, ub_h, ub_s, ub_v)

        # cv2.imshow("after filtering", preproc_img)
        # cv2.waitKey(500)
        cv2.imwrite( "tmp.png", masked_img);
        if i < 3 and np.any(masked_img_single != 255):
            hit_class = HIT_CLASS1
        elif i == 3 and np.any(masked_img_single != 255):
            hit_class = HIT_CLASS2

        cv2.imwrite( "tmp.png", masked_img)
        # cv2.imshow("current mask", masked_img)
        cv2.imshow("current mask", masked_img)
        cv2.waitKey(500)

        line_str.append(pytesser.image_file_to_string("tmp.png").rstrip("\n\r")) # remove newline at end of string)

        # TODO: if line_str empty, try with different setting; limit characters to single font type?

        # save entity
        # res_str += entity + ','
        
        # update left edge -> move to right
        left_edge += width

        i += 1

    if hit_class == "":
        # print("Color class unknown", end='')
        line_str.append("N/A")
    else:
        # print(hit_class, end='')
        line_str.append(hit_class)

    # # last iteration subroutine    
    # masked_img = crop(img, left_edge, top_edge, width, img.shape[1])
    # cv2.imwrite( "tmp.png", masked_img);
    # entity = pytesser.image_file_to_string("tmp.png").rstrip("\n\r") # remove newline at end of string

    # newline at end of image line
    # res_str = res_str.rstrip(',') + '\n'
    res_str = line_str

    print("{}".format(line_str))

    # pdb.set_trace()


    return line_str
    
def split_output(input_file, type1, type2):
    if args.write:
        out_allies = open(PATH_TO_OUTPUT + "allies.txt", 'w+')
    else:
        out_allies = open(PATH_TO_OUTPUT + "allies.txt", 'a+')
    writer_a = csv.writer(out_allies)
    if args.write:
        out_enemies = open(PATH_TO_OUTPUT + "enemies.txt", 'w+')
    else:
        out_enemies = open(PATH_TO_OUTPUT + "enemies.txt", 'a+')
    writer_e = csv.writer(out_enemies)
    for line in input_file:
        # pdb.set_trace()
        if line[3] == type1:
            # print("class ALLY")
            writer_a.writerow(line)
        elif line[3] == type2:
            # print("class ENEMY")
            writer_e.writerow(line)
        else:
            print("ERROR: class UNKNOWN")

def yes_or_no(question):
    reply = str(input(question+' (Y/n): ')).lower().strip()
    if reply == '':
        return True
    elif reply[0] == 'y':
        return True
    elif reply[0] == 'n':
        return False
    else:
        print("Invalid input. Type 'y', 'n' or leave blank for default 'Yes'")
        return yes_or_no(question)

def main():
    # read input image
    input_img = cv2.imread(args.input_image)
    print("Processing image file:", os.path.split(args.input_image)[1])
    name_outfile = os.path.splitext(os.path.split(args.input_image)[1])[0]
    if args.write:
        if not yes_or_no("If output files already exist, overwrite?"):
            print("No overwriting. Program exiting.")
            sys.exit(1)
        text_file = open(PATH_TO_OUTPUT + "output.txt", 'w+')
    else:
        text_file = open(PATH_TO_OUTPUT + "output.txt", 'a+')

    # writer for csv output file
    # writer = csv.writer(open(PATH_TO_OUTPUT + name_outfile + ".txt", 'a+'))
    writer = csv.writer(text_file)

    # set dimensions for cropping
    left_edge = LEFT_CROP
    top_edge = TOP_CROP
    width = RIGHT_CROP - LEFT_CROP
    height = HEIGHT_CROP
    cut1 = LEFT_CUT_CROP - LEFT_CROP # subtract to get width of first unit
    cut2 = RIGHT_CUT_CROP - LEFT_CUT_CROP # width of second/middle unit
    cut3 = RIGHT_CROP - RIGHT_CUT_CROP # right edge of crop

    print('### Tesseract output ###')

    # output file for text
    # text_file = open("output.txt", "w")
    
    # read line by line
    for i in range(NUM_LINES):
        ## preprocessing
        # crop input image and save back as image format
        cropped_img = crop(input_img, left_edge, top_edge, width, height)

        # pdb.set_trace()
        # by default language is eng, and page seg mode auto
        # txt = pytesser.image_file_to_string("tmp.png")

        cuts = (cut1, cut2, cut3)
        txt = OCRreadline(cropped_img, *cuts) # comma-separated line entries
    
        # print(txt, end='')
        # text_file.write(txt)
        writer.writerow(txt) # save into CSV output file

        # move top edge down by 'height'
        top_edge += height

    text_file.close()
    sys.exit(1)

if __name__ == '__main__':
    if args.split:
        with open(PATH_TO_OUTPUT + "output.txt", 'r') as text_file:
            reader = csv.reader(text_file)
            split_output(reader, HIT_CLASS1, HIT_CLASS2)
    else:
        main()