#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# IFF SDK samples (https://mr-te.ch/iff-sdk) are licensed under MIT License.
#
# Copyright (c) 2022-2025 MRTech SK, s.r.o.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

###############################################################
# Application name: Coloric
# Application allows easily build DCP profile for defined target and illuminant.
###############################################################
import tkinter as tk
from tkinter import *  
from tkinter import filedialog
from tkinter import messagebox
import math
from PIL import Image, ImageTk
from colormath.color_objects import sRGBColor,LabColor, XYZColor
from colormath.color_conversions import convert_color
import datetime
import os
import sys, getopt
import json
import shutil
import threading
import time
from enum import Enum
import cv2
import numpy as np


# Structures and Classes
#---------------------------------------------------
class CPoint:
    def __init__(self, x = 0, y = 0):
        self.x = x
        self.y = y

class CTetragonPoints:
    def __init__(self):
        self.lt = CPoint()
        self.rt = CPoint()
        self.rb = CPoint()
        self.lb = CPoint()

class CTetragonLines:
    def __init__(self):
        self.left = None
        self.right = None
        self.top = None
        self.bottom = None

class CCorner:
    def __init__(self):
        self.line1 = None
        self.line2 = None                

class CFrame:
    def __init__(self):
        self.tetra = CTetragonPoints()  
        self.start = CPoint()
        self.stop = CPoint() 
        self.rectangle = None

class CGrid:
    def __init__(self):
        self.frame = CFrame()
        self.lt_frame_corner = CCorner()
        self.rt_frame_corner = CCorner()
        self.rb_frame_corner = CCorner()
        self.lb_frame_corner = CCorner()
        self.lt_circle = None
        self.rt_circle = None
        self.rb_circle = None
        self.lb_circle = None 
        self.start_point = 0
    def delete_objects(self, canvas):
        if self.lt_frame_corner.line1 != None:
            canvas.delete(self.lt_frame_corner.line1)  
        if self.lt_frame_corner.line2 != None:
            canvas.delete(self.lt_frame_corner.line2) 
        if self.rt_frame_corner.line1 != None:
            canvas.delete(self.rt_frame_corner.line1)  
        if self.rt_frame_corner.line2 != None:
            canvas.delete(self.rt_frame_corner.line2) 
        if self.rb_frame_corner.line1 != None:
            canvas.delete(self.rb_frame_corner.line1)  
        if self.rb_frame_corner.line2 != None:
            canvas.delete(self.rb_frame_corner.line2) 
        if self.lb_frame_corner.line1 != None:
            canvas.delete(self.lb_frame_corner.line1)  
        if self.lb_frame_corner.line2 != None:
            canvas.delete(self.lb_frame_corner.line2) 
        if self.lt_circle != None:
            canvas.delete(self.lt_circle)  
        if self.rt_circle != None:
            canvas.delete(self.rt_circle)  
        if self.rb_circle != None:
            canvas.delete(self.rb_circle)  
        if self.lb_circle != None:
            canvas.delete(self.lb_circle)                                    

class CSpace_enum(Enum):
    C_XYZ = 0,
    C_LAB = 1          

class CGridPatches:
    def __init__(self, cht):
        #should be checked type of grid/target, for now as default will be used Macbeth ColorChecker 24 patches
        self.columns = cht.columns
        self.rows = cht.rows
        self.number_patches = self.columns * self.rows  
        self.patches = [CTetragonPoints() for i in range(self.number_patches)]  
        self.patches_lines = [CTetragonLines() for i in range(self.number_patches)]
        self.patches_triangles = [None for i in range(self.number_patches)]
        self.patches_colors = [] 
    def ColorCheckerPatches(self, cht):
        step_x = cht.xi / cht.grid_width
        step_y = cht.yi / cht.grid_height
        patch_width = (cht.w - 2 * cht.shrink) / (2 * cht.grid_width)
        patch_height = (cht.h - 2 * cht.shrink) / (2 * cht.grid_height)
        c_offs_x = (cht.x0 - cht.feducials.lt.x + cht.w / 2) / cht.grid_width
        c_offs_y = (cht.y0 - cht.feducials.lt.y + cht.h / 2) / cht.grid_height
        for y in range(self.rows):
            for x in range(self.columns):
                self.patches[y * self.columns + x].lt.x = c_offs_x + step_x * x - patch_width
                self.patches[y * self.columns + x].lt.y = c_offs_y + step_y * y - patch_height
                self.patches[y * self.columns + x].rt.x = c_offs_x + step_x * x + patch_width
                self.patches[y * self.columns + x].rt.y = c_offs_y + step_y * y - patch_height
                self.patches[y * self.columns + x].rb.x = c_offs_x + step_x * x + patch_width
                self.patches[y * self.columns + x].rb.y = c_offs_y + step_y * y + patch_height
                self.patches[y * self.columns + x].lb.x = c_offs_x + step_x * x - patch_width
                self.patches[y * self.columns + x].lb.y = c_offs_y + step_y * y + patch_height

