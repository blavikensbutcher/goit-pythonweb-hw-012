

``How to generate private key``

```shell
# Generate an RSA private key, of size 2048
openssl genrsa -out certs/jwt-private.pem 2048
```

```shell
# Extract the public key from the key pair, which can be used in a certificate
openssl rsa -in certs/jwt-private.pem -outform PEM -pubout -out certs/jwt-public.pem
```
