__author__ = 'shujiedeng'

import wx
import os
import multiprocessing
#from wx.lib.pubsub import pub
from plyfile import PlyData
import PIL
from PIL import Image
import glob

import psutil
import subprocess32
import sys
import time
#from multiprocessing import Process

IS_GTK = 'wxGTK' in wx.PlatformInfo
IS_WIN = 'wxMSW' in wx.PlatformInfo
IS_MAC = 'wxMac' in wx.PlatformInfo



process = None
processbar = None

# Indicate the openMVG binary directory
if IS_MAC:
    OPENMVG_SFM_BIN = "./utilities/MAC"
elif IS_WIN:
    OPENMVG_SFM_BIN = "utilities\\WIN"

CAMERA_SENSOR_WIDTH_DIRECTORY = os.path.join(os.path.join(os.path.expanduser('~'),"DigTrace"),"utilities")

#TIMEOUT_VALUE=TIMEOUT_VALUE # timeout of 1 hour per step
TIMEOUT_VALUE=None  # no timeouts


def process_checker():
    while True:
        #keepGoing, somevalue) = processbar.Update()
        #(keepGoing, somevalue) = processbar.Update()
        print(processbar)
        time.sleep(1)

def cancel_function(self):
    kill(process.pid)
    processbar.Destroy()


# ignore for now as it is not used (visual sfm)
def generation_pipeline1(fname,incremental_sfm, focal_length=None):
    # Indicate the openMVG binary directory
    if IS_MAC:
        VISUALSFM_BIN = "./utilities2/MAC"
    elif IS_WIN:
        VISUALSFM_BIN = "utilities2\\WIN"

    # to deactivate console window
    startupinfo = subprocess32.STARTUPINFO()
    startupinfo.dwFlags |= subprocess32.STARTF_USESHOWWINDOW

    # setting import and export directories based on the import folder
    input_eval_dir = fname
    output_eval_dir = os.path.join(input_eval_dir, "outputs")
    if not os.path.exists(output_eval_dir):
        os.mkdir(output_eval_dir)

    input_dir = input_eval_dir
    output_dir = os.path.join(output_eval_dir, "result.nvm")
    print ("Using input dir  : ", input_dir)
    print ("      output_dir : ", output_dir)



    skip = False # set true if skip generation
    if not skip:
        print ("================= Point Cloud Generation =========================")
        pIntrisics = subprocess32.Popen( [os.path.join(VISUALSFM_BIN, "VisualSFM"),  "sfm+pmvs", input_dir, output_dir], stdout=subprocess32.PIPE, startupinfo=startupinfo  )
        printSubprocessInfo(pIntrisics)
        pIntrisics.wait()

    generated_ply_path = os.path.join(output_eval_dir, "result.0.ply")
    if not os.path.exists(generated_ply_path):
        generated_ply_path = ""
    return generated_ply_path

