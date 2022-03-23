#!/usr/bin/env python3

"""
Creates icons from source files
"""

from warnings import warn
from argparse import ArgumentParser
import os 
import logging 

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

SIZES = [(256, 256) , ]

def arguments(args: list = None):

    global SIZES

    parser = ArgumentParser(prog = 'icon-make' , description = 'Creates icons from source files')
    
    parser.add_argument("file" , type = os.path.abspath , nargs = '+' , help = "Source file(s) to convert" )
    parser.add_argument("-s" , '--size' , type = lambda x : (int(x) ,)*2 , help = "Size to set to the file" , default =  SIZES)
    parser.add_argument('-o' , '--output' , '-d' , '--dest' , nargs = '+' ,  dest = 'output' , help = "Output/Destination icon file(s)" , default = list())

    if args is None:
        return parser.parse_args()

    return parser.parse_args(args)

def convert_engine(src, dest , sizes = SIZES):

    from PIL import Image 
    logger.debug("reading source file @{}".format(src))
    img = Image.open(src)

    w , h = img.size 

    if w != h:
        warn("Image dimensions are not same, can lead to graphic disproportion")

    img.save(dest , sizes = sizes )
    logger.info(f'Icon conversion {src}->{dest} successfully completed')

if __name__ == '__main__':

    import coloredlogs, pretty_traceback
    pretty_traceback.install()
    coloredlogs.install(fmt = "[%(name)s] %(asctime)s %(levelname)s : %(message)s" , level = logging.DEBUG)

    args = arguments()
    assert len(args.file) > 0 , f"No files to be converted to icons"
    
    if len(args.output) !=0 :
        
        if len(args.output) != len(args.file):
            raise ValueError("Number of input files should be same as number of output files")

        else:
            logger.debug("All file input and output names have been mentioned.")
            RENAME_NECESSITY = False 

    else:

        logger.info(f"No output names have been seen so far, assuming auto mode for extraction")
        RENAME_NECESSITY = True 


    for _idx, i_file in enumerate(args.file):

        o_file = (f'{os.path.splitext(i_file)[0]}.ico') if RENAME_NECESSITY else (args.output[_idx])
        convert_engine(i_file , o_file , args.size )