class Ccht:
    def __init__(self):
        self.space = 0
        self.columns = 0
        self.rows = 0
        self.number_of_patches = 0
        self.shrink = 1.0
        self.patches_rgb = []
        self.grid_patches = None
        self.w = 0
        self.h = 0
        self.x0 = 0
        self.y0 = 0
        self.xi = 0
        self.yi = 0
        self.grid_width = 0
        self.grid_height = 0
        self.feducials = CTetragonPoints()
    def Open_cht(self, filename):
        try:
            with open(filename,"r") as cht:
                #searching for BOXES  
                expected = False 
                columns = 1
                rows = 1
                boxes = False
                x_or_y = False 
                for line in cht:
                    if len(line) <= 1: continue 
                    
                    if line.find("BOXES") > -1:
                        boxes = True
                    if boxes:    
                        T = line.split()
                        if len(T) == 0:
                            continue
                        xy = False
                        if T[0] == "F":
                            #fiducials as T[3],...T[10]
                            self.feducials.lt.x = float(T[3])
                            self.feducials.lt.y = float(T[4])
                            self.feducials.rt.x = float(T[5])
                            self.feducials.rt.y = float(T[6])
                            self.feducials.rb.x = float(T[7])
                            self.feducials.rb.y = float(T[8])
                            self.feducials.lb.x = float(T[9])
                            self.feducials.lb.y = float(T[10])
                            self.grid_width = math.sqrt((float(T[5]) - float(T[3])) * (float(T[5]) - float(T[3])) + (float(T[6]) - float(T[4])) * (float(T[6]) - float(T[4])))
                            self.grid_height = math.sqrt((float(T[9]) - float(T[3])) * (float(T[9]) - float(T[3])) + (float(T[10]) - float(T[4])) * (float(T[10]) - float(T[4])))
                        elif T[0] == "X" and len(T[2]) == 1:
                            #tweezers, should be added parsing
                            self.rows = int(T[4])
                            self.columns = ord(T[2]) - 64
                            x_or_y = True
                            xy = True
                        elif T[0] == "Y" and len(T[4]) == 1:
                            #tweezers, should be added parsing
                            self.columns = int(T[2])
                            self.rows = ord(T[4]) - 64
                            x_or_y = False
                            xy = True
                        else:
                            #"Parse error"
                            pass
                        if xy:
                            self.w = float(T[5])
                            self.h = float(T[6])
                            self.x0 = float(T[7])
                            self.y0 = float(T[8])
                            self.xi = float(T[9])
                            self.yi = float(T[10])   
                    #searching for BOX_SHRINK    
                    if line.find("BOX_SHRINK") > -1:
                        self.shrink = float(line.split()[1])
                    #searching for EXPECTED    
                    if line.find("EXPECTED") > -1:
                        T = line.split()
                        if T[1] == "XYZ":
                            self.space = CSpace_enum.C_XYZ
                        if T[1] == "LAB":
                            self.space = CSpace_enum.C_LAB 
                        self.number_of_patches = int(T[2])  
                        self.patches_rgb.clear()
                        self.patches_rgb = [[0.0, 0.0, 0.0] for i in range(self.columns * self.rows)] 
                        expected = True 
                    #print(expected , self.columns , self.rows , self.number_of_patches, self.number_of_patches == (self.columns * self.rows))    
                    if expected and self.columns and self.rows:
                        T = line.split()
                        if x_or_y:
                            s = chr(65 + (columns - 1)) + str(rows)
                        else:    
                            s = chr(65 + (rows - 1)) + str(columns)
                        #print(T[0], s, columns, rows, self.columns, self.rows)
                        if T[0] == s:
                            color_found = True
                            if self.space == CSpace_enum.C_XYZ:
                                space = XYZColor(*[component/100 for component in [float(T[1]), float(T[2]), float(T[3])]])
                            else:
                                space = LABColor(*[component/100 for component in [float(T[1]), float(T[2]), float(T[3])]])    
                            rgb = convert_color(space, sRGBColor)
                            rgb_list = [255*color for color in rgb.get_value_tuple()]
                            self.patches_rgb[(rows - 1) * self.columns + (columns - 1)] = rgb_list
                            if x_or_y:
                                rows += 1
                                if rows > self.rows:
                                    rows = 1
                                    columns += 1
                            else:
                                columns += 1
                                if columns > self.columns:
                                    columns = 1
                                    rows += 1  
            if self.grid_patches != None: 
                del self.grid_patches
            if  self.columns and self.rows:   
                self.grid_patches = CGridPatches(self)
                self.grid_patches.ColorCheckerPatches(self)
                for i in range(self.columns * self.rows):
                    if len(self.patches_rgb) == 0:
                        l = "#FFFFFF" 
                    else:    
                        l = "#{}{}{}".format(hex(min(255, int(self.patches_rgb[i][0]))).lstrip("0x").zfill(2).upper(), hex(min(255, int(self.patches_rgb[i][1]))).lstrip("0x").zfill(2).upper(), hex(min(255, int(self.patches_rgb[i][2]))).lstrip("0x").zfill(2).upper())
                    self.grid_patches.patches_colors.append(l)
            return 0        
        except OSError as error: 
            messagebox.showwarning(title='Error', message=error)
            return 1
        return 0    

class CButtons_enum(Enum):
    OPEN_IMAGE = 0
    OPEN_WB = 1
    SAVE_IMAGE = 2
    GENERATE = 3
    SET_CROP = 4
    CROP = 5
    OPEN_CHT = 6
    SET_GRID = 7
              
class CButtons():
    def __init__(self, use_buttons):
        self.use_buttons = use_buttons 
        self.Group = None
        self.buttons_array = []
        if app.use_buttons == True:
            self.Group = LabelFrame(root, text = "")
            self.Group.pack(side=RIGHT)

            self.buttons_array.append(Button(self.Group, text="Open Image", command= OpenImageButtonClick))
            self.buttons_array[CButtons_enum.OPEN_IMAGE.value].pack(side=TOP, fill="x")
            self.buttons_array.append(Button(self.Group, text="Open White Balance", command= OpenWbButtonClick, state=DISABLED))
            self.buttons_array[CButtons_enum.OPEN_WB.value].pack(fill="x")
            self.buttons_array.append(Button(self.Group, text="Save Image", command= SaveImageButtonClick, state=DISABLED))
            self.buttons_array[CButtons_enum.SAVE_IMAGE.value].pack(fill="x")
            self.buttons_array.append(Button(self.Group, text="Generate", command= SaveFilesButtonClick, state=DISABLED))
            self.buttons_array[CButtons_enum.GENERATE.value].pack(fill="x")
            self.buttons_array.append(Button(self.Group, text="Set Cropping", command= SetCropAreaButtonClick, state=DISABLED))
            self.buttons_array[CButtons_enum.SET_CROP.value].pack(fill="x")
            self.buttons_array.append(Button(self.Group, text="Crop", command= DoCropButtonClick, state=DISABLED))
            self.buttons_array[CButtons_enum.CROP.value].pack(fill="x")
            self.buttons_array.append(Button(self.Group, text="Open .cht", command= OpenCHTButtonClick, state=DISABLED))
            self.buttons_array[CButtons_enum.OPEN_CHT.value].pack(fill="x")
            self.buttons_array.append(Button(self.Group, text="Set Grid", command= SetGridAreaButtonClick, state=DISABLED))
            self.buttons_array[CButtons_enum.SET_GRID.value].pack(fill="x")  
    def SetButtonState(self, button, state):
        if self.use_buttons:
            self.buttons_array[button]['state'] = state 

class CConfiguration():
    def __init__(self):
        self.input_cht_file = ""
        self.input_cie_file = ""
        self.output_directory = ""
        self.output_image_file = "Image.tif"
        self.feducial_marks_file = "FiducialMarks.txt"
        self.output_generate_file = ""
        self.scanin = ""
        self.dcamprof = ""
        self.dcamprof_opt_json = "make-profile"
        self.dcamprof_opt_dcp = "make-dcp"
        self.output_ti3_file = "Image.ti3"
        self.output_json_file = "Image.json"
        self.calibration_illuminant = "D50"
        self.output_dcp_file = "Image.dcp"
        self.unique_camera_name = "Camera"
        self.profile_name = "Profile"
        self.number_of_crops = 1
        self.lable_font = "Arial"
        self.label_font_size = 14
        self.folder_separator = os.sep
        self.executor = "{}" if os.name == 'nt' else "sh -exc .\\ {}"
        self.max_process_image_width = 2048
        self.max_process_image_height = 2048

        self.config_file = None

    def ParseConfigFile(self, config_file=None):
        self.config_file = config_file
        if self.config_file != None:
            try:
                with open(self.config_file, 'r+') as f:
                    file_content = f.read()
                    content = json.loads(file_content)
                    if "input cht file" in content:
                        self.input_cht_file = content["input cht file"]
                    if "input cie file" in content:
                        self.input_cie_file = content["input cie file"]
                    if "output directory" in content:
                        self.output_directory = content["output directory"]
                    if "output image file" in content:
                        self.output_image_file = content["output image file"]  
                    if "feducial marks file" in content:
                        self.feducial_marks_file = content["feducial marks file"]  
                    if "output generate file" in content:
                        self.output_generate_file = content["output generate file"]  
                    if "scanin" in content:
                        self.scanin = content["scanin"]  
                    if "dcamprof" in content:
                        self.dcamprof = content["dcamprof"]  
                    if "dcamprof opt json" in content:
                        self.dcamprof_opt_json = content["dcamprof opt json"]  
                    if "dcamprof opt dcp" in content:
                        self.dcamprof_opt_dcp = content["dcamprof opt dcp"]          
                    if "output ti3 file" in content:
                        self.output_ti3_file = content["output ti3 file"]    
                    if "output json file" in content:
                        self.output_json_file = content["output json file"]
                    if "calibration illuminant" in content:
                        self.calibration_illuminant = content["calibration illuminant"]    
                    if "output dcp file" in content:
                        self.output_dcp_file = content["output dcp file"]
                    if "unique camera name" in content:
                        self.unique_camera_name = content["unique camera name"]
                    if "profile name" in content:
                        self.profile_name = content["profile name"]  
                    if "number of crops" in content:
                        self.number_of_crops = int(content["number of crops"]) 
                        if self.number_of_crops < 0:
                            self.number_of_crops = 0
                    if "label font" in content:
                        self.label_font = content["label font"]  
                    if "label font size" in content:
                        self.label_font_size = int(content["label font size"])   
                    if "folder separator" in content:
                        self.folder_separator = content["folder separator"]
                    if "executor" in content:
                        self.executor = content["executor"] 
                    if "max process image width" in content:
                        self.max_process_image_width = int(content["max process image width"]) 
                    if "max process image height" in content:
                        self.max_process_image_height = int(content["max process image height"])  
                    return 0    
            except OSError as error: 
                messagebox.showwarning(title='Error', message=error)
                return 1
        return 1        
       
