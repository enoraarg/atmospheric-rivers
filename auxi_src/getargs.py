#!/usr/bin/python

import argparse

def str2bool(v):
    if type(v) == list :
        v = v[0]
    try :
        if isinstance(v, bool) :
            return v
        if v.lower() in ('yes', 'true', 't', 'y', '1') :
            return True
        elif v.lower() in ('no', 'false', 'f', 'n', '0') :
            return False
        else :
            return v
    except :
        return v

def getboolargs(pars) :
    for key in pars :
        #print(key,pars[key],type(pars[key]),str2bool(pars[key]))
        pars[key] = str2bool(pars[key])
    return pars # not necesseray as it modifies pars _in place_, but useful to apply directly within getargs

def getargs(defaultpars):
    parser = argparse.ArgumentParser(description='Dynamic arguments')
    namespace = argparse.Namespace(**defaultpars)
    # Add each key of the default dictionary as an argument
    # Expecting the same type
    for key, val in defaultpars.items():
        try:
            typ = type(val[0])
            nargs = "+"
        except TypeError:
            typ = type(val)
            nargs = None
        parser.add_argument('--'+key, nargs=nargs, type=typ)
        #parser.add_argument('--'+key, type=type(val))
    parser.parse_args(namespace=namespace)
    return getboolargs(vars(namespace))
