"""Muse gateway client: HTTPS auth + WebSocket/Noise-XX transport + protobuf envelopes.

Derived from the muse.ai web app's own protocol (route table + framing observed
in its client bundle). Talks to the user's personal VM gateway directly.
Restricted derivative of nikships/muse-cli; fixed review/read routes only.
Session acquisition is outside this module; no browser or cookie export exists.
"""
import json
import os
import struct
import threading
import time
import urllib.parse
import uuid
import re
import base64

from .policy import authorize

from curl_cffi import requests as rq
from curl_cffi.requests import WebSocket
from noise.connection import NoiseConnection, Keypair
from google.protobuf import descriptor_pb2, descriptor_pool, message_factory

_HERE = os.path.dirname(os.path.abspath(__file__))
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/153.0.0.0 Safari/537.36")
GATEWAY_HOST = "hatch.metaaivm.com"

_pool = descriptor_pool.DescriptorPool()
for _i in (0, 1):
    _fd = descriptor_pb2.FileDescriptorProto()
    with open(os.path.join(_HERE, f"desc{_i}.bin.b64"), "r", encoding="ascii") as fh:
        _fd.ParseFromString(base64.b64decode(fh.read().strip(), validate=True))
    _pool.Add(_fd)


def _msg(name):
    return message_factory.GetMessageClass(_pool.FindMessageTypeByName(name))


NoiseTransportFrame = _msg("ingress_rev_proxy.NoiseTransportFrame")
ServiceRequest = _msg("hatch.noise.ServiceRequest")
ServiceResponse = _msg("hatch.noise.ServiceResponse")
ServiceFrame = _msg("hatch.noise.ServiceFrame")
ApplicationRequest = _msg("hatch.noise.ApplicationRequest")

SERVICE_IDS = {"daemon": 0}


class AuthError(RuntimeError):
    pass



class GatewayError(RuntimeError):
    def __init__(self, status, payload):
        super().__init__(f"Muse gateway returned status {status}; response body suppressed")
        self.status = status
        self.payload = payload


def _hatch_headers(cookies, access_token=None):
    h = {
        "User-Agent": UA,
        "Referer": "https://muse.ai/",
        "Origin": "https://muse.ai",
        "Sec-Fetch-Site": "same-origin",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Dest": "empty",
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Cookie": cookies,
    }
    if access_token:
        h["Authorization"] = f"Bearer {access_token}"
    return h


def fetch_access_token(cookies):
    r = rq.post("https://muse.ai/api/auth/check", headers=_hatch_headers(cookies),
                data=b"", impersonate="chrome", timeout=20, allow_redirects=False)
    if r.status_code != 200:
        raise AuthError(f"auth/check -> {r.status_code}; session renewal must be performed personally")
    return r.json()["access_token"]


def fetch_hatch_token(cookies, access_token, vm_id):
    r = rq.post(
        "https://muse.ai/api/hatch/token",
        headers=_hatch_headers(cookies, access_token),
        json={"vmAddress": f"wss://{vm_id}.metaaivm.com/", "vmName": vm_id},
        impersonate="chrome", timeout=20, allow_redirects=False,
    )
    if r.status_code != 200:
        raise AuthError(f"hatch/token -> {r.status_code}")
    return r.json()["token"]



def fetch_session_info(cookies):
    """Discover the user's assigned personal VM (id + gateway URL)."""
    r = rq.get("https://muse.ai/api/session", headers=_hatch_headers(cookies),
               impersonate="chrome", timeout=20, allow_redirects=False)
    if r.status_code != 200:
        raise AuthError(f"api/session -> {r.status_code} (cookies expired? re-export)")
    try:
        info = r.json()
    except ValueError:
        raise AuthError(f"api/session returned non-JSON (response body suppressed)")
    if "vm_id" not in info:
        raise GatewayError(-1, "Muse VM unavailable; inspect Muse personally before another attempt")
    return info


