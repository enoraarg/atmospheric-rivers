'''
Module to dump and load python objects with pickle.
author : @enoraarg
'''
try :
    import cPickle as pickle
except ModuleNotFoundError :
    try :
        import pickle
    except ModuleNotFoundError :
        import os
        os.system('pip install pickle')
        import pickle
        print('pickle ok :)')
    except :
        print('sry no pickle available, hopefully dill is there to help you')

try :
    import dill
except ModuleNotFoundError :
    import os
    os.system('pip install dill')
    try :
        import dill
    except ModuleNotFoundError :
        try :
            print('trying dill with path......')
            from sys import path
            path.append('/home/m/m301048/.local/lib/python3.10/site-packages/')
            import dill
            print('dill ok yayy')
        except :
            #raise Warning('dill not found ?? try with pickle ??')
            print('dill not found ?? try with pickle ??')

def save_object_pickle(obj,outfile) :
    '''
    obj : python object to save.
    outfile (str) : Path to output file. extension must be `.pkl`
    '''
    pickle.dump(obj,outfile,pickle.HIGHEST_PROTOCOL)

def open_object_pickle(objfile) :
    '''
    objfile (str) : path to file, with extension `.pkl`
    '''
    with open(objfile, 'rb') as file :
        obj = pickle.load(file)
    return obj

def save_object(obj,outfile) :
    '''
    obj : python object to save.
    outfile (str) : Path to output file. extension must be `.pkl`
    '''
    #if outfile[-4:] != '.pkl' :
        #raise Exception('The output file is not .pkl
    with open(outfile, 'wb') as f:
        dill.dump(obj, f)
        
def open_object(objfile) :
    '''
    objfile (str) : path to file, with extension `.pkl`
    '''
    with open(objfile, 'rb') as file :
        obj = dill.load(file)
    return obj