##############################################################################
#
#       Organsises photo albums:
#       (1) Creates csv file of images tagged album_*
#       (2) Copies these images to album target directory in uncompressed and
#            compressed forms
#       (3) Deletes any other files in this directory that aren't the
#           tagged images
#
#       REQUIRES LIBIPTCDATA, RCLONE AND IMAGEMAGICK TO BE INSTALLED ON SYSTEM       
#
##############################################################################




import os, shutil, subprocess, csv, re, time


#------------------------------------------------------------------------------
#       Folder & file paths
#------------------------------------------------------------------------------

src_dir='/home/charl/TempSynoMount/TestPhotosOriginal'
# src_dir='/home/charl/TempPhotoMount/020_All_Photos/Charl_Kerrie_Family/2017'

album_file_path='/home/charl/TempSynoMount/TestAlbumStructure.csv'

target_dir_root='/home/charl/TempSynoMount/TestPhotoAlbums'

target_small_compressed_dir_root=('/home/charl/TempSynoMount/'
                                   'TestPhotoAlbumsSmall')

target_medium_compressed_dir_root=('/home/charl/TempSynoMount/'
                                   'TestPhotoAlbumsMedium')


#------------------------------------------------------------------------------
#      Other constants 
#------------------------------------------------------------------------------

SMALL_MAX_ALLOWED_LENGTH = 1000
MEDIUM_MAX_ALLOWED_LENGTH = 2048







def create_csv():
    """ creates csv file containing album structure"""

    with open(album_file_path, 'w', newline='') as album_file:
        album_writer = csv.writer(album_file)
        album_writer.writerow([
                                'source_file', 'album_tag', 'target_file', 
                                'target_file_compressed_small', 
                                'target_file_compressed_medium'
                              ])

        album_writer=csv.writer(album_file)

        for (rootdir, subfolders, fnames) in os.walk(src_dir):
            print('processing ', rootdir, '...')
            for fname in fnames:

                # Read iptc image tag with ptc command line function and pipe
                # The std output. Use Popen rather than run as can more easily
                # interact with stdout using Popen.commnuicate as below which 
                # automatically waits for e child process ot finish before
                # continuing with the python code
                fname_full=os.path.join(rootdir, fname)
                proc=subprocess.Popen(
                                     ['iptc', '--print=Keywords', fname_full],
                                     stdout=subprocess.PIPE, 
                                     stderr=subprocess.PIPE
                                    )

                # read piped data above into byte/binary variable and convert 
                # output to a standard string
                outs,errs = proc.communicate()
                output_str=outs.decode(encoding="utf-8", errors="ignore")
                
                #Extract all album tags using regular expression
                album_tags=re.findall('[^ ]*album_[^ \n]*', output_str)

                #write source file name, tag and target and compressed target 
                #to csv file
                for album_tag in album_tags:

                    target_file = (target_dir_root + os.sep 
                                + re.sub('^album_[a-zA-Z0-9]*_', '', album_tag)
                                + os.sep + fname)

                    target_file_compressed_small = target_file.replace(
                                            target_dir_root,
                                            target_small_compressed_dir_root
                                            )

                    target_file_compressed_medium = target_file.replace(
                                            target_dir_root, 
                                            target_medium_compressed_dir_root
                                            )

                    album_writer.writerow([
                                            fname_full, 
                                            album_tag, 
                                            target_file, 
                                            target_file_compressed_small, 
                                            target_file_compressed_medium
                                          ])


