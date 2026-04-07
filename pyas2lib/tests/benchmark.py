"""
Performance benchmark comparing crypto operations between branches.

Run on each branch to compare oscrypto vs cryptography performance.
Usage: python benchmark.py
"""
import os
import time
import statistics

from pyas2lib import as2, cms
from pyas2lib.as2 import Organization

TEST_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures")

# Detect backend and load certificate accordingly
try:
    from oscrypto import asymmetric
    BACKEND = "oscrypto"
    def load_cert(data):
        return asymmetric.load_certificate(data)
except ImportError:
    from pyas2lib.as2 import load_certificate
    BACKEND = "cryptography"
    def load_cert(data):
        return load_certificate(data)

ITERATIONS = 100


def load_fixtures():
    with open(os.path.join(TEST_DIR, "cert_test.p12"), "rb") as fp:
        private_key_data = fp.read()
    with open(os.path.join(TEST_DIR, "cert_test_public.pem"), "rb") as fp:
        public_key_data = fp.read()
    with open(os.path.join(TEST_DIR, "payload.txt"), "rb") as fp:
        test_data = fp.read()

    sign_key = Organization.load_key(private_key_data, "test")
    decrypt_key = Organization.load_key(private_key_data, "test")
    encrypt_cert = load_cert(public_key_data)
    verify_cert = load_cert(public_key_data)

    return sign_key, decrypt_key, encrypt_cert, verify_cert, test_data, private_key_data, public_key_data


def bench(name, func, iterations=ITERATIONS):
    """Run a benchmark and return timing stats."""
    # Warmup
    for _ in range(3):
        func()

    times = []
    for _ in range(iterations):
        start = time.perf_counter()
        func()
        elapsed = time.perf_counter() - start
        times.append(elapsed * 1000)  # ms

    avg = statistics.mean(times)
    med = statistics.median(times)
    std = statistics.stdev(times) if len(times) > 1 else 0
    mn = min(times)
    mx = max(times)
    total = sum(times)

    print(f"  {name:<45} avg={avg:7.2f}ms  med={med:7.2f}ms  std={std:6.2f}ms  min={mn:7.2f}ms  max={mx:7.2f}ms  total={total:8.1f}ms")
    return {"name": name, "avg": avg, "median": med, "std": std, "min": mn, "max": mx, "total": total}