class CCornerPoints_enum(Enum):
    POINT_LT = 0
    POINT_RT = 1
    POINT_RB = 2
    POINT_LB = 3

class CApp():
    def __init__(self, root):
        self.root = root
        self.root.geometry('%dx%d+0+0' % (int(self.root.winfo_screenwidth()), int(self.root.winfo_screenheight())))
        self.root.configure(bg="Black")
        try:
            self.root.state("zoomed") #doesn't work on Linux
        except:
            pass
        self.root.title("Coloric")

        self.use_buttons = False

        if self.use_buttons == False:
            self.label = Label(self.root, text='Application initialization', anchor=CENTER, font=("Arial", 14), height=3, bg="Black", fg="White")
            self.label.grid(row=0, sticky="nsew")
            self.canvas = tk.Canvas(self.root, bg="Black", width=int(self.root.winfo_screenwidth()), height=(int(self.root.winfo_screenheight())-self.label.winfo_height()))
            self.canvas.grid(row=1, sticky="nsew")
        else:
            self.canvas = tk.Canvas(root, bg="Black")
            self.canvas.pack(side=LEFT, fill=BOTH, expand=True)    

        self.croppedTestImageTk = None
        self.saveCroppedTestImageTk = None
        self.resizedTestImage = None
        self.resizedTestImageTk = None
        self.cv2Image = None

        self.buttons = None
        self.image_id = None
        self.proportion = 1
        self.proportion_crop_init = 1
        self.proportion_grid_init = 1
        self.line_width = 2
        self.background_id = None

        self.DEFINE_SEARCH_RADIUS = 12

        self.start_crop_rect = False
        self.draw_crop = False
        self.start_grid_rect = False
        self.draw_grid = False

        self.crop_frame = CFrame()

        self.grid = CGrid()

        self.cht = Ccht()

        self.Input_image_file = None
        self.Input_wb_file = None
        self.Input_config_file = None

        self.wb_kr = 1.0
        self.wb_kg = 1.0
        self.wb_kb = 1.0
        self.gamma = 2.2

        self.mutex = threading.Lock()
        self.thread_handle = None
        self.finish_thread = False

        self.config = None

        self.found_point_id = 0
        self.point_found = False
        self.setting_grid = False 

        self.proc_exec = False
 
# Init
#---------------------------------------------------
root = tk.Tk()

app = CApp(root)

# Fuctions
#---------------------------------------------------
###################################################
# Opens input image file
# file_name - Path and name of image to open
###################################################
def OpenImageFile(file_name):
    if file_name[-3:] == 'tif' or file_name[-4:] == 'tiff':
        app.saveCroppedTestImageTk = Image.open(file_name)
        app.cv2Image = cv2.imread(file_name, -1)
    else:   
        messagebox.showwarning(title='Error', message='Not supported image format')
        return 1

    coeff = 1    
    if app.config.max_process_image_width < app.saveCroppedTestImageTk.width or app.config.max_process_image_height < app.saveCroppedTestImageTk.height:
        if app.saveCroppedTestImageTk.width > app.saveCroppedTestImageTk.height:
            coeff = app.config.max_process_image_width / app.saveCroppedTestImageTk.width 
        else:
            coeff = app.config.max_process_image_height / app.saveCroppedTestImageTk.height    
    if coeff != 1:
        if app.cv2Image.dtype == np.uint16:  
            app.cv2Image = cv2.resize(app.cv2Image, (int(app.saveCroppedTestImageTk.width * coeff), int(app.saveCroppedTestImageTk.height * coeff)), interpolation = cv2.INTER_AREA)
        app.saveCroppedTestImageTk = app.saveCroppedTestImageTk.resize((int(app.saveCroppedTestImageTk.width * coeff), int(app.saveCroppedTestImageTk.height * coeff)))

    image_width = app.saveCroppedTestImageTk.width
    image_height = app.saveCroppedTestImageTk.height

    CropImageBuffer(0, 0, image_width, image_height)
    if app.wb_kr != 1.0 or app.wb_kg != 1.0 or app.wb_kb != 1.0:
        ApplyWhiteBalance(app.croppedTestImageTk.mode)
 
    #buttons
    if app.use_buttons == True:
        app.buttons.SetButtonState(CButtons_enum.SET_CROP.value, tk.NORMAL)
        app.buttons.SetButtonState(CButtons_enum.OPEN_CHT.value, tk.NORMAL)
        app.buttons.SetButtonState(CButtons_enum.SAVE_IMAGE.value, tk.NORMAL)
        app.buttons.SetButtonState(CButtons_enum.OPEN_WB.value, tk.NORMAL)
    return 0    

################################################### 
# Opens .json file with white balance coefficients
# file_name - Path and name of .json file to open
# apply_wb - If true, applies white balance coefficients to input image
###################################################
def OpenWbFile(file_name, apply_wb=False):
    try:
        with open(file_name, 'r+') as f:
            file_content = f.read()
            content = json.loads(file_content)
            found_some = False 
            if "r" in content:
                app.wb_kr = float(content["r"]) 
                found_some = True   
            if "g" in content:
                app.wb_kg = float(content["g"]) 
                found_some = True    
            if "b" in content:
                app.wb_kb = float(content["b"]) 
                found_some = True  
            if found_some == True and apply_wb == True:
                ApplyWhiteBalance(app.croppedTestImageTk.mode)
                ResizeImage()    
                DrawObjects() 
    except OSError as error: 
        messagebox.showwarning('Error', title=error)

###################################################
# Crops image buffers
# x0 - x coordinates of left top point
# y0 - y coordinates of left top point
# x1 - x coordinates of right bottom point
# y1 - y coordinates of right bottom point
###################################################
def CropImageBuffer(x0, y0, x1, y1):  
    app.saveCroppedTestImageTk = app.saveCroppedTestImageTk.crop((x0, y0, x1, y1))
    app.croppedTestImageTk = app.saveCroppedTestImageTk.copy() 
    if app.cv2Image.dtype == np.uint16:  
        app.cv2Image = app.cv2Image[int(y0):int(y1), int(x0):int(x1)]
   
###################################################
# Applies white balance coefficients to imput image
# mode - defines iamge pixel format
###################################################
def ApplyWhiteBalance(mode):
    pixelMap = app.croppedTestImageTk.load()
    for i in range(app.croppedTestImageTk.size[0]):
        for j in range(app.croppedTestImageTk.size[1]):
            if mode == "RGBA" or mode == "RGBX":
                pixelMap[i,j] = (int(pow(pixelMap[i,j][0] * app.wb_kr / 255, 1 / app.gamma) * 255), int(pow(pixelMap[i,j][1] * app.wb_kg / 255, 1 / 2.2) * 255), int(pow(pixelMap[i,j][2] * app.wb_kb / 255, 1 / 2.2) * 255), pixelMap[i,j][3])
            if mode == "RGB":
                pixelMap[i,j] = (int(pow(pixelMap[i,j][0] * app.wb_kr / 255, 1 / app.gamma) * 255), int(pow(pixelMap[i,j][1] * app.wb_kg / 255, 1 / 2.2) * 255), int(pow(pixelMap[i,j][2] * app.wb_kb / 255, 1 / 2.2) * 255))


