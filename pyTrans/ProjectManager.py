__author__ = 'shujiedeng'

import wx
import os
import json
import hashlib
import glob
import numpy as np
from MatplotPanel import MatplotPanel
from Loader import Loader
from Transformer import run_job, MyDropTarget
from Processor import MyDropTarget as dt
from distutils.dir_util import copy_tree, remove_tree
import time
import matplotlib.cm as cm
import zipfile

IS_GTK = 'wxGTK' in wx.PlatformInfo
IS_WIN = 'wxMSW' in wx.PlatformInfo
IS_MAC = 'wxMac' in wx.PlatformInfo

class ProjectManager():
    def __init__(self, parent):
        self.parent = parent
        self.photogrammetry = parent.notebook.photogrammetry_panel
        self.processor = parent.notebook.processor_panel
        self.transformer = parent.notebook.transformer_panel
        self.status_bar = parent.status_bar

        # save project file history
        self.psavefilehistory = wx.FileHistory(9)
        self.config_psavefile = wx.Config(localFilename = "pyTrans-psavefile1", style=wx.CONFIG_USE_LOCAL_FILE)
        self.psavefilehistory.Load(self.config_psavefile)

        self.project_file_filter = "Project (*.ftproj)|*.ftproj"

    def on_export(self, event):
        '''
            zip without compression
        '''
        # before save the project, check if ply-in-processing & processor-in-processing saved
        self.ask_save()

        # create the export zip file
        last_path = ""
        if self.psavefilehistory.GetCount() > 0:
            last_path = self.psavefilehistory.GetHistoryFile(0)

        exportdialog = wx.FileDialog(self.parent, "Export and zip project", last_path, "", "Project (*.zip)|*.zip", wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT)

        if exportdialog.ShowModal() != wx.ID_CANCEL:
            path, (zipname, ext) = os.path.dirname(exportdialog.GetPath()), os.path.splitext(os.path.basename(exportdialog.GetPath()))

            zf = zipfile.ZipFile(exportdialog.GetPath(), mode='w')
            try:
                # zip everything into this folder: photogrammetry listed folders and csv at the bottom, and .ftproj

                # photogramemtry listed folders
                for row in range(self.photogrammetry.list_ctrl.GetItemCount()):
                    self.recursive_zip_helper(self.photogrammetry.paths[row], exportdialog.GetPath(), zf)

                # csv at the bottom
                import warnings
                warnings.filterwarnings('error')
                for mpl in self.transformer.mpls:
                    fname = self.transformer.mpls[mpl].fname
                    try: # zip can archive duplicate files, but it will raise a warning, catch this warning to avoid duplication
                        zf.write(fname)
                    except UserWarning:
                        print "duplicate"

                # save the .ftproj file
                photogrammetry_info = self.save_photogrammetry(True)
                processor_info = self.save_processor(True)
                transformer_info = self.save_transformer(True)

                obj = {'project': {'photogrammetry': photogrammetry_info,
                                   'processor': processor_info,
                                   'transformer': transformer_info},
                       'zip': True}

                with open(zipname+'.ftproj', 'wb') as fp:
                    json.dump(obj, fp)
                zf.write(zipname+'.ftproj')

                # the previous with statement creates the .ftproj file in software root directory, need to delete it
                os.remove(zipname+'.ftproj')

            finally:
                print 'closing'
                zf.close()

            self.status_bar.SetStatusText('Project saved.')
            wx.Yield()

    # open a project on given path
    def open_project(self, path):
        fname, ext = os.path.splitext(path)
        if ext.lower() != '.ftproj':
            print "not a project file"
        # parse the project structure
        else:
            try:
                with open(path, 'r') as fp:
                    self.parent.status_bar.SetStatusText("")
                    project = json.load(fp)
                    zip = project['zip']
                    root = os.path.dirname(path)
                    self.open_photogrammetry(project['project']['photogrammetry'], zip, root)
                    self.open_transformer(project['project']['transformer'], zip, root)
                    self.open_processor(project['project']['processor'], zip, root)

                    # set the active tab
                    try:
                        self.parent.notebook.SetSelection(project['project']['active_tab'])
                    except:
                        print 'old Digtrace project, no active tab saved, opening Create'

                    # add proj name to the window title
                    head, tail = os.path.split(path)
                    self.parent.Title = self.parent.app_name + ' - ' + tail

            except ValueError:
                self.parent.status_bar.SetStatusText("invalid project file.")

    # when clicked open project
    def on_open(self, event):
        last_path = ""
        if self.psavefilehistory.GetCount() > 0:
            last_path = self.psavefilehistory.GetHistoryFile(0)

        openfiledialog = wx.FileDialog(self.parent, "Open files", last_path, "", self.project_file_filter, wx.FD_OPEN | wx.FD_FILE_MUST_EXIST)

        if openfiledialog.ShowModal() != wx.ID_CANCEL:
            self.clear_all()
            path = openfiledialog.GetPath()
            self.open_project(path)



    def on_save(self, event):
        # before save the project, check if ply-in-processing & processor-in-processing saved
        self.ask_save()

        # self.status_bar.SetStatusText('Saving project...')
        wx.Yield()
        # self.transformer.on_save(event)

        if self.psavefilehistory.GetCount() == 0:
            last_path = ""
        else:
            last_path = self.psavefilehistory.GetHistoryFile(0)

        savefiledialog = wx.FileDialog(self.parent, "Save file", last_path, "", self.project_file_filter, wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT)
        if savefiledialog.ShowModal() != wx.ID_CANCEL:
            path = savefiledialog.GetPath()

            active_tab = self.parent.notebook.GetSelection()
            photogrammetry_info = self.save_photogrammetry()
            processor_info = self.save_processor()
            transformer_info = self.save_transformer()


            obj = {'project': {'active_tab': active_tab,
                               'photogrammetry': photogrammetry_info,
                               'processor': processor_info,
                               'transformer': transformer_info},
                   'zip': False}

            with open(path, 'wb') as fp:
                json.dump(obj, fp)


            # keep file history
            index = path.rfind('\\')  # WIN
            if IS_MAC:  # identify the path separator based on the used system
                index = path.rfind('/')
            path = path[:index]
            self.psavefilehistory.AddFileToHistory(path)
            self.psavefilehistory.Save(self.config_psavefile)

            self.status_bar.SetStatusText('Project saved.')
            wx.Yield()

    def save_transformer(self, iszip=False):
        # mainly saving the project library prints at the bottom panel
        transformer_info = {}

        if hasattr(self.transformer, 'cntrpanel'):
            transformer_info['contour'] = True
        if len(self.transformer.mpls) > 0:
            bottom_panel = list()
            for mpl in self.transformer.mpls:
                fname = self.transformer.mpls[mpl].fname

                A = self.transformer.mpls[mpl].A
                if A is not None:
                    A = A.tolist()

                if hasattr(self.transformer.panel_master, 'mpl') and fname == self.transformer.panel_master.mpl.fname:
                    #lmark_xy = self.transformer.lmark_xy[0].tolist()
                    lmark_xy = self.transformer.mpls[mpl].lmark_xy
                    if lmark_xy is not None:
                        # self.q.put((fname, lmark_xy))
                        lmark_xy = lmark_xy.tolist()
                    entry = {'fname': fname if not iszip else os.path.join(*(fname.split(os.path.sep)[1:])),
                             'lmark_xy': lmark_xy,
                             'A': A,
                             'multiplier': self.transformer.mpls[mpl].multiplier,
                             'precision': self.transformer.mpls[mpl].precision,
                             'panel_master': True,
                             'hash': self.set_file_hash(fname)}
                elif hasattr(self.transformer.panel_source, 'mpl') and fname == self.transformer.panel_source.mpl.fname:
                    #lmark_xy = self.transformer.lmark_xy[1].tolist()
                    lmark_xy = self.transformer.mpls[mpl].lmark_xy
                    if lmark_xy is not None:
                        # self.q.put((fname, lmark_xy))
                        lmark_xy = lmark_xy.tolist()
                    entry = {'fname': fname if not iszip else os.path.join(*(fname.split(os.path.sep)[1:])),
                             'lmark_xy': lmark_xy,
                             'A': A,
                             'multiplier': self.transformer.mpls[mpl].multiplier,
                             'precision': self.transformer.mpls[mpl].precision,
                             'panel_source': True,
                             'hash': self.set_file_hash(fname)}
                else:
                    lmark_xy = self.transformer.mpls[mpl].lmark_xy
                    if lmark_xy is not None:
                        # self.q.put((fname, lmark_xy))
                        lmark_xy = lmark_xy.tolist()
                    entry = {'fname': fname if not iszip else os.path.join(*(fname.split(os.path.sep)[1:])),
                             'lmark_xy': lmark_xy,
                             'A': A,
                             'multiplier': self.transformer.mpls[mpl].multiplier,
                             'precision': self.transformer.mpls[mpl].precision,
                             'hash': self.set_file_hash(fname)}
                bottom_panel.append(entry)
            transformer_info['bottom_panel'] = bottom_panel
            return transformer_info
        return transformer_info

    def save_processor(self, iszip=False):
        processor_info = {}
        processor_info['color_plan'] = self.processor.toolbar.choiceCm.GetSelection()
        processor_info['black_white_toggle'] = self.processor.toolbar.GetToolState(wx.ID_FILE7)
        processor_info['contour_crop_toggle'] = self.processor.toolbar.GetToolState(wx.ID_FILE2)
        if self.processor.threshold_slider is not None:
            processor_info['threshold_value'] = self.processor.threshold_slider.Value
            processor_info['threshold_start'] = self.processor.threshold_slider.SelStart
            processor_info['threshold_end'] = self.processor.threshold_slider.SelEnd
        if self.processor.crop_contour_slider is not None:
            processor_info['crop_contour_value'] = self.processor.crop_contour_slider.Value
            processor_info['crop_contour_start'] = self.processor.crop_contour_slider.SelStart
            processor_info['crop_contour_end'] = self.processor.crop_contour_slider.SelEnd
        if hasattr(self.processor.panel_main, 'mpl'):
            processor_info['active_file'] = self.processor.current_fname if not iszip else os.path.join(*(self.processor.current_fname.split(os.path.sep)[1:]))
            processor_info['hash'] = self.set_file_hash(self.processor.current_fname)
            # processor_info['original_file'] = self.processor.panel_main.mpl.fname
            # processor_info['active_file'] = self.processor.panel_main.mpl.fname
            # processor_info['hash'] = self.set_file_hash(self.processor.panel_main.mpl.fname)
            # # save temp csv
            # if not self.processor.current_xyz is None:
            #     fname = str(int(time.time())) + os.path.basename(processor_info['original_file'])
            #     dirname = os.path.join(os.getcwd(), 'Temp')
            #     if not os.path.exists(dirname):
            #         os.makedirs(dirname)
            #     fpath = os.path.join(dirname, fname)
            #     # if threshold toggled off
            #     if not self.processor.toolbar.GetToolState(wx.ID_FILE7):
            #         np.savetxt(fpath, self.processor.current_xyz, fmt='%.4f')
            #     else:
            #         np.savetxt(fpath, self.processor.original_xyz, fmt='%.4f')
            #     if os.path.exists(fpath):
            #         processor_info['active_file'] = fpath
            #         processor_info['hash'] = self.set_file_hash(fpath)
            if self.processor.lmark_xy is not []:
                # lmark_list = []
                # for i, lm in enumerate(self.processor.lmark_xy):
                #     lmark_list.append({str(self.processor.texts[i]._text): lm.tolist()})
                processor_info['landmarks'] = self.processor.lmark_xy.tolist()
            processor_info['multiplier'] = self.processor.panel_main.mpl.multiplier
            processor_info['precision'] = self.processor.panel_main.mpl.precision
            processor_info['contour_level_start'] = self.processor.panel_main.mpl.contour_level_start


        # if self.processor.mayavi_panel is not None:
        #     processor_info['3d_view_toggle'] = True
        # else:
        #     processor_info['3d_view_toggle'] = False
        if self.processor.toolbar.GetToolState(wx.ID_FORWARD):
            if self.processor.contour_slider is not None and hasattr(self.processor.contour_slider, 'UserValue'):
                processor_info['contour_interval'] = self.processor.contour_slider.UserValue

        return processor_info

    def save_photogrammetry(self, iszip=False):
        photogrammetry_info = {}
        folder_list = []
        for row in range(self.photogrammetry.list_ctrl.GetItemCount()):
            hash_list = []
            input_images = glob.glob(os.path.join(self.photogrammetry.paths[row], "*.jpg"))
            for f in input_images:
                zipf = f if not iszip else os.path.join(*(f.split(os.path.sep)[1:])) # remove drive letter and slash following it
                hash_list.append({zipf: self.set_file_hash(f)})

            ply_path = self.photogrammetry.list_ctrl.GetItem(row, 1).GetText()
            if os.path.exists(ply_path):
                ply_hash = self.set_file_hash(ply_path)
            else:
                ply_hash = ""
            entry = {'folder_path': self.photogrammetry.paths[row] if not iszip else os.path.join(*(self.photogrammetry.paths[row].split(os.path.sep)[1:])),
                     'ply_path': ply_path if not iszip else os.path.join(*(ply_path.split(os.path.sep)[1:])),
                     'ply_hash': ply_hash,
                     'sensor_size': self.photogrammetry.list_ctrl.GetItem(row, 2).GetText().rstrip('\n'),
                     'input_images_hash': hash_list}
            folder_list.append(entry)
        photogrammetry_info['folder_list'] = folder_list
        if self.photogrammetry.thumbs_ctrl.GetItemCount() != 0:
            photogrammetry_info['thumbnail_folder'] = self.photogrammetry.thumbs_ctrl.GetShowDir() if not iszip else os.path.join(*(self.photogrammetry.thumbs_ctrl.GetShowDir().split(os.path.sep)[1:]))
        if hasattr(self.photogrammetry, 'image_path'):
            photogrammetry_info['display_image'] = self.photogrammetry.image_path if not iszip else os.path.join(*(self.photogrammetry.image_path.split(os.path.sep)[1:]))
        if self.photogrammetry.loaded_ply_index != -1:
            if not self.photogrammetry.ply_edited:
                photogrammetry_info['display_ply'] = self.photogrammetry.list_ctrl.GetItemText(self.photogrammetry.loaded_ply_index, 1) if not iszip else os.path.join(*(self.photogrammetry.list_ctrl.GetItemText(self.photogrammetry.loaded_ply_index, 1).split(os.path.sep)[1:]))
        #photogrammetry_info['scaling_method'] = self.photogrammetry.toolbar.choiceScale.GetSelection()

        return photogrammetry_info

    def open_photogrammetry(self, doc, iszip, root):
        print "open photogrammetry"
        #self.photogrammetry.toolbar.choiceScale.SetSelection(doc['scaling_method'])

        # load list
        for i, folder in enumerate(doc['folder_list']):
            folder_path = folder['folder_path'] if not iszip else os.path.join(root, folder['folder_path'])
            self.photogrammetry.add_list_item(folder_path)

            # if the images are the same, firstly the count should match
            if len(glob.glob(os.path.join(folder_path, "*.jpg"))) == len(folder['input_images_hash']):
                same_images = True
                # secondly, compare the hash
                for image in folder['input_images_hash']:
                    temp_image_path = os.path.join(root, image.keys()[0])
                    if os.path.exists(temp_image_path):
                        if self.compare_hash(image.values()[0], temp_image_path):  # check hash
                            continue
                    same_images = False
                    break
            else:
                same_images = False

            if same_images:
                ply_path = folder['ply_path'] if not iszip else os.path.join(root, folder['ply_path'])
                if os.path.exists(ply_path) and self.compare_hash(folder['ply_hash'], ply_path):
                    self.photogrammetry.list_ctrl.SetStringItem(i, 1, ply_path)
                    # if ply of this folder was displayed
                    if 'display_ply' in doc and not 'display_image' in doc:
                        if doc['display_ply'] == folder['ply_path']:
                            self.photogrammetry.displayPLY(i)
                else:
                    print "ply file has been changed. Please regenerate."
            else:
                print "images in folder " + str(folder_path) + " have been changed. Regenerate to update."

            # load thumbnails if it was shown
            if 'thumbnail_folder' in doc and doc['thumbnail_folder'] == folder['folder_path']:
                self.photogrammetry.displayThumbs(i)

        if 'display_image' in doc and not 'display_ply' in doc:
            display_image = doc['display_image'] if not iszip else os.path.join(root, doc['display_image'])
            self.photogrammetry.display_image(display_image)



    def open_processor(self, doc, iszip, root):
        print "open processor"
        if 'active_file' in doc:
            active_file_path = doc['active_file'] if not iszip else os.path.join(root, doc['active_file'])
            if self.compare_hash(doc['hash'], active_file_path):
                # self.load_processor_print(doc)
                for mpl in self.parent.prints:
                    if self.parent.prints[mpl].fname == active_file_path:
                        self.load_processor_print(doc, self.parent.prints[mpl], iszip, root)

                # set black-white toggle params
                if doc['black_white_toggle']:
                    # self.processor.do_threshold(doc['threshold_start'], doc['threshold_end'])
                    self.processor.toolbar.ToggleTool(wx.ID_FILE7, True)
                    evt = wx.PyCommandEvent(wx.EVT_BUTTON.typeId, wx.ID_FILE7)
                    self.processor.on_toggle_threshold(evt, doc['threshold_value'], doc['threshold_start'], doc['threshold_end'])

                # set black-white toggle params
                if doc['contour_crop_toggle']:
                    # self.processor.do_threshold(doc['threshold_start'], doc['threshold_end'])
                    self.processor.toolbar.ToggleTool(wx.ID_FILE2, True)
                    evt = wx.PyCommandEvent(wx.EVT_BUTTON.typeId, wx.ID_FILE2)
                    self.processor.on_toggle_crop_contour(evt, doc['crop_contour_value'], doc['crop_contour_start'], doc['crop_contour_end'], doc['contour_interval'])

                # set contour toggle
                elif 'contour_interval' in doc:
                    self.processor.toolbar.ToggleTool(wx.ID_FORWARD, True)
                    evt = wx.PyCommandEvent(wx.EVT_BUTTON.typeId, wx.ID_FORWARD)
                    self.processor.on_toggle_contours(evt, doc['contour_interval'])

                # set color plan, has to be the last otherwise will be override
                options = ["jet", "terrain", "bone", "copper", "gray", "hot", "Greys"]
                colormap = options[doc['color_plan']]
                self.processor.toolbar.choiceCm.SetSelection(doc['color_plan'])
                if 'contour_interval' not in doc and not doc['black_white_toggle']:  # enforce color plan if not in contour mode. because contour and b&w has grey colormap by default
                    evt = wx.PyCommandEvent(wx.EVT_CHOICE.typeId, self.processor.toolbar.choiceCm.GetId())
                    evt.String = colormap
                    self.processor.on_change_colormap(evt)

    def open_transformer(self, doc, iszip, root):
        print "open transformer"
        if 'bottom_panel' in doc:
            for model in doc['bottom_panel']:
                model_path = model['fname'] if not iszip else os.path.join(root, model['fname'])
                if self.compare_hash(model['hash'], model_path):
                    mpl = self.load_bottom_csv(model, iszip, root)
                    if 'panel_master' in model:
                        print "load panel master"
                        self.load_transformer_prints(0, mpl)  # panel_master
                    if 'panel_source' in model:
                        print "load panel source"
                        self.load_transformer_prints(1, mpl)  # panel_source

    def set_file_hash(self, file_path):
        BLOCKSIZE = 65536
        hasher = hashlib.sha512()
        with open(file_path, 'rb') as afile:
            buf = afile.read(BLOCKSIZE)
            while len(buf) > 0:
                hasher.update(buf)
                buf = afile.read(BLOCKSIZE)
        print(hasher.hexdigest())
        return hasher.hexdigest()

    def compare_hash(self, hash_code, file_path):
        return self.set_file_hash(file_path) == hash_code

    def load_bottom_csv(self, model, iszip, root):
        paths = []
        model_path = model['fname'] if not iszip else os.path.join(root, model['fname'])
        paths.append(model_path)
        result = run_job(paths, Loader(model['precision'], model['multiplier']))

        ch = self.transformer.sizer_thumbs.GetChildren()
        if len(ch) == 1 and type(ch[0].GetWindow()) is wx.StaticText:
            self.transformer.sizer_thumbs.Clear(True)

        not_loaded = ''
        loaded = 0
        sizes = ''
        for xyzi, xyz, fname, guessed_multiplier in result:
            if xyzi is None:
                not_loaded = not_loaded + os.path.basename(fname) + ', '

            else:
                loaded += 1

                # 'normalize' z axis: min(z)=0
                xyz, xyzi = self.parent.normalize_z_axis(xyz, xyzi, np.nanmin(xyzi[2]))

                #create a a np array from saved value of lmark_xy IF IT IS NOT None
                if model['lmark_xy'] is None:
                    xy=None
                else:
                    xy=np.copy(model['lmark_xy'])
                mpl = MatplotPanel(self.transformer.panel_thumbs, xyzi, xyz, model['multiplier'], model['precision'],
                                   title=os.path.basename(fname), fname=fname, lmark_xy=xy, A=np.asarray(model['A']))
                mpl.data = wx.TextDataObject(str(mpl.fig.canvas.GetId()))
                mpl.button_press_event = mpl.fig.canvas.mpl_connect('button_press_event', self.parent.on_drag)
                mpl.motion_notify_event = mpl.fig.canvas.mpl_connect('motion_notify_event', self.parent.on_mouseover)
                mpl.figure_leave_event = mpl.fig.canvas.mpl_connect('figure_leave_event', self.parent.on_figureleave)
                self.transformer.mpls[mpl.fig.canvas.GetId()] = mpl
                self.transformer.sizer_thumbs.Add(mpl, 0, wx.EXPAND | wx.ALL, 5)

                sizes = sizes + mpl.real_size_string() + '; '

                return mpl

    def load_transformer_prints(self, pid, mpl):
        # panel = self.transformer.window
        if pid == 0:
            panel = self.transformer.panel_master
        else:
            panel = self.transformer.panel_source

        sizer = panel.GetSizer()

        # Revert colormap of the print not being used any more
        if hasattr(panel, 'mpl') and panel.mpl:
            panel.mpl.delete_figure()
            panel.mpl.mpl_src.used = False
            panel.mpl.mpl_src.set_cmap()
            panel.mpl.mpl_src.pid = -1

        # Change colormap of the print being used
        mpl.used = True
        mpl.set_cmap('gray')
        mpl.pid = pid

        # Create a new plot, add it to a cleared sizer (clearing e.g. the static text) and subscribe to the event
        panel.mpl = MatplotPanel(panel, mpl.xyzi, mpl.xyz, mpl.multiplier, mpl.precision, (1, 1),  mpl,  mpl.title, mpl.fname, pid=pid, current_vmin=mpl.current_vmin, current_vmax=mpl.current_vmax)
        sizer.Clear(True)

        # restore landmarks if exist
        # wow Shujie what is this code :D
        if mpl.lmark_xy is not None and len(mpl.lmark_xy) > 0:
            self.transformer.lmark_xy[pid] = np.copy(mpl.lmark_xy)
            [h.remove() for h in self.transformer.lmark_h[pid] if h is not None]
            cnt1 = self.transformer.lmark_xy[pid].shape[0]
            cnt2 = len(self.transformer.lmark_h[pid])
            if cnt2 == 0:
                self.transformer.lmark_h[pid] = [None] * cnt1
                cnt2 = cnt1
                if len(self.transformer.lmark_h[1 - pid]) == 0:
                    self.transformer.lmark_h[1 - pid] = [None] * cnt1
            nan_arr = np.zeros((cnt2 - cnt1, 2))
            nan_arr[:] = np.NAN
            self.transformer.lmark_xy[pid] = np.vstack((self.transformer.lmark_xy[pid], nan_arr))
            self.transformer.lmark_h[pid][cnt1:cnt2] = [None] * (cnt2 - cnt1)

        # add plot title to the sizer
        txt = wx.StaticText(panel, wx.ID_ANY, mpl.title, style=wx.ALIGN_CENTER)
        txt.SetFont(wx.Font(18, wx.SWISS, wx.NORMAL, wx.NORMAL))
        txt.SetForegroundColour((128, 128, 128))
        sizer.Add(txt, flag=wx.CENTER)

        # add plot panel
        sizer.Add(panel.mpl, 1, wx.EXPAND | wx.ALL, 5)
        a = MyDropTarget(panel)
        panel.SetDropTarget(a)
        panel.mpl.canvas.mpl_connect('button_press_event', a.on_press)
        a.hid = panel.mpl.canvas.mpl_connect('motion_notify_event', a.on_motion)
        panel.mpl.canvas.mpl_connect('button_release_event', a.on_release)
        panel.mpl.fig.canvas.mpl_connect('key_press_event', a.on_key_press)
        panel.mpl.fig.canvas.mpl_connect('key_release_event', a.on_key_release)

        # Plot existing landmarks and save/update their handles
        if self.transformer.lmark_xy[pid].size:
            axis = panel.mpl.ax.axis()

            for i, h in enumerate(self.transformer.lmark_h[pid]):
                c = self.transformer.lmark_h[0][i]
                col = ''
                if c is not None:
                    col = c.get_markerfacecolor()
                else:
                   # get the contract color of the background and set it to the landmarker
                    color_value = (panel.mpl.xyzi[2][self.transformer.lmark_xy[pid][i,1]][self.transformer.lmark_xy[pid][i,0]] - panel.mpl.vmin) / (panel.mpl.vmax - panel.mpl.vmin)
                    if color_value <= 0.5:
                        color_value = color_value + 0.5
                    else:
                        color_value = color_value - 0.5
                    col = cm.jet(color_value)

                self.transformer.lmark_h[pid][i], = panel.mpl.ax.plot(self.transformer.lmark_xy[pid][i, 0],
                                                                    self.transformer.lmark_xy[pid][i, 1],
                                                                    marker='o',
                                                                    markerfacecolor=col,
                                                                    markersize=a.marker_size)


            if self.transformer.lmark_active and self.transformer.lmark_h[pid][self.transformer.lmark_active]:
                self.transformer.lmark_h[pid][self.transformer.lmark_active].set_markeredgewidth(a.active_width)
                self.transformer.lmark_h[pid][self.transformer.lmark_active].set_markeredgecolor(a.active_color)

            panel.mpl.ax.axis(axis)

        #enable icons
        self.transformer.toolbar.EnableTool(wx.ID_ADD, True)
        self.transformer.toolbar.EnableTool(wx.ID_FILE9, True)
        if pid==1:
            self.transformer.toolbar.EnableTool(wx.ID_SAVEAS, True)

        self.transformer.contour_refresh()

        # Force redraw: windows.Refresh() doesn't seem to work
        panel.SendSizeEvent()

    def load_processor_print(self, model, mpl, iszip, root):
        panel = self.processor.panel_main
        sizer = panel.GetSizer()

        # get mpl
        # paths = []
        # paths.append(model['active_file'])
        # result = run_job(paths, Loader(model['precision'], model['multiplier']))

        if self.processor.matplot_panel is not None:
            self.processor.matplot_panel.delete_figure()  # delete old figure to free memory

        # Create a new plot, add it to a cleared sizer (clearing e.g. the static text) and subscribe to the event
        # panel.mpl = MatplotPanel(panel, result[0][0], result[0][1], model['multiplier'], model['precision'], title=os.path.basename(model['active_file']), fname=model['active_file'], lmark_xy=model['landmarks'])
        fname = model['active_file'] if not iszip else os.path.join(root, model['active_file'])
        panel.mpl = MatplotPanel(panel, mpl.xyzi, mpl.xyz, model['multiplier'], model['precision'], title=os.path.basename(fname), fname=fname, lmark_xy=model['landmarks'])

        panel.mpl.contour_level_start = model['contour_level_start']
        mpl_src = panel.mpl

        # load landmarks
        if mpl_src.lmark_xy is not None and len(mpl_src.lmark_xy) > 0:
            #enable relevant icons
            self.processor.toolbar.EnableTool(wx.ID_DELETE, True)
            self.processor.toolbar.EnableTool(wx.ID_VIEW_LIST, True)

            self.processor.lmark_xy = np.copy(mpl_src.lmark_xy)

            for i, h in enumerate(self.processor.lmark_xy):
                h, = panel.mpl.ax.plot(self.processor.lmark_xy[i][0], self.processor.lmark_xy[i][1], 'o', markersize=self.processor.marker_size)

                self.processor.lmark_h.append(h)

                # get the contract color of the background and set it to the landmarker
                color_value = (panel.mpl.xyzi[2][self.processor.lmark_xy[i][1]][self.processor.lmark_xy[i][0]] - mpl_src.vmin) / (mpl_src.vmax - mpl_src.vmin)
                if color_value <= 0.5:
                    color_value = color_value + 0.5
                else:
                    color_value = color_value - 0.5
                color = cm.jet(color_value)
                self.processor.lmark_h[i].set_markerfacecolor(color)

                txt=panel.mpl.ax.text(self.processor.lmark_xy[i][0]-25, self.processor.lmark_xy[i][1]+25, " ", color=color)
                self.processor.texts.append(txt)

        drop_object = dt(panel)
        self.processor.matplot_panel = panel.mpl
        self.processor.mayavi_panel = None

        sizer.Clear(True)
        self.processor.slider_sizer.Clear(True)

        self.processor.current_xyz = mpl_src.xyz
        self.processor.current_xyzi = mpl_src.xyzi
        self.processor.current_fname = mpl_src.fname
        self.processor.original_xyz = mpl_src.xyz
        self.processor.original_xyzi = mpl_src.xyzi

        drop_object.rotate_mode = False

        self.processor.toolbar.ToggleTool(wx.ID_FILE7, False)
        self.processor.toolbar.ToggleTool(wx.ID_FILE8, False)
        self.processor.toolbar.ToggleTool(wx.ID_FILE9, False)
        self.processor.toolbar.ToggleTool(wx.ID_FIND, False)
        self.processor.toolbar.ToggleTool(wx.ID_ADD, False)
        self.processor.toolbar.ToggleTool(wx.ID_FORWARD, False)
        self.processor.toolbar.ToggleTool(wx.ID_ICONIZE_FRAME, False)


        # add plot panel
        sizer.Add(panel.mpl, 1, wx.EXPAND | wx.ALL, 5)
        panel.mpl.canvas.mpl_connect('button_press_event', self.processor.on_press)
        panel.mpl.canvas.mpl_connect('button_release_event', self.processor.on_release)

        # add plot title to the sizer
        txt = wx.StaticText(panel, wx.ID_ANY, mpl_src.title, style=wx.ALIGN_CENTER)
        txt.SetFont(wx.Font(18, wx.SWISS, wx.NORMAL, wx.NORMAL))
        txt.SetForegroundColour((128, 128, 128))
        sizer.Add(txt, flag=wx.CENTER)

        drop_object.create_side_panels(mpl_src)

        #set colormap selection jet active
        self.processor.toolbar.choiceCm.SetSelection(0)

        #enable icons
        self.processor.toolbar.EnableTool(wx.ID_SAVEAS, True)
        self.processor.toolbar.EnableTool(wx.ID_FIND, True)
        self.processor.toolbar.EnableTool(wx.ID_REDO, True)
        self.processor.toolbar.EnableTool(wx.ID_UP, True)
        self.processor.toolbar.EnableTool(wx.ID_FILE8, True)
        self.processor.toolbar.EnableTool(wx.ID_ICONIZE_FRAME, True)
        self.processor.toolbar.EnableTool(wx.ID_ADD, True)
        self.processor.toolbar.EnableTool(wx.ID_FILE9, True)
        self.processor.toolbar.EnableTool(wx.ID_FILE7, True)
        self.processor.toolbar.EnableTool(wx.ID_FILE1, True)
        self.processor.toolbar.EnableTool(wx.ID_FORWARD, True)
        self.processor.toolbar.choiceCm.Enable(True)

        self.processor.Refresh()

        # Force redraw: windows.Refresh() doesn't seem to work
        panel.SendSizeEvent() #needed

    def clear_all(self):
        self.processor.reset()
        self.photogrammetry.reset()
        self.transformer.reset()

    def ask_save(self):
        # photogrammetry only
        if self.photogrammetry.ply_edited and not self.processor.csv_edited:
            msg = "Save the processing 3D model to the Project Library before saving the project?"
            dlg = wx.MessageDialog(self.parent, msg, 'Alert!', wx.YES_NO|wx.ICON_INFORMATION)
            if dlg.ShowModal() == wx.ID_YES:
                dlg.Destroy()
                evt = wx.PyCommandEvent(wx.EVT_BUTTON.typeId, wx.ID_SAVEAS)
                self.photogrammetry.on_saveas(evt)


        # processor only
        elif not self.photogrammetry.ply_edited and self.processor.csv_edited:
            msg = "Save the processing print in Measure panel to the Project Library before saving the project?"
            dlg = wx.MessageDialog(self.parent, msg, 'Alert!', wx.YES_NO|wx.ICON_INFORMATION)
            if dlg.ShowModal() == wx.ID_YES:
                dlg.Destroy()
                evt = wx.PyCommandEvent(wx.EVT_BUTTON.typeId, wx.ID_SAVEAS)
                self.processor.on_save(evt)


        # both
        elif self.photogrammetry.ply_edited and self.processor.csv_edited:
            msg = "Save the processing 3D model and print in Measure panel to the Project Library before saving the project?"
            dlg = wx.MessageDialog(self.parent, msg, 'Alert!', wx.YES_NO|wx.ICON_INFORMATION)
            if dlg.ShowModal() == wx.ID_YES:
                dlg.Destroy()

                # fake button event calls
                evt1 = wx.PyCommandEvent(wx.EVT_BUTTON.typeId, wx.ID_SAVEAS)
                self.photogrammetry.on_saveas(evt1)

                evt2 = wx.PyCommandEvent(wx.EVT_BUTTON.typeId, wx.ID_SAVEAS)
                self.processor.on_save(evt2)

    def recursive_zip_helper(self, zipee_path, zip_to_path, zip_handle):
        # zippee_path: the directory of the content that will be zipped
        # zip_to_path: the directory where the zipped file is
        for root, dirs, files in os.walk(zipee_path):
            for a_file in files:
                zip_handle.write(os.path.join(root, a_file))