"""
COSC264 Assignment - Socket - TCP 2023
Author : Joshua Kim
Student ID : 68493559
"""

""" Client """


import socket
import sys
import struct

class MessageRequest(object):
    """Create an instance of a MessageRequest packet"""
    
    def __init__(self, type_request, username, receivername="", message=""):
        """initialize"""
        self.magic_num = 0xAE73
        self.id = type_request
        self.username = username
        self.username_len = len(username)
        self.receivername = receivername
        self.receiv_len = 0     
        self.message = message   
        self.mssg_len = 0
    
    def create_fixed_header(self):
        """create first seven bytes of the record"""
        return struct.pack(">HBBBH", self.magic_num, self.id, self.username_len, self.receiv_len, self.mssg_len)
     
    def encode(self):
        """encode with the message from the user"""
        self.mssg_len = len(self.message)
        self.receiv_len = len(self.receivername)                    
        name_receiver_mssg = self.username + self.receivername + self.message
        return bytearray(self.create_fixed_header()) + bytearray(name_receiver_mssg.encode("UTF-8"))
            
            
def checking_fixed_header(magic_num, id_num):
    """check the validity of the fixed header of the response from server"""
    result = True
    if (magic_num != 0xAE73) :
        print("ERROR: The first header value, Magic Number, from client is not matching.")
        result = False
    elif (id_num != 3):
        print("ERROR: The second header value, ID, from client is not matching.")
        result = False
    return result    


def reading_message(num_items, more_mssgs, response_from_server):
    """unpack and decode the message from the server"""
    if num_items == 0:
        final_message = "******** There is no message to read ********"
    else:
        final_message = ""
        count = 1
        try:
            while num_items > 0: 
                sender_len, mssg_len = struct.unpack(">BH", response_from_server[:3])
                sender = response_from_server[3:(sender_len+3)].decode("UTF-8") 
                message = response_from_server[(3+sender_len):(3+sender_len+mssg_len)].decode("UTF-8") 
                final_message += "{}. Sender : {}    Message : {}\n".format(count, sender, message)
                count += 1
                num_items -= 1
                if num_items != 0:
                    response_from_server = response_from_server[(3+sender_len+mssg_len):]
            dot_line = ("-" *55)+"\n"
            final_message = dot_line + final_message + dot_line
            ## if more_mssgs field is 1, have to print out and notify that there is more message in the server
            if more_mssgs == 1:
                star_line = ("*" *55)+"\n"
                final_message += (star_line + "**** There are more messages to read in the server ****\n" + star_line)
        except UnicodeDecodeError:
            print("ERROR : Response decoding failure")        
    return final_message
    
def enter_message_receiver():
    """ask user to enter message and the name of receiver to send when the type of request is "Create" """
    mssg_flag = False
    rcvr_flag = False
    while not mssg_flag or not rcvr_flag:
        if not mssg_flag:
            message = input("Please enter a message to send: ")
            if (1 > len(message) or len(message) >= 65535):
                continue        
            else:
                mssg_flag = True
        if not rcvr_flag:
            receiver = input("Please enter the name of the receiver: ")
            if (1 > len(receiver) or len(receiver) >= 255):
                continue
            else:
                rcvr_flag = True            
    return message, receiver
    
def creating_socket(server_IP, port_num):
    """Create socket for client"""
    try:
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.settimeout(1)  ##if next step takes longer than 1sec, network error will be assumed and raise error
        server_socket.connect((server_IP, port_num))
    except OSError as err:
        print(f"ERROR : {err}")  
        server_socket.close()
        sys.exit()
    except TimeoutError:
        print("TimeoutError : Processing time has exceeded over setTime, try again")
        server_socket.close()
        sys.exit()
    return server_socket    

def sending_request(server_IP, port_num, type_request, username):
    """user decides either to read or create a request and send it to server"""
    try:
        ## When user chooses "Create"
        if type_request == 2: 
            ## ask user to enter additional information for message and receiver to create
            message, receiver = enter_message_receiver()  
            server_socket = creating_socket(server_IP, port_num)
            mssg_request = MessageRequest(type_request, username, receiver, message)
            encoded_message = mssg_request.encode()
            amount = server_socket.send(encoded_message)
            if amount < len(encoded_message):
                raise OSError("Unable to send whole message")
            running = False
        ## When user chooses "Read"
        elif type_request == 1: 
            mssg_request = MessageRequest(type_request, username)
            server_socket = creating_socket(server_IP, port_num)
            encoded_message = mssg_request.encode()
            amount = server_socket.send(encoded_message)
            if amount < len(encoded_message):
                raise OSError("Unable to send whole message")                
            
            response_from_server = server_socket.recv(1024)
            magic_num, id_num, num_items, more_mssgs = struct.unpack(">HBBB", response_from_server[:5])
            
            if not checking_fixed_header(magic_num, id_num):
                server_socket.close()
                exit()
            message = reading_message(num_items, more_mssgs, response_from_server[5:])
            print(message)
            
            server_socket.close()
            exit()
                     
    except OSError as err:
        print(f"ERROR : {err}")
    except socket.gaierror as err:
        print(f"ERROR : {err}")        
    except TimeoutError as err:
        print(f"TimeoutError : {err}")
    except UnicodeDecodeError as err:
        print(f"ERROR : {err}")

    finally:
        if server_socket != None:
            server_socket.close()
            sys.exit()

def accept_parameters():
    """accept 4 parameters from user to start"""
    if len(sys.argv) != 5:
        print("Please enter: python client.py <ip_or_hostname> <port_number> <user_name> <request_type;read || create>")
        sys.exit()  
    ## get the IP number
    try:
        server_IP = socket.getaddrinfo(sys.argv[1], None)[0][4][0]
    except gaierror:
        print(f"ERROR : Host '{sys.argv[1]} does not exist")
    ## check the port number
    port_num = int(sys.argv[2])
    if port_num < 1024 or port_num > 64000:
        print("ERROR : Port Number has to be between 1024 and 64000(inclusive)")    
        sys.exit() 
    ## check length of user name
    username = sys.argv[3]
    if not( 1 <= len(username) <= 255):
        print("ERROR : User Name has to between 1 to 255(inclusive)")
        sys.exit()    
    ##check the type of the request between "read" and "create"
    type_R_C = sys.argv[4]
    if not (type_R_C == "read" or type_R_C == "create"):
        print("ERROR : There is no such a type.")
        sys.exit() 
    if type_R_C == "read":
        type_request = 1
    elif type_R_C == "create":
        type_request = 2
        
    return server_IP, port_num, username, type_request

def main():
    server_IP, port_num, username, type_request = accept_parameters()
    sending_request(server_IP, port_num, type_request, username)
    

    
main()