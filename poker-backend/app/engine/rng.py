import hashlib
import random
import os
import hmac

class DeterministicRNG:
    def __init__(self, seed_val):
        self.seed_val = seed_val
        self.rng = random.Random(seed_val)

    def shuffle(self, items):
        self.rng.shuffle(items)
        return items

    def randint(self, a, b):
        return self.rng.randint(a, b)
    
    @staticmethod
    def generate_seed(server_secret, hand_id):
        # Create a deterministic seed based on secret and hand_id
        raw = f"{server_secret}:{hand_id}".encode()
        return int(hashlib.sha256(raw).hexdigest(), 16)

    @staticmethod
    def generate_secret():
        return hashlib.sha256(os.urandom(32)).hexdigest()

    @staticmethod
    def compute_commitment(secret, hand_id):
        msg = f"{hand_id}".encode()
        key = secret.encode()
        return hmac.new(key, msg, hashlib.sha256).hexdigest()
