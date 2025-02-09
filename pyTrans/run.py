
import multiprocessing
import uuid
from ConfigParser import SafeConfigParser
#from multiprocessing import Queue
from MainFrame import MainFrame
import wx
import sys

VERSION = 'v.1.8.3'
app = wx.App(redirect=False)

#insert version number on splash
def insert_version_num(bmp, version):
    dc = wx.MemoryDC(bmp)
    gc = wx.GraphicsContext.Create(dc)
    gc.SetFont(wx.Font(14, wx.DEFAULT, wx.NORMAL, wx.BOLD), "White")
    gc.DrawText(version, 650, 525)
    del dc
    return bmp


if __name__ == '__main__':
    # freeze_support must be the first line
    multiprocessing.freeze_support()

    # Splash screen
    bitmap = wx.Bitmap('icons\\splash.png')
    splash_with_version = insert_version_num(bitmap, VERSION)
    splash = wx.SplashScreen(splash_with_version, wx.SPLASH_CENTRE_ON_SCREEN | wx.SPLASH_NO_TIMEOUT, 0, None, -1)
    splash.Show()



#import hashlib
#from zipfile import ZipFile, ZIP_DEFLATED
#from StringIO import StringIO

#import os


##########################################################################################################
######                      Commented out database stuff                                          ########
##########################################################################################################

# sql_host = 'PC34428.student.bournemouth.ac.uk'
# sql_user = 'writer'
# sql_pass = '02fc937cfc2cdf0bc23743ad846491d75bb34614'
# sql_db = 'ftrans'
# '''
# CREATE USER 'writer'@'%' IDENTIFIED BY '02fc937cfc2cdf0bc23743ad846491d75bb34614';
# GRANT SELECT (id_user, uuid) on ftrans.user TO 'writer'@'%';
# GRANT SELECT (id_file, sha1) on ftrans.file TO 'writer'@'%';
# GRANT SELECT on ftrans.landmark TO 'writer'@'%';
# GRANT INSERT on ftrans.* TO 'writer'@'%';
# '''
#
# # def dependencies_for_myprogram():
# # from scipy.sparse.csgraph import _validation
# # from scipy.special import _ufuncs_cxx
# # from matplotlib.backends import backend_tkagg
#
# # create, show and return the splash screen
#
#
#
# def uploader(q, uid):
#
#     import MySQLdb
#
#     # prepare file for upload
#     def prepare_file(fname):
#         content = open(fname, 'r').read()
#         sha1 = hashlib.sha1(content).hexdigest()
#         return sha1, content
#
#     # infinite loop
#     while True:
#         data = q.get()
#
#         # terminate the process if the main window has been closed
#         if not data[0]:
#             print("terminating the uploader process")
#             break
#
#         conn = None
#
#         try:
#             # connect to mySQL server
#             conn = MySQLdb.connect(host=sql_host, user=sql_user, passwd=sql_pass, db=sql_db)
#             curr = conn.cursor()
#             cur_time = time.strftime('%Y-%m-%d %H:%M:%S')
#
#             # create a user if necessary
#             curr.execute('''SELECT id_user FROM USER where UUID = %s''', (uid, ))
#             id_user = curr.fetchone()
#             if not id_user:
#                 query = '''INSERT INTO USER (UUID) VALUES (%s)'''
#                 curr.execute(query, (uid, ))
#                 id_user = curr.lastrowid
#
#
#             # upload prints if necessary and associate user with prints
#             id_landmark_set = []
#             for i in range(2):
#                 sha1, content = prepare_file(data[i])
#                 curr.execute('''SELECT id_file FROM FILE where SHA1 = %s''', (sha1, ))
#                 id_file = curr.fetchone()
#                 if not id_file:
#                     zipped = StringIO()
#                     zipFile = ZipFile(zipped, 'w')
#                     zipFile.writestr(sha1, bytes=content, compress_type=ZIP_DEFLATED)
#                     zipFile.close()
#
#                     query = '''INSERT INTO FILE (SHA1, DATA) VALUES (%s, %s)'''
#                     curr.execute(query, (sha1, zipped.getvalue()))
#                     id_file = curr.lastrowid
#
#                 query = '''INSERT INTO FILE_USER (TIME, FILE_NAME, ID_FILE, ID_USER) VALUES (%s, %s, %s, %s)'''
#                 curr.execute(query, (cur_time, os.path.basename(data[i]), id_file, id_user))
#
#                 # create a new landmark set
#                 query = '''INSERT INTO LANDMARK_SET (ID_USER, ID_FILE) VALUES (%s, %s)'''
#                 curr.execute(query, (id_user, id_file))
#                 id_landmark_set.append(curr.lastrowid)
#
#                 # upload landmarks if necessary and associate them with landmark set
#                 for j in range(data[i + 2].shape[0]):
#                     x, y = data[i + 2][j, 0], data[i + 2][j, 1]
#                     curr.execute('''SELECT id_landmark FROM LANDMARK where X = %s and Y = %s''', (x, y))
#                     id_landmark = curr.fetchone()
#                     if not id_landmark:
#                         query = '''INSERT INTO LANDMARK (X, Y) VALUES (%s, %s)'''
#                         curr.execute(query, (x, y))
#                         id_landmark = curr.lastrowid
#
#                         query = '''INSERT INTO LANDMARK_LANDMARK_SET (TIME, ID_LANDMARK, ID_LANDMARK_SET) VALUES (%s, %s, %s)'''
#                         curr.execute(query, (cur_time, id_landmark, id_landmark_set[i]))
#
#             # associate master print with source print
#             query = '''INSERT INTO MASTER_SOURCE (ID_LANDMARK_SET1, ID_LANDMARK_SET2) VALUES (%s, %s)'''
#             curr.execute(query, (id_landmark_set[0], id_landmark_set[1]))
#
#         except Exception, e:
#             print "Error: %s" % (e.args, )
#
#         finally:
#             if conn:
#                 conn.commit()
#                 conn.close()


