import bcrypt

def generate_hash(password: str) -> str:
    # Génère un hash bcrypt avec salt auto
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

if __name__ == "__main__":
    secret = "Session_Admin_12$"  # Ton password
    hashed_secret = generate_hash(secret)
    print(f"Hashed password: {hashed_secret}")