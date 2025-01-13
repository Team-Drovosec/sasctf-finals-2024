#!/usr/bin/python3
import random
import pb_pb2
import socket
import hashlib
import math
import sys
import checklib

socket.setdefaulttimeout(1)



def generate_random_string(length):
    a =  ""
    for i in range(length):
        a = a + chr(random.randint(ord('a'), ord('z')))
    return a

def recv_all(sock, msg_len):
    arr = b''
    while len(arr) < msg_len:
        arr += sock.recv(65536)
    return arr
def send_all(sock, msg, msg_len):
    sent_data_len = 0
    while sent_data_len < msg_len:
        sent_data_len += sock.send(msg[sent_data_len:])
    return
def authenticate_as_account(server_socket, account):
    #print('Authenticating as ', account.nickname)
    k = random.randint(0, int(account.q))
    #print('generated k', k)
    sigma = pow(int(account.gamma), k, int(account.group_n))
    #print('generated sigma', sigma)
    login_msg1_req = pb_pb2.LoginChallengeMsg1Request()
    login_msg1_req.nickname = account.nickname
    login_msg1_req.sigma = str(sigma)
    serialized_login_msg1 = login_msg1_req.SerializeToString()
    command = pb_pb2.Command()
    command.commandID = 1
    command.commandType = 0
    command.commandValue = serialized_login_msg1
    to_send = command.SerializeToString()
    try:
        to_send_len = len(to_send)
        to_send_len_bytes = to_send_len.to_bytes(4, 'little')
        server_socket.send(to_send_len_bytes)
        send_all(server_socket, to_send, to_send_len)
        x = server_socket.recv(4)
        num_bytes_to_read = int.from_bytes(x, 'little')
        x = recv_all(server_socket, num_bytes_to_read)
        recv_command = pb_pb2.Command()
        recv_command.ParseFromString(x)        
        login_msg1_resp = pb_pb2.LoginChallengeMsg1Response()
        login_msg1_resp.ParseFromString(recv_command.commandValue)
    except:
    	print('Failed to parse auth response 1 from server')
    	sys.exit(103)
    e = int(login_msg1_resp.e)
    
    x = k - int(account.a) * e
    s = x % int(account.q)
    l = (x - s) // int(account.q)
    lamb = pow(int(account.gamma), l, int(account.group_n))
    
    login_msg2_req = pb_pb2.LoginChallengeMsg2Request()
    login_msg2_req.s = str(s)
    login_msg2_req.lamb = str(lamb)
    serialized_login_msg2 = login_msg2_req.SerializeToString()
    command = pb_pb2.Command()
    command.commandID = 2
    command.commandType = 0
    command.commandValue = serialized_login_msg2
    to_send = command.SerializeToString()
    try:
        to_send_len = len(to_send)
        to_send_len_bytes = to_send_len.to_bytes(4, 'little')
        server_socket.send(to_send_len_bytes)
        send_all(server_socket, to_send, to_send_len)
        x = server_socket.recv(4)
        num_bytes_to_read = int.from_bytes(x, 'little')
        x = recv_all(server_socket, num_bytes_to_read)
    
        recv_command = pb_pb2.Command()
        recv_command.ParseFromString(x)
        
        login_msg2_resp = pb_pb2.LoginChallengeMsg2Response()
        login_msg2_resp.ParseFromString(recv_command.commandValue)
        
    except:
    	print('Failed to parse auth response 2 from server')
    	sys.exit(103)
    if login_msg2_resp.nickname != account.nickname:
        print('Authentication failed')
        sys.exit(103)


