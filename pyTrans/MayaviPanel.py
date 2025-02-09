__author__ = 'Rachid'
import wx

from traits.etsconfig.api import ETSConfig
ETSConfig.toolkit = 'wx'

import numpy as np

from traits.api import HasTraits, Instance
from traitsui.api import View, Item

from mayavi.sources.api import ArraySource
from mayavi.modules.api import Surface

from mayavi.core.ui.api import SceneEditor, MlabSceneModel
from mayavi import mlab

from traitsui.handler import Handler


class RemoveButtonsToolbarHandler(Handler):
    def position(self, info):
        editor = info.ui._editors[0]
        editor._scene._get_tool_bar_manager()._get_groups()[2].remove(
            editor._scene._get_tool_bar_manager()._get_groups()[2]._get_items()[1])


class MayaviPanel(wx.Panel):
    def __init__(self, parent, xyzi, multiplier, size=None,  title='', fname='', lmark_xy=None, memory=0):
        if size is None:
            #size_p = parent.GetSize()
            #size = (max(120, size_p[1]), size_p[1] - 30)
            size = parent.GetSize()

        wx.Panel.__init__(self, parent, wx.ID_ANY, size=size)

        self.xyzi = xyzi
        self.title = title
        self.lmark_xy = lmark_xy
        self.fname = fname
        self.master_fname = None
        self.master_lmark_xy = None
        self.cbar = None
        self.used = False
        self.multiplier=multiplier

        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(self.sizer)

        self.mayavi_view = MayaviView(self.xyzi, memory)

        # Use traits to create a panel, and use it as the content of this
        # wx frame.
        self.control = self.mayavi_view.edit_traits(
                        parent=self,
                        kind='subpanel',
                        handler=RemoveButtonsToolbarHandler()).control

        self.sizer.Clear()
        self.sizer.Add(self.control, 1, wx.EXPAND, wx.EXPAND, 5)

        self.SendSizeEvent()

    def update(self, xyzi):
        self.mayavi_view.update(xyzi)

class MayaviView(HasTraits):

    scene = Instance(MlabSceneModel, ())

    # The layout of the panel created by Traits
    view = View(Item('scene', editor=SceneEditor(), resizable=True,
                    show_label=False),
                    resizable=True)

    def __init__(self, xyzi, memory):
        HasTraits.__init__(self)

        x = np.transpose(xyzi[0])
        y = np.transpose(xyzi[1])

        #x = xyzi[0]
        #y = xyzi[1]
        z = -xyzi[2]
        z = np.transpose(z)

        if memory>0:
            mlab.surf(x, y, z, figure=self.scene.mayavi_scene)
        else:
            mlab.points3d(x, y, z, z, colormap="jet", mode='point', figure=self.scene.mayavi_scene)

        # src = ArraySource(scalar_data=z)
        # self.scene.engine.add_source(src)
        # src.add_module(Surface())


    def update(self, xyzi):
        self.scene.engine.scenes[0].children[0].remove()

        x = np.transpose(xyzi[0])
        y = np.transpose(xyzi[1])
        z = xyzi[2]

        mlab.surf(x, y, z, figure=self.scene.mayavi_scene)

        # src = ArraySource(scalar_data=z)
        # self.scene.engine.add_source(src)
        # src.add_module(Surface())


