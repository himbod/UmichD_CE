import socket
import time
import numpy as np
import struct
import cv2


N = 1024
cnt = 0
rData = []
Nout = 1
result = ""
resList = []

#Convert message to bit list
def msg2bt(msg):
    bt = []
    for i in range(len(msg)):
        for b in msg[i]:
            bt.append(int(b))
    return bt

#Convert bit list to msg
def bt2msg(bt):
    msg = ""
    for i in range(len(bt)):
        msg = msg + str(bt[i])
    return msg

#Convert binary byte to int
def bt2int(bt):
    w = 2 ** np.array(range(8))[::-1] #constant [1, 2, 4, 
    return np.dot(bt, w)
"""
#Convert int to binary bytes
def int2bt(num):
    bt = []
    if(num>128):
        bt.append[1]
        num = num-128
    else:
        bt.append[0]
    if(num>64):
        bt.append[1]
        num = num-64
    else:
        bt.append[0]
    if(num>128):
        bt.append[1]
        num = num-128
    else:
        bt.append[0]
"""    

#Find remainder of binary data / divisor
def divCRC(data, divisor):
    #print("#Pull first digits of data based on divisor length")
    
    #print("data: ", data, "divisor: ", divisor)
    
    newResults = []
    for i in range(len(divisor)):
        newResults.append(data[i])
    cnt = len(divisor) #Digit reached in divison
    running = True
    
    #print("#Division to find checksum/reminder")
    while(running):
        results = newResults
        newResults = []
        mark = False
        crc = []

        #print("#XOR last result with divisor for new result")    
        for i in range(len(divisor)):
            match = results[i] == divisor[i]
            if(results[i] != divisor[i]):
                newResults.append(1)
            elif(len(newResults)>0):
                newResults.append(0)

        #print("#Find what data is left to be used")
        leftover = []
        for i in range(cnt, len(data)):
            leftover.append(data[i])

        #print("#Fill result with leftover data until same length as divisor, if out of data end")
        for i in range(len(divisor)):
            if(len(newResults) < len(divisor)):
                if(len(leftover)<=i):
                    crc = (4*[0] + newResults)[-4:]
                    return(crc)
                newResults.append(leftover[i])
                cnt = cnt + 1
        #print(newResults)

#Get CRC code
def getCRC(data, divisor):
    
    #Fill data with zeros based on divisor length - 1
    for i in range(len(divisor)-1):
        data.append(0)
    
    res = (divCRC(data,divisor))
    
    return(res)

#Check CRC code
def checkCRC(frame, divisor):
    #data = frame[16:]
    
    #data = [1, 0, 1, 1, 0, 0, 1, 1, 0, 1, 0, 0]
    #divisor = [1, 1, 0, 0, 1]
    
    checkSum = divCRC(frame,divisor)
    if(checkSum == [0, 0, 0, 0]):
        return(0)
    else:
        return(1)

#Set up socket
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server_address = ('23.235.207.63', 9993) #change ports from 9990-9999
"""
#Read JPEG file 
with open('cats.jpg','rb') as f: #open jpeg in binary format
    buff = f.read()
f.close()
msg = ['{:08b}'.format(b) for b in buff] #buff to binary string
bt = msg2bt(msg) #binary to binary list
"""
#Read JPEG file 
ogImage = cv2.imread('cats.jpg')
shape = ogImage.shape
ogImage = ogImage.reshape(-1)
ogImage = list(ogImage)
msg = ['{:08b}'.format(b) for b in ogImage] #buff to binary string
bt = msg2bt(msg) #binary to binary list

print(ogImage, "Max: ", max(ogImage), "Min: ", min(ogImage))
print(bt)

Nf = int(np.ceil(len(bt)/N)) #Number of frames
print("frame #:", Nf)

sock.settimeout(0.1)
while True:
    #Set up packet
    frame = list([0, 1, 1, 1, 1, 1, 1, 0]) #Header
    cntArr = [int(b) for b in '{:08b}'.format(cnt%255)] #Frame counter
    frame += cntArr
    txData = bt[1024 * cnt:1024 * (cnt + 1)] #1024 bit data slice
    frame += txData
    crc = getCRC(frame, [1, 1, 0, 0, 1]) #Calculate CRC
    frame = frame[:-4]
    frame += crc
    frame += [0, 0, 0, 0]
    frame = np.array(frame).reshape(int(len(frame)/8), 8) #binary list -> list of bytes
    packet = [bt2int(b) for b in frame]
    
    #Send packet to server
    sent = sock.sendto(bytes(packet), server_address)
    #Recieve bounced back packet
    try:
        dataRecv, server = sock.recvfrom(2048)
    except socket.timeout:
        Nout += 1
    
    #print("#Convert recieved data into bit list")
    rev = ['{:08b}'.format(b) for b in dataRecv]#[:-1]
    rev = msg2bt(rev)
    
    #print("#Perform CRC check and resend if error (ARQ)")
    rev = rev[:-4]
    check = checkCRC(rev, [1, 1, 0, 0, 1])
    if(check == 0):
        rev = rev [16:-4]
        result = result + bt2msg(rev)
        resList += rev
        cnt = cnt + 1
    else:
        print("CRC ERROR Frame: ", cnt)
    
    if cnt == Nf:
        print('Done')
        break
    
    
    bytStr = ""
    txt = ""
    #for i in range(int(len(resList)/8)):
    #    for j in range(32):
     #       txt = txt + str(resList[(i*8) + j])
     #   bytStr = bytStr + bt2int(txt)

out = ""
resList = np.array(resList).reshape(int(len(resList)/8), 8) #binary list -> list of bytes
bytList = [bt2int(b) for b in resList]
bytList = np.array(bytList)
bytList = bytList.reshape(shape)
cv2.imwrite('1.jpg', bytList)
"""
for i in range(len(bytList)):
    out = out + str(bytList[i])
        
    
with open('1.jpg', 'wb') as f:
    #f.write(bytes(result, 'utf-8'))
    #for j in range(len(list32)):
    #    f.write(struct.pack('i', int(list32[j][::-1], 2)))
    f.write(out.encode())
f.close()
"""
    
    