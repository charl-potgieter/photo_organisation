##############################################################################
#
#       Organsises photo albums:
#       (1) Creates csv file of images tagged album_*
#       (2) Copys these images to album target directory (will overwrite 
#           any existing images
#
#       REQUIRES EXIV2, PYTHON 3.5+
#
##############################################################################



def read_config_values():
    """Reads values from the configuration files and returns dictionary"""
    
    if config_file_exists():
        import config
    else:
        raise ValueError ('Missing file config.py, please refer to documentation') 
    
    # Values in a hidden config file override the config file, useful to prevent user config settings being pushed to github
    if hidden_config_file_exists():
        import _config
        if config.config.keys() != _config.config.keys():
            raise ValueError ('keys in config files dont match hidden config file') 
        else:
            config_values = _config.config
    else:
        config_values = config.config
    
    return (config_values)


def config_file_exists():
    """ Check if a configuration file exists"""
    return(os.path.isfile('config.py'))


def hidden_config_file_exists():
    """ Check if hidden configuration file exists"""
    return(os.path.isfile('_config.py'))


def in_dir_exists(in_dir):
    """Check if in_dir directory exists"""
    return(os.path.isdir(in_dir))
            
            
def dir_exists(dir):
    """Check if out_dir directory exists"""
    return(os.path.isdir(dir))


def create_dir_and_parents(dir):
    """Create out_dir"""
    pathlib.Path(dir).mkdir(parents=True)

    
def dir_is_empty(dir):
    """Returns true if dir is empty otherwise false"""
    return (len(os.listdir(dir)) == 0)


def file_is_an_image(filepath):
    """retrurns true if filepath is an image otherwiser false"""
    # Extensions per exiv2 formats supporting both iptc and xmp read writes (with addition of jpg for jpegs)
    # https://dev.exiv2.org/projects/exiv2/wiki/Supported_image_formats
    image_extensions_lower_case = ['.jpeg','.jpg','.exv','.cr2','.tiff','.webp','.dng','.nef','.pef','.srw','.orf','.png','.pgf','.psd','.jp2']
    base_filename, file_extension = os.path.splitext(filepath)
    return (file_extension.lower() in image_extensions_lower_case)


def get_input_image(image_file_path):
    """Returns Pillow image at image_file_path and rotates if required"""
    input_image = Image.open(image_file_path)
    # If orientation is stored via exif metadata then transpose image and remove the orientation metadata
    input_image = ImageOps.exif_transpose(input_image)
    return(input_image)


def get_image_title(image_file_path):
    """Returns the XMP description of image at image_file_path (XMP description shows as 'title' in Windows Explorer)"""
    result = subprocess.run(['exiv2', '-g', 'Xmp.dc.description', '-Pv', image_file_path], stdout=subprocess.PIPE)
    title = result.stdout.decode(encoding="utf-8").strip()
    # remove text similiar to this 'lang="<something>"' that occurs at start of the string
    title = re.sub('lang=".*" ', '', title)
    return (title)


def get_image_caption(image_file_path, caption_prefix):
    """returns image caption, where caption  = XMP description if it starts caption_prefix"""
    image_title = get_image_title(image_file_path)
    if text_starts_with_prefix(image_title, caption_prefix):
        return(text_ex_prefix(image_title, caption_prefix))
    else:
        return(None)


def get_itpc_keywords(image_file_path):
    """Returns a list of itpc keyword"""
    result = subprocess.run(['exiv2', '-K', 'Iptc.Application2.Keywords', '-Pv', image_file_path], stdout=subprocess.PIPE)
    keywords = result.stdout.decode(encoding="utf-8").strip()
    keywordlist = keywords = keywords.split('\n')
    return(keywordlist)


def text_starts_with_prefix(text_to_check, prefix):
    """Returns true if text_to_check is not empty and starts with prefix"""
    if text_to_check == '' or text_to_check is None:
        return (False)
    elif prefix == '':
        return (True)
    elif text_to_check[:len(prefix)] == prefix:
        return (True)
    else:
        return (False)

    
def text_ex_prefix(input_text, prefix):
    """Returns input_text excluding prefix, stripped of leading and trailing spaces"""    
    return(input_text[-len(input_text) + len(prefix):].strip())


def generate_captioned_image(input_image, frame_ratio, border_ratio, border_colour, frame_colour,
                             caption_font, font_ratio, font_size_min, font_colour, caption):
    """ Adds frame, border and text caption to Pillow image img"""
    
    # Get / calculate dimensions
    original_image_width = input_image.size[0]
    original_image_height = input_image.size[1]
    max_original_image_side_length = max(original_image_width, original_image_height)
    border_thickness = round(max_original_image_side_length * border_ratio)
    frame_thickness =  round(max_original_image_side_length * frame_ratio)
    border_width = original_image_width + border_thickness * 2
    border_height = original_image_height + border_thickness * 2
    frame_width = border_width + frame_thickness * 2
    frame_height = border_height + frame_thickness * 2
    font_size = max(font_size_min,  round(max_original_image_side_length * font_ratio))
    
    # Paste original image inside border, then inside frame
    bordered_image = Image.new('RGB', (border_width, border_height), border_colour)
    bordered_image.paste(input_image, (border_thickness, border_thickness))
    framed_image = Image.new('RGB', (frame_width, frame_height), frame_colour)
    framed_image.paste(bordered_image, (frame_thickness, frame_thickness))
    
    # Add text to the framed image
    text_x = round(frame_width/2)
    text_y = round(frame_height - frame_thickness - border_thickness/2)
    caption_font = ImageFont.truetype(caption_font, font_size)
    ImageDraw.Draw(framed_image).text(xy=(text_x,text_y), text=caption, font=caption_font, fill=font_colour, anchor='mm')
    
    return(framed_image)


