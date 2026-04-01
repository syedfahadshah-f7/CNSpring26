import socket
import threading
import os

s = socket.socket()
s.bind(("localhost", 9999))
s.listen(3)
print("Waiting for client !!!\n")

clients = []


def broadcast(sender, mess):
    for client, addr in clients:
        if client != sender:
            client.send(f"Client {addr} sent: {mess}".encode())


def broadcastFile(sender, content, f):
    for client, addr in clients:
        if client != sender:
            # FIX: send to EACH client, not sender socket
            client.send(f"File: {f}".encode())
            client.sendall(content)
            client.send(b"EOF")

        print(f"File {f} successfully sent to client {addr}.\n")


def handleClient(c, addr):
    c.send("Welcome to the Giga Chat!\n".encode())
    print(f"Client Connected: {addr}\n")

    while True:
        mess = c.recv(2048).decode()

        if not mess:
            break

        if mess.lower() == "exit":
            print(f"Client {addr} exited the chat\n")
            break

        # FILE HANDLING
        if mess.startswith("File: "):
            f = mess.split("File: ")[1]
            fn, ext = f.rsplit(".", 1)

            if ext not in ["pdf", "txt"]:
                c.send("Invalid file type!".encode())
                continue

            opf = f"{fn}Write.{ext}"
            content = b""

            with open(opf, "wb") as file:
                while True:
                    cnt = c.recv(2048)

                    if b"EOF" in cnt:
                        cnt = cnt.replace(b"EOF", b"")
                        file.write(cnt)
                        content += cnt
                        break

                    file.write(cnt)
                    content += cnt

            broadcastFile(c, content, f)
            print(f"File {f} received from {addr}\n")

        # TEXT MESSAGE HANDLING
        else:
            flag = True

            # FIX: inappropriate check must be on mess, not binary
            for i in ["fuck", "bitch"]:
                if i in mess.lower():
                    c.send("Inappropriate text detected!!".encode())
                    flag = False
                    break

            if flag:
                print(f"Client {addr} Sent: {mess}")
                broadcast(c, mess)

    clients.remove((c, addr))
    c.close()


while True:
    c, addr = s.accept()
    clients.append((c, addr))
    threading.Thread(target=handleClient, args=(c, addr), daemon=True).start()
