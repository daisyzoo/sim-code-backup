"""Local PI0.5 policy RPC shared by paired evaluation."""
import pickle
import socket
import struct


def request(host, port, payload, timeout=90.):
    blob = pickle.dumps(payload, protocol=pickle.HIGHEST_PROTOCOL)
    with socket.create_connection((host, port), timeout=timeout) as conn:
        conn.settimeout(timeout)
        conn.sendall(struct.pack('!I', len(blob)) + blob)
        def read_exact(size):
            result = bytearray()
            while len(result) < size:
                chunk = conn.recv(size - len(result))
                if not chunk:
                    raise ConnectionError('PI0.5 server closed before complete response')
                result.extend(chunk)
            return bytes(result)
        size = struct.unpack('!I', read_exact(4))[0]
        reply = pickle.loads(read_exact(size))
        if not reply.get('ok'):
            raise RuntimeError(reply.get('error', 'policy request failed'))
        return reply