def check(ip):
    registered_accounts = []
    available_beers = []
    beer_put_account = 0
    connection_success = False
    server_socket = socket.socket()
    for i in range(3):
        try:
            server_socket.connect((ip, 3000))
            connection_success = True
        except:
            pass
    if (connection_success == False):
        sys.exit(104)
        
    num_of_accounts_to_register = random.randint(2, 4)
    
    for i in range(num_of_accounts_to_register):
        reg_request = pb_pb2.RegisterRequest()
        reg_request.nickname = generate_random_string(2000)
        # print(reg_request)
        serialized_reg_request = reg_request.SerializeToString()
        
        command = pb_pb2.Command()
        command.commandID = 0
        command.commandType = 0
        command.commandValue = serialized_reg_request
        to_send = command.SerializeToString()
        try:
            to_send_len = len(to_send)
            to_send_len_bytes = to_send_len.to_bytes(4, 'little')
            server_socket.send(to_send_len_bytes)
            send_all(server_socket, to_send, to_send_len)
            x = server_socket.recv(4)
            num_bytes_to_read = int.from_bytes(x, 'little')
            x = recv_all(server_socket, num_bytes_to_read)
            recv_command = pb_pb2.Command()
            recv_command.ParseFromString(x)
            reg_result = pb_pb2.RegisterResponse()
            reg_result.ParseFromString(recv_command.commandValue)
            # print(reg_result)
            #sys.exit(0)
        except Exception as e:
            print(e)
            print('Failed to register account')
            sys.exit(103)
        registered_accounts.append(reg_result)
    
    account_idx_1 = random.randint(0, num_of_accounts_to_register - 1) # Index for creating beers
    
    account_idx_2 = account_idx_1 # Index for writing reviews
    while account_idx_2 == account_idx_1:
        account_idx_2 = random.randint(0, len(registered_accounts) - 1)
          
    authenticate_as_account(server_socket, registered_accounts[account_idx_1])
    
    num_beers_to_create = random.randint(1, 2)
    beers = []
    for i in range(num_beers_to_create):
        beer_request = pb_pb2.AddBeerRequest()
        beer_request.beer_name = generate_random_string(1000)
        serialized_beer_request = beer_request.SerializeToString()
        command = pb_pb2.Command()
        command.commandID = 6
        command.commandType = 0
        command.commandValue = serialized_beer_request
        to_send = command.SerializeToString()
        try:
            to_send_len = len(to_send)
            to_send_len_bytes = to_send_len.to_bytes(4, 'little')
            server_socket.send(to_send_len_bytes)
            send_all(server_socket, to_send, to_send_len)
            x = server_socket.recv(4)
            num_bytes_to_read = int.from_bytes(x, 'little')
            x = recv_all(server_socket, num_bytes_to_read)
            recv_command = pb_pb2.Command()
            recv_command.ParseFromString(x)
            login_msg2_resp = pb_pb2.AddBeerResponse()
            login_msg2_resp.ParseFromString(recv_command.commandValue)
        except:
       		print('Failed to create beer')
       		sys.exit(103)
        if login_msg2_resp.beer_id <= 0:
        	print('Failed to create beer')
        	sys.exit(103)
        beers.append(login_msg2_resp.beer_id)
    authenticate_as_account(server_socket, registered_accounts[account_idx_2])
    comments_to_check = []
    for beer_id in beers:
        num_comments_to_add = random.randint(2, 4)
        for i in range(num_comments_to_add):
            add_comment_req = pb_pb2.AddCommentRequest()
            add_comment_req.beer_id = beer_id
            add_comment_req.comment = generate_random_string(16)
            #print('Adding comment', add_comment_req.comment)
            add_comment_req.private_key = registered_accounts[account_idx_2].a
            add_comment_req.is_private = False
            serialized_comment_request = add_comment_req.SerializeToString()
            
            command.commandID = 7
            command.commandType = 0
            command.commandValue = serialized_comment_request
            to_send = command.SerializeToString()
            try:
                to_send_len = len(to_send)
                to_send_len_bytes = to_send_len.to_bytes(4, 'little')
                server_socket.send(to_send_len_bytes)
                send_all(server_socket, to_send, to_send_len)
                x = server_socket.recv(4)
                num_bytes_to_read = int.from_bytes(x, 'little')
                x = recv_all(server_socket, num_bytes_to_read)
                #print(x)
                recv_command = pb_pb2.Command()
                recv_command.ParseFromString(x)
                add_comment_resp = pb_pb2.AddCommentResponse()
                add_comment_resp.ParseFromString(recv_command.commandValue)
            except:
            	print('Failed to add comment')
            	sys.exit(103)

            #print(add_comment_resp)
            comments_to_check.append((beer_id, add_comment_resp.comment_id))
    
    for value_to_check in comments_to_check:
        beer_id = value_to_check[0]
        for i in range(1, 101):
            list_comments_request = pb_pb2.ListCommentsRequest()
            list_comments_request.beer_id = beer_id
            list_comments_request.page = i
            serialized_list_comments_request = list_comments_request.SerializeToString()
            command =  pb_pb2.Command()
            command.commandID = 9
            command.commandType = 0
            command.commandValue = serialized_list_comments_request
            to_send = command.SerializeToString()
            try:
                to_send_len = len(to_send)
                to_send_len_bytes = to_send_len.to_bytes(4, 'little')
                server_socket.send(to_send_len_bytes)
                send_all(server_socket, to_send, to_send_len)
                x = server_socket.recv(4)
                num_bytes_to_read = int.from_bytes(x, 'little')
                x = recv_all(server_socket, num_bytes_to_read)
                recv_command = pb_pb2.Command()
                recv_command.ParseFromString(x)
            except:
                sys.exit(103) 
            comments_list = pb_pb2.ListCommentsResponse()
            comments_list.ParseFromString(recv_command.commandValue) 
            for comment in comments_list.comments:
                if comment.comment_id == value_to_check[1]:
                    break
            if comment.comment_id == value_to_check[1]:
                break
        if comment.comment_id != value_to_check[1]:
        	print('Failed to find previously created comment')
        	sys.exit(103)
        comment_sigma = int(comment.sigma)
        comment_sigma_bytes = comment_sigma.to_bytes(math.ceil(comment_sigma.bit_length() / 8), 'big')
        comment_sigma_bytes += b'\x00' * (8192 - len(comment_sigma_bytes))
        
        e_ff = hashlib.sha1(comment.comment_value.encode() + comment_sigma_bytes).digest()
        e_num = int.from_bytes(e_ff, 'big')
        # print('e', e_num)
        x = pow(int(registered_accounts[account_idx_2].gamma), int(comment.s), int(registered_accounts[account_idx_2].group_n))
        # print(x)
        x *= pow(int(registered_accounts[account_idx_2].alpha), e_num, int(registered_accounts[account_idx_2].group_n))
        x %= int(registered_accounts[account_idx_2].group_n)
        # print(pow(int(registered_accounts[account_idx_2].alpha), e_num, int(registered_accounts[account_idx_2].group_n)))
        x *= pow(int(comment.lamb), int(registered_accounts[account_idx_2].q), int(registered_accounts[account_idx_2].group_n))
        # print(pow(int(comment.lamb), int(registered_accounts[account_idx_2].q), int(registered_accounts[account_idx_2].group_n)))
        x %= int(registered_accounts[account_idx_2].group_n)
        # print('lam', int(comment.lamb))
        if x != comment_sigma:
        	print('Wrong digital signature')
        	sys.exit(103)
    server_socket.close()
    return
        
