import numpy as np
import scipy.linalg
#from mpl_toolkits.mplot3d import Axes3D
#import matplotlib.pyplot as plt
import pandas as pd
import cv2, pylab

# some 3-dim points
def flatten(data, xyzi,coords, direction):


    coords=np.sort(coords)
    start_coord=coords[0]
    end_coord=coords[1]

    X=xyzi[0]
    Y=xyzi[1]
    Z=xyzi[2]

    # XX = X.flatten()
    # YY = Y.flatten()

    m,n = Z.shape

    ZToFlatten=Z

# # apply opencv erode and dilate
# kernel = np.ones((5,5), np.uint8)
#
# ZToFlatten1 = cv2.erode(ZToFlatten, kernel, iterations=1)
# ZToFlatten1 = cv2.dilate(ZToFlatten, kernel, iterations=1)
# ZToFlatten2 = cv2.erode(ZToFlatten1, kernel, iterations=1)
# ZToFlatten2 = cv2.dilate(ZToFlatten1, kernel, iterations=1)
#
# ZToFlatten3=ZToFlatten
# for i in range(0,5):
#     ZToFlatten3 = cv2.erode(ZToFlatten3, kernel, iterations=1)
#     ZToFlatten3 = cv2.dilate(ZToFlatten3, kernel, iterations=1)
#
# ZToFlatten22 = cv2.erode(ZToFlatten, kernel, iterations=2)
# ZToFlatten22 = cv2.dilate(ZToFlatten, kernel, iterations=2)
# #ZToFlatten33 = cv2.erode(ZToFlatten, kernel, iterations=10)
# #ZToFlatten33 = cv2.dilate(ZToFlatten, kernel, iterations=10)
# #ZToFlatten33 = cv2.GaussianBlur(ZToFlatten,(49,49),0)
#
# kernel = np.ones((29,29),np.float32)/(29*29)
# ZToFlatten33 = cv2.filter2D(np.nan_to_num(ZToFlatten),-1,kernel)
#
# indecesToReplace=np.where(ZToFlatten1<0.01)
# ZToFlatten1[indecesToReplace]=None
# indecesToReplace=np.where(ZToFlatten1>100)
# ZToFlatten1[indecesToReplace]=None
#
# indecesToReplace=np.where(ZToFlatten2<0.01)
# ZToFlatten2[indecesToReplace]=None
# indecesToReplace=np.where(ZToFlatten2>100)
# ZToFlatten2[indecesToReplace]=None
#
# indecesToReplace=np.where(ZToFlatten3<0.01)
# ZToFlatten3[indecesToReplace]=None
# indecesToReplace=np.where(ZToFlatten3>100)
# ZToFlatten3[indecesToReplace]=None
#
# indecesToReplace=np.where(ZToFlatten22<0.01)
# ZToFlatten22[indecesToReplace]=None
# indecesToReplace=np.where(ZToFlatten22>100)
# ZToFlatten22[indecesToReplace]=None
#
# indecesToReplace=np.where(ZToFlatten33<0.01)
# ZToFlatten33[indecesToReplace]=None
# indecesToReplace=np.where(ZToFlatten33>100)
# ZToFlatten33[indecesToReplace]=None
#
# ax = plt.subplot(421)
# plt.imshow(ZToFlatten, origin='lower', interpolation='none')
# ax = plt.subplot(423)
# plt.imshow(ZToFlatten1, origin='lower', interpolation='none')
# #ax.set_title('Original image')
# ax = plt.subplot(425)
# plt.imshow(ZToFlatten2, origin='lower', interpolation='none')
# #ax.set_title('Flattened image')
# ax = plt.subplot(427)
# plt.imshow(ZToFlatten3, origin='lower', interpolation='none')
# #ax.set_title('Flattened image')
#
# ax = plt.subplot(422)
# plt.imshow(ZToFlatten, origin='lower', interpolation='none')
# ax = plt.subplot(424)
# plt.imshow(ZToFlatten1, origin='lower', interpolation='none')
# #ax.set_title('Original image')
# ax = plt.subplot(426)
# plt.imshow(ZToFlatten22, origin='lower', interpolation='none')
# #ax.set_title('Flattened image')
# ax = plt.subplot(428)
# plt.imshow(ZToFlatten33, origin='lower', interpolation='none')
# #ax.set_title('Flattened image')
#
#
#
# # try fitting the surface with erode/dilute x5

    u=np.reshape(ZToFlatten,(n*m,1),order='F')

    data[:,2]=u[:,0]

    # create a data section to flatten
    dataToFlatten=data

    if direction==1:
        minAxis=X[0,start_coord]
        maxAxis = X[0, end_coord]
        toFlatten1 = np.where(dataToFlatten[:, 0] >= minAxis)  # intentionally swapped
        toFlatten2 = np.where(dataToFlatten[:, 0] <= maxAxis)
    else:
        minAxis = Y[start_coord,0]
        maxAxis = Y[end_coord,0]
        toFlatten1 = np.where(dataToFlatten[:, 1] >= minAxis)  # intentionally swapped
        toFlatten2 = np.where(dataToFlatten[:, 1] <= maxAxis)

    dataToFlatten = dataToFlatten[np.intersect1d(toFlatten1, toFlatten2), :]


    flattenX,flattenY = np.meshgrid(np.arange(np.min(dataToFlatten[:,0]), np.max(dataToFlatten[:,0])+0.5, 0.5), np.arange(np.min(dataToFlatten[:,1]), np.max(dataToFlatten[:,1])+0.5, 0.5))

    XX = flattenX.flatten()
    YY = flattenY.flatten()

    #cut away all the values where z is nan
    nonNanIndices=np.where(~np.isnan(dataToFlatten[:,2]))
    dataToFlatten=dataToFlatten[nonNanIndices,:]
    dataToFlatten = dataToFlatten[0,:,:]


    # STAGE 1. We need to separate the bottom of the shoe from the thread. For this we use a linear regression,
    # and take everything below the regression line to use as input for quadratic regression

    # best-fit linear plane
    A = np.c_[dataToFlatten[:, 0], dataToFlatten[:, 1], np.ones(dataToFlatten.shape[0])]
    C, _, _, _ = scipy.linalg.lstsq(A, dataToFlatten[:, 2])  # coefficients

    surface1 = np.dot(np.c_[XX, YY, np.ones(XX.shape)], C).reshape(flattenX.shape)

    # plot points and fitted surface
    # fig = plt.figure()
    # ax = fig.gca(projection='3d')
    # ax.plot_surface(flattenX, flattenY, surface, rstride=1, cstride=1, alpha=0.2)
    # ax.scatter(dataToFlatten[:, 0], dataToFlatten[:, 1], dataToFlatten[:, 2], c='r', s=5)
    # plt.xlabel('X')
    # plt.ylabel('Y')
    # ax.set_zlabel('Z')
    # ax.axis('equal')
    # ax.axis('tight')
    # plt.show()

    if direction==1:
        ZToFlatten=Z[:,start_coord:end_coord+1]
    else:
        ZToFlatten = Z[start_coord:end_coord + 1,:]

    # x=range(0,n-1-minidx)
    # fit2=p2(x)
    # fit2=fit2-fit2[0]

    #fit2=np.matlib.repmat(fit2,m,1)

    # plt.figure(2)
    # ax = plt.subplot(211)
    # plt.plot(ZToFlatten[mid,:],'r')
    # plt.plot(surface1[mid,:])
    # ax = plt.subplot(212)
    # plt.plot(ZToFlatten[mid,:]-surface1[mid,:])

    nn,mm=surface1.shape

    shoeSurface=ZToFlatten-surface1
    Z1D=np.reshape(ZToFlatten,(nn*mm,1),order='C')
    shoeSurface1D=np.reshape(shoeSurface,(nn*mm,1),order='C')
    dataToFit=np.vstack((XX,YY,Z1D[:,0]))
    dataToFit=np.transpose(dataToFit)
    #cut away all the values > 0
    surfaceIndices=np.where(shoeSurface1D<=0)

    # forPlot=np.copy(dataToFit)
    # forPlot[notSurfaceIndices,2]=None
    # forPlot=forPlot[midInstances,2]
    # forPlot=forPlot[0,:]

    dataToFit=dataToFit[surfaceIndices,:]
    dataToFit = dataToFit[0,:,:]


    # STAGE 2: quadratic curve to fit the shoe
    # best-fit quadratic curve
    A = np.c_[np.ones(dataToFit.shape[0]), dataToFit[:, :2], np.prod(dataToFit[:, :2], axis=1), dataToFit[:, :2] ** 2]
    C, _, _, _ = scipy.linalg.lstsq(A, dataToFit[:, 2])
    # evaluate it on a grid
    surface2 = np.dot(np.c_[np.ones(XX.shape), XX, YY, XX * YY, XX ** 2, YY ** 2], C).reshape(flattenX.shape)


    # plt.figure(3)
    # ax = plt.subplot(211)
    # #plt.plot(ZToFlatten[mid,:],'r')
    # plt.plot(forPlot,'r')
    # plt.plot(surface2[mid,:])
    # pylab.ylim([4,11])


    # flatten the image
    surface2=surface2-np.nanmean(surface2[:,0])
    flat=ZToFlatten-surface2
    if direction==1:
        newZ = np.hstack((Z[:, 0:start_coord - 1], flat, Z[:, end_coord:n]))
    else:
        newZ = np.vstack((Z[0:start_coord - 1,:], flat, Z[end_coord:n,:]))
    # plt.figure(4)
    # ax = plt.subplot(211)
    # plt.imshow(Z, origin='lower', interpolation='none')
    # ax.set_title('Original image')
    # ax = plt.subplot(212)
    # plt.imshow(newZ, origin='lower', interpolation='none')
    # ax.set_title('Flattened image')

    # plt.show()

    flat_xyz=np.vstack((data[:,0],data[:,1],newZ.flatten(order='F')))
    flat_xyz=np.transpose(flat_xyz)
    flat_xyzi = (X, Y, newZ, xyzi[3], xyzi[4])

    return flat_xyz, flat_xyzi