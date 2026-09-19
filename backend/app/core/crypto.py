import base64
import hashlib
import json
from typing import Any, Dict, Tuple
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec, ed25519, padding, utils
from cryptography.hazmat.primitives.asymmetric.ec import EllipticCurvePublicKey, EllipticCurvePrivateKey
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey, Ed25519PrivateKey
from cryptography.exceptions import InvalidSignature

from app.core.exceptions import CryptographicVerificationError


def canonical_json_bytes(data: Dict[str, Any]) -> bytes:
    """
    Produces deterministic UTF-8 byte representation of a dictionary for cryptographic signing.
    Keys are sorted, whitespace is removed.
    """
    return json.dumps(data, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode('utf-8')


def compute_public_key_fingerprint(public_key_pem: str) -> str:
    """
    Computes SHA-256 fingerprint (hex) of the raw public key DER bytes.
    """
    clean_pem = public_key_pem.strip().encode('utf-8')
    try:
        loaded_key = serialization.load_pem_public_key(clean_pem)
        der_bytes = loaded_key.public_bytes(
            encoding=serialization.Encoding.DER,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        return hashlib.sha256(der_bytes).hexdigest()
    except Exception as e:
        # Fallback to direct string hash if parsing fails
        return hashlib.sha256(clean_pem).hexdigest()


def generate_backend_ecdsa_keypair() -> Tuple[str, str]:
    """
    Generates a secp256r1 (NIST P-256) ECDSA keypair for backend command signing.
    Returns (private_key_pem, public_key_pem).
    """
    private_key = ec.generate_private_key(ec.SECP256R1())
    public_key = private_key.public_key()

    priv_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    ).decode('utf-8')

    pub_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    ).decode('utf-8')

    return priv_pem, pub_pem


def sign_payload(payload: Dict[str, Any], private_key_pem: str) -> str:
    """
    Signs canonical JSON bytes of payload using ECDSA P-256 or Ed25519.
    Returns base64-encoded signature.
    """
    data_bytes = canonical_json_bytes(payload)
    priv_key = serialization.load_pem_private_key(private_key_pem.encode('utf-8'), password=None)

    if isinstance(priv_key, EllipticCurvePrivateKey):
        signature = priv_key.sign(data_bytes, ec.ECDSA(hashes.SHA256()))
    elif isinstance(priv_key, Ed25519PrivateKey):
        signature = priv_key.sign(data_bytes)
    else:
        raise ValueError("Unsupported private key type for signing")

    return base64.b64encode(signature).decode('utf-8')


def verify_signature(payload: Dict[str, Any], signature_b64: str, public_key_pem: str) -> bool:
    """
    Verifies base64 signature against canonical JSON bytes of payload using public key.
    Raises CryptographicVerificationError if invalid.
    """
    try:
        signature_bytes = base64.b64decode(signature_b64)
        data_bytes = canonical_json_bytes(payload)
        pub_key = serialization.load_pem_public_key(public_key_pem.encode('utf-8'))

        if isinstance(pub_key, EllipticCurvePublicKey):
            pub_key.verify(signature_bytes, data_bytes, ec.ECDSA(hashes.SHA256()))
        elif isinstance(pub_key, Ed25519PublicKey):
            pub_key.verify(signature_bytes, data_bytes)
        else:
            raise CryptographicVerificationError("Unsupported public key algorithm")
        return True
    except (InvalidSignature, ValueError, TypeError) as e:
        raise CryptographicVerificationError(f"Signature verification failed: {str(e)}")
    except Exception as e:
        raise CryptographicVerificationError(f"Cryptographic error during verification: {str(e)}")


def compute_audit_hash(prev_hash: str, actor_id: str, action: str, resource_id: str, timestamp_iso: str, details_json: str) -> str:
    """
    Computes a cryptographic SHA-256 hash for tamper-evident audit chaining.
    """
    content = f"{prev_hash}|{actor_id}|{action}|{resource_id}|{timestamp_iso}|{details_json}"
    return hashlib.sha256(content.encode('utf-8')).hexdigest()