# MAIN GENERATION PIPELINE / PROCESS
def generation_pipeline((fname, focal_length, downsize_flag), incremental_sfm, mesh_on, log, threads_count, queue):
    startTime = time.time()


    generated_ply_path = ""
    skip = False #set to false if don't want to skip the whole generation process

    # logging to file
    sys.stdout = open(os.path.join(fname, "log" + str(int(time.time())) + ".txt"), "w", 0)

    processbar = wx.ProgressDialog("Generation of " + fname, "Please wait...", maximum=100, parent=None, style=wx.PD_APP_MODAL | wx.PD_AUTO_HIDE | wx.PD_CAN_ABORT | wx.PD_ELAPSED_TIME)
    # for child in processbar.GetChildren():
    #     if isinstance(child, wx.Button):
    #         child.Bind(wx.EVT_BUTTON, cancel_function)

    #processbar = MyProgressDialog(None, 1, "Please wait...", "Generation of " + fname)

    #start process which checks whether cancel button has been pressed
    # p = Process(target=process_checker)
    # p.start()

    try:
        (keepGoing, somevalue) = processbar.Update(0, "Please Wait...")
        if not keepGoing:
            processbar.Destroy()
            return ""

        # setting import and export directories based on the import folder
        input_eval_dir = fname
        output_eval_dir = os.path.join(input_eval_dir, "outputs")
        if not os.path.exists(output_eval_dir):
            os.mkdir(output_eval_dir)

        # if downsize_flag set, downsize to 3264, save in fname/resize
        if downsize_flag == "Yes":
            input_dir, width, height = downsizeImages(fname)
        else:
            input_dir = input_eval_dir
            width, height = None, None



        output_dir = os.path.join(output_eval_dir, "result.nvm")
        print ("Using input dir  : ", input_dir)
        print ("      output_dir : ", output_eval_dir)

        camera_file_params = os.path.join(CAMERA_SENSOR_WIDTH_DIRECTORY, "sensor_width_camera_database.txt")

        # Create the output/matches folder if not present
        matches_dir = os.path.join(output_eval_dir, "matches")
        if not os.path.exists(matches_dir):
            os.mkdir(matches_dir)



        if skip: #skip photogrammetry
            # automatically return generated path
            if incremental_sfm:
                reconstruction_dir = os.path.join(output_eval_dir, "reconstruction_sequential")
            else:
                reconstruction_dir = os.path.join(output_eval_dir,"reconstruction_global")

            generated_ply_path = os.path.join(reconstruction_dir, "PMVS", "models", os.path.basename(fname) + ".ply")


        else: # run photogrammetry

            #to deactivate console window
            startupinfo = subprocess32.STARTUPINFO()
            startupinfo.dwFlags |= subprocess32.STARTF_USESHOWWINDOW

            print ("1. Intrinsics analysis")
            if focal_length == None:
                pIntrisics = subprocess32.Popen( [os.path.join(OPENMVG_SFM_BIN, "openMVG_main_SfMInit_ImageListing"),  "-i", input_dir, "-o", matches_dir, "-d", camera_file_params, "-c", "3"], stdout=sys.stdout, stderr=sys.stdout, startupinfo=startupinfo  )
            else:
                if downsize_flag == "":  #not resize_flag
                    pIntrisics = subprocess32.Popen( [os.path.join(OPENMVG_SFM_BIN, "openMVG_main_SfMInit_ImageListing"),  "-i", input_dir, "-o", matches_dir, "-d", camera_file_params, "-c", "3", "-f", str(focal_length)], stdout=sys.stdout, stderr=sys.stdout, startupinfo=startupinfo  )
                else:
                    k = str(focal_length) + ";0;" + str(width/2.0) + ";0;" + str(focal_length) + ";" + str(height/2.0) + ";0;0;1"   #"f;0;ppx; 0;f;ppy; 0;0;1"
                    pIntrisics = subprocess32.Popen( [os.path.join(OPENMVG_SFM_BIN, "openMVG_main_SfMInit_ImageListing"),  "-i", input_dir, "-o", matches_dir, "-d", camera_file_params, "-c", "3", "-k", k], stdout=sys.stdout, stderr=sys.stdout, startupinfo=startupinfo  )
            # log(pIntrisics)
            try:
                pIntrisics.communicate(timeout=TIMEOUT_VALUE) #original timeout value: 100
            except subprocess32.TimeoutExpired:
                kill(pIntrisics.pid)
                print "step 1 killed because of timeout"
                return ""

            # queue.put(10)
            # sum = 0
            # while not queue.empty():
            #     a = queue.get()
            #     sum += a
            # if sum != 0:
            #     queue.put(sum)
            #     print "gotcha!!"
            #     print sum
            #     wx.CallAfter(pub.sendMessage, "update", msg=str(sum))
            #     wx.GetApp().ProcessPendingEvents()


            (keepGoing, somevalue) = processbar.Update(10, "Step 1/10 done.")
            if not keepGoing:
                processbar.Destroy()
                return ""

            print ("2. Compute features")
            pFeatures = subprocess32.Popen( [os.path.join(OPENMVG_SFM_BIN, "openMVG_main_ComputeFeatures"),  "-i", os.path.join(matches_dir,"sfm_data.json"), "-o", matches_dir, "-m", "SIFT", "-f" , "1"], stdout=subprocess32.PIPE, stderr=sys.stdout, startupinfo=startupinfo )

            try:
                keepGoing = printSubprocessInfo(pFeatures, processbar, 10)
                if keepGoing is False:  # keepGoing may be None, so cannot use if not keepGoing
                    return ""
                pFeatures.communicate(timeout=TIMEOUT_VALUE) #original timeout value: 300
            except subprocess32.TimeoutExpired:
                kill(pFeatures.pid)
                print "step 2 killed because of timeout"
                return ""

            # status_bar.SetValue(20)
            (keepGoing, somevalue) = processbar.Update(20, "Step 2/10 done.")
            if not keepGoing:
                processbar.Destroy()
                return ""

            if not incremental_sfm: #global_sfm

                print ("3. Compute matches")
                start_time = time.time()
                pMatches = subprocess32.Popen( [os.path.join(OPENMVG_SFM_BIN, "openMVG_main_ComputeMatches"),  "-i", os.path.join(matches_dir,"sfm_data.json"), "-o", matches_dir, "-g", "e", "-f", "1"], stdout=sys.stdout, stderr=sys.stdout, startupinfo=startupinfo )

                try:
                    pMatches.communicate(timeout=TIMEOUT_VALUE) #original timeout value: 900
                except subprocess32.TimeoutExpired:
                    kill(pMatches.pid)
                    print "step 3 killed because of timeout"
                    return ""

                (keepGoing, somevalue) = processbar.Update(30, "Step 3/10 done.")
                if not keepGoing:
                    processbar.Destroy()
                    return ""


                reconstruction_dir = os.path.join(output_eval_dir,"reconstruction_global")

                print('Elapsed time for step 3: %f seconds' % (time.time() - start_time))

                print ("4. Do Global reconstruction")
                pRecons = subprocess32.Popen( [os.path.join(OPENMVG_SFM_BIN, "openMVG_main_GlobalSfM"),  "-i", os.path.join(matches_dir,"sfm_data.json"), "-m", matches_dir, "-o", reconstruction_dir], stdout=sys.stdout, stderr=sys.stdout, startupinfo=startupinfo )

                try:
                    pRecons.communicate(timeout=TIMEOUT_VALUE) #original timeout value: 900
                except subprocess32.TimeoutExpired:
                    kill(pRecons.pid)
                    print "step 4 killed because of timeout"
                    return ""

                (keepGoing, somevalue) = processbar.Update(40, "Step 4/10 done.")
                if not keepGoing:
                    processbar.Destroy()
                    return ""

            else: # incremental_sfm

                print ("3. Compute matches")
                pMatches = subprocess32.Popen( [os.path.join(OPENMVG_SFM_BIN, "openMVG_main_ComputeMatches"),  "-i", os.path.join(matches_dir,"sfm_data.json"), "-o", matches_dir, "-f", "1"], stdout=sys.stdout, stderr=sys.stdout, startupinfo=startupinfo )
                try:
                    pMatches.communicate(timeout=TIMEOUT_VALUE) #original timeout value: 900
                except subprocess32.TimeoutExpired:
                    kill(pMatches.pid)
                    print "step 3 killed because of timeout"
                    return ""

                (keepGoing, somevalue) = processbar.Update(30, "Step 3/10 done.")
                if not keepGoing:
                    processbar.Destroy()
                    return ""


                reconstruction_dir = os.path.join(output_eval_dir, "reconstruction_sequential")
                step4_success = False
                while not step4_success:
                    try:
                        print ("4. Do Incremental/Sequential reconstruction")
                        #set manually the initial pair to avoid the prompt question
                        # list = glob.glob(os.path.join(input_dir, "*.jpg"))
                        # if len(list) >= 2:
                            # print os.path.basename(list[0])
                        pReco = subprocess32.Popen( [os.path.join(OPENMVG_SFM_BIN, "openMVG_main_IncrementalSfM"),  "-i", os.path.join(matches_dir,"sfm_data.json"), "-m", matches_dir, "-o", reconstruction_dir], stdout=sys.stdout, stderr=sys.stdout, startupinfo=startupinfo)
                        pReco.communicate(timeout=TIMEOUT_VALUE) #original timeout value: 900
                    except subprocess32.TimeoutExpired:
                        kill(pReco.pid)
                        # printSubprocessInfo(pReco)
                        print "step 4 killed because of timeout"
                        continue
                    step4_success = True

                (keepGoing, somevalue) = processbar.Update(40, "Step 4/10 done.")
                if not keepGoing:
                    processbar.Destroy()
                    return ""

            print ("5. Colorize Structure")
            pColor = subprocess32.Popen( [os.path.join(OPENMVG_SFM_BIN, "openMVG_main_ComputeSfM_DataColor"),  "-i", os.path.join(reconstruction_dir,"sfm_data.bin"), "-o", os.path.join(reconstruction_dir,"colorized.ply")], stdout=sys.stdout, stderr=subprocess32.PIPE, startupinfo=startupinfo  )
            try:
                stdout, stderr = pColor.communicate(timeout=TIMEOUT_VALUE) #original timeout value: 300
                if 'sfm_data.json" cannot be read' in stderr:
                    print stderr
                    return ""
            except subprocess32.TimeoutExpired:
                kill(pColor.pid)
                print "step 5 killed because of timeout"
                return ""

            (keepGoing, somevalue) = processbar.Update(50, "Step 5/10 done.")
            if not keepGoing:
                processbar.Destroy()
                return ""

            print ("6. Structure from Known Poses (robust triangulation)")
            pTriang = subprocess32.Popen( [os.path.join(OPENMVG_SFM_BIN, "openMVG_main_ComputeStructureFromKnownPoses"),  "-i", os.path.join(reconstruction_dir,"sfm_data.bin"), "-m", matches_dir, "-o", os.path.join(reconstruction_dir,"robust.ply")], stdout=sys.stdout, stderr=sys.stdout, startupinfo=startupinfo )
            try:
                pTriang.communicate(timeout=TIMEOUT_VALUE) #original timeout value: 300
            except subprocess32.TimeoutExpired:
                kill(pTriang.pid)
                print "step 6 killed because of timeout"
                return ""

            (keepGoing, somevalue) = processbar.Update(60, "Step 6/10 done.")
            if not keepGoing:
                processbar.Destroy()
                return ""

            # MVE is slower, generates mesh and does not generate holes
            # PMVS is faster but no mesh and can generate holes
            if mesh_on == 0:
                generated_ply_path = dense_cloud_PMVS(reconstruction_dir, processbar)
            else:
                generated_ply_path = dense_cloud_MVE(reconstruction_dir, processbar)
            # downsampling(reconstruction_dir)
            # generated_ply_path = os.path.join(reconstruction_dir, "MVE", "mve_output_mesh_clean.ply")  #bun_zipper_res4
            # generated_ply_path = os.path.join(output_eval_dir, "result.0.ply")

        if not os.path.exists(generated_ply_path):
            generated_ply_path = ""

        processbar.Destroy()

        # redirect stdout to console
        # sys.stdout = sys.__stdout__
        # redirect stdout to logfile

        endTime = time.time()
        print("Elapsed total time:")
        print(endTime - startTime)

        sys.stdout = log

        return generated_ply_path
    except:
        processbar.Destroy()
        return ""
