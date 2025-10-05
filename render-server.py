import socket
import threading
import os
# It just for auto-server

class KiffyServer:
    def __init__(self, host='0.0.0.0', port=8888):
        self.host = host
        self.port = port
        self.clients = {}
        self.starred_users = set()
        self.admins = set()
        self.admin_password = "kiffyadmin123"
        
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
    def start(self):
        port = int(os.environ.get('PORT', 8888))
        self.server_socket.bind((self.host, port))
        self.server_socket.listen(10)
        print(f"🚀 Kiffy Server started on port {port}")
        
        while True:
            client_socket, addr = self.server_socket.accept()
            thread = threading.Thread(target=self.handle_client, args=(client_socket, addr))
            thread.daemon = True
            thread.start()

    def handle_client(self, client_socket, addr):
        username = None
        try:
            client_socket.send("🎯 Username: ".encode())
            username = client_socket.recv(1024).decode().strip()
            
            if not username or username in self.clients:
                client_socket.send("❌ Username taken".encode())
                client_socket.close()
                return
            
            self.clients[username] = {'socket': client_socket, 'anchor': None}
            
            welcome_msg = f"🎉 {username} joined ({len(self.clients)} online)"
            self.broadcast(welcome_msg, client_socket)
            
            help_msg = f"✅ Welcome {username}!\n💡 Commands: /users /s /anchor /unanchor /exit"
            client_socket.send(help_msg.encode())
            
            while True:
                message = client_socket.recv(1024).decode()
                if not message or message.strip() == '/exit':
                    break
                    
                if message.strip() == '/users':
                    users = ", ".join(self.clients.keys())
                    client_socket.send(f"👥 Online: {users}".encode())
                elif message.startswith('/s '):
                    parts = message[3:].split(' ', 1)
                    if len(parts) == 2:
                        target, msg = parts
                        self.send_private(username, target, msg, client_socket)
                elif message.startswith('/anchor '):
                    target = message[8:].strip()
                    if target in self.clients:
                        self.clients[username]['anchor'] = target
                        client_socket.send(f"🔗 Anchor to {target}".encode())
                    else:
                        client_socket.send(f"❌ User {target} not found".encode())
                elif message.strip() == '/unanchor':
                    self.clients[username]['anchor'] = None
                    client_socket.send("🔓 Anchor disabled".encode())
                else:
                    if self.clients[username]['anchor']:
                        target = self.clients[username]['anchor']
                        self.send_private(username, target, message, client_socket)
                    else:
                        self.broadcast(f"💬 {username}: {message}", client_socket)
                        
        except:
            pass
        finally:
            if username and username in self.clients:
                del self.clients[username]
                leave_msg = f"👋 {username} left ({len(self.clients)} online)"
                self.broadcast(leave_msg, None)
            client_socket.close()

    def send_private(self, from_user, to_user, message, sender_socket):
        if to_user in self.clients:
            try:
                self.clients[to_user]['socket'].send(f"🔒 {from_user}: {message}".encode())
                sender_socket.send(f"✅ PM to {to_user}".encode())
            except:
                sender_socket.send(f"❌ User {to_user} offline".encode())
        else:
            sender_socket.send(f"❌ User {to_user} not found".encode())

    def broadcast(self, message, exclude_socket):
        disconnected = []
        for user, client in self.clients.items():
            try:
                if client['socket'] != exclude_socket:
                    client['socket'].send(message.encode())
            except:
                disconnected.append(user)
        
        for user in disconnected:
            if user in self.clients:
                del self.clients[user]

if __name__ == "__main__":
    server = KiffyServer()
    server.start()
