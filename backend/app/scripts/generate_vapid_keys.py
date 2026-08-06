"""Generate VAPID key pair for Browser Push (.env)."""

from cryptography.hazmat.primitives import serialization
from py_vapid import Vapid01
from py_vapid.utils import b64urlencode


def main() -> None:
    vapid = Vapid01()
    vapid.generate_keys()
    private_pem = vapid.private_pem().decode()
    public_bytes = vapid.public_key.public_bytes(
        encoding=serialization.Encoding.X962,
        format=serialization.PublicFormat.UncompressedPoint,
    )
    public_key = b64urlencode(public_bytes)
    print("# Add these to backend/.env")
    print(f"VAPID_PRIVATE_KEY={private_pem!r}")
    print("# Or paste the PEM with literal newlines escaped as \\n")
    print("----- BEGIN PRIVATE PEM -----")
    print(private_pem)
    print("----- END PRIVATE PEM -----")
    print(f"VAPID_PUBLIC_KEY={public_key}")
    print("VAPID_SUBJECT=mailto:alerts@clinicaltrialnavigator.local")


if __name__ == "__main__":
    main()