#this is not used at the moment
def dense_cloud_MVE(reconstruction_dir, processbar):
    # to deactivate console window
    startupinfo = subprocess32.STARTUPINFO()
    startupinfo.dwFlags |= subprocess32.STARTF_USESHOWWINDOW

    resolution = 2
    print ("7. convert the openMVG SfM scene to the MVE format")
    pConvert = subprocess32.Popen( [os.path.join(OPENMVG_SFM_BIN, "openMVG_main_openMVG2MVE2"),  "-i", os.path.join(reconstruction_dir,"sfm_data.bin"), "-o", reconstruction_dir], stdout=sys.stdout, stderr=sys.stdout, startupinfo=startupinfo )
    try:
        pConvert.wait(timeout=TIMEOUT_VALUE) #original timeout value: 300
    except subprocess32.TimeoutExpired:
        kill(pConvert.pid)
        print "step 7 killed because of timeout"
        return ""

    # (keepGoing, somevalue) = processbar.Update(70, "Step 7/10 done.")
    # if not keepGoing:
    #     processbar.Destroy()
    #     return ""

    print("8. ------------ generate dense cloud points ------------------")
    print("dmrecon")
    # dmrecon -s$resolution $directory
    pRecons = subprocess32.Popen( [os.path.join(OPENMVG_SFM_BIN, "dmrecon"),  "-s"+str(resolution), os.path.join(reconstruction_dir, "mve")], stdout=sys.stdout, stderr=sys.stdout, startupinfo=startupinfo )
    try:
        pRecons.wait(timeout=TIMEOUT_VALUE) #original timeout value: 1200
    except subprocess32.TimeoutExpired:
        kill(pRecons.pid)
        print "step 8 killed because of timeout"
        return ""

    print("scene2pset")
    # scene2pset -ddepth-L$resolution -iundist-L$resolution -n -s -c $directory $directory/OUTPUT.ply
    #pRecons = subprocess32.Popen( [os.path.join(OPENMVG_SFM_BIN, "scene2pset"),  "-ddepth-L"+str(resolution), "-iundist-L"+str(resolution), "-s", os.path.join(reconstruction_dir, "mve"), os.path.join(reconstruction_dir, "mve", "mve_output.ply")], stdout=sys.stdout, stderr=sys.stdout, startupinfo=startupinfo )
    pRecons = subprocess32.Popen(
        [os.path.join(OPENMVG_SFM_BIN, "scene2pset"), "-ddepth-L" + str(resolution), "-iundist-L" + str(resolution),
         "-s", os.path.join(reconstruction_dir, "mve"),"-F0", os.path.join(reconstruction_dir, "mve", "mve_output0.ply")],
        stdout=sys.stdout, stderr=sys.stdout, startupinfo=startupinfo)
    try:
        pRecons.wait(timeout=TIMEOUT_VALUE) #original timeout value: 1200
    except subprocess32.TimeoutExpired:
        kill(pRecons.pid)
        print "step 8 killed because of timeout"
        return ""

    pRecons = subprocess32.Popen(
        [os.path.join(OPENMVG_SFM_BIN, "scene2pset"), "-ddepth-L" + str(resolution), "-iundist-L" + str(resolution),
         "-s", os.path.join(reconstruction_dir, "mve"),"-F1", os.path.join(reconstruction_dir, "mve", "mve_output1.ply")],
        stdout=sys.stdout, stderr=sys.stdout, startupinfo=startupinfo)
    try:
        pRecons.wait(timeout=TIMEOUT_VALUE) #original timeout value: 1200
    except subprocess32.TimeoutExpired:
        kill(pRecons.pid)
        print "step 8 killed because of timeout"
        return ""

    pRecons = subprocess32.Popen(
        [os.path.join(OPENMVG_SFM_BIN, "scene2pset"), "-ddepth-L" + str(resolution), "-iundist-L" + str(resolution),
         "-s", os.path.join(reconstruction_dir, "mve"),"-F2", os.path.join(reconstruction_dir, "mve", "mve_output2.ply")],
        stdout=sys.stdout, stderr=sys.stdout, startupinfo=startupinfo)
    try:
        pRecons.wait(timeout=TIMEOUT_VALUE) #original timeout value: 1200
    except subprocess32.TimeoutExpired:
        kill(pRecons.pid)
        print "step 8 killed because of timeout"
        return ""

    pRecons = subprocess32.Popen(
        [os.path.join(OPENMVG_SFM_BIN, "scene2pset"), "-ddepth-L" + str(resolution), "-iundist-L" + str(resolution),
         "-s", os.path.join(reconstruction_dir, "mve"),"-F3", os.path.join(reconstruction_dir, "mve", "mve_output3.ply")],
        stdout=sys.stdout, stderr=sys.stdout, startupinfo=startupinfo)
    try:
        pRecons.wait(timeout=TIMEOUT_VALUE) #original timeout value: 1200
    except subprocess32.TimeoutExpired:
        kill(pRecons.pid)
        print "step 8 killed because of timeout"
        return ""

    # (keepGoing, somevalue) = processbar.Update(80, "Step 8/10 done.")
    # if not keepGoing:
    #     processbar.Destroy()
    #     return ""

    print("9. ------------ triangulate mesh ------------------")
    print("fssrecon")
    # fssrecon $directory/OUTPUT.ply $directory/OUTPUT_MESH.ply
    pFSSRecons = subprocess32.Popen( [os.path.join(OPENMVG_SFM_BIN, "fssrecon"),
                                      os.path.join(reconstruction_dir, "mve", "mve_output0.ply"),
                                      os.path.join(reconstruction_dir, "mve", "mve_output1.ply"),
                                      os.path.join(reconstruction_dir, "mve", "mve_output2.ply"),
                                      os.path.join(reconstruction_dir, "mve", "mve_output3.ply"),
                                      os.path.join(reconstruction_dir, "mve", "mve_output_mesh.ply")], stdout=sys.stdout, stderr=sys.stdout, startupinfo=startupinfo )
    try:
        pFSSRecons.wait(timeout=TIMEOUT_VALUE) #original timeout value: 1200
    except subprocess32.TimeoutExpired:
        kill(pFSSRecons.pid)
        print "step 9/1 killed because of timeout"
        return ""

    # (keepGoing, somevalue) = processbar.Update(90, "Step 9/10 done.")
    # if not keepGoing:
    #     processbar.Destroy()
    #     return ""

    print("meshclean")
    # meshclean $directory/OUTPUT_MESH.ply $directory/OUTPUT_MESH_CLEAN.ply
    pMesh = subprocess32.Popen( [os.path.join(OPENMVG_SFM_BIN, "meshclean"), os.path.join(reconstruction_dir, "mve", "mve_output_mesh.ply"), os.path.join(reconstruction_dir, "mve", "mve_output_mesh_clean.ply")], stdout=sys.stdout, stderr=sys.stdout, startupinfo=startupinfo )
    try:
        pMesh.wait(timeout=TIMEOUT_VALUE) #original timeout value: 1200
    except subprocess32.TimeoutExpired:
        kill(pMesh.pid)
        print "step 9/2 killed because of timeout"
        return ""

    # (keepGoing, somevalue) = processbar.Update(99, "Step 10/10 done.")
    # if not keepGoing:
    #     processbar.Destroy()
    #     return ""

    generated_ply_path = os.path.join(reconstruction_dir, "MVE", "mve_output_mesh_clean.ply")
    return generated_ply_path

