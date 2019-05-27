#!/usr/bin/env python
# -*- coding:utf-8 -*-

import sys
import os
import fllb
import shutil
import ctypes
import re
import math
try:
    from PySide2 import QtWidgets as QtGui
    from PySide2 import QtCore
except ImportError:
    from PySide import QtGui
    from PySide import QtCore
    

#*******************************************
#*******************************************
#UI界面
#*******************************************
#*******************************************
def getHumanReadableSize(file):
    size = os.path.getsize(file)
    size = abs(size)
    if size ==0:
        return '0 B'
    units = ['B','KB','MB','GB','TB','PB','EB','ZB','YB']
    p  = math.floor(math.log(size,2) / 10)
    return '%.2f %s' %(size / math.pow(1024,p),units[int(p)])
#*******************************************
#*******************************************
#copy all path file
#*******************************************
#*******************************************        
class CopyProject(QtGui.QDialog):

    def __init__(self, parent=None):
        super(CopyProject,self).__init__(parent)
        import hou
        self._hou = hou
        self._app = QtGui.QApplication.instance()
        self.ErrorList = []#存在files路径的路径
        self.NoFileList = []#存储本地没有文件路径
        self.setWindowTitle('copy_project')
        self.resize(300,201)
        self.initUI()
    def initUI(self):


        endPro=QtGui.QLabel(u"工程")
        self.end_line=QtGui.QLineEdit()#拖入文本框

        self.look=QtGui.QPushButton(u"浏览")

        self.move_button=QtGui.QPushButton(u"迁移")#执行按钮
        close_button=QtGui.QPushButton(u"关闭")
        
        self.copyLabel = QtGui.QLabel("")
        self.progressBar = QtGui.QProgressBar()


        lat1=QtGui.QHBoxLayout()
        lat1.addWidget(endPro)
        lat1.addWidget(self.end_line)
        lat1.addWidget(self.look)

        lat2=QtGui.QHBoxLayout()
        lat2.addWidget(self.move_button)
        lat2.addWidget(close_button)

        lat3=QtGui.QHBoxLayout()
        lat3.addWidget(self.progressBar)
      


        lay=QtGui.QVBoxLayout()
        lay.addLayout(lat1)
        lay.addStretch()
        lay.addLayout(lat2)
        lay.addStretch()
        lay.addLayout(lat3)
        lay.addWidget(self.copyLabel)
        lay.addStretch()
        self.setLayout(lay)
        
        self.look.clicked.connect(self.openFile)
        self.move_button.clicked.connect(self.copyFiles)
        close_button.clicked.connect(self.close)

   
    #获取盘符 [C:/,D:/,E:/,F:/]
    def openFile(self):
        filename=QtGui.QFileDialog.getExistingDirectory(self,"choose directory",r"C:\Users\Administrator\Desktop")
        self.end_line.setText(str(filename))
        #---------------------------------------------------获取电脑的磁盘名称包括网络映射磁盘---------------------------------------------------------#
    def driver(self):
        lpBuffer = ctypes.create_string_buffer(78)
        ctypes.windll.kernel32.GetLogicalDriveStringsA(ctypes.sizeof(lpBuffer), lpBuffer)
        vol = lpBuffer.raw.split('\x00')
        vol=list(set(vol))
        lt=[]
        for i in vol:
            if i!="":
                t=i.replace("\\","/")
                lt.append(t) 
        return lt
    
    #得到所有需要拷贝的文件列表
    def getPath(self):
        # list=['/obj/','/ch/','/img/','/mat/','/out/','shop','vex']
        list=['/obj/','/mat/']
        mylist=[]
        myDict = {}
        driverList = self.driver()
        self.copyLabel.setText(u'正在保存houdini文件')
        project=self.end_line.text()
        #遍历所有层级，获取子节点，得到所有参数，判断盘符是否在参数里面，如果在，筛选出来
        fp=self._hou.hipFile.path()
        # fp=self._hou.hipFile.basename()
        file_name, file_ext = os.path.splitext(fp)
        self.fullhip=file_name+"_Pack"+file_ext

        self._hou.hipFile.save(self.fullhip)
        self.copyLabel.setText(u'正在修改工程路径:')
        for t in range(len(list)):
            root = self._hou.node(list[t])
            child=root.allSubChildren()
            self.progressBar.setMinimum(0)#设置路径
            self.progressBar.setMaximum(len(child))
            for index,pa in enumerate(child):
                self.progressBar.setValue(int(index)+1)
                if pa!=():
                    param= pa.parms()
                    for p in param:
                            for d in driverList:
                                try:
                                    path_hou=str(p.eval())
                                except:
                                    print '###########'
                                    print pa
                                    print param
                                    print '*********'
                                if d in path_hou:
                                    if 'UDIM)' in path_hou:#处理UDIM贴图
                                        matPath = path_hou.replace(":","")
                                        if "files" not in path_hou and project not in matPath:
                                            try:
                                                p.set((project+"/files/"+matPath).replace("\\","/"))#此处使用了绝对路径
                                                mylist.append(path_hou)
                                            except:
                                                pass
                                        else:
                                            self.ErrorList.append(path_hou)
                                    else:
                                        information = fllb.query(path_hou,unSeqExts='',sequencePattern = '.#.',getAllSubs=False)
                                        if information !=[]:
                                            type_file = information[0]["type"]
                                            if type_file != "seq":
                                                path_b=os.path.basename(path_hou)
                                                fullname=path_hou.replace(":","")
                                                #print fullname
                                                if "files" not in path_hou and project not in path_hou:
                                                    try:
                                                        p.set((project+"/files/"+fullname).replace("\\","/"))#此处使用了相对路径
                                                        mylist.append(path_hou)
                                                    except:
                                                        pass
                                                else:
                                                    self.ErrorList.append(path_hou)
                                            else:
                                                full_path = information[0]["path"]
                                                num= full_path.count("#")
                                                if num>1:
                                                    fpath=full_path.replace("#"*num,"$F"+str(num))
                                                else:
                                                    fpath=full_path.replace("#"*num,"$F")
                                                fpath=fpath.replace(":","")
                                                if "files" not in path_hou and project not in fpath:
                                                    try:
                                                        p.set((project+"/files/"+fpath).replace("\\","/"))#此处使用了绝对路径
                                                        mylist.append(path_hou)
                                                    except:
                                                        pass
                                                else:
                                                    self.ErrorList.append(path_hou)
                                        else:
                                            self.NoFileList.append(path_hou)
                self._app.processEvents()
        return  mylist                    
        
    #匹配序列帧，返回文件列表
    def matchFiles(self,path):
        #print path
        #path=['F:/tie/ser/Color_Ring_001.tga', 'F:/tie/ser/Color_Sphere_000.tga']
        path_list=[]#所有文件的列表（序列帧和单帧）
        #lostlist=[]#丢失文件的列表
        self.copyLabel.setText(u'正在匹配序列帧:')
        self.progressBar.setMinimum(0)#匹配序列帧
        self.progressBar.setMaximum(len(path))
        for index,singer in enumerate(path):
            self.progressBar.setValue(int(index)+1)
            if 'UDIM)' in singer:
                dirname = os.path.dirname(singer)
                try:
                    myroot = os.listdir(dirname)
                except:
                    continue
                basename = os.path.basename(singer)
                type_exr= basename.split('%')[0]
                if myroot != []:
                    for f in myroot:
                        if type_exr in f:
                            temp_file = os.path.join(dirname, f)
                            temp_file = temp_file.replace("\\", '/')
                            path_list.append(temp_file)
                else:
                    path_list.append(singer)
            else:   
                information = fllb.query(singer,unSeqExts='',sequencePattern = '.#.',getAllSubs=False)
                if information !=[]:
                    type_file = information[0]["type"]
                    type_exr = os.path.basename(information[0]["path"].split("#")[0])
                    if type_file == "seq":
                        file_name, file_ext = os.path.splitext(singer)
                        dirname=os.path.dirname(file_name)
                        basename=os.path.basename(file_name)
                        myroot=os.listdir(dirname)
                        if myroot != []:
                            for f in myroot:
                                if type_exr in f:
                                    temp_file=os.path.join(dirname,f)
                                    temp_file=temp_file.replace("\\",'/')
                                    path_list.append(temp_file)
                    else:
                        path_list.append(singer)
            self._app.processEvents()
        return path_list
    #根据目录建立多及目录，以及拷贝文件
    def copyFiles(self):
        #self.move_button.setDisable(0)
        project=self.end_line.text()
        project_use=project+"/"+"files"
        path=self.matchFiles(self.getPath())
        if path==[]:
            QtGui.QMessageBox.information(self,"Information",u"请检查文件路径或者参数路径是否包含files")
            return 

        #print os.path.dirname("F:/tie/www/2c09b1a0.bmp")
        if not os.path.exists(project_use):#如果工程下存在该files不建立，反之建立
            os.mkdir(project_use)
        self.progressBar.setMinimum(0)#拷贝文件
        self.progressBar.setMaximum(len(path))
        for index,f in enumerate(path):
            self.progressBar.setValue(int(index)+1)
            self.copyLabel.setText(u'正在拷贝: %s ,文件大小:%s'%(os.path.basename(f),getHumanReadableSize(f)))
            self._app.processEvents()
            os.chdir(project_use)
            r_path=os.path.dirname(f).replace(":","")
            # print r_path
            try:
                root=os.makedirs( r_path )#如果存在目录则跳过
            except Exception as e:
                pass
            ispaths = os.path.join(project_use + "/" + r_path, os.path.split(f)[-1]).replace('\\','/')
            if not os.path.exists(ispaths):
                try:
                    shutil.copy2(f, project_use + "/" + r_path)
                except Exception as e:
                    pass
                    QtGui.QMessageBox.information(self,"Information",u"请检查文件")
            self._app.processEvents()
            # else:
                # continue
            # try:
                # shutil.copy2(f,project_use+"/"+r_path)
            # except Exception as e:
                # pass
                # QtGui.QMessageBox.information(self,"Information",u"please check file if copy!")


        # self.progressBar.setValue(100)
        self.move_button.setDisabled(1)#设置按钮不能点击
        self._hou.hipFile.save(self.fullhip)
        self.copyLabel.setText(u'完成全部迁移')
        QtGui.QMessageBox.information(self,"Information",u"复制完成!")
        
                   
                                       
# app = QtGui.QApplication.instance()
# if app ==None:
    # app = QtGui.QApplication(sys.argv)
dialog = CopyProject(parent=QtGui.QApplication.activeWindow())
dialog.show()
# app.exec_()
    
'''
def main():
    import sys
    sys.path.append(r"C:\Users\Administrator\Desktop\copy_project_v03")
    
    import copy_project_t
    reload(copy_project_t)
    
    dialog = copy_project_t.CopyProject()
    dialog.show()

main()'''


    

#此处用作houdini里进行的测试代码
#序列帧样式必需这样 xcc_001
#x_sd_dede_12_001
# xxxx_001.exr
# xxxx001.exr

#如果是xxx_001_qwe 或xxx001dfd
#这样的无法识别

    
'''import hou

hou.hipFile.basename()
hou.hipFile.path()

hou.hipFile.save("D:/1.hip")'''


    



