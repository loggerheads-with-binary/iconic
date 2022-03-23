from argparse import ArgumentParser, Namespace
import os, subprocess
from . import icon_make
import logging

"""
Sets icons to different files, also allows retrieval. 
Can also be used to create icons to be then set to some file
"""


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

convert_engine = icon_make.convert_engine

TYPES_ALLOWED = ['lnk/url' , 'lnk' , 'url' , 'exe' , 'folder' , 'dir' , 'drive' , 'reg']

def arguments(args : list = None):

    global types_allowed

    parser = ArgumentParser(prog = 'icon-set' , description = "Sets/Retrieves icons on Windows" ,
                            epilog = f'Stored @{os.path.dirname(os.path.abspath(__file__))}')

    parser.add_argument("file" , type = os.path.abspath ,
                        help = 'Path to the shortcut/folder/program/drive you are setting the icon for')

    # parser.add_argument("--type" , choices = types_allowed , default = None ,
    #                     help = "Type of setting icon. DEFAULT pulled from the file type")

    parser.add_argument('-i' , '--icon' , '--icon-file' , type = os.path.abspath , dest = 'icon' , default = None ,
                        help = 'Path to the icon file to be used')

    parser.add_argument('-r' , '--retrieve' , '--get' , '--obtain' , action = 'store_const' , default = 'set' , const = 'get' ,
                        dest = 'mode' , help = "Retrieve the icon file instead of setting an icon")

    add_parser = parser.add_argument_group("Additional Functionalities")

    add_parser.add_argument("-d" , '--drive' , '--drive-mode' , '--mode=drive' , action = 'store_true' , dest = 'drive_mode' , 
                        help = "Set icon to drive through the windows registry. NOTE: Requires admin elevated shell privileges.")

    add_parser.add_argument('-a' , '--assoc' , '--file-assoc' , '--file-association' , dest = 'assoc' , action = 'store_const' , const = True,
                            default = None , help = "Retrieve/set file association icons through registry")

    process_parser = parser.add_argument_group("Process a source file")

    process_parser.add_argument('--src' , '--isrc' , '--icon-source' , type = os.path.abspath , dest = 'icon_source' , default = None ,
                        help = 'Source file to generate icon. Only .png/.bmp/.jpg files accepted')

    process_parser.add_argument('--idest'  , '--icon-dest' , type = os.path.abspath , dest = 'icon_dest'  , default = None ,
                        help = 'Destination file to be generated if using source file. DEFAULT just creates .ico of same original file')

    if args is None:
        return parser.parse_args()

    return parser.parse_args(args)

##NOTE: Icon = None => get mode; else set mode 
def icon_shortcut(file , icon = None):

    import win32com.client 
    shell = win32com.client.Dispatch("WScript.Shell")

    shortcut = shell.CreateShortcut(file)

    if icon is None:
        logger.info("Retrieving shortcut icon path")
        return shortcut.IconLocation 

    else:
        logger.info("Setting shortcut icon path")
        shortcut.IconLocation = os.path.abspath(icon)
        logger.debug('Saving changes')
        shortcut.save()
        return None 

class IconSet():

    def folder(self , icon , folder ):

        assert os.path.isdir(folder) , f'The given file is not a directory'

        from configparser import ConfigParser

        config = ConfigParser()
        desktop_ini = os.path.join(folder , 'desktop.ini')
        logger.debug(f"Desktop.ini file: {desktop_ini}")

        if not os.path.exists(desktop_ini):
            open(desktop_ini , 'w+').close()
            
        config.read(desktop_ini)

        if not config.has_section(".ShellClassInfo"):
            config.add_section(".ShellClassInfo")

        config.set('.ShellClassInfo' , 'IconResource' , f"{os.path.abspath(icon)},0")

        logger.debug("Unlocking desktop.ini")
        subprocess.call(f"attrib -h -s \"{desktop_ini}\"")

        with open(desktop_ini , 'w+') as filehandle:
           config.write(filehandle)

        logger.debug("Locking desktop.ini")
        subprocess.call(f"attrib +h +s \"{desktop_ini}\"")

        return True 

    def shortcut(self , icon, file):

        return icon_shortcut(file , icon)
        
    def executable(self , icon, file):

        x = subprocess.call(['rcedit.exe' , file , '--set-icon' , icon])

        if x !=0 :
            raise RuntimeError("Setting icon file failed")

        logger.info(f"Icon {icon} successfully set on {file}")

        return True

    def drive(self , icon , file):

        import re 

        ##The program changes the environment variable ICON_SET_RUNNING to 1 temporarily to make sure the warning is not raised from registry_edit
        
        logger.debug("Setting 'ICON_SET_RUNNING' environment variable")
        os.environ['ICON_SET_RUNNING'] = '1' 
        from .registry_edit import write_reg 

        assert re.match(r"^[A-Z](\:|\:\\)?$" , file), f'Path: `{file}` is not a drive'
        logger.debug("Valid drive")
        
        status = write_reg(drive = file , icon = icon)
        
        if status is   True:
            logger.info(f"Icon {icon} set for Drive: {file}")

        else:
            
            #logger.error("Icon not set on drive")
            raise RuntimeError("Icon setting unsuccessful")

        os.environ.pop("ICON_SET_RUNNING")
        logger.debug("Popped 'ICON_SET_RUNNING' environment variable")

        return True 

    def assoc(self , icon , file):

        from .registry_edit import write_assoc
        write_assoc(file , icon)

