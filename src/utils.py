from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
import uuid
import socket
def aes_ctr_encrypt(key, nonce, plaintext):
    """AES-CTR模式加密函数
    Args:
        key: bytes格式的加密密钥
        nonce: bytes格式的初始向量
        plaintext: 待加密的原始数据
    Returns:
        bytes格式的加密数据
    """
    cipher = Cipher(algorithms.AES(key), modes.CTR(nonce), backend=default_backend())
    encryptor = cipher.encryptor()
    return encryptor.update(plaintext) + encryptor.finalize()


def aes_ctr_decrypt(key, nonce, ciphertext):
    """AES-CTR模式解密函数
    Args:
        key: bytes格式的解密密钥
        nonce: bytes格式的初始向量（需要与加密时使用的相同）
        ciphertext: bytes格式的加密数据
    Returns:
        bytes格式的解密后的原始数据
    """
    cipher = Cipher(algorithms.AES(key), modes.CTR(nonce), backend=default_backend())
    decryptor = cipher.decryptor()
    plaintext = decryptor.update(ciphertext) + decryptor.finalize()
    return plaintext

def get_device_id():
    mac = uuid.UUID(int=uuid.getnode()).hex[-12:]

    return ":".join([mac[i:i + 2] for i in range(0, 12, 2)])

def get_local_ip():
    try:
        # 创建一个临时 socket 连接来获取本机 IP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return '127.0.0.1'