###################################################
# Interpolates grid patch coordinates
###################################################
def InterpolateLine(start, end, pos):
    ret = CPoint()
    ret.x = start.x + (end.x - start.x) * pos
    ret.y = start.y + (end.y - start.y) * pos
    return ret

###################################################
# Interpolates grid patch coordinates
###################################################
def TransformPoint(point):
    left_line = InterpolateLine(app.grid.frame.tetra.lt, app.grid.frame.tetra.lb, point.y)
    right_line = InterpolateLine(app.grid.frame.tetra.rt, app.grid.frame.tetra.rb, point.y)
    ret = InterpolateLine(left_line, right_line, point.x)
    return ret

###################################################
# Updates grid
###################################################
def update_grid():
    if app.grid.frame.start.x < app.grid.frame.stop.x and app.grid.frame.start.y < app.grid.frame.stop.y:
        app.grid.frame.tetra.lt.x = app.grid.frame.start.x
        app.grid.frame.tetra.lt.y = app.grid.frame.start.y
        app.grid.frame.tetra.rt.x = app.grid.frame.stop.x
        app.grid.frame.tetra.rt.y = app.grid.frame.start.y
        app.grid.frame.tetra.rb.x = app.grid.frame.stop.x
        app.grid.frame.tetra.rb.y = app.grid.frame.stop.y
        app.grid.frame.tetra.lb.x = app.grid.frame.start.x
        app.grid.frame.tetra.lb.y = app.grid.frame.stop.y
        app.grid.start_point = CCornerPoints_enum.POINT_LT
    elif app.grid.frame.start.x < app.grid.frame.stop.x and app.grid.frame.start.y > app.grid.frame.stop.y:
        app.grid.frame.tetra.lt.x = app.grid.frame.start.x
        app.grid.frame.tetra.lt.y = app.grid.frame.stop.y
        app.grid.frame.tetra.rt.x = app.grid.frame.stop.x
        app.grid.frame.tetra.rt.y = app.grid.frame.stop.y
        app.grid.frame.tetra.rb.x = app.grid.frame.stop.x
        app.grid.frame.tetra.rb.y = app.grid.frame.start.y
        app.grid.frame.tetra.lb.x = app.grid.frame.start.x
        app.grid.frame.tetra.lb.y = app.grid.frame.start.y
        app.grid.start_point = CCornerPoints_enum.POINT_LB
    elif app.grid.frame.start.x > app.grid.frame.stop.x and app.grid.frame.start.y < app.grid.frame.stop.y:
        app.grid.frame.tetra.lt.x = app.grid.frame.stop.x
        app.grid.frame.tetra.lt.y = app.grid.frame.start.y
        app.grid.frame.tetra.rt.x = app.grid.frame.start.x
        app.grid.frame.tetra.rt.y = app.grid.frame.start.y
        app.grid.frame.tetra.rb.x = app.grid.frame.start.x
        app.grid.frame.tetra.rb.y = app.grid.frame.stop.y
        app.grid.frame.tetra.lb.x = app.grid.frame.stop.x
        app.grid.frame.tetra.lb.y = app.grid.frame.stop.y
        app.grid.start_point = CCornerPoints_enum.POINT_RT
    elif app.grid.frame.start.x > app.grid.frame.stop.x and app.grid.frame.start.y > app.grid.frame.stop.y:
        app.grid.frame.tetra.lt.x = app.grid.frame.stop.x
        app.grid.frame.tetra.lt.y = app.grid.frame.stop.y
        app.grid.frame.tetra.rt.x = app.grid.frame.start.x
        app.grid.frame.tetra.rt.y = app.grid.frame.stop.y
        app.grid.frame.tetra.rb.x = app.grid.frame.start.x
        app.grid.frame.tetra.rb.y = app.grid.frame.start.y
        app.grid.frame.tetra.lb.x = app.grid.frame.stop.x
        app.grid.frame.tetra.lb.y = app.grid.frame.start.y       
        app.grid.start_point = CCornerPoints_enum.POINT_RB
    CheckSaveFiles()    
  
###################################################
# Checks distance between points
# p1 - first point
# p2 - second point
###################################################        
def FindNearestPoint(p1, p2):
    scale = app.proportion / app.proportion_grid_init
    if math.sqrt((p1.x * scale - p2.x) * (p1.x * scale - p2.x) + (p1.y * scale - p2.y) * (p1.y * scale - p2.y)) < app.DEFINE_SEARCH_RADIUS:
        return True
    return False 

###################################################
# Deletes all grid object allocated 
################################################### 
def DeleteGridObjects():
    app.grid.delete_objects(app.canvas)  

    for i in range(app.cht.grid_patches.number_patches):
        if app.cht.grid_patches.patches_lines[i].top != None:
            app.canvas.delete(app.cht.grid_patches.patches_lines[i].top)     
        if app.cht.grid_patches.patches_lines[i].right != None:
            app.canvas.delete(app.cht.grid_patches.patches_lines[i].right)     
        if app.cht.grid_patches.patches_lines[i].bottom != None:
            app.canvas.delete(app.cht.grid_patches.patches_lines[i].bottom)     
        if app.cht.grid_patches.patches_lines[i].left != None:
            app.canvas.delete(app.cht.grid_patches.patches_lines[i].left) 
        if app.cht.grid_patches.patches_triangles[i] != None:
            app.canvas.delete(app.cht.grid_patches.patches_triangles[i])                         

