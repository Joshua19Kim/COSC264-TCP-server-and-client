"""
COSC264 Assignment - Socket - TCP 2023
Author : Joshua Kim
Student ID : 68493559
"""

""" Server """

import socket
import sys
import struct

class MessageResponse(object):
    """Create an instance of a MessageRequest packet. When the sender from client requests to create, it will keep the massages and sender's name in the server, based on the name of receiver. When the receiver request to read, this server will send collected messages with sender's name."""
    
    def __init__(self, sender=""):
        """initialize"""
        self.sender = sender
        self.collected_message = []
        self.sender_len_list = []
        self.message_len_list = []
        self.magic_num = 0xAE73
        self.id = 0x0003
        self.sending_num_items = 0
        self.num_items = 0
        self.more_mssgs = 0
        
    def add_message(self, message):
        """save the message with sender name in server"""
        self.num_items += 1
        new_message = self.sender + message
        self.collected_message.append(new_message)
        self.sender_len_list.append(len(self.sender))
        self.message_len_list.append(len(message))
        
    def create_fixed_header(self):
        """create first five bytes of the record"""
        return bytearray(struct.pack(">HBBB", self.magic_num, self.id, self.sending_num_items, self.more_mssgs))

    def encode(self):
        self.sending_num_items = self.num_items
        if self.sending_num_items >= 256:
            self.sending_num_items = 255
            self.more_mssgs = 1
        after_header = bytearray()
        for i in range(self.sending_num_items):
            after_header += bytearray(struct.pack(">BH", self.sender_len_list[i], self.message_len_list[i])) + bytearray(self.collected_message[i].encode("UTF-8"))
            self.num_items -= 1
        final_message = self.create_fixed_header() + after_header , self.sending_num_items
        self.collected_message = self.collected_message[self.sending_num_items:]
        self.sender_len_list = self.sender_len_list[self.sending_num_items:]
        self.message_len_list = self.message_len_list[self.sending_num_items:]        
        self.more_mssgs = 0
        return final_message
    
    
def checking_fixed_header(magic_num, id_num, name_len, receiv_len, mssg_len):
    """check the validity of message from client"""
    result = True
    if (magic_num != 0xAE73) :
        raise ValueError("ERROR: The first header value, Magic Number, from client is not matching.")
    elif (id_num != 1 and id_num != 2):
        raise ValueError("ERROR: The second header value, ID, from client is not matching.")
    elif (name_len < 1):
        raise ValueError("ERROR: The third header value, Length of User, is less than 1.")
    elif (id_num == 1):
        if receiv_len != 0 or mssg_len != 0:
            raise ValueError("ERROR: The last two header value from client are not correct.")
    elif (id_num == 2):
        if receiv_len < 1 or mssg_len < 1:
            raise ValueError("ERROR: The last two header value from client are not correct.")
    return result


def reading_message(request_from_client,id_num, name_len, receiv_len, mssg_len):
    """read the message from the client and return with message, sender and receiver as strings"""
    if id_num == 1:
        sender = request_from_client[:(name_len)].decode("UTF-8") 
        return sender ## This person is considered as a receiver after this as requested to read
    
    if id_num == 2:
        message = request_from_client[(name_len+receiv_len):].decode("UTF-8")   
        if (len(message) != mssg_len):
            raise ValueError("ERROR: Length of the received message does not match")
        sender = request_from_client[:(name_len)].decode("UTF-8") 
        receiver = request_from_client[(name_len):(name_len+receiv_len)].decode("UTF-8") 
        return message, sender, receiver


def create_socket(port_number):
    """Create socket for server"""
    try:
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.bind(("0.0.0.0",port_number))
        server_socket.listen(5)
    
    except OSError as err:
        print(f"ERROR : {err}")    
        server_socket.close()
        sys.exit()    
    return server_socket, port_number
    

def receive_respond(server_socket, port_number):
    """Create a socket with given port number, receive a request from the client and also respond to them.
    """
    receiver_dict = dict() ##Store different receivers with their own objest for MessageRequest in dictionary
    while True: 
        try:
            client_socket, client_address = server_socket.accept()
            client_socket.settimeout(1)
            print(f"Incomming connection IP address : {client_address[0]}, Port Number : {client_address[1]}")            
            request_from_client = client_socket.recv(1024) ##receive the request from the client
            
            magic_num, id_num, name_len, receiv_len, mssg_len = struct.unpack(">HBBBH", request_from_client[:7])
            
            ## check the validity of the request
            if not checking_fixed_header(magic_num, id_num, name_len, receiv_len, mssg_len):
                client_socket.close()
                continue
            
            ## When the user wants to read all the message stored in this server
            if id_num == 1: 
                receiver= reading_message(request_from_client[7:],id_num, name_len, receiv_len, mssg_len)
                if receiver not in receiver_dict: ## if receiver name is not stored in server, it means no message.
                    print("Client sent a request to read, but there is no message. Informed to client")
                    no_receiver = MessageResponse()
                    encoded_mssg, num_mssg = no_receiver.encode()
                    client_socket.send(encoded_mssg)
                    client_socket.close()

                else:
                    encoded_mssg, num_mssg = receiver_dict[receiver].encode()
                    print(f"Successfully sent {num_mssg} message(s) to Receiver: {receiver}") 
                    client_socket.send(encoded_mssg)
                    client_socket.close()
            
            ## When the user wants to create message as a sender
            elif id_num == 2: 
                message, sender, receiver = reading_message(request_from_client[7:],id_num, name_len, receiv_len, mssg_len)
                if receiver not in receiver_dict:
                    receiver_packet = MessageResponse(sender)
                    receiver_dict[receiver] = receiver_packet
                
                receiver_dict[receiver].add_message(message)     
                print("-------------Received Message from Client-------------")
                print(f"Sender : {sender}")
                print(f"Receiver : {receiver}")
                print(f"Message : {message}")
                print("-" * 54)
                client_socket.close()
                
        except OSError as err:
            print(f"ERROR : {err}")
            client_socket.close()
            continue
        except socket.gaierror as err:
            print(f"ERROR : {err}")
            client_socket.close()
            continue
        except TimeoutError :
            print("Processing time has exceeded over setTime, try again") 
            client_socket.close()
            continue
        except UnicodeDecodeError:
            print("ERROR : Response decoding failure")  
            client_socket.close()
            continue
        except KeyboardInterrupt:
            print("*** NOTICE : Finished sockets and Exit ***")
            client_socket.close()
            server_socket.close()
            sys.exit()
            
def get_port_number():
    """ask user to enter port number"""
    if len(sys.argv) != 2:
        print("Please enter: python server.py <port number>")
        exit()
    port_num = int(sys.argv[1])    
    if port_num < 1024 or port_num > 64000:
        raise ValueError("Port Number has to be between 1024 and 64000(inclusive)")
    
    return port_num
    
def main():
    server_socket, port_number = create_socket(get_port_number())
    receive_respond(server_socket, port_number)

    
main()