def copy_images():
    """copy images to create folders containing albums"""

    

    with open(album_file_path) as album_file:

        album_reader=csv.DictReader(album_file)

        for row in album_reader:

            # Create copies of images in uncompressed album
            target_file=row['target_file']
            if not os.path.isfile(target_file):
                print('copying ', target_file)
                target_path=os.path.split(target_file)[0]
                os.makedirs(target_path, exist_ok=True)
                shutil.copy2(row['source_file'], target_file)


            # Create copies of images in small compressed album
            target_file=row['target_file_compressed_small']
            if not os.path.isfile(target_file):
                print('copying ', target_file)
                target_path=os.path.split(target_file)[0]
                os.makedirs(target_path, exist_ok=True)
                shutil.copy2(row['source_file'], target_file)


                # Read image width and height using imagemagick into standard 
                # output and convert binary to normal string with decode
                proc=subprocess.Popen([
                                        'identify', 
                                        '-format', 
                                        '"%w"', 
                                        target_file
                                        ],
                                        stdout=subprocess.PIPE, 
                                        stderr=subprocess.PIPE
                                    )
                outs,errs = proc.communicate()
                original_width=int(outs.decode().replace('\"', ''))
                proc=subprocess.Popen([
                                        'identify', 
                                        '-format', 
                                        '"%h"', 
                                        target_file
                                        ], 
                                        stdout=subprocess.PIPE, 
                                        stderr=subprocess.PIPE
                                    )
                outs,errs = proc.communicate()
                original_height=int(outs.decode().replace('\"', ''))
                
                max_img_side=max(original_width, original_height)
                if max_img_side>SMALL_MAX_ALLOWED_LENGTH:
                    compression_ratio = str(round(
                                                    SMALL_MAX_ALLOWED_LENGTH /
                                                    max_img_side * 100
                                                )) + "%"
                    proc=subprocess.call([
                                            'mogrify', 
                                            '-resize', 
                                            compression_ratio, 
                                            target_file
                                        ])                
 

            # Create copies of images in medium  compressed album
            target_file=row['target_file_compressed_medium']
            if not os.path.isfile(target_file):
                print('copying ', target_file)
                target_path=os.path.split(target_file)[0]
                os.makedirs(target_path, exist_ok=True)
                shutil.copy2(row['source_file'], target_file)


                # Read image width and height using imagemagick into standard 
                # output and convert binary to normal string with decode
                proc=subprocess.Popen(
                                        [
                                        'identify', 
                                        '-format', '"%w"', 
                                        target_file
                                        ], 
                                        stdout=subprocess.PIPE, 
                                        stderr=subprocess.PIPE
                                     )

                outs,errs = proc.communicate()
                original_width=int(outs.decode().replace('\"', ''))
                proc=subprocess.Popen(['identify', '-format', '"%h"', target_file], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                outs,errs = proc.communicate()
                original_height=int(outs.decode().replace('\"', ''))
                
                max_img_side=max(original_width, original_height)
                if max_img_side>MEDIUM_MAX_ALLOWED_LENGTH:
                    compression_ratio = str(round(MEDIUM_MAX_ALLOWED_LENGTH / max_img_side * 100)) + "%"
                    proc=subprocess.call(['mogrify', '-resize', compression_ratio, target_file])                
                    

    

def delete_non_album_files():
    """deletes any file in album directory that are not tagged images that belong in that album"""

    #Read all target images as per the csv file into a list
    with open(album_file_path) as album_file:
        album_reader=csv.DictReader(album_file)
        image_list=[]
        image_list_compressed_small=[]
        image_list_compressed_medium=[]
        for row in album_reader:
            image_list.append(row['target_file'])
            image_list_compressed_small.append(row['target_file_compressed_small'])
            image_list_compressed_medium.append(row['target_file_compressed_medium'])

    
    
    #Delete files in album folder that are not in the tagged image list in the csv file
    for (rootdir, subfolders, fnames) in os.walk(target_dir_root):
        for fname in fnames:
            fname_path=os.path.join(rootdir, fname)
            if not fname_path in image_list:
                print ('Deleting ', fname_path)
                os.remove (fname_path)


    #Delete files in SMALL COMPRESSED album folder that are not in the tagged image list in the csv file
    for (rootdir, subfolders, fnames) in os.walk(target_small_compressed_dir_root):
        for fname in fnames:
            fname_path=os.path.join(rootdir, fname)
            # 2nd and statement prevents deletion of hidden files, e.g. those used for syncing folders
            if (not fname_path in image_list_compressed_small) and (fname[0]!='.'):
                print ('Deleting ', fname_path)
                os.remove (fname_path)


    #Delete files in MEDIUM COMPRESSED album folder that are not in the tagged image list in the csv file
    for (rootdir, subfolders, fnames) in os.walk(target_medium_compressed_dir_root):
        for fname in fnames:
            fname_path=os.path.join(rootdir, fname)
            # 2nd and statement prevents deletion of hidden files, e.g. those used for syncing folders
            if (not fname_path in image_list_compressed_medium) and (fname[0]!='.'):
                print ('Deleting ', fname_path)
                os.remove (fname_path)





def send_to_dropbox():
    """Clones medium photo albums to dropbox.   Assumes rclone is already configured on system"""

    print ('\nSending compressed photos to dropbox...')
    subprocess.run(["timeout", "1h", "rclone", "sync", "--config", "/home/charl/.rclone.conf", target_medium_compressed_dir_root, "DropBox:PhotoAlbumsCompressed"])
    
    #Commented out as dropbox account is too full at the moment to accomodate uncompressed photos
    #print ('\nSending uncompressed photos to dropbox...')
    #subprocess.run(["timeout", "1h", "rclone", "sync", "--config", "/home/charl/.rclone.conf", target_dir_root, "DropBox:PhotoAlbums"])
    

if __name__ == "__main__":

    t0 = time.time()

    create_csv()
    # copy_images()
    # delete_non_album_files()
    # send_to_dropbox()

    t1 = time.time()
    print(t1 - t0)