###################################################
# Draws all graphical object to Canvas
################################################### 
def DrawObjects():
    #update background
    width = app.canvas.winfo_width()
    height = app.canvas.winfo_height()
    if app.background_id != None:
        app.canvas.delete(app.background_id)
    app.background_id = app.canvas.create_rectangle(0, 0, width, height, fill="black")

    if app.resizedTestImageTk == None:
        return

    #display image
    if app.image_id != None:
        app.canvas.delete(app.image_id)
    
    offset_x = int((width - app.resizedTestImageTk.width() + 0.5) / 2)
    app.image_id = app.canvas.create_image((offset_x, 0), image=app.resizedTestImageTk, anchor="nw")
    image_pos = app.canvas.bbox(app.image_id)

    #draw grid or crop if enabled
    if app.draw_grid:
        DeleteGridObjects()
        radius = app.DEFINE_SEARCH_RADIUS
        scale = app.proportion / app.proportion_grid_init
        app.grid.lt_circle = app.canvas.create_oval(app.grid.frame.tetra.lt.x  * scale - radius + image_pos[0], app.grid.frame.tetra.lt.y  * scale - radius, app.grid.frame.tetra.lt.x  * scale + radius + image_pos[0], app.grid.frame.tetra.lt.y  * scale + radius, outline="red", dash=(3,5))
        app.grid.rt_circle = app.canvas.create_oval(app.grid.frame.tetra.rt.x * scale - radius + image_pos[0], app.grid.frame.tetra.rt.y * scale - radius, app.grid.frame.tetra.rt.x * scale + radius + image_pos[0], app.grid.frame.tetra.rt.y * scale + radius, outline="red", dash=(3,5))
        app.grid.rb_circle = app.canvas.create_oval(app.grid.frame.tetra.rb.x * scale - radius + image_pos[0], app.grid.frame.tetra.rb.y * scale - radius, app.grid.frame.tetra.rb.x * scale + radius + image_pos[0], app.grid.frame.tetra.rb.y * scale + radius, outline="red", dash=(3,5))
        app.grid.lb_circle = app.canvas.create_oval(app.grid.frame.tetra.lb.x * scale - radius + image_pos[0], app.grid.frame.tetra.lb.y * scale - radius, app.grid.frame.tetra.lb.x * scale + radius + image_pos[0], app.grid.frame.tetra.lb.y  * scale + radius, outline="red", dash=(3,5))
        
        app.grid.lt_frame_corner.line1 = app.canvas.create_line(app.grid.frame.tetra.lt.x  * scale + image_pos[0], app.grid.frame.tetra.lt.y  * scale, app.grid.frame.tetra.lt.x * scale + radius + image_pos[0], app.grid.frame.tetra.lt.y * scale, fill="white", width=app.line_width * scale, dash=(3,5))
        app.grid.lt_frame_corner.line2 = app.canvas.create_line(app.grid.frame.tetra.lt.x  * scale + image_pos[0], app.grid.frame.tetra.lt.y  * scale, app.grid.frame.tetra.lt.x * scale + image_pos[0], app.grid.frame.tetra.lt.y * scale + radius, fill="white", width=app.line_width * scale, dash=(3,5))

        app.grid.rt_frame_corner.line1 = app.canvas.create_line(app.grid.frame.tetra.rt.x  * scale + image_pos[0], app.grid.frame.tetra.rt.y  * scale, app.grid.frame.tetra.rt.x * scale - radius + image_pos[0], app.grid.frame.tetra.rt.y * scale, fill="white", width=app.line_width * scale, dash=(3,5))
        app.grid.rt_frame_corner.line2 = app.canvas.create_line(app.grid.frame.tetra.rt.x  * scale + image_pos[0], app.grid.frame.tetra.rt.y  * scale, app.grid.frame.tetra.rt.x * scale + image_pos[0], app.grid.frame.tetra.rt.y * scale + radius, fill="white", width=app.line_width * scale, dash=(3,5))

        app.grid.rb_frame_corner.line1 = app.canvas.create_line(app.grid.frame.tetra.rb.x  * scale + image_pos[0], app.grid.frame.tetra.rb.y  * scale, app.grid.frame.tetra.rb.x * scale - radius + image_pos[0], app.grid.frame.tetra.rb.y * scale, fill="white", width=app.line_width * scale, dash=(3,5))
        app.grid.rb_frame_corner.line2 = app.canvas.create_line(app.grid.frame.tetra.rb.x  * scale + image_pos[0], app.grid.frame.tetra.rb.y  * scale, app.grid.frame.tetra.rb.x * scale + image_pos[0], app.grid.frame.tetra.rb.y * scale - radius, fill="white", width=app.line_width * scale, dash=(3,5))

        app.grid.lb_frame_corner.line1 = app.canvas.create_line(app.grid.frame.tetra.lb.x  * scale + image_pos[0], app.grid.frame.tetra.lb.y  * scale, app.grid.frame.tetra.lb.x * scale + radius + image_pos[0], app.grid.frame.tetra.lb.y * scale, fill="white", width=app.line_width * scale, dash=(3,5))
        app.grid.lb_frame_corner.line2 = app.canvas.create_line(app.grid.frame.tetra.lb.x  * scale + image_pos[0], app.grid.frame.tetra.lb.y  * scale, app.grid.frame.tetra.lb.x * scale + image_pos[0], app.grid.frame.tetra.lb.y * scale - radius, fill="white", width=app.line_width * scale, dash=(3,5))

        i = 0
        for y in range(app.cht.grid_patches.rows):
            for x in range(app.cht.grid_patches.columns):   
                lt = TransformPoint(app.cht.grid_patches.patches[i].lt)
                rt = TransformPoint(app.cht.grid_patches.patches[i].rt)
                rb = TransformPoint(app.cht.grid_patches.patches[i].rb)
                lb = TransformPoint(app.cht.grid_patches.patches[i].lb)
                color = "white"
                if app.grid.start_point == CCornerPoints_enum.POINT_LT:
                    color = app.cht.grid_patches.patches_colors[i]
                if app.grid.start_point == CCornerPoints_enum.POINT_RT:
                    color = app.cht.grid_patches.patches_colors[y * app.cht.grid_patches.columns - x + app.cht.grid_patches.columns - 1]    
                if app.grid.start_point == CCornerPoints_enum.POINT_RB:
                    color = app.cht.grid_patches.patches_colors[(app.cht.grid_patches.rows - 1 - y)  * app.cht.grid_patches.columns - x + app.cht.grid_patches.columns - 1] 
                if app.grid.start_point == CCornerPoints_enum.POINT_LB:
                    color = app.cht.grid_patches.patches_colors[(app.cht.grid_patches.rows - 1 - y)  * app.cht.grid_patches.columns + x]            
                app.cht.grid_patches.patches_lines[i].top = app.canvas.create_line(lt.x * scale + image_pos[0], lt.y * scale, rt.x * scale + image_pos[0], rt.y * scale, fill="white", width=1.5 * app.line_width * scale, dash=(3,5))
                app.cht.grid_patches.patches_lines[i].right = app.canvas.create_line(rt.x * scale + image_pos[0], rt.y * scale, rb.x * scale + image_pos[0], rb.y * scale, fill="white", width=1.5 * app.line_width * scale, dash=(3,5))
                app.cht.grid_patches.patches_lines[i].bottom = app.canvas.create_line(rb.x * scale + image_pos[0], rb.y * scale, lb.x * scale + image_pos[0], lb.y * scale, fill="white", width=1.5 * app.line_width * scale, dash=(3,5))
                app.cht.grid_patches.patches_lines[i].left = app.canvas.create_line(lb.x * scale + image_pos[0], lb.y * scale, lt.x * scale + image_pos[0], lt.y * scale, fill="white", width=1.5 * app.line_width * scale, dash=(3,5))
                app.cht.grid_patches.patches_triangles[i] = app.canvas.create_polygon(lt.x * scale + image_pos[0] + 2, lt.y * scale + 2, rt.x * scale + image_pos[0] - 2, rt.y * scale + 2, lb.x * scale + image_pos[0] + 2, lb.y * scale - 2, lt.x * scale + image_pos[0] + 2, lt.y * scale + 2, outline=color, fill=color)
                i += 1
    if app.draw_crop:
        scale = app.proportion / app.proportion_crop_init
        if app.crop_frame.rectangle != None:
            app.canvas.delete(app.crop_frame.rectangle)
        app.crop_frame.rectangle = app.canvas.create_rectangle(app.crop_frame.start.x * scale + image_pos[0], app.crop_frame.start.y * scale, app.crop_frame.stop.x * scale + image_pos[0], app.crop_frame.stop.y * scale, outline="red", width=app.line_width * scale, dash=(3,5)) 

###################################################
# Handle to mouse double cleck
################################################### 
def handle_mouse_double(event):
    if app.proc_exec == True:
        return
    if app.buttons.use_buttons == False:
        app.mutex.release()  

