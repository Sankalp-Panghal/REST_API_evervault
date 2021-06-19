# --- Requirements ---
#pip install flask
#pip install pycryptodome
#pip install shutil
#pip install -r requirements.txt

from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP
from flask import Flask, request, jsonify
import base64
import os
import shutil
import json

from Crypto.Signature import pkcs1_15
from Crypto.Hash import SHA256 



#---------------------- CHECK KEYS PRESENT OR CREATE AND WRITE THEM-----------------------
if "keys" in os.listdir(os.getcwd()) and "public.key" in os.listdir("keys") and "private.key" in os.listdir("keys"):
    pub_key = RSA.import_key(open("keys/public.key","rb").read())
    pri_key = RSA.import_key(open("keys/private.key","rb").read())
else:  
    # Generate
    try:
        shutil.rmtree("keys")
    except:
        pass
    os.mkdir("keys")
    key = RSA.generate(2048)
    pri_key = key.export_key()
    pub_key = key.public_key().export_key()
    with open("keys/public.key","wb") as f:
        f.write(pub_key)
    with open("keys/private.key","wb") as f:
        f.write(pri_key)

##########################################
encryptor = PKCS1_OAEP.new(pub_key)
decryptor = PKCS1_OAEP.new(pri_key)
##########################################

app = Flask(__name__)

#---------------------- ENDPOINT 1 - ENCRYPT -----------------------
@app.route("/encrypt",methods = ["GET","POST"])
def encrypt_api():
    data = request.get_json()
    for name in data:
        ob = data[name]
        if type(ob) != str:
            ob = json.dumps(data[name])
        data[name] = base64.b64encode(encryptor.encrypt(ob.encode('utf-8'))).decode()
    return jsonify(data)


#---------------------- ENDPOINT 2 - ENCRYPT -----------------------
def mydecrypt(data):
    for name in data:
        if data[name][-2:] == "==":     #DETECTING IF FIELD IS ENCRYPTED, by our base64
            ob_string = decryptor.decrypt(base64.b64decode(data[name].encode())).decode()
            try:
                ob = int(ob_string)
                data[name] = ob
                continue
            except:
                pass

            try:
                ob = json.loads(ob_string)
                data[name] = ob
                continue
            except:
                pass

            data[name] = ob_string
    return data

@app.route("/decrypt",methods = ["GET","POST"])
def decrypt_api():
    data = request.get_json()
    data = mydecrypt(data)
    return jsonify(data) 


#---------------------- ENDPOINT 3 - SIGN -----------------------
@app.route("/sign", methods=["GET","POST"])
def sign_api():
    data = json.dumps(request.get_json())
    print("SIGN OF ", data)
    signature = sign(data.encode())
    return base64.b64encode(signature).decode()

#---------------------- ENDPOINT 4 - VERIFY -----------------------
@app.route("/verify", methods=["GET","POST"])
def verify_api():
    data = request.get_json()
    signature = base64.b64decode(data["signature"].encode())
    inner_data = mydecrypt(data["data"])
    if verify(json.dumps(inner_data).encode(),signature):
        return (" ",204)
    else:
        return (" ", 400)

    # Inner data can contain encrypted fields


def sign(message):
    hash = SHA256.new(message)  #Create hash of the message
    signer = pkcs1_15.new(pri_key) #Create signature with private key
    signature = signer.sign(hash)   
    return signature

def verify(message,signature):
    hash = SHA256.new(message)
    match = None
    try:
        pkcs1_15.new(pub_key).verify(hash,signature)
        match = True
    except:
        match = False
    return match

app.run(port = 6362)