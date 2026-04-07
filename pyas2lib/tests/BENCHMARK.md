# Performance Benchmark: `cryptography` vs `oscrypto`

Benchmark comparing the `cryptography` library (branch `feature/replace-oscrypto-with-cryptography`) against `oscrypto` (branch `cargoo`).

**Test environment:** macOS, Python 3.10, 100 iterations per operation.

## Summary

| Operation | oscrypto (ms) | cryptography (ms) | Speedup |
|---|---:|---:|---:|
| **Signing (pkcs1v15, sha256)** | 11.72 | 1.57 | **7.5x** |
| **Signing (pss, sha256)** | 12.24 | 1.54 | **7.9x** |
| **Signing (pkcs1v15, sha512)** | 11.75 | 1.55 | **7.6x** |
| **Signing (pss, sha512)** | 11.81 | 1.54 | **7.7x** |
| **Verify (pkcs1v15, sha256)** | 0.76 | 0.15 | **5.1x** |
| **Verify (pss, sha256)** | 0.21 | 0.16 | **1.3x** |
| **Encrypt (aes_256, pkcs1v15)** | 0.42 | 0.20 | **2.1x** |
| **Encrypt (aes_256, oaep)** | 0.88 | 0.19 | **4.6x** |
| **Decrypt (aes_256, pkcs1v15)** | 10.01 | 0.69 | **14.5x** |
| **Decrypt (aes_256, oaep)** | 10.40 | 0.70 | **14.9x** |

### End-to-End AS2 Message (Build + Parse)

| Scenario | oscrypto (ms) | cryptography (ms) | Speedup |
|---|---:|---:|---:|
| Plain message | 1.41 | 1.07 | **1.3x** |
| Signed | 17.03 | 5.20 | **3.3x** |
| Encrypted | 14.69 | 4.20 | **3.5x** |
| Signed + Encrypted | 30.28 | 7.61 | **4.0x** |
| Signed + Encrypted + Compressed | 30.67 | 8.25 | **3.7x** |

### Total Benchmark Time

| Backend | Total |
|---|---:|
| oscrypto | **27.3s** |
| cryptography | **4.4s** |
| Speedup | **6.2x** |

## Key Findings

- **Decryption** sees the largest improvement at ~15x faster.
- **Signing** is ~7.5x faster across all digest/algorithm combinations.
- **End-to-end signed+encrypted messages** are ~4x faster.
- **Encryption with OAEP** improves ~4.6x vs ~2.1x for PKCS1v15, indicating oscrypto's OAEP implementation was particularly slow.
- **Compression** is identical since both backends use zlib directly.

## Full Raw Output

### `cryptography` backend