def dense_cloud_PMVS(reconstruction_dir, processbar):
    # to deactivate console window
    startupinfo = subprocess32.STARTUPINFO()
    startupinfo.dwFlags |= subprocess32.STARTF_USESHOWWINDOW

    # openMVG_main_openMVG2PMVS -i Dataset/outReconstruction/sfm_data.json -o Dataset/outReconstruction
    print ("7. convert the openMVG SfM scene to the PMVS format")
    pConvert = subprocess32.Popen( [os.path.join(OPENMVG_SFM_BIN, "openMVG_main_openMVG2PMVS"),  "-i", os.path.join(reconstruction_dir,"sfm_data.bin"), "-o", reconstruction_dir], stdout=sys.stdout, stderr=sys.stdout, startupinfo=startupinfo)
    try:
        pConvert.communicate(timeout=TIMEOUT_VALUE) #original timeout value: 300
    except subprocess32.TimeoutExpired:
        kill(pConvert.pid)
        print "step 7 killed because of timeout"
        return ""

    (keepGoing, somevalue) = processbar.Update(70, "Step 7/10 done.")
    if not keepGoing:
        processbar.Destroy()
        return ""

    print("8. ------------ generate dense cloud points using PMVS ------------------")
    print "$ cmvs \\Pictures\\result.nvm.cmvs\\00\\ 50 12"
    pRecons = subprocess32.Popen( [os.path.join(OPENMVG_SFM_BIN, "cmvs"), os.path.join(reconstruction_dir, "PMVS\\"), "50", "12"], stdout=sys.stdout, stderr=sys.stdout, startupinfo=startupinfo )
    try:
        pRecons.communicate(timeout=TIMEOUT_VALUE) #original timeout value: 100
    except subprocess32.TimeoutExpired:
        kill(pRecons.pid)
        print "step 8 killed because of timeout"
        return ""

    (keepGoing, somevalue) = processbar.Update(80, "Step 8/10 done.")
    if not keepGoing:
        processbar.Destroy()
        return ""

    pRecons = subprocess32.Popen( [os.path.join(OPENMVG_SFM_BIN, "genOption"), os.path.join(reconstruction_dir, "PMVS\\")], stdout=sys.stdout, stderr=sys.stdout, startupinfo=startupinfo )
    try:
        pRecons.communicate(timeout=TIMEOUT_VALUE) #original timeout value: 500
    except subprocess32.TimeoutExpired:
        kill(pRecons.pid)
        print "step 9 killed because of timeout"
        return ""

    (keepGoing, somevalue) = processbar.Update(90, "Step 9/10 done.")
    if not keepGoing:
        processbar.Destroy()
        return ""

    print "$ pmvs2 \\Pictures\\result.nvm.cmvs\\00\\ option-0000"
    pRecons = subprocess32.Popen( [os.path.join(OPENMVG_SFM_BIN, "pmvs2"), os.path.join(reconstruction_dir, "PMVS\\"), "option-0000"], stdout=sys.stdout, stderr=subprocess32.PIPE, startupinfo=startupinfo  )
    try:
        keepGoing = pmvsProgress(pRecons, processbar, 90)
        if not keepGoing:
            return ""
        pRecons.communicate(timeout=TIMEOUT_VALUE) #original timeout value: 1200
    except subprocess32.TimeoutExpired:
        kill(pRecons.pid)
        print "step 10 killed because of timeout"
        return ""

    (keepGoing, somevalue) = processbar.Update(99, "Step 10/10 done.")
    if not keepGoing:
        processbar.Destroy()
        return ""

    print "save ply as binary"
    readpath = os.path.join(reconstruction_dir, "PMVS", "models", "option-0000.ply")
    fname = os.path.basename(os.path.dirname(os.path.dirname(reconstruction_dir)))
    writepath = os.path.join(reconstruction_dir, "PMVS", "models", fname + ".ply")
    plydata = PlyData.read(str(readpath))
    plydata = PlyData([plydata['vertex']], text=False, byte_order='<')
    plydata.write(str(writepath))

    # sometimes ply generated but no data
    filesize = os.path.getsize(str(writepath))
    if filesize < 2000L:
        os.remove(writepath)
        print "file not generated. consider change the initial pair."
        return ""

    generated_ply_path = writepath
    return generated_ply_path

