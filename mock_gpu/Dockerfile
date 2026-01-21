FROM python:3.9-slim-bookworm

# Install SSH Server, Wget, Curl, Ping
RUN apt-get update && apt-get install -y openssh-server wget curl iputils-ping nano && mkdir -p /var/run/sshd

# Configure SSH
RUN sed -i 's/#PermitRootLogin prohibit-password/PermitRootLogin yes/' /etc/ssh/sshd_config
RUN sed -i 's/#PasswordAuthentication yes/PasswordAuthentication no/' /etc/ssh/sshd_config

# Setup Root User .ssh
WORKDIR /root
RUN mkdir -p .ssh && chmod 700 .ssh

# Install demo SSH key pair (matches what backend/routes/demo.py returns)
RUN echo "-----BEGIN RSA PRIVATE KEY-----\n\
    MIIEpAIBAAKCAQEAw01ykx/OEP8vY1E6YxIcNQ0o8egURbxuLWbPTfKt/L6GjC79\n\
    yW76LLIyFPAwaI0wS2S0XP4JpVobjkcZGb2KVuLiOPjgWt9sEajSwt9IZjukz88k\n\
    uSz15JbTbDFcO35S1BB7MQ8R5x8GbwEo4WSAygXv00AKs46NdD/H5ldBRqrHgBjb\n\
    rN3eYCzmSQI8XBzlQJCu4hjyyDeNvm9xxVBj+iFko7R3VEZK3qjW0BlOmjbuE03x\n\
    WavN/cLrBVBg/I2Ejs4ircL8nGuStpOW6lR0PBb6CvdHSIeXJOCCk7mGNImtpITU\n\
    PhEsHCcvB7AkJSKMGdzR5HLOMI5JSmO65G7gkwIDAQABAoIBAEfybQX0DobGa1+s\n\
    GdVLY6bLjUzokSdLjk8dc7skbqIQUiKsYQPm5TS4BKkf/sVVVfhARg2H7GfEtSgJ\n\
    2x5Xa/IsLOiODqCLdBVhWxs9BD/dMw73IXEyNfea9JID8RVdqQfEdo2RHqhFDqqw\n\
    A65cxvEllL7+9bJGDqhHos2hUUPFmmx13BgL7gTdWCvmVDa2ZiLBwFOcdTaVphoM\n\
    vy2Nyuy9KAovv7go/QF7Cyzt1Cucw2gIkdyJWRdQPpfyR84+gSQGzCuLzFUwmf9b\n\
    4g+cx5NBdVyJsnvaESncFRsFjpgpC4zBGCU1P3ScsA2MzcslFVJct1IkqQ5cafsX\n\
    D1viFwECgYEA+dIrhRqbkbt/Gi+DKemGOHUP6GJzWOkn+fnCacdXKidlbLxK288l\n\
    D/0kF5UNTSEv86AlqvE4bVoCY+hcE07N5DMtZYsvFmT9k4OfQPsZVyGw0e7Ig3W5\n\
    C4lVK/ZVNadyIKUXOPww8ci5eEnKoZy1ikFujB/F9ijMfizUcvn72IECgYEAyCIT\n\
    H4Td1KVSZRLSTDGamZG0YbVoqihoGTSr6lomZENn8t0Y+sWqbUDNC5N4JlCxOkur\n\
    kYsO6dTHboAZJzbb5CanTN9PPjRS1Cjvdter8YMF90U9HzAZ31Kp9ioVHwvkbzb2\n\
    Xw7hKh1ZaWW9mvbBo6kYrIc0+tzO0kyeFtfuTxMCgYAglY0fm0zXQUFexPuyp8bd\n\
    7kbY5J5u5lpUfIMjEOEJmoHcIOMSsH4BC999Q++sM7vxZt4C4dueR7MwHMqFqi2o\n\
    qhQtvm2x2hJI/03yR84SU06g0yhMHTq5inwVc9fBW8nDAEV7JUms/6VRTy6izbHQ\n\
    CqDEnhBP/xpNCsPbC0gSAQKBgCoccWWqcXrzJnk6EqIRtfQmYoxEvbdANVdIa/wt\n\
    5/Ik9NR3jXAG86t1fS+4Ygm95OzdS0aeug6dxTENJz3HH1HMiFt2iZgPLnaR/oFF\n\
    NFrnNPQoz4mmd2s0W6r+g986g2Cbcg/ic6KG9m9lBxZ6YZhsVlLHSHCY0bQShxlL\n\
    akudAoGBAMK8fUvSwQlfLsw8EwYppuKPELd2znH/cFUZySi2gNqnKWIToBUM0i7w\n\
    1vBtzEWzKpT7OoOsb3ZKtLxpvjxL057i6VKBwwDjgJJGAnmuGgzzCYbkDa5j0M+S\n\
    qvddffu8CeMDo7e2nYa/7VgxcDQfFGspx9gnV0iojEFVi1jXzTD8\n\
    -----END RSA PRIVATE KEY-----" | tr -d '\n' | sed 's/\\n/\n/g' > /root/.ssh/id_rsa && \
    chmod 600 /root/.ssh/id_rsa && \
    ssh-keygen -y -f /root/.ssh/id_rsa > /root/.ssh/authorized_keys && \
    chmod 600 /root/.ssh/authorized_keys

# Expose SSH Port
EXPOSE 22

# Start SSH Daemon
CMD ["/usr/sbin/sshd", "-D"]