class IconGet():

    def folder(self, icon = None, folder = None):
        
        from configparser import ConfigParser

        desktop_ini = os.path.join(folder , 'desktop.ini')
        logger.debug(f"Desktop.ini file: {desktop_ini}")

        if not os.path.exists(desktop_ini):
            raise FileNotFoundError('desktop.ini not found in target folder')

        logger.debug("Found desktop.ini; setting up parser")

        config = ConfigParser()
        config.read(desktop_ini)

        assert config.has_section(".ShellClassInfo"), f'ShellClassInfo Section does not exist in desktop.ini'
        assert config.has_option(".ShellClassInfo" , 'IconResource'), f'IconResource Value does not in desktop.ini'

        val = config.get(".ShellClassInfo" , 'IconResource')

        logger.info("Successfully retrieved icon path")

        if __name__ == '__main__':
            print(val)
        
        return val 

    def shortcut(self , icon = None , file = None):

        icon = icon_shortcut(file , None)        
        logger.info("Path to icon file is listed below")
        
        if __name__ == '__main__':
            print(icon)
        
        return icon 
    
    ##TODO: Complete this part 
    def dll(self , icon : list = None, file = None , count : list = [0]):
 
        if icon is None:
            raise Exception("For executables, icon paths need to be defined as they have to be saved there")

        if len(icon) != len(count):
            raise ValueError("Number of icons to be extracted don't match output")

        from .ico_extract import IconExtractor

        xtractor = IconExtractor(file)

        raise NotImplementedError("Function not completed yet")

    def executable(self , icon = None , file = None):

        if icon is None:
            raise Exception("For executables, icon paths need to be defined as they have to be saved there")

        logger.debug("Extracting icon from an executable")

        from .ico_extract import IconExtractor

        logger.debug("Loading program file")
        xtractor = IconExtractor(file)
        #xtractor._get_group_icon_entries()

        xtractor.export_icon(icon)  
        logger.info(f"Icon from {file} saved at {icon}")


        # import win32ui
        # import win32gui
        # import win32con
        # import win32api

        # ico_x = win32api.GetSystemMetrics(win32con.SM_CXICON)
        # ico_y = win32api.GetSystemMetrics(win32con.SM_CYICON)

        # large, small = win32gui.ExtractIconEx(file,0)
        # win32gui.DestroyIcon(small[0])

        # logger.debug("Windows GUI Icon extraction completed")

        # hdc = win32ui.CreateDCFromHandle(win32gui.GetDC(0))
        # hbmp = win32ui.CreateBitmap()
        # hbmp.CreateCompatibleBitmap(hdc, ico_x, ico_x)
        # hdc = hdc.CreateCompatibleDC()

        # logger.debug("Icon Extraction completed")

        # hdc.SelectObject(hbmp)
        # hdc.DrawIcon((0,0), large[0])

        # hbmp.SaveBitmapFile( hdc, '_icon.tmp.bmp')
        # logger.debug("Icon saved temporarily as _icon.tmp.bmp")

        # convert_engine('_icon.tmp.bmp' , icon)
        # logger.info(f"Executable icon saved as {icon}")

        # os.remove('_icon.tmp.bmp')
        # logger.debug("Temporary file '_icon.tmp.bmp' has been removed")

    def drive(self , icon = None , file = None):
        
        import re          
        assert re.match(r"^[A-Z](\:|\:\\)?$" , file), f'Path: `{file}` is not a drive'


        ##The program changes the environment variable ICON_SET_RUNNING to 1 temporarily to make sure the warning is not raised from registry_edit
        
        logger.debug("Setting 'ICON_SET_RUNNING' environment variable")
        os.environ['ICON_SET_RUNNING'] = '1'
        from .registry_edit import read_reg 

        icon = read_reg(file, flags = (True,False))

        if icon[0] is True:
            icon = icon[1]

        else:
            raise ValueError("Could not obtain icon file path")

        if __name__ == '__main__':
            print(icon)
        
        os.environ.pop("ICON_SET_RUNNING")
        logger.debug("Popped 'ICON_SET_RUNNING' environment variable")

        return icon

    def _prog_assoc(self , icon  = None , file = None):

        import win32ui
        import win32gui
        import win32con
        import win32api
        from PIL import Image   

        """
        From Stack Overflow: https://stackoverflow.com/questions/25511706/get-associated-filetype-icon-for-a-file
        """ 

        tempDirectory = os.getenv("temp")
        tempfile = os.path.join(tempDirectory , f'icon_res.tmp.bmp')
        logger.debug("setup temporary file %s" %tempfile)

        logger.debug("Extracting icon from source program")
        ico_x = win32api.GetSystemMetrics(win32con.SM_CXICON)
        large, small = win32gui.ExtractIconEx(file,0)
        win32gui.DestroyIcon(small[0])


        logger.debug("Creating bitmap")
        #creating a destination memory DC
        hdc = win32ui.CreateDCFromHandle( win32gui.GetDC(0) )
        hbmp = win32ui.CreateBitmap()
        hbmp.CreateCompatibleBitmap(hdc, ico_x, ico_x)
        hdc = hdc.CreateCompatibleDC()

        hdc.SelectObject( hbmp )

        #draw a icon in it
        logger.debug("DrawIcon::Post Processing")
        hdc.DrawIcon( (0,0), large[0] )
        win32gui.DestroyIcon(large[0])

        #convert picture
        logger.debug("Creating temporary bitmap file")
        hbmp.SaveBitmapFile( hdc, tempfile)

        logger.debug("Converting to ico file")
        im = Image.open(tempfile)
        im.save(icon)

        logger.debug("Removing temporary bitmap file")
        os.remove(tempfile)

        return im 

    def assoc(self , icon = None , file = None):

        from .registry_edit import read_assoc

        s = read_assoc(os.path.splitext(file)[-1])

        if s[0] is False:
            logger.warning(f'DefaultIcon does not exist for file type. Searching programID')    

            if icon is None:
                raise RuntimeError("Since there is no DefaultIcon; an icon path is needed to store the generated file")

            self._prog_assoc(icon = icon , ext = ext)

        else:
            return s[-1]

