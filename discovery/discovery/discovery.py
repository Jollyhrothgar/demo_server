import socket
import select
import threading as thread
import time

PORT = 4242
TIMEOUT = 1
RETRY = 5
DISC_REQUEST = "discovery request"
SERV_REQUEST = "service|{0}"
DISC_RESPONSE = "discovery|{0}"

def select_unused_port():
    """
    Select and return an unused local port as a string.
    """
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(('localhost', 0))
    addr, port = s.getsockname()
    s.close()
    return port

def discoverable(service_name=None,port=None):
    '''
    Starts a discovery service using either a unique service name or a
    unique service port. Non-blocking
    '''
    if not port:
        port = PORT
    services = set([service_name])
    def wait():
        s = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        try:
            s.bind(('',port))
        except OSError:
            print("Existing discovery service found on machine on this port. Delegating service discovery to existing service.")
            s.sendto(SERV_REQUEST.format(service_name).encode('utf-8'),('localhost',port))
            return

        s.setblocking(0)
        print("Service '{}' is now accepting discovery requests".format(service_name if service_name else port))

        while True:
            result = select.select([s],[],[])
            m,client = s.recvfrom(1024)
            m = m.decode('utf-8')
            if m == DISC_REQUEST:
                print("Discovery request recieved from '{}'".format(client[0]))

                for service in services:
                    t = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
                    t.sendto(DISC_RESPONSE.format(service).encode('utf-8'),client)
                    t.close()
            elif m.split("|")[0] == SERV_REQUEST.split("|")[0]:
                service = m.split("|")[1]
                if service in services:
                    print("Duplicate service delegation recieved for service '{}'".format(service))
                else:
                    services.add(service)
                    print("Service delegation recieved for service '{}'".format(service))

    t = thread.Thread(target = wait)
    t.start()
    return

def get_ip(service_name=None,port=None,service_found=None):
    '''
    Get the IP of a service on the network based on its unique service name
    or its unique service port. If service_found is specified, the function
    will not block and will call the service_found callback with the specified
    IP. Otherwise, the function will block and will return the IP of the
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
    retries = 0
    while True:
        s = _send_broadcast(DISC_REQUEST.encode('utf-8'),port)

        message_recieved = select.select([s],[],[],TIMEOUT)
        if message_recieved[0]:
            m,server = s.recvfrom(1024)
            print("Service on port '{}' found at ip {}".format(port,server[0]))
            return server[0]

        print("Broadcast discovery timed out, starting sweep discovery")
        s = _sweep_request(DISC_REQUEST.encode('utf-8'),port)

        while True:
            message_recieved = select.select([s],[],[],TIMEOUT)
            if message_recieved[0]:
                m,server = s.recvfrom(1024)
                if m.decode('utf-8').split("|")[0] == DISC_RESPONSE.split("|")[0]:
                    print("Service on port '{}' found at ip {}".format(port,server[0]))
                    return server[0]
        print("Discovery failed, retrying in {} seconds".format(RETRY*(2**retries)))
        time.sleep(RETRY*(2**retries))
        retries +=1

def get_ip_by_service_name(service_name):
    retries = 0
    while True:
        s = _send_broadcast(DISC_REQUEST.encode('utf-8'),PORT)

        while True:
            message_recieved = select.select([s],[],[],TIMEOUT)
            if message_recieved[0]:
                m,server = s.recvfrom(1024)
                m = m.decode('utf-8')
                if m.split('|')[1] == service_name:
                    print("Service '{}' found at ip {}".format(service_name,server[0]))
                    return server[0]
            else:
                break

        print("Broadcast discovery timed out, starting sweep discovery")
        s = _sweep_request(DISC_REQUEST.encode('utf-8'),PORT)

        while True:
            message_recieved = select.select([s],[],[],TIMEOUT)
            if message_recieved[0]:
                m,server = s.recvfrom(1024)
                m = m.decode('utf-8')
                print("Service '{}' found at ip {}".format(m.split('|')[1],server[0]))
                if m.split('|')[1] == service_name:
                    return server[0]
            else:
                break

        print("Discovery failed, retrying in {} seconds".format(RETRY*(2**retries)))
        time.sleep(RETRY*(2**retries))
        retries += 1

def _send_broadcast(msg,port):
    s = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
    s.setsockopt(socket.SOL_SOCKET,socket.SO_BROADCAST,1)
    s.sendto(msg,('<broadcast>',port))
    return s

def _sweep_request(msg,port):
    s = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    ip = [(s.connect(('8.8.8.8', 53)), s.getsockname()[0], s.close()) for s in [socket.socket(socket.AF_INET, socket.SOCK_DGRAM)]][0][1].split(".")
    print("Searching for services on the {}.{}.X.XXX subnet".format(ip[0],ip[1]))
    for subnet in range(2):
        for dest in range(255):
            ip[2] = str(subnet)
            ip[3] = str(dest+1)
            try:
                s.sendto(msg,('.'.join(ip),port))
            except:
                pass
    return s

if __name__ == "__main__":
    # print(get_ip(port=3498))
    # print(get_ip(service_name="something"))
    # print(get_ip(service_name="something else"))

    # for testing: comment if you want to discover the discovery service
    # discoverable(service_name = "something")
    # discoverable(service_name = "something else")
    # while True:
        # pass
    pass
