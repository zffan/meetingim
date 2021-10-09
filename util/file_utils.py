# -*- coding: utf-8 -*-#

# -------------------------------------------------------------------------------
# Name:         file_utils
# Description:  
# Date:         2020/8/10
# -------------------------------------------------------------------------------
import os
import zipfile

class File_utils(object):

    @staticmethod
    def unzip_file(zip_src, dst_dir):
        r = zipfile.is_zipfile(zip_src)
        if r:
            fz = zipfile.ZipFile(zip_src, 'r')
            for file in fz.namelist():
                fz.extract(file, dst_dir)
        else:
            raise Exception('This is not zip')

    @staticmethod
    def zip_file(src_dir, zip_file_name):
        if zip_file_name.endswith('.zip'):
            zip_name = zip_file_name
        else:
            zip_name = zip_file_name + '.zip'
        z = zipfile.ZipFile(zip_name, 'w', zipfile.ZIP_DEFLATED)
        for dirpath, dirnames, filenames in os.walk(src_dir):
            fpath = dirpath.replace(src_dir, '')
            fpath = fpath and fpath + os.sep or ''
            for filename in filenames:
                z.write(os.path.join(dirpath, filename), fpath + filename)
                print(u'==压缩成功==')
        z.close()

    @staticmethod
    def project_root_path(project_name=None):
        """
        获取当前项目根路径
        :param project_name:
        :return: 根路径
        """
        PROJECT_NAME = 'AutoFrame' if project_name is None else project_name
        project_path = os.path.abspath(os.path.dirname(__file__))
        sep = os.sep
        root_path = project_path[:project_path.find("{}{}".format(PROJECT_NAME, sep)) + len("{}{}".format(PROJECT_NAME,sep))]
        return root_path

if __name__ == '__main__':
    File_utils.project_root_path("AmberIM")