class Gateway:
    """One authenticated connection to the personal VM gateway."""

    def __init__(self, cookies, vm_id=None, access_token=None, hatch_token=None, allow_send=False):
        self.allow_send = allow_send
        if vm_id is None:
            vm_id = fetch_session_info(cookies)["vm_id"]
        if not isinstance(vm_id, str) or not re.fullmatch(r"[A-Za-z0-9-]{1,100}", vm_id):
            raise ValueError("invalid Muse VM id")
        self.vm_id = vm_id
        access_token = access_token or fetch_access_token(cookies)
        hatch_token = hatch_token or fetch_hatch_token(cookies, access_token, vm_id)
        url = (f"wss://{GATEWAY_HOST}/v1/noise?vm_id={vm_id}"
               f"&auth_token={urllib.parse.quote(hatch_token, safe='')}")
        self.ws = WebSocket()
        # verify=True is required: curl_cffi's WebSocket.connect defaults to
        # verify=None, which disables TLS certificate verification entirely.
        self.ws.connect(url, impersonate="chrome", timeout=20, verify=True)
        noise = NoiseConnection.from_name(b"Noise_XX_25519_AESGCM_SHA256")
        noise.set_as_initiator()
        noise.set_keypair_from_private_bytes(Keypair.STATIC, os.urandom(32))
        noise.start_handshake()
        self.ws.send_bytes(bytes(noise.write_message(b"")), timeout=20)
        m2, _ = self.ws.recv(timeout=20)
        noise.read_message(bytes(m2))
        self.ws.send_bytes(bytes(noise.write_message(b"")), timeout=20)
        assert noise.handshake_finished
        self.noise = noise
        self.stream = 1
        self._send_lock = threading.Lock()
        self._recv_lock = threading.Lock()

    # -- low-level framing -------------------------------------------------
    def _send_envelope(self, service_id, frame_bytes):
        outer = ServiceRequest(service=service_id, payload=frame_bytes)
        chunk_id = struct.unpack("<q", os.urandom(8))[0]
        fr = NoiseTransportFrame(chunk_id=chunk_id, chunk_index=0, total_chunks=1,
                                 payload=outer.SerializeToString())
        with self._send_lock:
            self.ws.send_bytes(bytes(self.noise.encrypt(fr.SerializeToString())), timeout=20)

    def _read_frame(self, timeout=20):
        # Serialized so two threads can never interleave ws.recv / Noise
        # decrypt (which corrupts the transport state -> BAD_DECRYPT).
        # Callers must still avoid *logical* races: only one thread should
        # be consuming frames at a time, or responses get misrouted.
        with self._recv_lock:
            data, _flags = self.ws.recv(timeout=timeout)
            if len(data) > 8_000_000:
                raise GatewayError(-1, "gateway frame exceeds limit")
            pt = bytes(self.noise.decrypt(bytes(data)))
        ntf = NoiseTransportFrame()
        ntf.ParseFromString(pt)
        sr = ServiceResponse()
        sr.ParseFromString(ntf.payload)
        sf = ServiceFrame()
        sf.ParseFromString(sr.payload)
        return sf

    def _open(self, method, path_params=None, body=None, query=None, route=None):
        if route is not None or path_params or query:
            raise PermissionError("custom routes and query overrides are disabled")
        verb, path = authorize(method, body, allow_send=self.allow_send)
        route = {"http": verb, "path": path}
        if method == 'markdown.read':
            body = None  # Validated reference is already encoded in the fixed read path.
        if verb == "GET":
            query, body = body, None
        for k, v in (path_params or {}).items():
            path = path.replace("{" + k + "}", urllib.parse.quote(str(v), safe=""))
        if query:
            qs = urllib.parse.urlencode({k: v for k, v in query.items() if v is not None})
            if qs:
                path = path + ("&" if "?" in path else "?") + qs
        raw = b"" if body is None else (body if isinstance(body, bytes) else json.dumps(body).encode())
        req = ApplicationRequest(verb=route["http"], path=path, body=raw, end_body=True)
        h = req.headers.add()
        h.key = "x-request-id"
        h.value = str(uuid.uuid4())
        if raw:
            h2 = req.headers.add()
            h2.key = "content-type"
            h2.value = "application/json"
        frame = ServiceFrame(stream_id=self.stream)
        frame.request.CopyFrom(req)
        sid = self.stream
        self.stream += 1
        self._send_envelope(SERVICE_IDS.get(route.get("service", "daemon"), 0),
                            frame.SerializeToString())
        return sid

    # -- unary request/response --------------------------------------------
    def submit_review(self, body, timeout=20):
        """Wait for this stream's response headers; acceptance is not completion.

        A missing response is uncertain and must never trigger an automatic resend.
        Error payloads are not returned because they may contain private content.
        """
        sid = self._open('chat.stream', body=body)
        deadline = time.monotonic() + timeout
        for _ in range(1000):
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                break
            frame = self._read_frame(timeout=remaining)
            if frame.stream_id != sid:
                continue
            kind = frame.WhichOneof('kind')
            if kind == 'reset':
                raise GatewayError(-1, 'review stream reset before acceptance')
            if kind == 'response':
                status = frame.response.status
                if not 200 <= status < 300:
                    raise GatewayError(status, 'review stream rejected; private response body suppressed')
                return {'acknowledged': True, 'status': status, 'stream_id': sid}
        raise TimeoutError('Muse did not acknowledge this review stream')

    def request(self, method, path_params=None, body=None, query=None, timeout=30, route=None):
        sid = self._open(method, path_params, body, query, route=route)
        status, chunks, deadline = None, [], time.monotonic() + timeout
        complete, received, frames = False, 0, 0
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                break
            sf = self._read_frame(timeout=remaining)
            frames += 1
            if frames > 1000:
                raise GatewayError(-1, "gateway response exceeds frame limit")
            if sf.stream_id != sid:
                continue
            kind = sf.WhichOneof("kind")
            if kind == "response":
                status = sf.response.status
                if sf.response.body:
                    chunks.append(bytes(sf.response.body))
                    received += len(sf.response.body)
                if sf.response.end_body:
                    complete = True
                    break
            elif kind == "body_chunk":
                chunks.append(bytes(sf.body_chunk.data))
                received += len(sf.body_chunk.data)
                if sf.body_chunk.end_body:
                    complete = True
                    break
            elif kind == "reset":
                raise GatewayError(-1, f"stream reset {sf.reset.code}: {sf.reset.reason}")
            if received > (1_000_000 if method == 'markdown.read' else 8_000_000):
                raise GatewayError(-1, "gateway response exceeds byte limit")
        if status is None or not complete:
            raise TimeoutError(f"incomplete response for {method}")
        payload = b"".join(chunks)
        if len(payload) > (1_000_000 if method == 'markdown.read' else 8_000_000):
            raise GatewayError(-1, "gateway response exceeds byte limit")
        if status < 200 or status >= 300:
            raise GatewayError(status, payload[:500].decode("utf-8", "replace"))
        return payload

    def call_json(self, method, path_params=None, body=None, query=None, timeout=30):
        raw = self.request(method, path_params, body, query, timeout)
        try:
            d = json.loads(raw) if raw else {}
        except json.JSONDecodeError:
            raise GatewayError(-1, f"non-JSON response: {raw[:200]!r}")
        if isinstance(d, dict) and d.get("ok") is False:
            raise GatewayError(-1, f"api error: {d.get('error')}")
        return d.get("result", d) if isinstance(d, dict) else d

    def close(self):
        try:
            self.ws.close()
        except Exception:  # noqa: BLE001
            pass
