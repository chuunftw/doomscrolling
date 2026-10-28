"""Prepare fixed one-source requests; record attempts before any possible network send."""
import hashlib
import json
import secrets
from pathlib import Path

from .policy import identifier, reel_prompt, session_id, source_url
from .storage import beneath, write_json

FIELDS = {'version', 'request_id', 'source', 'session_id', 'prompt', 'sha256'}


def digest(document):
    value = {key: item for key, item in document.items() if key != 'sha256'}
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(',', ':')).encode()).hexdigest()


def load_request(root, request_id):
    path = beneath(root, 'requests/' + identifier(request_id) + '.json')
    if path.stat().st_size > 50_000:
        raise ValueError('request file exceeds size limit')
    document = json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(document, dict) or set(document) != FIELDS or document['version'] != 1:
        raise ValueError('unsupported request schema')
    if document['request_id'] != request_id:
        raise ValueError('request id does not match file')
    session_id(document['session_id'])
    if document['source'] != source_url(document['source']) or document['prompt'] != reel_prompt(document['source']):
        raise ValueError('request contains an unsupported URL or prompt')
    if document['sha256'] != digest(document):
        raise ValueError('request digest mismatch')
    return document


def prepare(root, request_id, url, thread):
    request_id = identifier(request_id)
    url, thread = source_url(url), session_id(thread)
    path = beneath(root, 'requests/' + request_id + '.json')
    document = {'version': 1, 'request_id': request_id, 'source': url, 'session_id': thread, 'prompt': reel_prompt(url)}
    document['sha256'] = digest(document)
    if path.exists():
        raise FileExistsError('request already exists; inspect it rather than overwriting it')
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x', encoding='utf-8') as output:
        json.dump(document, output, indent=2, ensure_ascii=False)
    return document


def dispatch(root, request_id, approved_digest, connect):
    document = load_request(root, request_id)
    if not secrets.compare_digest(str(approved_digest), document['sha256']):
        raise PermissionError('approve the exact digest printed by prepare/inspect before dispatch')
    receipt = beneath(root, 'receipts/' + request_id + '.json')
    receipt.parent.mkdir(parents=True, exist_ok=True)
    # Exclusive create before connect/send. A timeout never automatically retries
    # a request which may already have reached the remote agent.
    with receipt.open('x', encoding='utf-8') as output:
        json.dump({'state': 'attempt-started', 'request_id': request_id, 'sha256': approved_digest}, output)
    gateway = None
    try:
        gateway = connect()
        gateway._open('chat.stream', body={
            'session_id': document['session_id'], 'node_id': 'reels-' + secrets.token_hex(8),
            'capabilities': {}, 'items': [{'type': 'text', 'text': document['prompt']}]})
        result = {'state': 'sent-unconfirmed', 'request_id': request_id, 'sha256': approved_digest,
                  'session_id': document['session_id'],
                  'note': 'Transport sent bytes. Server acceptance/completion is not proven. Read the selected session before any retry.'}
        write_json(receipt, result)
        return result
    except Exception:
        write_json(receipt, {'state': 'uncertain', 'request_id': request_id, 'sha256': approved_digest,
                             'note': 'No automatic retry. Inspect the selected Muse session; a task may have started.'})
        raise RuntimeError('Dispatch did not finish cleanly. Inspect the local receipt and Muse before retrying; sensitive error details suppressed.') from None
    finally:
        if gateway:
            gateway.close()
