import socket
import threading

class KiffyClient:
    def __init__(self):
        self.socket = None
        self.running = False
        self.username = None
        self.is_admin = False
        
    def connect(self, server_ip, server_port=8888):
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((server_ip, server_port))
            self.running = True
            
            username_prompt = self.socket.recv(1024).decode('utf-8')
            print(username_prompt, end='')
            self.username = input()
            self.socket.send(self.username.encode('utf-8'))
            
            response = self.socket.recv(1024).decode('utf-8')
            if "password" in response:
                print(response, end='')
                password = input()
                self.socket.send(password.encode('utf-8'))
                response = self.socket.recv(1024).decode('utf-8')
            
            print(f"\n{response}")
            
            if "Wrong" in response or "taken" in response or "Invalid" in response:
                return False
                
            # Проверяем, стал ли пользователь админом
            if "admin" in response.lower():
                self.is_admin = True
                
            receive_thread = threading.Thread(target=self.receive_messages)
            receive_thread.daemon = True
            receive_thread.start()
            
            return True
            
        except Exception as e:
            print(f"❌ Connection failed: {e}")
            return False
    
    def receive_messages(self):
        while self.running:
            try:
                message = self.socket.recv(1024).decode('utf-8')
                if not message:
                    break
                print(f"\n{message}")
                self.show_prompt()
            except:
                break
    
    def send_message(self, message):
        try:
            self.socket.send(message.encode('utf-8'))
        except:
            print("❌ Failed to send")
    
    def show_prompt(self):
        admin_indicator = "🌟 " if self.is_admin else ""
        print(f"\n💬 {admin_indicator}{self.username} > ", end="", flush=True)
    
    def start_chat(self):
        print(f"\n💬 Chat started: {self.username}")
        print("💡 Commands: /users /s [user] [msg] /anchor [user] /unanchor /exit")
        if self.is_admin:
            print("🌟 Admin: /star [user] /unstar [user] /global [msg] /setemoji [emoji] /makeadmin [user] /removeadmin [user]")
        print("-" * 40)
        
        try:
            while self.running:
                self.show_prompt()
                message = input()
                
                if message.lower() == '/exit':
                    self.running = False
                    self.send_message('/exit')
                    break
                elif message.strip():
                    self.send_message(message)
                    
        except KeyboardInterrupt:
            print("\n👋 Leaving...")
        finally:
            self.running = False
            if self.socket:
                self.socket.close()

if __name__ == "__main__":
    client = KiffyClient()
    
    print("🚀 KIFFY MESSENGER")
    server_ip = input("📍 Server IP: ").strip()
    
    if client.connect(server_ip):
        client.start_chat()
    else:
        print("❌ Failed to connect")