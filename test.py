"""
We import the mlpux module here, as well as the module we want to inspect.

"""
import mlpux 

from a_test_module import test_module
import time

from formencode.variabledecode import variable_decode
from formencode.variabledecode import variable_encode

import requests

import discovery

# @mlpux.Demo()
# def square(x):
    # return x*x

def run_tests():
    # Check what happens when functions are run (the decorator is processed)
    print(80*'=')
    print("Test 1: a module with no arguments")
    ret_val = test_module.no_args()

    print(80*'=')
    print("Test 2: a module with float arguments")
    ret_val = test_module.square(10.)
    print(ret_val)

    print(80*'=')
    print("Test 3: a module with two arguments that are string and int")
    ret_val = test_module.str_args(mystr="Jillywanker",myint=147)
    print(ret_val)

    print(80*'=')
    print("Test 4: a module with arguments that do not specifiy type, and returns a python dict object")
    ret_val = test_module.args_notype(1, 2, "Mr. Dingleberry")
    print(ret_val)

    print(80*'=')
    print("Test 5: a module with arguments that do not specifiy type, and returns json str")
    ret_val = test_module.args_notype_clone(1, 2, "Mrs. Dingleberry")
    print(ret_val)

    print(80*'=')
    print("Test 6: args and kwargs in functions")
    ret_val = test_module.arbitrary_func(1,2,3,27,cat="hat",zoo="blue")
    print(ret_val)
    
    print(80*'=')
    print("Test 7: a particularly complex signature")
    ret_val = test_module.hard_func(
            1,2,3,
            arg1="dude", 
            arg2="whereis", 
            default1="mycar", 
            default2=20,
            extra='hi', 
            extra2='blowme'
    )
    print(ret_val)

def run_network_tests():
    print(80*'+')
    print("RUNNING NETWORK TESTS")

    print(80*"=")
    # Now run tests with network requests
    r = requests.get('http://0.0.0.0:52758/execute/square',{'x':10})
    print('SENT:',r.url)
    print('RESPONSE:', r.text)
    
    r = requests.get('http://0.0.0.0:52758/execute/square',{'args':'[10]'})
    print('SENT:',r.url)
    print('RESPONSE:', r.text)


if __name__ == '__main__':
    run_tests()
    #run_network_tests()
