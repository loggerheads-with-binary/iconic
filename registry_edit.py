import winreg 
import warnings 
import logging 
import os 

"""
Does the necessary registry edit part for drives and file associations
"""


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

if not 'ICON_SET_RUNNING' in os.environ:
    warnings.warn("The registry_edit script works only for iconic package due to setup")

#BASE_KEY  = r"HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\DriveIcons"
BASE_KEY = winreg.HKEY_LOCAL_MACHINE
REAL_KEY = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\DriveIcons"
VALUE_NAME = ""

##Cross platform way to identify admin status
def is_admin():
    
    try:
        import os 
        return bool(os.getuid() == 0)

    except AttributeError:
        import ctypes
        return bool(ctypes.windll.shell32.IsUserAnAdmin() != 0)

def _read_reg(key , base = BASE_KEY , value = VALUE_NAME):

    global VALUE_NAME , REAL_KEY

    logger_ = logging.getLogger("read-reg")
    logger_.setLevel(logging.DEBUG)

    ##Do not need admin access to read registry 
    
    try:

        try:

            reg_key = winreg.OpenKey(base , key , 0 , winreg.KEY_READ)
            logger_.debug("Drive Registry Key already exists")            

        except:

            logger_.error("DriveIcon registry key does not exist")
            return (False , None)

        val , _ = winreg.QueryValueEx(reg_key , value)
        winreg.CloseKey(reg_key)
        
        return (True, val)

    except WindowsError:

        logger_.error("WindowsError occured")
        return (False, None) 

    except:
        raise 

def _write_reg(key , val , base = BASE_KEY , value_name = VALUE_NAME):

    global REAL_KEY , VALUE_NAME
    
    logger_ = logging.getLogger("write-reg")
    logger_.setLevel(logging.DEBUG)
    
    try:
        
        try:

            reg_key = winreg.OpenKey(base , key , 0 , winreg.KEY_WRITE)
            logger_.debug("Drive Registry Key already exists")

        except:

            winreg.CreateKey(base , key)
            logger_.debug("Drive registry key created")
            
            reg_key = winreg.OpenKey(base , key , 0 , winreg.KEY_WRITE)
            logger_.debug("Loaded registry key")

        winreg.SetValueEx(reg_key , value_name , 0 , winreg.REG_SZ , val)   
        winreg.CloseKey(reg_key)

        return True      

    except WindowsError:

        logger_.error("Windows Error occured")
        return False 

    except:
        raise 

def write_reg(drive , icon  = None , label = None):

    global logger


    assert is_admin(), f'Registry can only be edited in admin mode'
    logger.info("User is in admin mode")

    status = status_2 = True

    if icon is not None:
        
        logger.info(f"Setting icon for drive {drive}")
        key = f'{REAL_KEY}\\{drive[0].upper()}\\DefaultIcon'
        status = _write_reg(key , icon)

        if status is True:
            logger.info(f"Icon {icon} successfully set for drive {drive}")

        else:
            logger.error(f'Drive icon setting unsuccessful')

    if label is not None:

        logger.info(f'Setting a default label for drive {drive}')
        key = f'{REAL_KEY}\\{drive[0].upper()}\\DefaultLabel'

        status_2 = _write_reg(key , label)

        if status_2 is True:
            logger.info(f"Label {label} successfully set for drive {drive}")        

        else:
            logger.error(f'Drive label setting unsuccessful')

    return bool(status & status_2)

def read_reg(drive , flags = (True , True)):

    ##Get both keys

    """
    Flags:
        1st one: For Icon
        2nd one: For Label
    """     

    assert isinstance( flags , (list , tuple)), f'Flags should be list or tuple'
    assert len(flags ) == 2 , f'Precisely only two boolean flags are allowed'
    assert isinstance(flags[0] , bool) and isinstance(flags[1] , bool) , f'Both flags should be boolean values'

    r = [True , '' , '']

    if flags == (False , False):
        return r

    

    if flags[0] is True:

        logger.debug("Reading registry for drive icon path")

        key = f'{REAL_KEY}\\{drive[0].upper()}\\DefaultIcon' 
        vals = _read_reg(key)

        if vals[0] is False:
            logger.error("Could not find registry key for drive icon")
            r[1] = None 

        else:
            logger.debug("Successfully obtained drive icon path")
            r[1] = vals[1]

    if flags[1] is True: 

        logger.debug("Reading registry for drive label")

        key = f'{REAL_KEY}\\{drive[0].upper()}\\DefaultLabel' 
        vals = _read_reg(key)

        if vals[0] is False:
            logger.error("Could not find registry key for drive label")
            #r.append(None)
            r[1] = None

        else:
            logger.debug("Successfully obtained drive label")
            #r.append(vals[1])  
            r[1] = vals[1]

    r[0] =  all(map( lambda x : x is not None , r[1:] ))        ##True only if all values are not None
    return tuple(r)

def write_assoc(ext , icon = None):

    pass
    assert is_admin() , f'Registry can only be edited in admin mode'

    s = _write_reg(f"{ext}\\DefaultIcon" , val = icon , base = winreg.HKEY_CLASSES_ROOT)
    
    if s:
        logger.info(f"Succcessfully set default icon {icon} for file extension {ext}")

    else:
        logger.warning(f'Some error occured in setting icon')

    return s

read_assoc = lambda ext , icon = None : _read_reg(key = f"{ext}\\DefaultIcon" , base = winreg.HKEY_CLASSES_ROOT)