def put(ip, flag):
    connection_success = False
    server_socket = socket.socket()
    for i in range(3):
        try:
            server_socket.connect((ip, 3000))
            connection_success = True
        except:
            pass
    if (connection_success == False):
        sys.exit(104)
        
    reg_request = pb_pb2.RegisterRequest()
    reg_request.nickname = generate_random_string(16)
    serialized_reg_request = reg_request.SerializeToString() 
    command = pb_pb2.Command()
    command.commandID = 0
    command.commandType = 0
    command.commandValue = serialized_reg_request
    to_send = command.SerializeToString()
    try:
        #byt
        to_send_len = len(to_send)
        to_send_len_bytes = to_send_len.to_bytes(4, 'little')
        server_socket.send(to_send_len_bytes)
        send_all(server_socket, to_send, to_send_len)
        x = server_socket.recv(4)
        num_bytes_to_read = int.from_bytes(x, 'little')
        x = recv_all(server_socket, num_bytes_to_read)
        recv_command = pb_pb2.Command()
        recv_command.ParseFromString(x)
        reg_result = pb_pb2.RegisterResponse()
        reg_result.ParseFromString(recv_command.commandValue)
    except Exception as e:
        print('Failed to register account')
        sys.exit(103)
    authenticate_as_account(server_socket, reg_result)
    beer_request = pb_pb2.AddBeerRequest()
    beer_request.beer_name = generate_random_string(16)
    serialized_beer_request = beer_request.SerializeToString()
    command = pb_pb2.Command()
    command.commandID = 6
    command.commandType = 0
    command.commandValue = serialized_beer_request
    to_send = command.SerializeToString()
    try:
        to_send_len = len(to_send)
        to_send_len_bytes = to_send_len.to_bytes(4, 'little')
        server_socket.send(to_send_len_bytes)
        send_all(server_socket, to_send, to_send_len)
        x = server_socket.recv(4)
        num_bytes_to_read = int.from_bytes(x, 'little')
        x = recv_all(server_socket, num_bytes_to_read)
        recv_command = pb_pb2.Command()
        recv_command.ParseFromString(x)
        login_msg2_resp = pb_pb2.AddBeerResponse()
        login_msg2_resp.ParseFromString(recv_command.commandValue) 
    except Exception as e:
        print('Failed to add beer')
        sys.exit(103)
       
    out_beer_id = login_msg2_resp.beer_id
    
    for i in range(random.randint(20, 25)):
        add_comment_req = pb_pb2.AddCommentRequest()
        add_comment_req.beer_id = out_beer_id
        add_comment_req.comment = generate_random_string(random.randint(16, 20))
        #print('Adding comment', add_comment_req.comment)
        add_comment_req.private_key = reg_result.a
        add_comment_req.is_private = False
        serialized_comment_request = add_comment_req.SerializeToString()
        
        command.commandID = 7
        command.commandType = 0
        command.commandValue = serialized_comment_request
        to_send = command.SerializeToString()
        try:
            to_send_len = len(to_send)
            to_send_len_bytes = to_send_len.to_bytes(4, 'little')
            server_socket.send(to_send_len_bytes)
            send_all(server_socket, to_send, to_send_len)
            x = server_socket.recv(4)
            num_bytes_to_read = int.from_bytes(x, 'little')
            x = recv_all(server_socket, num_bytes_to_read)
            #print(x)
            recv_command = pb_pb2.Command()
            recv_command.ParseFromString(x)
            add_comment_resp = pb_pb2.AddCommentResponse()
            add_comment_resp.ParseFromString(recv_command.commandValue)
        except Exception as e:
            print('Failed to add comment')
            sys.exit(103)  
    add_comment_req = pb_pb2.AddCommentRequest()
    add_comment_req.beer_id = out_beer_id
    add_comment_req.comment = flag
    #print('Adding comment', add_comment_req.comment)
    add_comment_req.private_key = reg_result.a
    add_comment_req.is_private = True
    serialized_comment_request = add_comment_req.SerializeToString()
    
    command.commandID = 7
    command.commandType = 0
    command.commandValue = serialized_comment_request
    to_send = command.SerializeToString()
    try:
        to_send_len = len(to_send)
        to_send_len_bytes = to_send_len.to_bytes(4, 'little')
        server_socket.send(to_send_len_bytes)
        send_all(server_socket, to_send, to_send_len)
        x = server_socket.recv(4)
        num_bytes_to_read = int.from_bytes(x, 'little')
        x = recv_all(server_socket, num_bytes_to_read)
        #print(x)
        recv_command = pb_pb2.Command()
        recv_command.ParseFromString(x)
        add_comment_resp = pb_pb2.AddCommentResponse()
        add_comment_resp.ParseFromString(recv_command.commandValue)
    except Exception as e:
        print('Failed to add comment')
        sys.exit(103)       
    server_socket.close()
    return reg_request.nickname, reg_result.a, add_comment_req.beer_id, add_comment_resp.comment_id
    
