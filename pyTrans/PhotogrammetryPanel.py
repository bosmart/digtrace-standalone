__author__ = 'shujiedeng'

import wx

from traits.etsconfig.api import ETSConfig
ETSConfig.toolkit = 'wx'

import numpy as np
import math

from traits.api import HasTraits, Instance, Range, Float, Array, on_trait_change
from traitsui.api import View, Item, Action, Handler
from mayavi.core.ui.api import SceneEditor, MlabSceneModel
from mayavi import mlab

import vtk
from tvtk.api import tvtk
from plyfile import PlyData

import os
import multiprocessing
from Loader import Loader
from MatplotPanel import MatplotPanel


import ply

IS_GTK = 'wxGTK' in wx.PlatformInfo
IS_WIN = 'wxMSW' in wx.PlatformInfo
IS_MAC = 'wxMac' in wx.PlatformInfo

class PhotogrammetryPanel(wx.Panel):
    def __init__(self, parent, fname=''):
        size = parent.GetSize()

        wx.Panel.__init__(self, parent, wx.ID_ANY, size=size)

        self.fname = fname  # actually fpath
        self.used = False

        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(self.sizer)

        self.mayavi_view = MayaviView(self.fname)

        # Use traits to create a panel, and use it as the content of this
        # wx frame.
        self.control = self.mayavi_view.edit_traits(
                        parent=self,
                        kind='subpanel').control

        self.sizer.Clear()
        self.sizer.Add(self.control, 1, wx.EXPAND, wx.EXPAND, 5)

        self.panel_thumbs = parent.Parent.panel_thumbs_bottom
        self.sizer_thumbs = parent.Parent.sizer_thumbs_bottom
        self.prints = parent.Parent.prints

        self.status_bar = parent.Parent.status_bar

        self.SendSizeEvent()

        self.picker_obj = self.mayavi_view.scene.mayavi_scene.on_mouse_pick(self.picker_callback)
        self.picker_obj.tolerance = 0.01

        self.markers = []
        self.scale_param = 1.0
        self.output_csv = ""

        self.width = None
        self.height = None

        self.picker_obj_crop = self.mayavi_view.scene.mayavi_scene.on_mouse_pick(self.crop_callback)
        self.picker_obj_crop.tolerance = 0.1
        self.crop_markers = []  # store the index of picked points

        self.picker_obj_measure = self.mayavi_view.scene.mayavi_scene.on_mouse_pick(self.measure_callback)
        self.picker_obj_measure.tolerance = 0.02
        self.measure_markers = []  # store the index of picked points

        self.marker_scale = self.set_marker_scale(self.mayavi_view.point_array[0])
        print self.marker_scale

    # def update(self, fname):
    #     self.mayavi_view.update(fname)

    # this sets the size of the markers used for distance measurement, cropping and scaling automatically base on the data
    def set_marker_scale(self, point):
        value = (abs(point[0]) + abs(point[1]) + abs(point[2])) / 3.0
        return math.pow(10, math.floor(math.log10(value))-1)

    # placing markers for the distance measurement and calculating the distance
    def measure_callback(self, picker_obj_measure):
        if self.GrandParent.toolbar.GetToolState(self.GrandParent.toolbar.ID_MEASURE):
            self.picker_obj_measure = picker_obj_measure
            picked = self.picker_obj_measure.actors
            if self.mayavi_view.pts.actor.actor._vtk_obj in [o._vtk_obj for o in picked]:
                landmark = self.mayavi_view.point_array[self.picker_obj_measure.point_id]
                # landmark = self.picker_obj.pick_position
                if len(self.measure_markers) < 2:
                    self.measure_markers.append(landmark)
                    mlab.points3d(landmark[0], landmark[1], landmark[2], mode='2dcircle', color=(0, 1, 0), scale_factor=self.marker_scale, scale_mode='none', reset_zoom=False)
                if len(self.measure_markers) == 2:
                    dist = np.linalg.norm(self.measure_markers[1]-self.measure_markers[0])
                    print dist
                    msg = str(dist) + " mm"
                    self.status_bar.SetStatusText(msg)
                    wx.MessageBox(self.status_bar.GetStatusText(), 'Distance',
                              wx.OK | wx.ICON_INFORMATION)
                    #remove markers after dispaying measurement
                    self.mayavi_view.remove_markers()
                    self.measure_markers = []

    # 4 point crop (defining the crop box and calling the crop function)
    def crop_callback(self, picker_obj_crop):
        # threshold = 0.01  # loop closing point if distance smaller than the threshold




        if self.GrandParent.toolbar.GetToolState(wx.ID_CUT):
            self.picker_obj_crop = picker_obj_crop
            picked = self.picker_obj_crop.actors
            if self.mayavi_view.pts.actor.actor._vtk_obj in [o._vtk_obj for o in picked]:
                print self.picker_obj_crop.point_id
                # if not self.picker_obj_crop.point_id < 50:  # when cannot close cropping
                self.status_bar.SetStatusText('')
                self.crop_markers.append(self.picker_obj_crop.point_id)
                if len(self.crop_markers) == 0:
                    print len(self.crop_markers)
                    # mlab.points3d(self.mayavi_view.point_array[self.crop_markers[0]][0],
                    #               self.mayavi_view.point_array[self.crop_markers[0]][1],
                    #               self.mayavi_view.point_array[self.crop_markers[0]][2],
                    #               mode='point', color=(0, 1, 0), scale_factor=0.01, scale_mode='none')
                elif len(self.crop_markers) < 4 and len(self.crop_markers) > 0:
                    # if very close to the first marker, consider as closing loop
                    # dist = np.linalg.norm(self.mayavi_view.point_array[self.picker_obj_crop.point_id] - self.mayavi_view.point_array[self.crop_markers[0]])
                    print len(self.crop_markers)
                    # if dist > threshold:
                    # self.crop_markers.append(self.picker_obj_crop.point_id)
                    # draw line between this point and the previous point
                    self.draw_line(self.mayavi_view.point_array[self.crop_markers[-2]], self.mayavi_view.point_array[self.crop_markers[-1]], np.max(self.mayavi_view.point_array[:,2]))
                elif len(self.crop_markers) == 4:  # auto closing crop polygon
                    self.draw_line(self.mayavi_view.point_array[self.crop_markers[-1]], self.mayavi_view.point_array[self.crop_markers[0]], np.max(self.mayavi_view.point_array[:,2]))
                    self.crop()
                # else:
                #     self.status_bar.SetStatusText('Invalid point selection.')

    def draw_line(self, a, b, minz):
        N = 20  # The number of points per line
        x = np.linspace(a[0], b[0], N)
        y = np.linspace(a[1], b[1], N)
        #z = np.linspace(a[2], b[2], N)
        z = np.repeat(minz, N)
        s = np.linspace(1, 1, N)
        connections = np.vstack([np.arange(0, N - 1.5), np.arange(1, N - .5)]).T
        src = mlab.pipeline.scalar_scatter(x, y, z, s)
        src.mlab_source.dataset.lines = connections
        src.update()
        lines = mlab.pipeline.stripper(src)
        mlab.pipeline.surface(lines, colormap='Accent', line_width=5, opacity=1, reset_zoom=False)
        # mlab.plot3d([a[0], b[0]], [a[1], b[1]], [minz+1, minz+1], color=(0,1,0), line_width=20, tube_radius=None)

    def crop(self):
        # basic idea: consider each edge of the cropping polygon as a cropping plane, keep points fall inside all planes
        # 1) find two vectors on each cropping plane (for getting the normal later)
        #    one is the cropping edge itself, the other is the normal defined by the edge itself and its neighbour edge
        # 2) the two vectors defines the cropping plane, use the two to get the normal of the cropping plane.
        #    the direction of the normal is pointing to the inside of the polygon
        # 3) find the points are on which side of each plane, inside is 1, outside is -1. add the signs up
        #    if one point is inside of all planes, the sum should equal to the number of cropping planes
        # 4) get the index of the points inside, using the index is for getting their corresponding color
        vp = []  # store vector of each side of the crop polygon
        vp2 = []  # store the second vector of each side of crop polygon
        for i, marker in enumerate(self.crop_markers):
            if i < len(self.crop_markers) - 1:
                p = np.subtract(self.mayavi_view.point_array[self.crop_markers[i+1]], self.mayavi_view.point_array[marker])  # vectors on the crop polygon plane
            else:
                p = np.subtract(self.mayavi_view.point_array[self.crop_markers[0]], self.mayavi_view.point_array[marker])
            vp.append(p)
        for i, v in enumerate(vp):
            if i < len(vp) - 1:
                p2 = np.cross(vp[i], vp[i+1])  # actually normal of the neighbouring two plane sides
            else:
                p2 = np.cross(vp[i], vp[0])
            vp2.append(p2)
        n = np.cross(vp2, vp)  # the normals of inside

        sign_array = np.zeros(len(self.mayavi_view.point_array))
        for i, marker in enumerate(self.crop_markers):
            sign_array = np.add(sign_array, self.getSide(self.mayavi_view.point_array, self.mayavi_view.point_array[marker], n[i]))
        points_inside_index = np.where(sign_array == len(self.crop_markers))

        self.mayavi_view.point_array = np.array(self.mayavi_view.point_array)[points_inside_index]
        self.mayavi_view.color_array = np.array(self.mayavi_view.color_array)[points_inside_index]

        # update drawing
        self.mayavi_view.update()
        self.crop_markers = []

        # set edited flag
        self.GrandParent.ply_edited = True

    def invert(self,x,y,z):
        u = self.mayavi_view.point_array
        q = np.vstack((u[:, 0]*pow(-1,x), u[:, 1]*pow(-1,y), u[:, 2] * pow(-1,z)))
        q=np.transpose(q)
        self.mayavi_view.point_array=q
        self.mayavi_view.update()

    # helper function to decide whether the point is inside the box
    def getSide(self, points, origin, normal):
        assert len(points) > 0
        # origins = np.tile(origin, (len(points), 1))
        v = np.subtract(points, origin)
        if len(normal) == 1:
            dot_product = np.dot(v, normal)
        else:
            dot_product = np.einsum('ji,i->j', v, np.array(normal))  # element wise dot

        return np.sign(dot_product)

    # scale call back
    # sets markers for scale operation.
    # when clicked on a "hole" selection is either empty or some default point (could be ID=0) is selected.
    def picker_callback(self, picker_obj):
        if self.GrandParent.toolbar.GetToolState(wx.ID_CONVERT):
            self.picker_obj = picker_obj
            #choice = self.Parent.Parent.toolbar.choiceScale.GetSelection()
            choice = 0 #2 points scale is automatically selected, because 4 points is not working
            # picker_obj.tolerance = 0.001
            picked = self.picker_obj.actors
            # two points scale
            if choice == 0:
                if self.mayavi_view.pts.actor.actor._vtk_obj in [o._vtk_obj for o in picked]:
                    landmark = self.mayavi_view.point_array[self.picker_obj.point_id]
                    # landmark = self.picker_obj.pick_position
                    if len(self.markers) < 2:
                        self.markers.append(landmark)
                        print self.mayavi_view.point_array[self.picker_obj.point_id]
                        print self.markers
                        mlab.points3d(landmark[0], landmark[1], landmark[2], mode='2dcross', color=(0, 1, 0), scale_factor=self.marker_scale, scale_mode='none', reset_zoom=False)
                    if len(self.markers) == 2:
                        dist = np.linalg.norm(self.markers[1]-self.markers[0])
                        print dist
                        flag = self.SetDistancePopup(dist)
                        # print self.mayavi_view.point_array
                        if flag:
                            self.Scale(choice)

            # four points scale
            elif choice == 1:
                if self.mayavi_view.pts.actor.actor._vtk_obj in [o._vtk_obj for o in picked]:
                    landmark = self.mayavi_view.point_array[self.picker_obj.point_id]
                    if len(self.markers) < 4:
                        self.markers.append(landmark)
                        print self.mayavi_view.point_array[self.picker_obj.point_id]
                        print self.markers
                        mlab.points3d(landmark[0], landmark[1], landmark[2], mode='2dcross', color=(0, 1, 0), scale_factor=self.marker_scale, scale_mode='none', reset_zoom=False)
                        # mlab.text3d(landmark[0], landmark[1], landmark[2], str(len(self.markers)), scale=(2, 2, 2))

                        if len(self.markers) == 2:
                            self.width = self.SetWHPopup()
                        elif len(self.markers) == 3:
                            self.height = self.SetWHPopup()
                    if len(self.markers) == 4 and self.width != None and self.height != None:
                        print "four points!"
                        self.Scale(choice)

    # popup for 2-point scaling
    def SetDistancePopup(self, distance):
        dlg = wx.TextEntryDialog(self, 'Enter the distance between the selected two points in (mm)', 'Data Entry')
        dlg.SetValue(str(self.scale_param))
        flag = False
        if dlg.ShowModal() == wx.ID_OK:
            # self.SetStatusText('You entered: %s\n' % dlg.GetValue())
            print dlg.GetValue()
            self.scale_param = float(dlg.GetValue()) / distance
            print self.scale_param
            flag = True
        else:
            # remove pickers
            self.mayavi_view.remove_markers()
            self.markers = []
            flag = False
        dlg.Destroy()
        return flag

    # popup for 4-point scaling
    def SetWHPopup(self): # set width and height if scale using four points
        if len(self.markers) == 2:
            dlg = wx.TextEntryDialog(self, 'Enter the distance between the first and second point in (mm)\ntop left and top right point (width)', 'Data Entry')
        elif len(self.markers) == 3:
            dlg = wx.TextEntryDialog(self, 'Enter the distance between the second and third point in (mm)\ntop right and bottom right point (height)', 'Data Entry')
        dlg.SetValue(str("0.00"))
        if dlg.ShowModal() == wx.ID_OK:
            # self.SetStatusText('You entered: %s\n' % dlg.GetValue())
            print dlg.GetValue()
        else:
            # remove last picker
            self.mayavi_view.remove_last_marker()
            self.markers.pop(-1)
            return None
        value = float(dlg.GetValue())
        dlg.Destroy()
        return value

    def Scale(self, choice):
        # transform = vtk.vtkTransform()
        # transform.Scale(self.scale_param, self.scale_param, self.scale_param)
        # new_points = transform.TransformPoint(self.mayavi_view.point_array)
        # new_points = transform.PostMultiply(self.mayavi_view.point_array)
        #if len(self.markers) == 2:
        if choice == 0:
            transform = [[self.scale_param, 0 ,0], [0, self.scale_param, 0], [0, 0, self.scale_param]]
            new_points = np.mat(self.mayavi_view.point_array) * np.mat(transform)
        # if len(self.markers) == 4 and self.width != None and self.height != None:
        elif choice == 1:
            transform = self.four_point_transform(self.markers, self.width, self.height)
            print transform
            print self.mayavi_view.point_array
            pts = self.mayavi_view.point_array[:,(0,1)] # extract first two columns (x,y)
            ones_column = np.ones((np.shape(self.mayavi_view.point_array)[0], 1))
            pts = np.hstack((pts, ones_column))
            new_points = np.mat(pts) * np.mat(transform)
            print new_points
            print np.shape(new_points)
            print np.shape(self.mayavi_view.point_array)
            # new_points = np.hstack((new_points[:,0:2], self.mayavi_view.point_array[:,2:3]))
            # TODO: temporarily set depth scale param to (S_width + S_height)/2
            self.get_scale_param()
            print self.scale_param
            new_points = np.hstack((new_points[:,0:2], self.mayavi_view.point_array[:,2:3] * self.scale_param))
            print "after scale"

        new_points = np.array(new_points, dtype=np.float32)

        self.mayavi_view.point_array = new_points
        self.mayavi_view.update()

        self.marker_scale = self.marker_scale * self.scale_param

        # self.PLY2CSV(new_points)
        # self.load_csv()
        # clean up/reset in case there are other point clouds need scaling
        self.scale_param = 1.0
        self.width = None
        self.height = None
        self.markers = []

        # selt ply edited flag
        self.GrandParent.ply_edited = True

    # for 4 points scale
    def order_points(self, pts):
        # initialzie a list of coordinates that will be ordered
        # such that the first entry in the list is the top-left,
        # the second entry is the top-right, the third is the
        # bottom-right, and the fourth is the bottom-left
        rect = np.zeros((4, 2), dtype = "float32")

        # the top-left point will have the smallest sum, whereas
        # the bottom-right point will have the largest sum
        # s = pts.sum(axis = 1)
        s = np.sum(pts, axis=1)
        rect[0] = pts[np.argmin(s)]
        rect[2] = pts[np.argmax(s)]

        # now, compute the difference between the points, the
        # top-right point will have the smallest difference,
        # whereas the bottom-left will have the largest difference
        diff = np.diff(pts, axis = 1)
        rect[1] = pts[np.argmin(diff)]
        rect[3] = pts[np.argmax(diff)]

        # return the ordered coordinates
        return rect

    # for 4 points scale
    def four_point_transform(self, pts, width, height):
        # obtain a consistent order of the points and unpack them
        # individually
        pts = np.array(pts)
        pts = pts[:, (0,1)]
        rect = self.order_points(pts)

        dst = np.array([
            [0, 0],
            [width, 0],
            [width, height],
            [0, height]], dtype = "float32")

        # compute the perspective transform matrix and then apply it
        M = cv2.getPerspectiveTransform(rect, dst)
        # warped = cv2.warpPerspective(image, M, (width, height))

        # return the warped image
        return M

    # for 4-point scale, get average of width scale and height scale parameters
    def get_scale_param(self):
        w_dist = np.linalg.norm(self.markers[1]-self.markers[0])
        h_dist = np.linalg.norm(self.markers[2]-self.markers[1])
        self.scale_param = (self.width / w_dist + self.height / h_dist) / 2.0


    # 3D crop
    def cube_crop(self):  # 3d crop
        self.mayavi_view.clear_drawing()

        self.mayavi_view.pts = mlab.pipeline.scalar_scatter(self.mayavi_view.point_array[:,0],
                                                            self.mayavi_view.point_array[:,1],
                                                            self.mayavi_view.point_array[:,2],
                                                            mode='point', figure=self.mayavi_view.scene.mayavi_scene)
        # Use a geometry_filter to filter with a bounding box
        geometry_filter = mlab.pipeline.user_defined(self.mayavi_view.pts,
                                           filter='GeometryFilter', figure=self.mayavi_view.scene.mayavi_scene)
        geometry_filter.filter.extent_clipping = True
        # Connect our dialog to the filter
        self.extent_dialog = ExtentDialog(
                    data_x_min=round(np.amin(self.mayavi_view.point_array[:,0]), 2), data_x_max=round(np.amax(self.mayavi_view.point_array[:,0]), 2),
                    data_y_min=round(np.amin(self.mayavi_view.point_array[:,1]), 2), data_y_max=round(np.amax(self.mayavi_view.point_array[:,1]), 2),
                    data_z_min=round(np.amin(self.mayavi_view.point_array[:,2]), 2), data_z_max=round(np.amax(self.mayavi_view.point_array[:,2]), 2),
                    filter=geometry_filter.filter,
                    point_array=self.mayavi_view.point_array, color_array=self.mayavi_view.color_array)
        # We need to use 'edit_traits' and not 'configure_traits()' as we do
        # not want to start the GUI event loop (the call to mlab.show())
        # at the end of the script will do it.
        self.extent_dialog.edit_traits()

        # The geometry_filter leaves hanging points, we need to add a
        # CleanPolyData filter to get rid of these.
        clip = mlab.pipeline.user_defined(geometry_filter, filter='CleanPolyData', figure=self.mayavi_view.scene.mayavi_scene)

        # Finally, visualize the remaining points with spheres using a glyph module
        points = mlab.pipeline.glyph(clip, mode='point', figure=self.mayavi_view.scene.mayavi_scene)
        # self.mayavi_view.point_array = np.array(clip.outputs[0].points.to_array())

        # assign color
        sc=tvtk.UnsignedCharArray()
        sc.from_array(self.mayavi_view.color_array)
        self.mayavi_view.pts.mlab_source.dataset.point_data.scalars = sc
        self.mayavi_view.pts.mlab_source.dataset.modified()

        mlab.outline()

        # set edited flag
        self.GrandParent.ply_edited = True

    def save_ply(self, path):

        # current_pts = self.mayavi_view.scene.mayavi_scene.children[0].children[0].children[0].mlab_source
        # self.mayavi_view.point_array = np.vstack((current_pts.x, current_pts.y, current_pts.z))
        # self.mayavi_view.point_array = np.transpose(self.mayavi_view.point_array)
        # self.mayavi_view.color_array = current_pts.dataset.point_data.scalars.to_array()

        ply.write_ply(path, points_np=np.hstack((self.mayavi_view.point_array,self.mayavi_view.color_array)), as_text=False)



    def PLY2CSV(self, data, path, percent, random):

        #decrease csv size
        data=data[self.decrease_size(percent, random, data.shape[0]),:]

        with open(path, 'w') as f:
            f.write('X,Y,Z\n')
            for entry in data:
                # f.write("%.4f,%.4f,%.4f\n" % (entry.item(0, 0), entry.item(0,1), entry.item(0, 2)))
                f.write("%.4f,%.4f,%.4f\n" % (entry[0], entry[1], entry[2]))
                # print entry
                # print(entry.item(0, 1))
            self.output_csv = path
            f.close()

    #decrease the size (delete the rows) of csv
    def decrease_size(self, percent, random, size):

        remaining_indices = np.arange(0, size-1)

        #if 100 percent, no deletion needed
        if percent==100:
            return remaining_indices

        #randomly
        if random:
            remaining_indices=np.random.choice(np.arange(0, size-1), percent*size/100, False)

        #every n-th row
        else:
            remaining_indices=np.arange(0, size-1, 100/percent)
        return remaining_indices

    # load into the bottom panel
    def load_csv(self):
        if os.path.isfile(self.output_csv):
            # replace all .ftproj files with .csv/.asc files (remove duplicates!)
            paths = []
            paths.append(self.output_csv)

            import time

            print('Load and interpolate of one file')
            start_time = time.time()
            #TODO: fixed multipliers, need to change
            result = run_job(paths, Loader(0.5, 1))

            not_loaded = ''
            loaded = 0
            for xyzi, xyz, fname, guessed_multiplier in result:
                if xyzi is None:
                    not_loaded = not_loaded + os.path.basename(fname) + ', '

                else:
                    loaded += 1

                    # set thumbs panel
                    ch = self.sizer_thumbs.GetChildren()
                    if len(ch) == 1 and type(ch[0].GetWindow()) is wx.StaticText:
                        self.sizer_thumbs.Clear(True)

                    # 'normalize' z axis: min(z)=0
                    xyz, xyzi = self.Parent.Parent.Parent.Parent.normalize_z_axis(xyz, xyzi, np.nanmin(xyzi[2]))

                    #TODO: user customise multiplier and perecision when saving
                    mpl = MatplotPanel(self.panel_thumbs, xyzi, xyz, multiplier=1.0, precision=0.5, title=os.path.basename(fname), fname=fname, lmark_xy=None, A=None)
                    mpl.data = wx.TextDataObject(str(mpl.fig.canvas.GetId()))
                    mpl.button_press_event = mpl.fig.canvas.mpl_connect('button_press_event', self.Parent.Parent.Parent.Parent.on_drag)
                    mpl.motion_notify_event = mpl.fig.canvas.mpl_connect('motion_notify_event', self.Parent.Parent.Parent.Parent.on_mouseover)
                    mpl.figure_leave_event = mpl.fig.canvas.mpl_connect('figure_leave_event', self.Parent.Parent.Parent.Parent.on_figureleave)
                    self.prints[mpl.fig.canvas.GetId()] = mpl
                    self.sizer_thumbs.Add(mpl, 0, wx.EXPAND | wx.ALL, 5)

                    self.panel_thumbs.SendSizeEvent()
                    msg = '%d print(s) loaded.' % loaded
                    if len(not_loaded) > 0:
                        msg = msg + ' ' + not_loaded[0:len(not_loaded) - 2] + ' not loaded!'
                    self.status_bar.SetStatusText(msg)
                    wx.Yield()

            print('Elapsed time %f seconds' % (time.time() - start_time))

    # save noninterpolated csv
    def save_noninterpolated_csv(self):
        fname, ext = os.path.splitext(self.output_csv)
        output = fname+'_noninterpolated.csv'


    # def get_precision(self):
    #     choice = self.toolbar.choicePrec.GetSelection()
    #     if choice == 0:
    #         return 0.25
    #     elif choice == 1:
    #         return 0.50
    #     elif choice == 2:
    #         return 1.00
    #
    # def get_multiplier(self):
    #     choice = self.toolbar.choiceMult.GetSelection()
    #     return pow(10, choice)