```
==========================================================================================
pyas2-lib Performance Benchmark  |  Backend: cryptography  |  Iterations: 100
==========================================================================================

[Compression]
  compress                                      avg=   0.04ms  med=   0.04ms  std=  0.00ms  min=   0.04ms  max=   0.06ms  total=     4.3ms
  decompress                                    avg=   0.02ms  med=   0.02ms  std=  0.00ms  min=   0.02ms  max=   0.03ms  total=     1.8ms

[Signing]
  sign (pkcs1v15, sha256)                       avg=   1.57ms  med=   1.53ms  std=  0.16ms  min=   1.44ms  max=   2.36ms  total=   157.2ms
  sign (pss, sha256)                            avg=   1.54ms  med=   1.51ms  std=  0.15ms  min=   1.45ms  max=   2.37ms  total=   153.5ms
  sign (pkcs1v15, sha512)                       avg=   1.55ms  med=   1.52ms  std=  0.14ms  min=   1.44ms  max=   2.35ms  total=   154.6ms
  sign (pss, sha512)                            avg=   1.54ms  med=   1.52ms  std=  0.13ms  min=   1.44ms  max=   2.29ms  total=   153.6ms

[Verification]
  verify (pkcs1v15, sha256)                     avg=   0.15ms  med=   0.15ms  std=  0.01ms  min=   0.15ms  max=   0.21ms  total=    15.3ms
  verify (pss, sha256)                          avg=   0.16ms  med=   0.16ms  std=  0.01ms  min=   0.15ms  max=   0.20ms  total=    15.8ms

[Encryption]
  encrypt (rc2_128_cbc, rsaes_pkcs1v15)         avg=   0.24ms  med=   0.24ms  std=  0.01ms  min=   0.23ms  max=   0.28ms  total=    23.9ms
  encrypt (rc2_128_cbc, rsaes_oaep)             avg=   0.23ms  med=   0.23ms  std=  0.01ms  min=   0.23ms  max=   0.29ms  total=    23.4ms
  encrypt (rc4_128_cbc, rsaes_pkcs1v15)         avg=   0.19ms  med=   0.19ms  std=  0.01ms  min=   0.18ms  max=   0.29ms  total=    19.5ms
  encrypt (rc4_128_cbc, rsaes_oaep)             avg=   0.19ms  med=   0.19ms  std=  0.01ms  min=   0.18ms  max=   0.27ms  total=    19.1ms
  encrypt (aes_128_cbc, rsaes_pkcs1v15)         avg=   0.20ms  med=   0.19ms  std=  0.01ms  min=   0.19ms  max=   0.22ms  total=    19.6ms
  encrypt (aes_128_cbc, rsaes_oaep)             avg=   0.20ms  med=   0.20ms  std=  0.01ms  min=   0.19ms  max=   0.25ms  total=    19.9ms
  encrypt (aes_192_cbc, rsaes_pkcs1v15)         avg=   0.20ms  med=   0.20ms  std=  0.01ms  min=   0.19ms  max=   0.24ms  total=    20.0ms
  encrypt (aes_192_cbc, rsaes_oaep)             avg=   0.20ms  med=   0.19ms  std=  0.02ms  min=   0.19ms  max=   0.28ms  total=    20.0ms
  encrypt (aes_256_cbc, rsaes_pkcs1v15)         avg=   0.20ms  med=   0.20ms  std=  0.01ms  min=   0.19ms  max=   0.23ms  total=    19.9ms
  encrypt (aes_256_cbc, rsaes_oaep)             avg=   0.20ms  med=   0.19ms  std=  0.01ms  min=   0.19ms  max=   0.24ms  total=    19.5ms
  encrypt (tripledes_192_cbc, rsaes_pkcs1v15)   avg=   0.23ms  med=   0.23ms  std=  0.01ms  min=   0.22ms  max=   0.34ms  total=    23.0ms
  encrypt (tripledes_192_cbc, rsaes_oaep)       avg=   0.23ms  med=   0.22ms  std=  0.01ms  min=   0.22ms  max=   0.26ms  total=    22.6ms

[Decryption]
  decrypt (rc2_128_cbc, rsaes_pkcs1v15)         avg=   0.70ms  med=   0.67ms  std=  0.14ms  min=   0.64ms  max=   1.48ms  total=    70.1ms
  decrypt (rc2_128_cbc, rsaes_oaep)             avg=   0.71ms  med=   0.68ms  std=  0.13ms  min=   0.65ms  max=   1.47ms  total=    70.7ms
  decrypt (rc4_128_cbc, rsaes_pkcs1v15)         avg=   0.68ms  med=   0.65ms  std=  0.13ms  min=   0.63ms  max=   1.42ms  total=    68.0ms
  decrypt (rc4_128_cbc, rsaes_oaep)             avg=   0.70ms  med=   0.67ms  std=  0.14ms  min=   0.64ms  max=   1.59ms  total=    69.6ms
  decrypt (aes_128_cbc, rsaes_pkcs1v15)         avg=   0.69ms  med=   0.66ms  std=  0.15ms  min=   0.63ms  max=   1.43ms  total=    68.6ms
  decrypt (aes_128_cbc, rsaes_oaep)             avg=   0.69ms  med=   0.66ms  std=  0.13ms  min=   0.64ms  max=   1.41ms  total=    68.9ms
  decrypt (aes_192_cbc, rsaes_pkcs1v15)         avg=   0.68ms  med=   0.66ms  std=  0.13ms  min=   0.63ms  max=   1.46ms  total=    68.5ms
  decrypt (aes_192_cbc, rsaes_oaep)             avg=   0.70ms  med=   0.67ms  std=  0.13ms  min=   0.64ms  max=   1.46ms  total=    69.8ms
  decrypt (aes_256_cbc, rsaes_pkcs1v15)         avg=   0.69ms  med=   0.66ms  std=  0.14ms  min=   0.63ms  max=   1.47ms  total=    68.7ms
  decrypt (aes_256_cbc, rsaes_oaep)             avg=   0.70ms  med=   0.68ms  std=  0.13ms  min=   0.64ms  max=   1.46ms  total=    69.9ms
  decrypt (tripledes_192_cbc, rsaes_pkcs1v15)   avg=   0.72ms  med=   0.69ms  std=  0.13ms  min=   0.66ms  max=   1.49ms  total=    71.7ms
  decrypt (tripledes_192_cbc, rsaes_oaep)       avg=   0.72ms  med=   0.70ms  std=  0.13ms  min=   0.67ms  max=   1.46ms  total=    72.0ms

[End-to-End AS2 Message Build + Parse]
  plain message (build+parse)                   avg=   1.07ms  med=   0.99ms  std=  0.22ms  min=   0.89ms  max=   2.22ms  total=   106.8ms
  signed message (build+parse)                  avg=   5.20ms  med=   4.98ms  std=  0.72ms  min=   4.14ms  max=   7.32ms  total=   519.8ms
  encrypted message (build+parse)               avg=   4.20ms  med=   4.39ms  std=  0.67ms  min=   2.74ms  max=   5.62ms  total=   420.2ms
  signed+encrypted (build+parse)                avg=   7.61ms  med=   7.64ms  std=  0.71ms  min=   6.23ms  max=   9.77ms  total=   761.2ms
  signed+encrypted+compressed (build+parse)     avg=   8.25ms  med=   8.25ms  std=  1.16ms  min=   6.23ms  max=  15.84ms  total=   825.3ms

==========================================================================================
Total benchmark time: 4.4s
Backend: cryptography
==========================================================================================
```

