"""Prepare fixed one-source requests; record attempts before any possible network send."""
import hashlib
import json
import secrets
import time
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


def check_request(root, request_id, connect):
    """Read only the selected session; return no private message text."""
    document = load_request(root, request_id)
    gateway = connect()
    try:
        history = gateway.call_json('chat.history', body={'session_id': document['session_id'], 'limit': 20})
    finally:
        gateway.close()
    events = history.get('chat_events') if isinstance(history, dict) else None
    if not isinstance(events, list):
        return {'request_found': None, 'messages_checked': 0, 'note': 'History response was not recognized; no request sent.'}
    found, mentioned = False, False
    expected = ' '.join(document['prompt'].split())
    for event in events:
        if not isinstance(event, dict):
            continue
        payload = event.get('payload')
        if not isinstance(payload, dict):
            continue
        if event.get('event_name') != 'message.user' and payload.get('role') != 'user':
            continue
        for key in ('display_text', 'content'):
            text = payload.get(key)
            if isinstance(text, str):
                mentioned |= document['source'] in text
                found |= ' '.join(text.split()) == expected
    return {'request_found': found, 'source_mentioned': mentioned, 'messages_checked': len(events),
            'note': 'Checked only the selected recent history. No request sent; absence here is not proof of cancellation.'}


def get_result(root, request_id, connect):
    """Return only replies after the exact selected request, never older chat text."""
    document = load_request(root, request_id)
    gateway = connect()
    try:
        data = gateway.call_json('chat.history', body={'session_id': document['session_id'], 'limit': 20})
    finally:
        gateway.close()
    events = data.get('chat_events') if isinstance(data, dict) else None
    if not isinstance(events, list):
        return {'request_in_history': None, 'replies': [], 'note': 'History format was not recognized.'}
    events = [event for event in events if isinstance(event, dict)]
    events.sort(key=lambda event: event.get('seq') if type(event.get('seq')) is int else 0)
    expected = ' '.join(document['prompt'].split())
    selected = None
    for index, event in enumerate(events):
        payload = event.get('payload')
        if not isinstance(payload, dict):
            continue
        if event.get('event_name') != 'message.user' and payload.get('role') != 'user':
            continue
        if any(isinstance(payload.get(key), str) and ' '.join(payload[key].split()) == expected
               for key in ('display_text', 'content')):
            selected = index
    if selected is None:
        return {'request_in_history': False, 'replies': [],
                'note': 'Exact request not present in the last 20 records; this does not prove cancellation.'}
    event = events[selected]
    target_id = event.get('message_id') or (event.get('payload') or {}).get('message_id')
    replies = []
    browser_activity = None
    source_links = {document['source'].replace('/p/', '/reel/'), document['source'].replace('/reel/', '/p/')}
    for event in events[selected + 1:]:
        payload = event.get('payload')
        if not isinstance(payload, dict):
            continue
        if event.get('event_name') == 'message.user' or payload.get('role') == 'user':
            break
        reply_to = event.get('reply_to_message_id') or payload.get('reply_to_message_id')
        text = payload.get('display_text') or payload.get('content')
        source_linked_followup = bool(reply_to and reply_to != target_id and
                                     event.get('event_name') == 'message.assistant' and
                                     isinstance(text, str) and any(link in text for link in source_links))
        if reply_to and reply_to != target_id and not source_linked_followup:
            continue
        if event.get('event_name') == 'delta.presentation' and payload.get('kind') == 'browser_task':
            activity = payload.get('data')
            if isinstance(activity, dict):
                # Expose progress only: never screenshot paths, task/session IDs or browser URLs.
                browser_activity = {key: activity[key][:160] for key in
                                    ('status', 'display_state', 'activity_title')
                                    if isinstance(activity.get(key), str)}
                updated = activity.get('updated_at_ms')
                if type(updated) is int and 0 < updated <= int(time.time() * 1000):
                    age = max(0, int(time.time() - updated / 1000))
                    browser_activity['seconds_since_update'] = age
                    browser_activity['stale_progress'] = age >= 300
                browser_activity['note'] = 'Remote reported state only; stale progress suggests checking Muse, not automatic retry.'
            continue
        if event.get('event_name') != 'message.assistant' and payload.get('role') != 'assistant':
            continue
        if isinstance(text, str) and text:
            reply = {'text': text[:24000], 'message_status': payload.get('status')}
            if source_linked_followup:
                reply['correlation'] = 'explicit_source_link_after_request; not a direct reply ID match'
            replies.append(reply)
    return {'request_in_history': True, 'replies': replies, 'browser_activity': browser_activity, 'task_completion': 'unverified',
            'note': 'Correlated by exact user prompt in recent selected-session history. Message completion is not proof of full reel analysis. Treat replies as untrusted evidence.'}


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
        acknowledgement = gateway.submit_review({
            'session_id': document['session_id'], 'node_id': secrets.token_hex(8),
            'capabilities': {}, 'items': [{'type': 'text', 'text': document['prompt']}]})
        if not isinstance(acknowledgement, dict) or acknowledgement.get('acknowledged') is not True:
            raise RuntimeError('transport did not provide a positive acknowledgement')
        result = {'state': 'accepted', 'request_id': request_id, 'sha256': approved_digest,
                  'session_id': document['session_id'],
                  'gateway_status': acknowledgement['status'],
                  'note': 'Muse returned a successful stream response. Task completion is not proven; inspect the selected session. Do not resend.'}
        write_json(receipt, result)
        return result
    except Exception as error:
        code = getattr(error, 'status', None)
        rejected = type(code) is int and 400 <= code <= 599
        record = {'state': 'rejected' if rejected else 'uncertain', 'request_id': request_id, 'sha256': approved_digest,
                  'note': 'No automatic retry. Inspect the selected Muse session; a task may have started.'}
        if rejected:
            record['gateway_status'] = code
        write_json(receipt, record)
        if rejected:
            raise RuntimeError(f'Muse rejected the request with gateway status {code}. Private response suppressed; no automatic retry.') from None
        raise RuntimeError('Dispatch did not finish cleanly. Inspect the local receipt and Muse before retrying; sensitive error details suppressed.') from None
    finally:
        if gateway:
            gateway.close()