def main():
    sign_key, decrypt_key, encrypt_cert, verify_cert, test_data, private_key_data, public_key_data = load_fixtures()

    print(f"=" * 90)
    print(f"pyas2-lib Performance Benchmark  |  Backend: {BACKEND}  |  Iterations: {ITERATIONS}")
    print(f"=" * 90)

    results = []

    # --- Compression ---
    print("\n[Compression]")
    results.append(bench("compress", lambda: cms.compress_message(test_data)))
    compressed = cms.compress_message(test_data)
    results.append(bench("decompress", lambda: cms.decompress_message(compressed)))

    # --- Signing ---
    print("\n[Signing]")
    for digest in ["sha256", "sha512"]:
        results.append(bench(
            f"sign (pkcs1v15, {digest})",
            lambda d=digest: cms.sign_message(test_data, digest_alg=d, sign_key=sign_key)
        ))
        results.append(bench(
            f"sign (pss, {digest})",
            lambda d=digest: cms.sign_message(test_data, digest_alg=d, sign_key=sign_key, sign_alg="rsassa_pss")
        ))

    # --- Signature Verification ---
    print("\n[Verification]")
    sig_pkcs1 = cms.sign_message(test_data, digest_alg="sha256", sign_key=sign_key)
    sig_pss = cms.sign_message(test_data, digest_alg="sha256", sign_key=sign_key, sign_alg="rsassa_pss")
    results.append(bench("verify (pkcs1v15, sha256)", lambda: cms.verify_message(test_data, sig_pkcs1, verify_cert)))
    results.append(bench("verify (pss, sha256)", lambda: cms.verify_message(test_data, sig_pss, verify_cert)))

    # --- Encryption ---
    print("\n[Encryption]")
    enc_algorithms = [
        "rc2_128_cbc",
        "rc4_128_cbc",
        "aes_128_cbc",
        "aes_192_cbc",
        "aes_256_cbc",
        "tripledes_192_cbc",
    ]
    for enc_alg in enc_algorithms:
        for key_alg in ["rsaes_pkcs1v15", "rsaes_oaep"]:
            results.append(bench(
                f"encrypt ({enc_alg}, {key_alg})",
                lambda e=enc_alg, k=key_alg: cms.encrypt_message(test_data, e, encrypt_cert, k)
            ))

    # --- Decryption ---
    print("\n[Decryption]")
    for enc_alg in enc_algorithms:
        for key_alg in ["rsaes_pkcs1v15", "rsaes_oaep"]:
            encrypted = cms.encrypt_message(test_data, enc_alg, encrypt_cert, key_alg)
            results.append(bench(
                f"decrypt ({enc_alg}, {key_alg})",
                lambda e=encrypted: cms.decrypt_message(e, decrypt_key)
            ))

    # --- End-to-End AS2 Message ---
    print("\n[End-to-End AS2 Message Build + Parse]")

    org = as2.Organization(
        as2_name="some_organization",
        sign_key=private_key_data,
        sign_key_pass="test",
        decrypt_key=private_key_data,
        decrypt_key_pass="test",
    )
    partner = as2.Partner(
        as2_name="some_partner",
        verify_cert=public_key_data,
        encrypt_cert=public_key_data,
    )

    def find_org(as2_id):
        return org

    def find_partner(as2_id):
        return partner

    # Plain message
    def build_parse_plain():
        out = as2.Message(org, partner)
        out.build(test_data)
        raw = out.headers_str + b"\r\n" + out.content
        inp = as2.Message()
        inp.parse(raw, find_org_cb=find_org, find_partner_cb=find_partner)

    results.append(bench("plain message (build+parse)", build_parse_plain))

    # Signed message
    partner.sign = True
    partner.encrypt = False
    partner.compress = False

    def build_parse_signed():
        out = as2.Message(org, partner)
        out.build(test_data)
        raw = out.headers_str + b"\r\n" + out.content
        inp = as2.Message()
        inp.parse(raw, find_org_cb=find_org, find_partner_cb=find_partner)

    results.append(bench("signed message (build+parse)", build_parse_signed))

    # Encrypted message
    partner.sign = False
    partner.encrypt = True
    partner.compress = False

    def build_parse_encrypted():
        out = as2.Message(org, partner)
        out.build(test_data)
        raw = out.headers_str + b"\r\n" + out.content
        inp = as2.Message()
        inp.parse(raw, find_org_cb=find_org, find_partner_cb=find_partner)

    results.append(bench("encrypted message (build+parse)", build_parse_encrypted))

    # Signed + Encrypted
    partner.sign = True
    partner.encrypt = True
    partner.compress = False

    def build_parse_signed_encrypted():
        out = as2.Message(org, partner)
        out.build(test_data)
        raw = out.headers_str + b"\r\n" + out.content
        inp = as2.Message()
        inp.parse(raw, find_org_cb=find_org, find_partner_cb=find_partner)

    results.append(bench("signed+encrypted (build+parse)", build_parse_signed_encrypted))

    # Signed + Encrypted + Compressed
    partner.sign = True
    partner.encrypt = True
    partner.compress = True

    def build_parse_full():
        out = as2.Message(org, partner)
        out.build(test_data)
        raw = out.headers_str + b"\r\n" + out.content
        inp = as2.Message()
        inp.parse(raw, find_org_cb=find_org, find_partner_cb=find_partner)

    results.append(bench("signed+encrypted+compressed (build+parse)", build_parse_full))

    # --- Summary ---
    print(f"\n{'=' * 90}")
    print(f"Total benchmark time: {sum(r['total'] for r in results) / 1000:.1f}s")
    print(f"Backend: {BACKEND}")
    print(f"{'=' * 90}")


if __name__ == "__main__":
    main()