engine = IconSet()

def driver(args : Namespace):

    global logger, Processor, engine 

    if (args.icon is None) and (args.icon_source is None) and (args.mode == 'set'):
        raise ValueError("No input icon file or source file provided")

    elif (args.icon is not None) and (args.mode == 'set') :

        if os.path.splitext(args.icon)[-1] != '.ico':
            raise TypeError(f"Icon file is invalid with extension `{os.path.splitext(args.icon)[-1]}` instead of `.ico`")

        if not os.path.exists(args.icon):
            raise FileNotFoundError("Icon file does not exist")

        logger.info("Icon file exists")

    elif args.icon_source is not None:

        if not os.path.exists(args.icon_source):
            raise FileNotFoundError("Source file for the icon does not exist @{}".format(args.icon_source))

        ext = os.path.splitext(args.icon_source)[-1]



        # if not os.path.splitext(args.icon_source)[-1] in ['.bmp' , '.png' , '.jpg' , '.jpeg']:
        #     raise Exception("Icon resource file is invalid; cannot use `{}` files".format(os.path.splitext(args.icon_source)[-1]))

        logger.info(f"Creating icon from source file {args.icon_source}")

        if args.icon_dest is None:

            args.icon_dest = f'{args.icon_source}.ico'

        if ext == '.exe':

            IconGet().executable(icon = args.icon_dest , file = args.icon_source)
            logger.info("Icon file extracted from soufce executable file")

        elif os.path.isdir(args.icon_source):

            args.icon_source = IconGet().folder(folder = args.icon_source)
            logger.debug("Obtained icon path of source folder")
            convert_engine(args.icon_source , args.icon_dest)
            logger.info("Icon file generated from icon file of source directory")

        else:

            convert_engine(args.icon_source , args.icon_dest)
            logger.info("Icon file generated from source image file")
        

        args.icon = args.icon_dest

    if not (os.path.exists(args.file) or (args.assoc is not None )) :
        raise FileNotFoundError("File to set icon on does not exist")

    logger.debug(f"Icon file: {args.icon}")
    logger.debug(f"Target file: {args.file}")

    if args.drive_mode:

        logger.debug("Set to Drive Mode")
        engine.drive(args.icon , args.file)

    elif args.assoc is not None:

        logger.critical("Association mode is still in a debug stage")

        logger.debug("Setting up file association mode")
        engine.assoc( args.icon , args.file )


    else:

        if os.path.isdir(args.file):

            logger.info("Selected file is a directory")
            logger.debug("Using directory method")
            engine.folder(args.icon , args.file)

        elif os.path.splitext(args.file)[-1] in (".lnk" , ".url"):

            logger.info("Selected file is a windows shortcut")
            logger.debug("Using windows shortcut method")
            engine.shortcut(args.icon , args.file)         
        
        elif os.path.splitext(args.file)[-1] == '.exe':

            logger.info("Selected file is a windows executable")
            logger.debug("Using windows executable method")
            engine.executable(args.icon , args.file)

        logger.info("Operation completed")

if __name__ == '__main__':

    import pretty_traceback , coloredlogs

    pretty_traceback.install()
    coloredlogs.install(fmt = "[%(name)s] %(asctime)s %(levelname)s : %(message)s" , level = logging.DEBUG)

    args = arguments()

    if args.mode == 'get':
        engine = IconGet()

    elif args.mode == "set":
        engine = IconSet()

    else:
        raise NotImplementedError("Mode can only be get/set; not {}".format(args.mode))

    logger.debug("Arguments Parsed")
    driver(args)