###################################################
# Handle to mouse right button releasing
################################################### 
def handle_mouse_rb_released(event):
    if app.proc_exec == True:
        return
    if app.draw_grid:
        if app.image_id == None:
            return
        image_pos = app.canvas.bbox(app.image_id)
        p = CPoint()
        p.x = event.x - image_pos[0]
        p.y = event.y
        if FindNearestPoint(app.grid.frame.tetra.lt, p): 
            app.grid.start_point = CCornerPoints_enum.POINT_LT 
        if FindNearestPoint(app.grid.frame.tetra.rt, p): 
            app.grid.start_point = CCornerPoints_enum.POINT_RT 
        if FindNearestPoint(app.grid.frame.tetra.rb, p): 
            app.grid.start_point = CCornerPoints_enum.POINT_RB 
        if FindNearestPoint(app.grid.frame.tetra.lb, p): 
            app.grid.start_point = CCornerPoints_enum.POINT_LB
        DrawObjects() 
    if app.buttons.use_buttons == False and app.draw_crop == True:
        SetCropAreaButtonClick()

###################################################
# Handle to mouse left button releasing
###################################################
def handle_mouse_lb_released(event):
    if app.proc_exec == True:
        return
    if app.start_crop_rect:
        if isCropSet() == True:
            app.start_crop_rect = False
    if app.setting_grid and isGridSet() == False:
        app.start_grid_rect = True
        app.grid.frame.start.x = 0
        app.grid.frame.start.y = 0
        app.grid.frame.stop.x = 0
        app.grid.frame.stop.y = 0
        app.draw_grid = False
        app.setting_grid = False        

###################################################
# Handle to mouse button events
###################################################
def handle_mouse(event):
    if app.proc_exec == True:
        return
    if app.image_id == None:
        return
    image_pos = app.canvas.bbox(app.image_id)
    if event.x > image_pos[0] and event.y > image_pos[1] and event.x < image_pos[2] and event.y < image_pos[3]:
        x = event.x - image_pos[0]
        y = event.y
        if "Motion" in str(event):
            button1_pressed = False
            if "Button1" in str(event):
                button1_pressed = True
            if app.draw_grid:
                if  button1_pressed and app.point_found == True: #left button pressed
                    scale =  app.proportion_grid_init / app.proportion
                    if app.found_point_id == CCornerPoints_enum.POINT_LT:
                        app.grid.frame.tetra.lt.x = x * scale
                        app.grid.frame.tetra.lt.y = y * scale
                    if app.found_point_id == CCornerPoints_enum.POINT_RT:
                        app.grid.frame.tetra.rt.x = x * scale
                        app.grid.frame.tetra.rt.y = y * scale
                    if app.found_point_id == CCornerPoints_enum.POINT_RB:
                        app.grid.frame.tetra.rb.x = x * scale
                        app.grid.frame.tetra.rb.y = y * scale
                    if app.found_point_id == CCornerPoints_enum.POINT_LB:
                        app.grid.frame.tetra.lb.x = x * scale
                        app.grid.frame.tetra.lb.y = y * scale            
                elif button1_pressed and app.setting_grid:
                    app.grid.frame.stop.x = x
                    app.grid.frame.stop.y = y
                    update_grid()
                else:
                    app.setting_grid = False
            else:        
                if button1_pressed and app.start_crop_rect:
                    app.draw_crop = True   
                    app.crop_frame.stop.x = x
                    app.crop_frame.stop.y = y
                    app.buttons.SetButtonState(CButtons_enum.CROP.value, tk.NORMAL)
            button1_pressed = False        
        elif "ButtonPress" in str(event):
            if app.start_grid_rect:
                app.start_grid_rect = False
                app.grid.frame.start.x = x
                app.grid.frame.start.y = y
                app.grid.frame.stop.x = x
                app.grid.frame.stop.y = y
                app.proportion_grid_init =app.proportion
                app.draw_grid = True
                app.setting_grid = True
            else:
                if app.draw_grid:
                    p = CPoint()
                    p.x = x
                    p.y = y
                    app.point_found = False
                    if FindNearestPoint(app.grid.frame.tetra.lt, p):
                        app.found_point_id = CCornerPoints_enum.POINT_LT
                        app.point_found = True
                    if FindNearestPoint(app.grid.frame.tetra.rt, p):
                        app.found_point_id = CCornerPoints_enum.POINT_RT
                        app.point_found = True
                    if FindNearestPoint(app.grid.frame.tetra.rb, p):
                        app.found_point_id = CCornerPoints_enum.POINT_RB
                        app.point_found = True
                    if FindNearestPoint(app.grid.frame.tetra.lb, p):
                        app.found_point_id = CCornerPoints_enum.POINT_LB
                        app.point_found = True
                else: 
                    if app.start_crop_rect and isCropSet() == False:
                        SetCropAreaButtonClick()
                        app.draw_crop = False    
                        app.crop_frame.start.x = x
                        app.crop_frame.start.y = y
                        app.crop_frame.stop.x = x
                        app.crop_frame.stop.y = y
                        app.proportion_crop_init = app.proportion
                        app.buttons.SetButtonState(CButtons_enum.CROP.value, tk.DISABLED)
        DrawObjects()

###################################################
# Image resizer
###################################################
def ResizeImage():
    geometry = root.geometry()
    root_width = int(geometry[0:geometry.index("x")])
    root_height = int(geometry[geometry.index("x")+1:geometry.index("+")])
    if app.use_buttons == False:
        app.canvas.config(width=root_width-4, height=root_height-app.label.winfo_height()-4)
    width = app.canvas.winfo_width()
    height = app.canvas.winfo_height()

    if width <= 1 or height <= 1:
        return

    if app.croppedTestImageTk == None:
        return
        
    useHeight = height < width
    if useHeight:
        measurement = height
    else:
        measurement = width

    if useHeight:
        app.proportion = measurement / app.croppedTestImageTk.height
    else:
        app.proportion = measurement / app.croppedTestImageTk.width
        
    app.resizedTestImage = app.croppedTestImageTk.resize((int(app.croppedTestImageTk.width*app.proportion), int(app.croppedTestImageTk.height*app.proportion)))

    app.resizedTestImageTk = ImageTk.PhotoImage(app.resizedTestImage)

###################################################
# Handle application events
###################################################
def handle_configure(event):
    ResizeImage()    
    DrawObjects()

###################################################
# Image cropping
###################################################
def CropImage():
    x0 = 0
    y0 = 0
    x1 = 0
    y1 = 0

    if isCropSet():
        if app.crop_frame.stop.x > app.crop_frame.start.x:
            x0 = app.crop_frame.start.x
            x1 = app.crop_frame.stop.x
        else:
            x0 = app.crop_frame.stop.x
            x1 = app.crop_frame.start.x
        if app.crop_frame.stop.y > app.crop_frame.start.y:
            y0 = app.crop_frame.start.y
            y1 = app.crop_frame.stop.y
        else:
            y0 = app.crop_frame.stop.y
            y1 = app.crop_frame.start.y
        CropImageBuffer(x0 / app.proportion, y0 / app.proportion, x1 / app.proportion, y1 / app.proportion)
        ApplyWhiteBalance(app.croppedTestImageTk.mode)
        ResizeImage()    
        DrawObjects()
        app.buttons.SetButtonState(CButtons_enum.CROP.value, tk.DISABLED)

###################################################
# Checks if grid was set by user
###################################################
def isGridSet():
    if app.grid.frame.start.x != app.grid.frame.stop.x and app.grid.frame.start.y != app.grid.frame.stop.y:
        return True
    return False   

###################################################
# Checks if cropping ROI was set by user
###################################################
def isCropSet():
    if app.crop_frame.start.x != app.crop_frame.stop.x and app.crop_frame.start.y != app.crop_frame.stop.y:
        return True
    return False              

