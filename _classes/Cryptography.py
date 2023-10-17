from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from Crypto.Cipher import AES, PKCS1_OAEP, PKCS1_OAEP 
from Crypto.PublicKey import RSA
from Crypto.Random import get_random_bytes
from Crypto.Util.Padding import pad
import base64, os
from base64 import b64encode, b64decode

key_name = "ChattyAndroidKey"
padding = padding.PKCS1v15()
#padding = , padding.OAEP(mgf=padding.MGF1(algorithm=hashes.SHA256()), algorithm=hashes.SHA256(), label=None)

def bytes_to_text(b: bytearray): return b.decode('utf-8')
def bytes_from_text(text: str):  return text.encode('utf-8')
def bytes_to_base64text(b: bytearray): return base64.b64encode(b).decode('utf-8')
def bytes_from_base64text(text: str):  return base64.b64decode(text)
def bytes_to_liststring(b: bytearray): return ':'.join(map(str, list(b)))	#To avoid cross platform character encoding issues bytes->list(int)->str
def bytes_from_liststring(list_string: list): return bytearray(list(map(int, list_string.split(':')))) #str->list(int)->bytes

def generate_aes_key(): return get_random_bytes(32)

def get_aes_certificate(): #Exports cert a string
	file = f"certs/content.pem"
	if not os.path.isfile(file):
		key_bytes = generate_aes_key()
		with open(file, "wb") as file:
			file.write(key_bytes)
	else:
		with open(file, "rb") as file:
			key_bytes = file.read()
	return bytes_to_base64text(key_bytes)
	
def save_aes_certificate(text: str): #imports cert from string
	file = f"certs/content.pem"
	key_bytes = bytes_from_base64text(text)
	with open(file, "wb") as file:
		file.write(key_bytes)

def key_exists():
	private_key_file = f"certs/{key_name}_private.pem"
	public_key_file = f"certs/{key_name}_public.pem"
	return os.path.isfile(public_key_file) and os.path.isfile(private_key_file)

def save_certificate(private_key_bytes, public_key_bytes):
	private_key_file = f"certs/{key_name}_private.pem"
	public_key_file = f"certs/{key_name}_public.pem"
	with open(private_key_file, "wb") as private_key_file:
		private_key_file.write(private_key_bytes)
	with open(public_key_file, "wb") as public_key_file:
		public_key_file.write(public_key_bytes)

def generate_key_pair():
	private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048, backend=default_backend())
	public_key = private_key.public_key()
	private_key_bytes = private_key.private_bytes(encoding=serialization.Encoding.PEM, format=serialization.PrivateFormat.TraditionalOpenSSL, encryption_algorithm=serialization.NoEncryption()	)
	public_key_bytes = public_key.public_bytes( encoding=serialization.Encoding.PEM, format=serialization.PublicFormat.SubjectPublicKeyInfo )
	save_certificate(private_key_bytes, public_key_bytes)

def get_private_key():
	private_key_file = f"certs/{key_name}_private.pem"
	if not key_exists(): generate_key_pair()
	with open(private_key_file, "rb") as private_key_file:
		private_key_bytes = private_key_file.read()
		private_key = serialization.load_pem_private_key(private_key_bytes, password=None, backend=default_backend())
	return private_key

def get_public_key():
	public_key_file = f"certs/{key_name}_public.pem"
	if not key_exists(): generate_key_pair()
	with open(public_key_file, "rb") as public_key_file:
		public_key_bytes = public_key_file.read()
		public_key = serialization.load_pem_public_key(public_key_bytes, backend=default_backend())
	return public_key

def get_public_key_as_string(der_encoded: bool = True):
	public_key_file = f"certs/{key_name}_public.pem"
	if not key_exists(): generate_key_pair()
	with open(public_key_file, "rb") as public_key_file:
		key_bytes = public_key_file.read()
	if der_encoded:
		pem_key = serialization.load_pem_public_key(key_bytes, backend=default_backend())
		key_bytes = pem_key.public_bytes(encoding=serialization.Encoding.DER, format=serialization.PublicFormat.SubjectPublicKeyInfo)
	return bytes_to_base64text(key_bytes)
		
def get_public_key_from_string(public_key_string: str, der_encoded: bool = True):
	public_key_bytes = bytes_from_base64text(public_key_string)
	try:
		if der_encoded:
			return serialization.load_der_public_key(public_key_bytes, backend=default_backend())
		else:
			return serialization.load_pem_public_key(public_key_bytes, backend=default_backend())
	except Exception as e:
		print("Error in get_public_key_from_string")
		print(e)
		return None
	
