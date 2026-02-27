from fastapi import FastAPI
import os

app = FastAPI()

SECRET_FILE = "/vault/secrets/config"

def read_secret():
    try:
        with open(SECRET_FILE, "r") as f:
            return f.read()
    except:
        return "No secret found"

@app.get("/")
def home():
    secret = read_secret()
    return {
        "message": "Vault Secret Values",
        "secret": secret
    }