def copy_metadata(input_filepath, output_filepath):
    """copies image metadata from infile to outfile"""
    ps = subprocess.run(['exiv2', '-e', '-a', input_filepath], check=True, capture_output=True)
    op = subprocess.run(['exiv2', '-i' '-a', output_filepath], input=ps.stdout)


def create_csv(in_dir, out_dir, csv_summary_file_path, album_tag_prefix, caption_prefix):
    """ creates csv file containing 'source_file', 'album_tag', 'target_file'and 'caption'"""

    with open(csv_summary_file_path, 'w', newline='') as album_file:
        album_writer = csv.writer(album_file)
        album_writer.writerow(['source_file', 'album_tag', 'target_file', 'caption'])
        for (rootdir, subfolders, fnames) in os.walk(in_dir):
            print('processing ', rootdir, '...')
            for fname in fnames:
                if file_is_an_image(fname):
                    fname_full=os.path.join(rootdir, fname)
                    caption = get_image_caption(fname_full, caption_prefix)                  
                    keywords = get_itpc_keywords (fname_full)
                    for keyword in keywords:
                        if text_starts_with_prefix(keyword, album_tag_prefix):
                            album_name = text_ex_prefix(keyword, album_tag_prefix)
                            target_file = out_dir + os.sep + album_name + os.sep + fname
                            album_writer.writerow([fname_full, album_name, target_file, caption])

                            
def copy_images(csv_summary_file_path, frame_ratio, border_ratio, border_colour, frame_colour, caption_font,
               font_ratio, font_size_min, font_colour):
    """copy images to create folders based on info in csv_summary_file path containing albums, captioning images if applicable"""
    with open(csv_summary_file_path) as album_file:
        album_reader=csv.DictReader(album_file)
        for image_details in album_reader:
            target_path=os.path.split(image_details['target_file'])[0]
            os.makedirs(target_path, exist_ok=True)
            if not os.path.isfile(image_details['target_file']):
                print('copying ', image_details['target_file'])
                if image_details['caption'] !='' and image_details['caption'] != None:
                    input_image = get_input_image(image_details['source_file'])
                    output_image= generate_captioned_image(input_image=input_image, frame_ratio = frame_ratio, 
                        border_ratio = border_ratio, border_colour = border_colour, frame_colour = frame_colour,
                        caption_font = caption_font, font_ratio = font_ratio, font_size_min = font_size_min,                                   
                        font_colour = font_colour, caption = image_details['caption'])
                    output_image.save(image_details['target_file'])
                    copy_metadata(image_details['source_file'], image_details['target_file'])
                else:
                    shutil.copy2(image_details['source_file'], image_details['target_file'])   

                
def display_untagged_images_in_target(csv_summary_file_path, out_dir):
    """Displays any files in target directory that are not tagged for album inclusion"""
    
    #Read all target images as per the csv file into a list
    with open(csv_summary_file_path) as album_file:
        album_reader=csv.DictReader(album_file)
        image_list = []
        for image_detail in album_reader:
            image_list.append(image_detail['target_file'])

    for (rootdir, subfolders, fnames) in os.walk(out_dir):
        for fname in fnames:
            fname_path=os.path.join(rootdir, fname)
            if not fname_path in image_list:
                print ('WARNING: ' +  fname_path + ' exists in target directory but is not tagged.  Potential manual delete required')


if __name__ == "__main__":

    from PIL import Image, ImageDraw, ImageFont, ImageOps
    import os, shutil, subprocess, csv, re
                
    inputs = read_config_values()
    create_csv(in_dir = inputs['in_dir'], out_dir = inputs['out_dir'], 
               csv_summary_file_path= inputs['csv_summary_file_path'], album_tag_prefix =  inputs['album_tag_prefix'], 
               caption_prefix = inputs['caption_prefix'])
    copy_images(csv_summary_file_path=inputs['csv_summary_file_path'], frame_ratio=inputs['frame_ratio'], 
                border_ratio = inputs['border_ratio'], border_colour = inputs['border_colour'], 
                frame_colour = inputs['frame_colour'], caption_font = inputs['caption_font'],
                font_ratio = inputs['font_ratio'], font_size_min = inputs['font_size_min'], 
                font_colour = inputs['font_colour'])
    display_untagged_images_in_target( csv_summary_file_path =  inputs['csv_summary_file_path'], out_dir = inputs['out_dir'])
    print ('\n' + 'processing complete')