# def downsampling(dir):
#     PCLBIN = "C:\\Program Files\\PCL 1.6.0\\bin"
#     print ("covert ply to pcd")
#     pDownsample = subprocess32.Popen( [os.path.join(PCLBIN, "pcl_ply2pcd_release"), os.path.join(dir, "MVE", "mve_output.ply"), os.path.join(dir, "MVE", "mve_output.pcd")], stdout=subprocess32.PIPE )
#     printSubprocessInfo(pDownsample)
#     pDownsample.wait()
#
#     print("Downsampling")
#     pDownsample = subprocess32.Popen( [os.path.join("pcl_voxel_grid_release"),  os.path.join(dir, "MVE", "mve_output.pcd"), os.path.join(dir, "MVE", "downsampled.pcd")], stdout=subprocess32.PIPE )
#     printSubprocessInfo(pDownsample)
#     pDownsample.wait()
#
#     print("convert pcd to ply")
#     pDownsample = subprocess32.Popen( [os.path.join("pcl_pcd2ply_release"),  os.path.join(dir, "MVE", "downsampled.pcd"), os.path.join(dir, "MVE", "downsampled.ply")], stdout=subprocess32.PIPE )
#     printSubprocessInfo(pDownsample)
#     pDownsample.wait()

# downsizing the image to the default size. To check how exactly the downsizing works (sampling?)
def downsizeImages(path):
    # if resize folder exists, check if downsized images exists, if yes, break
    images = glob.glob(path + '\\*.jpg')
    resize_path = os.path.join(path, "resize")
    if len(images) > 0:
        if os.path.exists(resize_path):
            images_resize = glob.glob(resize_path + '\\*.jpg')
            if len(images) == len(images_resize):
                img0 = PIL.Image.open(images_resize[0])
                width, height = img0.size
                img0.close()
                return resize_path, width, height
            else: # delete existed images then re-resizing pictures
                map(os.unlink, (os.path.join(resize_path, f) for f in os.listdir(resize_path)))

        #when resize_path doesn't exist or resize directory is cleared up
        img0 = PIL.Image.open(images[0])
        width, height = img0.size
        img0.close()
        if max(width, height) > 3264: #this is the default max value for width, found by Shujie empirically
            if not os.path.exists(resize_path):
                os.makedirs(resize_path)
            ratio = 3264.0 / max(width, height) # TODO: define 3264 as a variable, also appears in calculate_focal() in photogramemtry
            print ratio
            for i, image in enumerate(images):
                im = Image.open(image)
                new_size = int(width * ratio), int(height * ratio)
                im.thumbnail(new_size, Image.ANTIALIAS)
                exif = im.info['exif']
                im.save(os.path.join(resize_path, str(i) + ".jpg"), 'JPEG', exif=exif)
            return resize_path, new_size[0], new_size[1]
    return path, None, None