class MayaviView(HasTraits):

    scene = Instance(MlabSceneModel, ())

    # The layout of the panel created by Traits
    view = View(Item('scene', editor=SceneEditor(), resizable=True, show_label=False))

    def __init__(self, fname):
        HasTraits.__init__(self)

        # plot the data
        reader = vtk.vtkPLYReader()
        if reader.CanReadFile(fname) == 0:
            print('Error: Invalid PLY file.')
        elif reader.CanReadFile(fname) == 1:
            print('Loading generated PLY file.')
            reader.SetFileName(os.path.join(fname))
            # reader.Update()
            # output = reader.GetOutput()
            # points = output.GetPoints()
            # self.point_array = vtk_to_numpy(points.GetData()) # points xyz
            # # invert z direction
            # self.point_array[:,2] *= -1
            # color_array = vtk_to_numpy(output.GetPointData().GetScalars()) # points color

            plydata = PlyData.read(str(fname))
            vertex = plydata['vertex']
            (x, y, z) = (vertex[t] for t in ('x', 'y', 'z'))
            # invert z direction for viewing
            z = -1.0 * z

            self.point_array = np.vstack((x, y, z))
            self.point_array = np.transpose(self.point_array)

            # choose either red or red_diffuse fields
            try:
                self.color_array = np.vstack((plydata['vertex']['red'], plydata['vertex']['green'], plydata['vertex']['blue']))
            except:
                self.color_array = np.vstack((plydata['vertex']['diffuse_red'], plydata['vertex']['diffuse_green'], plydata['vertex']['diffuse_blue']))
            self.color_array = np.transpose(self.color_array)

            sc=tvtk.UnsignedCharArray()
            sc.from_array(self.color_array)

            self.pts=mlab.points3d(x,y,z, mode='point', figure=self.scene.mayavi_scene)
            self.pts.mlab_source.dataset.point_data.scalars = sc
            self.pts.mlab_source.dataset.modified()

            mlab.outline()
            #mlab.show() #commented and still works. check

    # redraw mayavi
    def update(self):
        # clear old image

        self.clear_drawing()


        # redraw
        self.pts=mlab.points3d(self.point_array[:, 0],self.point_array[:, 1],self.point_array[:, 2], mode='point', figure=self.scene.mayavi_scene)
        self.pts.mlab_source.dataset.point_data.scalars = self.color_array
        self.pts.mlab_source.dataset.modified()
        mlab.outline()

    def remove_markers(self):
        for c in range(len(self.scene.engine.scenes[0].children)):
            if c != 0:
                self.scene.engine.scenes[0].children[-1].remove()

    def remove_last_marker(self):
        self.scene.engine.scenes[0].children[-1].remove()

    def remove_all(self):
        for s in range(len(self.scene.engine.scenes)):
            self.scene.engine.scenes[s].remove()

    def clear_drawing(self):
        for s in range(len(self.scene.engine.scenes)):
            for c in range(len(self.scene.engine.scenes[s].children)):
                self.scene.engine.scenes[s].children[-1].remove()

