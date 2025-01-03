# localhost-proxy

This project is only in experimental stages. A easier way to setup this would probably be to use [localtunnel](https://github.com/localtunnel/) - although I would like to get this to work using only the ssh-client.

-------------------

A simple ssh server that allows you to proxy localhost and get a public URL for it.

## Server Setup

Setup a docker-compose file with two secrets: `ssh_host_key` and `ssh_password`. 

The `ssh_host_key` should be a private key that can be used to authenticate the server. Example command to generate it is:
```bash
openssl genpkey -algorithm RSA -out ssh_host_key -pkeyopt rsa_keygen_bits:2048
```

The `ssh_password` should be a clear-text password that the client will use to authenticate with the server.

## Client Usage

## Inspiration/Credits

Inspired by [localhost.run](https://localhost.run/).

Made by [Elias Lundell](https://eliaslundell.se).
