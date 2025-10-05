import socket
import threading
import time
from datetime import datetime
import re
import getpass

class KiffyServer:
    def __init__(self, host='0.0.0.0', port=8888):
        self.host = host
        self.port = port
        self.clients = {}
        self.starred_users = set()
        self.admins = set()  # Множество админов
        self.global_emoji = "📢"  # Эмодзи для глобальных сообщений
        
        print("KIFFY SERVER SETUP")
        print("=" * 40)
        self.admin_password = getpass.getpass("Set admin password: ")
        print("=" * 40)
        
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
    def get_server_ip(self):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            s.close()
            return local_ip
        except:
            return "localhost"
    
    def is_valid_username(self, username):
        return bool(re.match(r'^[a-zA-Z0-9_]+$', username))
    
    def give_star(self, target_user):
        if target_user in self.clients:
            self.starred_users.add(target_user)
            self.clients[target_user]['star'] = True
            return True
        return False
    
    def remove_star(self, target_user):
        if target_user in self.starred_users:
            self.starred_users.remove(target_user)
            if target_user in self.clients:
                self.clients[target_user]['star'] = False
            return True
        return False
    
    def make_admin(self, username):
        """Сделать пользователя админом"""
        if username in self.clients:
            self.admins.add(username)
            self.clients[username]['admin'] = True
            return True
        return False
    
    def remove_admin(self, username):
        """Убрать права админа"""
        if username in self.admins:
            self.admins.remove(username)
            if username in self.clients:
                self.clients[username]['admin'] = False
            return True
        return False
    
    def send_global_message(self, from_user, message):
        """Отправить глобальное сообщение всем пользователям"""
        formatted_message = f"{self.global_emoji} [GLOBAL] {from_user}: {message}"
        self.broadcast(formatted_message, None)
        return True
    
    def change_global_emoji(self, new_emoji):
        """Изменить эмодзи для глобальных сообщений"""
        self.global_emoji = new_emoji
        return True
    
    def start(self):
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(10)
        
        server_ip = self.get_server_ip()
        
        print("KIFFY MESSENGER SERVER STARTED")
        print("=" * 50)
        print(f"Server IP: {server_ip}")
        print(f"Port: {self.port}")
        print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("Waiting for connections...")
        print("=" * 50)
        
        while True:
            client_socket, addr = self.server_socket.accept()
            thread = threading.Thread(target=self.handle_client, args=(client_socket, addr))
            thread.daemon = True
            thread.start()
    
    def format_username(self, username):
        if username in self.starred_users:
            return f"🌟 {username}"
        return username
    
    def send_private_message(self, from_user, to_user, message):
        if to_user in self.clients:
            try:
                formatted_from = self.format_username(from_user)
                private_msg = f"🔒 {formatted_from}: {message}"
                self.clients[to_user]['socket'].send(private_msg.encode('utf-8'))
                return True
            except:
                return False
        return False
    
    def set_anchor(self, username, target_user):
        if target_user in self.clients:
            self.clients[username]['anchor_target'] = target_user
            return True
        return False
    
    def remove_anchor(self, username):
        if username in self.clients and 'anchor_target' in self.clients[username]:
            del self.clients[username]['anchor_target']
            return True
        return False
    
    def broadcast(self, message, sender_socket=None):
        disconnected = []
        
        for username, client_info in list(self.clients.items()):
            try:
                if client_info['socket'] != sender_socket:
                    client_info['socket'].send(message.encode('utf-8'))
            except:
                disconnected.append(username)
        
        for username in disconnected:
            if username in self.clients:
                del self.clients[username]
                if username in self.starred_users:
                    self.starred_users.remove(username)
                if username in self.admins:
                    self.admins.remove(username)
                leave_msg = f"👋 {self.format_username(username)} left ({len(self.clients)} online)"
                self.broadcast(leave_msg, None)
    
    def handle_client(self, client_socket, addr):
        username = None
        is_admin = False
        
        try:
            client_socket.send("🎯 Username: ".encode('utf-8'))
            username = client_socket.recv(1024).decode('utf-8').strip()
            
            if not username:
                client_socket.close()
                return
            
            if not self.is_valid_username(username):
                client_socket.send("❌ Invalid username! Only letters, numbers, _".encode('utf-8'))
                client_socket.close()
                return
            
            if username in self.clients:
                client_socket.send("❌ Username taken!".encode('utf-8'))
                client_socket.close()
                return
            
            # Проверка пароля для admin
            if username == "admin":
                client_socket.send("🔑 Admin password: ".encode('utf-8'))
                password = client_socket.recv(1024).decode('utf-8').strip()
                if password == self.admin_password:
                    is_admin = True
                    self.make_admin(username)
                    client_socket.send("✅ Admin access granted!".encode('utf-8'))
                else:
                    client_socket.send("❌ Wrong password!".encode('utf-8'))
                    client_socket.close()
                    return
            
            self.clients[username] = {
                'socket': client_socket,
                'anchor_target': None,
                'star': username in self.starred_users,
                'admin': is_admin
            }
            
            formatted_username = self.format_username(username)
            welcome_msg = f"🎉 {formatted_username} joined ({len(self.clients)} online)"
            self.broadcast(welcome_msg, client_socket)
            
            online_users = ", ".join([self.format_username(u) for u in self.clients.keys() if u != username])
            help_msg = f"✅ Welcome {formatted_username}!\n👥 Online: {online_users}\n💡 Commands: /users /s [user] [msg] /anchor [user] /unanchor /exit"
            
            if is_admin:
                help_msg += "\n🌟 Admin: /star [user] /unstar [user] /global [msg] /setemoji [emoji] /makeadmin [user] /removeadmin [user]"
            
            client_socket.send(help_msg.encode('utf-8'))
            
            while True:
                message = client_socket.recv(1024).decode('utf-8')
                if not message:
                    break
                    
                if message.strip().lower() == '/exit':
                    break
                elif message.strip().lower() == '/users':
                    users_list = "👥 Online: " + ", ".join([self.format_username(u) for u in self.clients.keys()])
                    client_socket.send(users_list.encode('utf-8'))
                    continue
                elif message.startswith('/s '):
                    parts = message[3:].split(' ', 1)
                    if len(parts) == 2:
                        target_user, private_msg = parts
                        if self.send_private_message(username, target_user, private_msg):
                            client_socket.send(f"✅ PM sent to {target_user}".encode('utf-8'))
                        else:
                            client_socket.send(f"❌ User {target_user} not found".encode('utf-8'))
                    else:
                        client_socket.send("❌ Use: /s [user] [msg]".encode('utf-8'))
                    continue
                elif message.startswith('/anchor '):
                    target_user = message[8:].strip()
                    if self.set_anchor(username, target_user):
                        client_socket.send(f"🔗 Anchor to {target_user}".encode('utf-8'))
                    else:
                        client_socket.send(f"❌ User {target_user} not found".encode('utf-8'))
                    continue
                elif message.strip().lower() == '/unanchor':
                    if self.remove_anchor(username):
                        client_socket.send("🔓 Anchor disabled".encode('utf-8'))
                    else:
                        client_socket.send("ℹ️ No anchor active".encode('utf-8'))
                    continue
                elif is_admin and message.startswith('/star '):
                    target_user = message[6:].strip()
                    if self.give_star(target_user):
                        client_socket.send(f"🌟 Star given to {target_user}".encode('utf-8'))
                        star_msg = f"🎉 {target_user} received Kiffy Star 🌟"
                        self.broadcast(star_msg, None)
                    else:
                        client_socket.send(f"❌ User {target_user} not found".encode('utf-8'))
                    continue
                elif is_admin and message.startswith('/unstar '):
                    target_user = message[8:].strip()
                    if self.remove_star(target_user):
                        client_socket.send(f"❌ Star removed from {target_user}".encode('utf-8'))
                    else:
                        client_socket.send(f"❌ User {target_user} no star".encode('utf-8'))
                    continue
                elif is_admin and message.startswith('/global '):
                    global_msg = message[8:].strip()
                    if global_msg:
                        self.send_global_message(username, global_msg)
                        client_socket.send("✅ Global message sent".encode('utf-8'))
                    else:
                        client_socket.send("❌ Use: /global [message]".encode('utf-8'))
                    continue
                elif is_admin and message.startswith('/setemoji '):
                    new_emoji = message[10:].strip()
                    if new_emoji:
                        self.change_global_emoji(new_emoji)
                        client_socket.send(f"✅ Global emoji changed to {new_emoji}".encode('utf-8'))
                    else:
                        client_socket.send("❌ Use: /setemoji [emoji]".encode('utf-8'))
                    continue
                elif is_admin and message.startswith('/makeadmin '):
                    target_user = message[11:].strip()
                    if self.make_admin(target_user):
                        client_socket.send(f"✅ {target_user} is now admin".encode('utf-8'))
                        # Уведомляем нового админа
                        if target_user in self.clients:
                            self.clients[target_user]['socket'].send("🎉 You are now an admin! Use /help for admin commands".encode('utf-8'))
                    else:
                        client_socket.send(f"❌ User {target_user} not found".encode('utf-8'))
                    continue
                elif is_admin and message.startswith('/removeadmin '):
                    target_user = message[13:].strip()
                    if target_user == "admin":
                        client_socket.send("❌ Cannot remove main admin".encode('utf-8'))
                    elif self.remove_admin(target_user):
                        client_socket.send(f"✅ Admin rights removed from {target_user}".encode('utf-8'))
                    else:
                        client_socket.send(f"❌ User {target_user} not admin".encode('utf-8'))
                    continue
                    
                if username in self.clients and self.clients[username].get('anchor_target'):
                    target_user = self.clients[username]['anchor_target']
                    if self.send_private_message(username, target_user, message):
                        client_socket.send(f"🔗 Sent to {target_user}".encode('utf-8'))
                    else:
                        client_socket.send(f"❌ User {target_user} offline".encode('utf-8'))
                else:
                    formatted_username = self.format_username(username)
                    formatted_msg = f"💬 {formatted_username}: {message}"
                    self.broadcast(formatted_msg, client_socket)
                
        except:
            pass
        finally:
            if username and username in self.clients:
                del self.clients[username]
                if username in self.admins and username != "admin":
                    self.admins.remove(username)
                formatted_username = self.format_username(username)
                leave_msg = f"👋 {formatted_username} left ({len(self.clients)} online)"
                self.broadcast(leave_msg, None)
            client_socket.close()

if __name__ == "__main__":
    server = KiffyServer()
    server.start()