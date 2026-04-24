import hashlib
import struct


DIFFICULTY_BITS = 28


def has_leading_zero_bits(digest: bytes, bits: int) -> bool:
    full_zero_bytes = bits // 8
    remaining_bits = bits % 8

    if digest[:full_zero_bytes] != b"\x00" * full_zero_bytes:
        return False

    if remaining_bits == 0:
        return True

    next_byte = digest[full_zero_bytes]
    return next_byte < (1 << (8 - remaining_bits))


def hash_pow(email: str, github_url: str, nonce: int) -> bytes:
    data = (
            email.encode("utf-8")
            + b"\n"
            + github_url.encode("utf-8")
            + b"\n"
            + struct.pack(">Q", nonce)
    )
    return hashlib.sha256(data).digest()


def mine(email: str, github_url: str, start_nonce: int = 0) -> int:
    nonce = start_nonce

    while nonce <= 2**63 - 1:
        digest = hash_pow(email, github_url, nonce)

        if has_leading_zero_bits(digest, DIFFICULTY_BITS):
            print("Found nonce:", nonce)
            print("Hash:", digest.hex())
            return nonce

        if nonce % 1_000_000 == 0:
            print("Tried", nonce)

        nonce += 1

    raise RuntimeError("No valid nonce found")


if __name__ == "__main__":
    email = "aioannou@student.tudelft.nl"
    github_url = "https://github.com/ioantreas/ipv8-pow-client"

    nonce = mine(email, github_url)
    print("nonce =", nonce)