def encrypt_with_aes(byte_array, key, iv):
	try:
		if False:
			cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
			encryptor = cipher.encryptor()
			encrypted_message = encryptor.update(byte_array) + encryptor.finalize()
			return encrypted_message
		else:
			byte_array = pad(byte_array, 16)
			cipher = AES.new(key, AES.MODE_CBC, iv)
			return cipher.encrypt(byte_array)
	except Exception as e:
		print("Error in encrypt_with_aes")
		print(e)
		return None

def decrypt_with_aes(byte_array, key, iv):
	try:
		if False:
			cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
			decryptor = cipher.decryptor()
			decrypted_message = decryptor.update(byte_array) + decryptor.finalize()
			return decrypted_message
		else:		
			cipher = AES.new(key, AES.MODE_CBC, iv)
			return cipher.decrypt(byte_array)
	except Exception as e:
		print("Error in decrypt_with_aes")
		print(e)
		return None
	
def encrypt_with_rsa(byte_array, public_key):
	try:
		return public_key.encrypt(byte_array, padding)
	except Exception as e:
		print(e)
		return None

def decrypt_with_rsa(encrypted_bytes, private_key):
	try:
		return private_key.decrypt(encrypted_bytes, padding)
	except Exception as e:
		print(e)
		return None

def encrypt_string_aes(text, aes_key_string=""):
	result = ""
	aes_key = bytes_from_base64text(aes_key_string)
	iv = get_random_bytes(16)
	source_bytes = bytes_from_text(text)
	encrypted_bytes = encrypt_with_aes(source_bytes, aes_key, iv)
	if encrypted_bytes != None: 
		result = bytes_to_base64text(iv) + "|" + bytes_to_base64text(encrypted_bytes)
	return result

def decrypt_string_aes(text, aes_key_string=""):
	result = ""
	aes_key = bytes_from_base64text(aes_key_string)
	x = text.split("|")
	if len(x) == 2:
		iv = bytes_from_base64text(x[0])
		encrypted_bytes = bytes_from_base64text(x[1])
		decrypted_bytes = decrypt_with_aes(encrypted_bytes, aes_key, iv)
		if decrypted_bytes != None: 
			padding_value = decrypted_bytes[-1]
			if padding_value < 1 or padding_value > 16:
				print("Invalid padding value: " + str(padding_value))
			decrypted_bytes = decrypted_bytes[:-padding_value]
			result = bytes_to_text(decrypted_bytes)
	else:
		print("Malformed AES encrypted text.")
	return result

def encrypt_string_rsa(text, public_key_string=""):
	result = ""
	#print(f"Encrypting string length: {len(text)} text: {text[:50]}")
	public_key = get_public_key()
	if public_key_string !="":
		public_key = get_public_key_from_string(public_key_string)
		if public_key == None: 
			print("Failed to load the given public key")
			return ""
	source_bytes = bytes_from_text(text)
	if len(text) < 190:
		#print("Short string is directly encrypted")
		encrypted_bytes = encrypt_with_rsa(source_bytes, public_key)
		result = bytes_to_base64text(encrypted_bytes)
	else:
		#print("Long string is encrypted with AES")
		aes_key = generate_aes_key()
		encrypted_aes_key = encrypt_with_rsa(aes_key, public_key)
		#print(f"Created and encrypted new AES key. Len: {len(encrypted_aes_key)}")
		iv = get_random_bytes(16)
		encrypted_bytes = encrypt_with_aes(source_bytes, aes_key, iv)
		result = bytes_to_base64text(encrypted_aes_key)
		result += "|" + bytes_to_base64text(iv)
		result += "|" + bytes_to_base64text(encrypted_bytes)
	return result

def decrypt_string_rsa(text):
	result = ""
	x = text.split("|")
	if len(x) == 1:
		#print("Short string is directly decrypted")
		decrypted_bytes = decrypt_with_rsa(bytes_from_base64text(text), get_private_key())
		if decrypted_bytes != None: result = bytes_to_text(decrypted_bytes)
	elif len(x) == 3:
		#print("Long string is decrypted with AES")
		encrypted_aes_key = bytes_from_base64text(x[0])
		decrypted_aes_key = decrypt_with_rsa(encrypted_aes_key, get_private_key())
		aes_key = decrypted_aes_key
		iv = bytes_from_base64text(x[1])
		encrypted_bytes = bytes_from_base64text(x[2])
		decrypted_bytes = decrypt_with_aes(encrypted_bytes, aes_key, iv)
		if decrypted_bytes != None: result = bytes_to_text(decrypted_bytes)
	else:
		print("Decrypt string, malformed input array")
	return result

def test_cryptography(text: str, public_key_string:str=""):
	print("Testing encryption...")
	print("public_key_string", public_key_string)
	t1 = encrypt_string_rsa(text)
	#print(f"Encrypted: {t1}")
	t2 = decrypt_string_rsa(t1)
	print(f"Output: {t2}")
	print(f"Result matches source: {text == t2}")