### `oscrypto` backend

```
==========================================================================================
pyas2-lib Performance Benchmark  |  Backend: oscrypto  |  Iterations: 100
==========================================================================================

[Compression]
  compress                                      avg=   0.04ms  med=   0.04ms  std=  0.00ms  min=   0.04ms  max=   0.06ms  total=     4.3ms
  decompress                                    avg=   0.02ms  med=   0.02ms  std=  0.00ms  min=   0.02ms  max=   0.03ms  total=     1.9ms

[Signing]
  sign (pkcs1v15, sha256)                       avg=  11.72ms  med=  11.70ms  std=  0.55ms  min=  10.71ms  max=  13.33ms  total=  1172.1ms
  sign (pss, sha256)                            avg=  12.24ms  med=  12.06ms  std=  0.65ms  min=  11.31ms  max=  14.72ms  total=  1224.4ms
  sign (pkcs1v15, sha512)                       avg=  11.75ms  med=  11.65ms  std=  0.46ms  min=  11.01ms  max=  12.90ms  total=  1174.8ms
  sign (pss, sha512)                            avg=  11.81ms  med=  11.56ms  std=  0.66ms  min=  10.97ms  max=  13.78ms  total=  1180.8ms

[Verification]
  verify (pkcs1v15, sha256)                     avg=   0.76ms  med=   0.75ms  std=  0.04ms  min=   0.71ms  max=   0.90ms  total=    76.0ms
  verify (pss, sha256)                          avg=   0.21ms  med=   0.20ms  std=  0.02ms  min=   0.18ms  max=   0.26ms  total=    20.8ms

[Encryption]
  encrypt (rc2_128_cbc, rsaes_pkcs1v15)         avg=   0.47ms  med=   0.46ms  std=  0.03ms  min=   0.42ms  max=   0.60ms  total=    47.2ms
  encrypt (rc2_128_cbc, rsaes_oaep)             avg=   0.91ms  med=   0.90ms  std=  0.03ms  min=   0.86ms  max=   1.12ms  total=    90.8ms
  encrypt (rc4_128_cbc, rsaes_pkcs1v15)         avg=   0.40ms  med=   0.40ms  std=  0.02ms  min=   0.38ms  max=   0.56ms  total=    40.2ms
  encrypt (rc4_128_cbc, rsaes_oaep)             avg=   0.86ms  med=   0.86ms  std=  0.03ms  min=   0.81ms  max=   0.96ms  total=    86.4ms
  encrypt (aes_128_cbc, rsaes_pkcs1v15)         avg=   0.42ms  med=   0.41ms  std=  0.02ms  min=   0.39ms  max=   0.52ms  total=    41.7ms
  encrypt (aes_128_cbc, rsaes_oaep)             avg=   0.87ms  med=   0.86ms  std=  0.03ms  min=   0.83ms  max=   1.03ms  total=    86.5ms
  encrypt (aes_192_cbc, rsaes_pkcs1v15)         avg=   0.41ms  med=   0.41ms  std=  0.02ms  min=   0.39ms  max=   0.48ms  total=    40.9ms
  encrypt (aes_192_cbc, rsaes_oaep)             avg=   0.88ms  med=   0.87ms  std=  0.04ms  min=   0.82ms  max=   1.02ms  total=    88.1ms
  encrypt (aes_256_cbc, rsaes_pkcs1v15)         avg=   0.42ms  med=   0.41ms  std=  0.02ms  min=   0.39ms  max=   0.50ms  total=    41.5ms
  encrypt (aes_256_cbc, rsaes_oaep)             avg=   0.88ms  med=   0.87ms  std=  0.03ms  min=   0.80ms  max=   1.00ms  total=    88.0ms
  encrypt (tripledes_192_cbc, rsaes_pkcs1v15)   avg=   0.48ms  med=   0.46ms  std=  0.06ms  min=   0.43ms  max=   0.98ms  total=    47.8ms
  encrypt (tripledes_192_cbc, rsaes_oaep)       avg=   0.95ms  med=   0.93ms  std=  0.08ms  min=   0.85ms  max=   1.43ms  total=    95.0ms

[Decryption]
  decrypt (rc2_128_cbc, rsaes_pkcs1v15)         avg=  10.41ms  med=  10.09ms  std=  1.59ms  min=   9.67ms  max=  25.34ms  total=  1041.0ms
  decrypt (rc2_128_cbc, rsaes_oaep)             avg=  10.21ms  med=  10.18ms  std=  0.33ms  min=   9.57ms  max=  11.02ms  total=  1020.8ms
  decrypt (rc4_128_cbc, rsaes_pkcs1v15)         avg=  10.06ms  med=   9.95ms  std=  0.47ms  min=   9.56ms  max=  12.90ms  total=  1005.8ms
  decrypt (rc4_128_cbc, rsaes_oaep)             avg=  10.32ms  med=  10.23ms  std=  0.41ms  min=   9.80ms  max=  11.69ms  total=  1031.9ms
  decrypt (aes_128_cbc, rsaes_pkcs1v15)         avg=  10.24ms  med=  10.19ms  std=  0.37ms  min=   9.72ms  max=  12.26ms  total=  1024.1ms
  decrypt (aes_128_cbc, rsaes_oaep)             avg=  10.22ms  med=  10.10ms  std=  0.33ms  min=   9.88ms  max=  12.27ms  total=  1021.7ms
  decrypt (aes_192_cbc, rsaes_pkcs1v15)         avg=  10.00ms  med=   9.93ms  std=  0.27ms  min=   9.64ms  max=  10.80ms  total=  1000.2ms
  decrypt (aes_192_cbc, rsaes_oaep)             avg=  10.10ms  med=  10.01ms  std=  0.34ms  min=   9.58ms  max=  11.25ms  total=  1009.7ms
  decrypt (aes_256_cbc, rsaes_pkcs1v15)         avg=  10.01ms  med=   9.93ms  std=  0.44ms  min=   9.52ms  max=  13.67ms  total=  1000.8ms
  decrypt (aes_256_cbc, rsaes_oaep)             avg=  10.40ms  med=  10.27ms  std=  0.50ms  min=   9.83ms  max=  13.97ms  total=  1040.0ms
  decrypt (tripledes_192_cbc, rsaes_pkcs1v15)   avg=  10.16ms  med=  10.06ms  std=  0.38ms  min=   9.66ms  max=  11.72ms  total=  1015.7ms
  decrypt (tripledes_192_cbc, rsaes_oaep)       avg=  10.37ms  med=  10.20ms  std=  0.63ms  min=   9.74ms  max=  14.28ms  total=  1036.9ms

[End-to-End AS2 Message Build + Parse]
  plain message (build+parse)                   avg=   1.41ms  med=   1.39ms  std=  0.17ms  min=   1.04ms  max=   1.92ms  total=   141.2ms
  signed message (build+parse)                  avg=  17.03ms  med=  16.96ms  std=  0.70ms  min=  15.62ms  max=  18.59ms  total=  1702.7ms
  encrypted message (build+parse)               avg=  14.69ms  med=  14.64ms  std=  1.15ms  min=  12.76ms  max=  22.93ms  total=  1469.0ms
  signed+encrypted (build+parse)                avg=  30.28ms  med=  30.10ms  std=  1.00ms  min=  27.84ms  max=  33.11ms  total=  3027.6ms
  signed+encrypted+compressed (build+parse)     avg=  30.67ms  med=  30.53ms  std=  1.11ms  min=  29.00ms  max=  37.59ms  total=  3066.6ms

==========================================================================================
Total benchmark time: 27.3s
Backend: oscrypto
==========================================================================================
```

## How to Run

```bash
python benchmark.py
```

The script auto-detects which backend is installed and labels results accordingly.