###################################################
# Sets graphical parametrs to default
###################################################
def SetDefaults():
    #grid defaults
    app.grid.frame.start.x = 0
    app.grid.frame.start.y = 0
    app.grid.frame.stop.x = 0
    app.grid.frame.stop.y = 0

    app.grid.frame.tetra.lt.x = 0
    app.grid.frame.tetra.lt.y = 0
    app.grid.frame.tetra.rt.x = 0
    app.grid.frame.tetra.rt.y = 0
    app.grid.frame.tetra.rb.x = 0
    app.grid.frame.tetra.rb.y = 0
    app.grid.frame.tetra.lb.x = 0
    app.grid.frame.tetra.lb.y = 0

    app.draw_grid = False
    app.start_grid_rect = False

    #crop defaults
    app.crop_frame.start.x = 0
    app.crop_frame.start.y = 0
    app.crop_frame.stop.x = 0
    app.crop_frame.stop.y = 0

    app.draw_crop = False

    CheckSaveFiles()

###################################################
# Change button state
###################################################
def CheckSaveFiles():
    isGrid = 0
    isGrid += app.grid.frame.tetra.lt.x
    isGrid += app.grid.frame.tetra.lt.y
    isGrid += app.grid.frame.tetra.rt.x
    isGrid += app.grid.frame.tetra.rt.y
    isGrid += app.grid.frame.tetra.rb.x
    isGrid += app.grid.frame.tetra.rb.y
    isGrid += app.grid.frame.tetra.lb.x
    isGrid += app.grid.frame.tetra.lb.y
    
    if app.saveCroppedTestImageTk != None and isGrid != 0:
        app.buttons.SetButtonState(CButtons_enum.GENERATE.value, tk.NORMAL)
    else:
        app.buttons.SetButtonState(CButtons_enum.GENERATE.value, tk.DISABLED)
  

#Botton handlers
###################################################
# Opens input image file
###################################################
def OpenImageButtonClick():
    filename = filedialog.askopenfilename(title='open', filetypes=[('TIF Files', '*.tif'), ('PNG Files', '*.png')])
    if filename != '':
        OpenImageFile(filename)
        SetDefaults()
        ResizeImage()    
        DrawObjects()

###################################################
# Opens white balance file
###################################################
def OpenWbButtonClick():
    filename = filedialog.askopenfilename(title='open', filetypes=[('JSON Files', '*.json')])
    if filename != '':
        OpenWbFile(filename, True)

###################################################
# Saves image
###################################################
def SaveImageButtonClick():
    types = [('TIF Files', '*.tif'), ('PNG Files', '*.png')]
    file = filedialog.asksaveasfile(title='save', filetypes=types, defaultextension=types)
    app.saveCroppedTestImageTk.save(file.name)

###################################################
# Saves all output files
###################################################
def SaveFilesButtonClick():
    try:
        output_directory = app.config.output_directory
        if output_directory == "":
            output_directory = "." #os.getcwd()
        elif os.path.exists(output_directory) == False:
            os.mkdir(output_directory)
            
        #save image
        output_image_file = app.config.output_image_file
        if output_image_file == "":
            messagebox.showwarning('Error', title='Output image name is not defined!!!')
            return 1
        image_file = output_directory + app.config.folder_separator + output_image_file    
        if app.cv2Image.dtype == np.uint16:
            cv2.imwrite(image_file, app.cv2Image)
        else: 
            app.saveCroppedTestImageTk.save(image_file) 
        #save fiducial marks coordinates
        feducial_marks_file = app.config.feducial_marks_file
        if feducial_marks_file == "":
            feducial_marks_file = 'FiducialMarks.txt'
        fid_file = output_directory + app.config.folder_separator + feducial_marks_file
        if app.grid.start_point == CCornerPoints_enum.POINT_LT:
            x0 = int(app.grid.frame.tetra.lt.x / app.proportion_grid_init)
            y0 = int(app.grid.frame.tetra.lt.y / app.proportion_grid_init)
            x1 = int(app.grid.frame.tetra.rt.x / app.proportion_grid_init)
            y1 = int(app.grid.frame.tetra.rt.y / app.proportion_grid_init)
            x2 = int(app.grid.frame.tetra.rb.x / app.proportion_grid_init)
            y2 = int(app.grid.frame.tetra.rb.y / app.proportion_grid_init)
            x3 = int(app.grid.frame.tetra.lb.x / app.proportion_grid_init)
            y3 = int(app.grid.frame.tetra.lb.y / app.proportion_grid_init)
        if app.grid.start_point == CCornerPoints_enum.POINT_RT:
            x0 = int(app.grid.frame.tetra.rt.x / app.proportion_grid_init)
            y0 = int(app.grid.frame.tetra.rt.y / app.proportion_grid_init)
            x1 = int(app.grid.frame.tetra.rb.x / app.proportion_grid_init)
            y1 = int(app.grid.frame.tetra.rb.y / app.proportion_grid_init)
            x2 = int(app.grid.frame.tetra.lb.x / app.proportion_grid_init)
            y2 = int(app.grid.frame.tetra.lb.y / app.proportion_grid_init)
            x3 = int(app.grid.frame.tetra.lt.x / app.proportion_grid_init)
            y3 = int(app.grid.frame.tetra.lt.y / app.proportion_grid_init) 
        if app.grid.start_point == CCornerPoints_enum.POINT_RB:
            x0 = int(app.grid.frame.tetra.rb.x / app.proportion_grid_init)
            y0 = int(app.grid.frame.tetra.rb.y / app.proportion_grid_init)
            x1 = int(app.grid.frame.tetra.lb.x / app.proportion_grid_init)
            y1 = int(app.grid.frame.tetra.lb.y / app.proportion_grid_init)
            x2 = int(app.grid.frame.tetra.lt.x / app.proportion_grid_init)
            y2 = int(app.grid.frame.tetra.lt.y / app.proportion_grid_init)
            x3 = int(app.grid.frame.tetra.rt.x / app.proportion_grid_init)
            y3 = int(app.grid.frame.tetra.rt.y / app.proportion_grid_init)
        if app.grid.start_point == CCornerPoints_enum.POINT_LB:
            x0 = int(app.grid.frame.tetra.lb.x / app.proportion_grid_init)
            y0 = int(app.grid.frame.tetra.lb.y / app.proportion_grid_init)
            x1 = int(app.grid.frame.tetra.lt.x / app.proportion_grid_init)
            y1 = int(app.grid.frame.tetra.lt.y / app.proportion_grid_init)
            x2 = int(app.grid.frame.tetra.rt.x / app.proportion_grid_init)
            y2 = int(app.grid.frame.tetra.rt.y / app.proportion_grid_init)
            x3 = int(app.grid.frame.tetra.rb.x / app.proportion_grid_init)
            y3 = int(app.grid.frame.tetra.rb.y / app.proportion_grid_init)           
        fid = "{},{},{},{},{},{},{},{}".format(x0, y0, x1, y1, x2, y2, x3, y3)

        with open(fid_file, 'w') as f:
            f.write(fid)
        #save scanin command  
        output_generate_file = app.config.output_generate_file
        if output_generate_file == "":
            messagebox.showwarning('Error', title='Generate file is not defined!!!')
            return 1
        fid_file = output_directory + app.config.folder_separator + output_generate_file
        fid_file_ok = False
        with open(fid_file, 'w') as f:
            cie_file = "{}cie".format(app.config.input_cht_file[:-3])
            if app.config.input_cie_file != "":
                cie_file = app.config.input_cie_file
            scanin = app.config.scanin
            if scanin == "":
                messagebox.showwarning('Error', title='scanin tool is not defined!!!')
                return 1
            output_ti3_file = app.config.output_ti3_file
            if output_ti3_file == "":  
                output_ti3_file = 'Output.ti3' 
            scanin_cmd = ".{}{} -dipn -F {} -O \"{}\" \"{}\" \"{}\" \"{}\" \"{}diag.tif\"\n".format(app.config.folder_separator, scanin, fid, output_directory + app.config.folder_separator + output_ti3_file, image_file, app.config.input_cht_file, cie_file, output_directory + app.config.folder_separator)
            f.write(scanin_cmd)
            dcamprof = app.config.dcamprof
            if dcamprof == "":
                messagebox.showwarning('Error', title='dcamprof tool is not defined!!!')
                return 1
            output_json_file = app.config.output_json_file
            if output_json_file == "":  
                output_json_file = 'Output.json'    
            dcamprof_json = ".{}{} {} -i {} \"{}\" \"{}\"\n".format(app.config.folder_separator, dcamprof, app.config.dcamprof_opt_json, app.config.calibration_illuminant, output_directory + app.config.folder_separator + output_ti3_file, output_directory + app.config.folder_separator + output_json_file)
            f.write(dcamprof_json)
            output_dcp_file = app.config.output_dcp_file
            if output_dcp_file == "":  
                output_dcp_file = 'Output.dcp'
            dcamprof_dcp = ".{}{} {} -n \"{}\" -d \"{}\" \"{}\" \"{}\"\n".format(app.config.folder_separator, dcamprof, app.config.dcamprof_opt_dcp, app.config.unique_camera_name, app.config.profile_name, output_directory + app.config.folder_separator + output_json_file, output_directory + app.config.folder_separator + output_dcp_file)
            f.write(dcamprof_dcp)
            fid_file_ok = True
        returned_value = 0    
        if fid_file_ok == True: 
            returned_value = os.system(app.config.executor.format(fid_file))     
        else:
            returned_value = 1 
    except OSError as error: 
        messagebox.showwarning('Error', title=error)
        returned_value = 1 
    return returned_value       
 