def get(ip, flag_data, flag_value):
    connection_success = False
    server_socket = socket.socket()
    for i in range(3):
        try:
            server_socket.connect((ip, 3000))
            connection_success = True
        except:
            pass
    if connection_success == False:
        sys.exit(104)
    
    flag_value_split = flag_value.split(";")
    username = flag_value_split[0]
    beer_id = flag_value_split[2]
    priv_key = flag_value_split[1]
    comment_id = int(flag_value_split[3])
    
    reg_request = pb_pb2.GetUserDetailsRequest()
    reg_request.nickname = username
    reg_request.page = 1
    serialized_reg_request = reg_request.SerializeToString() 
    command = pb_pb2.Command()
    command.commandID = 15
    command.commandType = 0
    command.commandValue = serialized_reg_request
    to_send = command.SerializeToString()
    
    try:
        to_send_len = len(to_send)
        to_send_len_bytes = to_send_len.to_bytes(4, 'little')
        server_socket.send(to_send_len_bytes)
        send_all(server_socket, to_send, to_send_len)
        x = server_socket.recv(4)
        num_bytes_to_read = int.from_bytes(x, 'little')
        x = recv_all(server_socket, num_bytes_to_read)
        #print(x)
        recv_command = pb_pb2.Command()
        recv_command.ParseFromString(x)        
        user_details_response = pb_pb2.GetUserDetailsResponse()
        user_details_response.ParseFromString(recv_command.commandValue)    
    except Exception as e:
        print('Failed to get user details')
        sys.exit(103)
    registered_account = pb_pb2.RegisterResponse()
    registered_account.group_n = user_details_response.group_n
    registered_account.gamma = user_details_response.gamma
    registered_account.q = user_details_response.q
    registered_account.alpha = user_details_response.alpha
    registered_account.nickname = username
    registered_account.a = priv_key
    #print('fuck', registered_account)
    authenticate_as_account(server_socket, registered_account)
    #print(user_details_response)
       
    for i in range(1, 101):
        list_comments_request = pb_pb2.ListCommentsRequest()
        #print(beer_id)
        #print(i)
        list_comments_request.beer_id = int(beer_id)
        list_comments_request.page = i
        serialized_list_comments_request = list_comments_request.SerializeToString()
        command = pb_pb2.Command()
        command.commandID = 9
        command.commandType = 0
        command.commandValue = serialized_list_comments_request
        to_send = command.SerializeToString()
        try:
            to_send_len = len(to_send)
            to_send_len_bytes = to_send_len.to_bytes(4, 'little')
            server_socket.send(to_send_len_bytes)
            send_all(server_socket, to_send, to_send_len)
            x = server_socket.recv(4)
            num_bytes_to_read = int.from_bytes(x, 'little')
            x = recv_all(server_socket, num_bytes_to_read)
            recv_command = pb_pb2.Command()
            recv_command.ParseFromString(x)
        except Exception as e:
            print('Failed to read comment list')
            sys.exit(103)

        comments_list = pb_pb2.ListCommentsResponse()
        comments_list.ParseFromString(recv_command.commandValue)
        #print(comments_list) 
        for comment in comments_list.comments:  
            if comment.comment_id == comment_id and comment.comment_value == flag_data:
                return

    sys.exit(102)       
    
if sys.argv[1] == "check":
    check(sys.argv[2])
    sys.exit(101)
    
if sys.argv[1] == "put":
    #print('put')
    username, private_key, beer_id, comment_id = put(sys.argv[2], sys.argv[4])
    print(f'{username};{private_key};{beer_id};{comment_id}', file=sys.stderr)
    print(f'{username};{beer_id};{comment_id}')
    sys.exit(101)
    
    
if sys.argv[1] == "get":
    get(sys.argv[2], sys.argv[4], sys.argv[3])
    sys.exit(101)