# for 3d cropping
class TC_Handler(Handler):

    def do_save(self, info):
        points_inside_index = np.where((info.object.point_array[:, 0] > info.object.x_min)
                                       & (info.object.point_array[:, 0] < info.object.x_max)
                                       & (info.object.point_array[:, 1] > info.object.y_min)
                                       & (info.object.point_array[:, 1] < info.object.y_max)
                                       & (info.object.point_array[:, 2] > info.object.z_min)
                                       & (info.object.point_array[:, 2] < info.object.z_max))
        info.object.point_array = np.array(info.object.point_array)[points_inside_index]
        info.object.color_array = np.array(info.object.color_array)[points_inside_index]
        info.ui.dispose()

# 3d cropping dialog
class ExtentDialog(HasTraits):
    """ A dialog to graphical adjust the extents of a filter.
    """

    # Data extents
    data_x_min = Float
    data_x_max = Float
    data_y_min = Float
    data_y_max = Float
    data_z_min = Float
    data_z_max = Float

    x_min = Range('data_x_min', 'data_x_max', 'data_x_min')
    x_max = Range('data_x_min', 'data_x_max', 'data_x_max')
    y_min = Range('data_y_min', 'data_y_max', 'data_y_min')
    y_max = Range('data_y_min', 'data_y_max', 'data_y_max')
    z_min = Range('data_z_min', 'data_z_max', 'data_z_min')
    z_max = Range('data_z_min', 'data_z_max', 'data_z_max')

    filter = Instance(HasTraits, allow_none=False)

    point_array = Array
    color_array = Array

    @on_trait_change('x_min,x_max,y_min,y_max,z_min,z_max')
    def update_extent(self):
        if (self.filter is not None
                    and self.x_min < self.x_max
                    and self.y_min < self.y_max
                    and self.z_min < self.z_max
                            ):
            self.filter.extent = (self.x_min, self.x_max,
                                  self.y_min, self.y_max,
                                  self.z_min, self.z_max)

    save_button = Action(name="Save", action="do_save")

    view = View('x_min', 'x_max', 'y_min', 'y_max', 'z_min', 'z_max',
                buttons=[save_button, 'Cancel'],
                handler=TC_Handler(),
                title='Edit extent', resizable=True)


# run parallel job
def run_job(items, obj):
    cnt = len(items)
    cores = multiprocessing.cpu_count()

    if cnt > 1 and cores > 1:
        print('Using multiprocess')
        pool = multiprocessing.Pool(processes=min(cnt, cores))
        result = pool.map(obj, items)
        pool.close()
    else:
        print('Using single process')
        result = list()
        for item in items:
            result.append(obj.__call__(item))
    return result