def kill(proc_pid):
    process = psutil.Process(proc_pid)
    for proc in process.children(recursive=True):
        proc.kill()
    process.kill()

def log(proc):
    # print
    while True:
        line = proc.stdout.readline()
        wx.Yield()
        if line.strip() == "":
            pass
        else:
            # print line.strip()
            sys.stdout.write(line.strip()+'\n')
        # if not line: break
        if not line: return True

# log for setp2,
# the progress was initially shown by ASCII stars (*)
# increase progressbar by 1 percent for each 5 stars
def printSubprocessInfo(proc, processbar, perc):
    # print
    while True:
        char = proc.stdout.read(5)          # read by character
        if not char: break
        elif char == '*****':
            # print char
            sys.stdout.write(char)
            perc = perc + 1
            (keepGoing, somevalue) = processbar.Update(perc)
            if not keepGoing:
                processbar.Destroy()
                kill(proc.pid)
                return False
        else:
            sys.stdout.write(char)

# to show progress, look at ascii output and increase progress bar accordingly
def pmvsProgress(proc, processbar, perc):
    # print
    while True:
        line = proc.stderr.readline()
        if not line: return True
        elif 'Expanding patches' in line:
            print line.strip()
            # sys.stdout.write(line)
            perc = perc + 1
            if perc < 99:
                (keepGoing, somevalue) = processbar.Update(perc)
                if not keepGoing:
                    processbar.Destroy()
                    kill(proc.pid)
                    return False
        else:
            print line


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

class MyProgressDialog(wx.Dialog):
    def __init__(self, parent, id, title, text=''):
        wx.Dialog.__init__(self, parent, id, title, size=(200,150), style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER)

        self.text = wx.StaticText(self, -1, text)
        self.gauge = wx.Gauge(self, -1)
        self.closebutton = wx.Button(self, wx.ID_CLOSE)
        self.closebutton.Bind(wx.EVT_BUTTON, self.OnClose)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.text, 0 , wx.EXPAND)
        sizer.Add(self.gauge, 0, wx.ALIGN_CENTER)
        sizer.Add(self.closebutton, 0, wx.ALIGN_CENTER)

        self.SetSizer(sizer)
        self.Show()

    def Update(self, percent,text):
        self.gauge.SetValue(percent)
        self.text.SetLabelText(text)

    def OnClose(self, event):
        self.Destroy()
        global process
        process.kill()

