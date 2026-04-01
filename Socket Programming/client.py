import socket
import threading
import os
import time

c = socket.socket()
c.connect(("localhost", 9999))


def recvMess():
    while True:
        mess = c.recv(2048).decode()
        if not mess:
            break

        if mess.lower() == "exit":
            break

        # FIX: file header handling remains same, but file receive loop fixed
        if mess.startswith("File: "):
            f = mess.split("File: ")[1]
            fn, ext = f.rsplit(".", 1)
            opf = f"{fn}CWrite.{ext}"

            with open(opf, "wb") as file:
                while True:
                    cnt = c.recv(2048)

                    # FIX: stop only on EOF marker, not empty recv
                    if b"EOF" in cnt:
                        cnt = cnt.replace(b"EOF", b"")
                        file.write(cnt)
                        break

                    file.write(cnt)

            print(f"Received File {f} From the Server.\n")

        else:
            print(mess)

    c.close()


def sendMess():
    while True:
        inp = input("Enter Message: ")

        if not inp:
            break

        if inp.lower() == "exit":
            c.send(b"exit")
            print("You Exited The Chat\n")
            break

        if inp.startswith("sendFile: "):
            f = inp.split("sendFile: ")[1]

            if not os.path.exists(f):
                print("File Not exist!\n")
                continue

            # FIX: send file header properly
            c.send(f"File: {f}".encode())
            time.sleep(0.1)

            with open(f, "rb") as file:
                while True:
                    cnt = file.read(2048)
                    if not cnt:          # FIX: cnt must be read before checking
                        break
                    c.send(cnt)

            # FIX: explicit EOF marker
            time.sleep(0.1)
            c.send(b"EOF")

        else:
            c.send(inp.encode())

    c.close()


threading.Thread(target=recvMess, daemon=True).start()
sendMess()
