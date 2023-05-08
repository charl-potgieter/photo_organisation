config = {
    'in_dir': '/SourceFolder',
    
    'out_dir': '/TargetFolder',
    
    # Path of csv file that summarises photos and captions of images
    'csv_summary_file_path' : '/folder/fname.csv', 
    
    #If not blank, only itpc keywords with this prefic are moved to album directories
    'album_tag_prefix' : '',
    
    # Percentage of frame compared to longest side of image
    'frame_ratio': 0.0075,

    # Percentage of borders compared to longest side of image (Border is area between frame and image)
    'border_ratio': 0.05,
    
    'border_colour': 'RGB(220,220,220)',
    
    'frame_colour': 'RGB(120,75,50)',
 
    # Note below needs to be a TrueType or OpenType font as required by python-pillow and needs to be installed on the system
    'caption_font': 'DejaVuSerif.ttf',
    
    # Font size as a percentage of image longest side 
    # Font size is set with a ratio as otherwise even large font will appear very small on a high res image that is shrunk to fit on screen
    'font_ratio' :  0.015,
    
    # Allows for setting of a minimum font size covering event where size calcualted by ratio above is too small on a low res image
    'font_size_min': 80,
    
    'font_colour': 'RGB(0,0,0)',
    
    # Only caption images if XMP description (Windows title) contains below prefix.  If blank all descriptions will be used for captioning
    'caption_prefix' : '<cjp>'
    
}