###################################################
# Init cropping ROI
###################################################
def SetCropAreaButtonClick():
    SetDefaults()
    app.start_crop_rect = True

###################################################
# Applies image cropping
###################################################  
def DoCropButtonClick():
    CropImage()

###################################################
# Init grid setting
###################################################
def SetGridAreaButtonClick():
    SetDefaults()
    app.start_grid_rect = True
    DrawObjects()

###################################################
# Opens Colorchecker .cht file
###################################################
def OpenCHTButtonClick():
    SetDefaults()
    app.buttons.SetButtonState(CButtons_enum.SET_GRID.value, tk.DISABLED)
   
    types = [('CHT Files', '*.cht')]
    app.config.input_cht_file = filedialog.askopenfilename(title='open', filetypes=types, defaultextension=types)
    if app.config.input_cht_file != '':
        app.cht.Open_cht(app.config.input_cht_file)
        app.buttons.SetButtonState(CButtons_enum.SET_GRID.value, tk.NORMAL)
 
# Event handlers 
#---------------------------------------------------    
root.bind("<Configure>", handle_configure)
app.canvas.bind("<Motion>", handle_mouse)
app.canvas.bind('<Button-1>', handle_mouse)
app.canvas.bind('<ButtonRelease-3>', handle_mouse_rb_released)
app.canvas.bind('<Double-Button-1>', handle_mouse_double)
app.canvas.bind('<ButtonRelease-1>', handle_mouse_lb_released)

#main
#---------------------------------------------------
def Usage():
    print('Coloric [options]')
    print('options:')
    print('-i Input image (supported format .tif)')
    print('-t Input color checker cht file')
    print('-r White balance red coefficient')
    print('-g White balance green coefficient')
    print('-b White balance blue coefficient')
    print('-w White balance json file')
    print('-s Calibration illuminant')
    print('-o Output directory')
    print('-c Configuration json file')
    print('-h Help')
#--------------------------------------------------- 
def main(argv):
    app.config = CConfiguration() 

    try:
        opts, args = getopt.getopt(argv,"i:h:t:r:g:b:w:s:o:c:")
    except getopt.GetoptError:
        Usage()
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            Usage()
            sys.exit(0)
        elif opt in ("-i"):
            app.Input_image_file = arg
        elif opt in ("-t"):
            app.config.input_cht_file = arg
        elif opt in ("-r"):
            app.wb_kr = float(arg)  
        elif opt in ("-g"):
            app.wb_kg = float(arg)  
        elif opt in ("-b"):
            app.wb_kb = float(arg) 
        elif opt in ("-w"):
            app.Input_wb_file = arg 
        elif opt in ("-s"):
            app.config.calibration_illuminant = arg 
        elif opt in ("-o"):
            app.config.output_directory = arg 
        elif opt in ("-c"):
            if app.config.ParseConfigFile(arg) == 1:
                os._exit(1)
            app.label.config(font=(app.config.label_font, app.config.label_font_size))

    if app.Input_wb_file:
        OpenWbFile(app.Input_wb_file)          
    if app.Input_image_file:
        if OpenImageFile(app.Input_image_file) == 1:
            os._exit(1)
        SetDefaults()
  
        if app.config.input_cht_file != "":
            if app.cht.Open_cht(app.config.input_cht_file) == 1:
                os._exit(1)    
            app.buttons.SetButtonState(CButtons_enum.SET_GRID.value, tk.NORMAL)

def thread_function(name):
    if app.saveCroppedTestImageTk == None:
        messagebox.showwarning('Error', 'Input image was not defined!!!')
        os._exit(1)
    app.mutex.acquire() 
    if app.finish_thread == True:
        return  
    for i in range(app.config.number_of_crops): 
        app.label["text"] = '#' + str(i + 1) + ':' + 'Setting crop ROI: \n Hold mouse left button and move cursor to define ROI, \n Left button double click to apply, right click to reset'      
        SetCropAreaButtonClick() 
        app.mutex.acquire() 
        if app.finish_thread == True:
            return   
        app.proc_exec = True  
        app.label["text"] = 'Processing....'  
        CropImage()
        app.proc_exec = False 
    app.label["text"] = 'Setting color patch grid: \n Hold mouse left button and move cursor to set grid, \n Left button double click to apply' 
    SetGridAreaButtonClick() 
    app.mutex.acquire() 
    if app.finish_thread == True:
        return  
    error = 0     
    if isGridSet():  
        app.label["text"] = 'Generating files....'
        app.proc_exec = True
        error = SaveFilesButtonClick()
        app.proc_exec = False
    else: 
        messagebox.showwarning('Error', 'Grid has not been set!!!')
        error = 1
    app.label["text"] = ('Done' if error == 0 else 'Failed') + ' \n Left button double click to close application'
    app.mutex.acquire()   
    os._exit(0 if error == 0 else 1)

def close_window():
    if app.thread_handle != None and app.thread_handle.is_alive():
        app.finish_thread = True
        app.mutex.release()
        app.thread_handle.join()
    root.destroy()
    os._exit(1)

if __name__ == "__main__":
    app.buttons = CButtons(app.use_buttons) 
    main(sys.argv[1:])
    if app.use_buttons == False:
        app.thread_handle = threading.Thread(target=thread_function, args=(1,))
        app.thread_handle.start() 
 
root.protocol("WM_DELETE_WINDOW", close_window)
root.mainloop()