if __name__ == '__main__':




    # retrieve or generate unique user id
    config = SafeConfigParser()
    config.read('config.ini')

    uid = None
    if config.has_section('main') and config.has_option('main', 'uid'):
        uid = config.get('main', 'uid')

    if not uid:
        uid = str(uuid.uuid4())
        if not config.has_section('main'):
            config.add_section('main')
        config.set('main', 'uid', uid)
        with open('config.ini', 'w') as f:
            config.write(f)

    # uploader process
    #q = Queue()
    # p = Process(target=uploader, args=(q, uid))
    # p.start()

    # q.put((r'C:\Dropbox\Consultancy\Applied Sciences\Transformer\FirstTrial\H22.csv', r'C:\Dropbox\Consultancy\Applied Sciences\Transformer\FirstTrial\H23.csv', np.random.rand(3, 2), np.random.rand(3, 2)))



    #no resize style
    no_resize = wx.DEFAULT_FRAME_STYLE & ~ (wx.RESIZE_BORDER |
                                            wx.RESIZE_BOX |
                                            wx.MAXIMIZE_BOX) | wx.TAB_TRAVERSAL

    #normal style
    normal = wx.DEFAULT_FRAME_STYLE | wx.TAB_TRAVERSAL

    #widget inspector, uncomment to run
    # import wx.lib.inspection
    # wx.lib.inspection.InspectionTool().Show()

    #frame = MainFrame(None, no_resize)
    c_x, c_y, c_w, c_h = wx.ClientDisplayRect()

    if len(sys.argv)>1:
        frame = MainFrame(None,  pos=(c_x, c_y), size=(c_w, c_h), style=no_resize, version=VERSION, proj_path=sys.argv[1])
    else:
        frame = MainFrame(None, pos=(c_x, c_y), size=(c_w, c_h), style=no_resize, version=VERSION)

    # Make the frame maximised by uncommenting following lines
    #frame.Maximize()
    (w, h) = frame.GetSizeTuple()
    frame.SetSizeHints(w, h, w, h)

    # testing project opening
    # frame.project_manager.open_project('E:\\Digtrace_9.ftproj')

    splash.Close()
    splash.Destroy()
    app.MainLoop()



    # terminate the uploader process
    # p.terminate()
    #q.put((False,))




