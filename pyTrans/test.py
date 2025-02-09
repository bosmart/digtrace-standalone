from traits.etsconfig.api import ETSConfig
ETSConfig.toolkit = 'qt4'

import numpy
from mayavi.mlab import *

t = numpy.linspace(0, 4 * numpy.pi, 20)
cos = numpy.cos
sin = numpy.sin

x, y, z = numpy.random.random((3, 40))

points3d(x, y, z)

show()
