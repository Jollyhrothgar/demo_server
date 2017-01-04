import socket
import select
import threading as thread
PORT = 4242

def discoverable(service_name=None,port=None):
    '''
    Starts a discovery service using either a unique service name or a
    unique service port. Non-blocking
    '''
    if not port:
        port = PORT
    def wait():
        s = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
        s.bind(('',port))
        s.setblocking(0)
        while True:
            result = select.select([s],[],[])
            m,client = s.recvfrom(1024)
            
            # print(client)

            t = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
            t.sendto("discovery|{}".format(service_name).encode('utf-8'),client)
            t.close()
    t = thread.Thread(target = wait)
    t.start()
    return

def get_ip(service_name=None,port=None,service_found=None):
    '''
    Get the IP of a service on the network based on its unique service name
    or its unique service port. If service_found is specified, the function
    will not block and will call the service_found callback with the specified
    IP. Otherwise, the function  will block and will return the IP of the
    specified service
    '''
    def block(service_name,port):
        if service_name:
            return get_ip_by_service_name(service_name)
        else:
            return get_ip_by_port(port)

    if not service_name and not port:
        print("Error: either service_name or port must be specified in order to discover service")
        return

    if not service_found:
        return block(service_name,port)
    else:
        t = thread.Thread(target = lambda : service_found(block(service_name,port))) 
        t.start()

def get_ip_by_port(port):
    s = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
    s.setsockopt(socket.SOL_SOCKET,socket.SO_BROADCAST,1)
    s.sendto("discovery request".encode('utf-8'),('<broadcast>',port))

    m,server = s.recvfrom(1024)
    return server[0]

def get_ip_by_service_name(service_name):
    s = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
    s.setsockopt(socket.SOL_SOCKET,socket.SO_BROADCAST,1)
    s.sendto("discovery request".encode('utf-8'),('<broadcast>',PORT))

    #Wait until the proper service responds
    while True:
        m,server = s.recvfrom(1024)
        m = m.decode('utf-8')
        if m.split('|')[1] == service_name:
            return server[0]

# print(get_ip(service_name="something"))
# discoverable(service_name="something")
# while True:
    # pass
