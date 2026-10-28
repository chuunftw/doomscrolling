"""Retrieve only selected-source generated Markdown; never execute its contents."""
import hashlib
import json
import re
from pathlib import PurePosixPath

from .policy import markdown_ref
from .review import load_request
from .storage import beneath


def markdown_resources(event):
    payload = event.get('payload') or {}
    if not isinstance(payload, dict):
        return []
    found = set()

    def add(item):
        if isinstance(item, dict):
            if item.get('missing'):
                return
            variants = item.get('variants')
            item = item.get('path') or (variants.get('original') if isinstance(variants, dict) else None)
        try:
            found.add(markdown_ref(item))
        except ValueError:
            pass

    for resources in (event.get('resources'), payload.get('resources')):
        if isinstance(resources, list):
            for item in resources:
                add(item)
    data = payload.get('data')
    if isinstance(data, dict):
        add(data.get('file'))
        for items in data.values():
            if isinstance(items, list):
                for item in items:
                    add(item)
    for text in (payload.get('content'), payload.get('display_text'), payload.get('fallback_text'),
                 data.get('fallback_text') if isinstance(data, dict) else None):
        if isinstance(text, str):
            for ref in re.findall(r'sandbox://[^\s)<>"\]]+', text):
                add(ref)
    return sorted(found)


def collect_markdown(root, request_id, connect, filename=None):
    """Bounded selected-chat read, verified source association, immutable local copies.

    An exact user-selected filename may identify a later follow-up in the same chat;
    automatic discovery stops at the next user turn. Neither path guesses remote files.
    """
    document = load_request(root, request_id)
    if filename is not None:
        markdown_ref('sandbox://workspace/' + filename)
        if '/' in filename:
            raise ValueError('select a filename, not a path')
    links = {document['source'].replace('/p/', '/reel/'), document['source'].replace('/reel/', '/p/')}
    gateway = connect()
    try:
        data = gateway.call_json('chat.history', body={'session_id': document['session_id'], 'limit': 20})
        events = data.get('chat_events') if isinstance(data, dict) else None
        if not isinstance(events, list):
            return {'files': [], 'state': 'history-unrecognized'}
        candidates = set()
        active = False
        target = None
        for event in sorted((e for e in events if isinstance(e, dict)),
                            key=lambda e: e.get('seq') if type(e.get('seq')) is int else 0):
            payload = event.get('payload') or {}
            if not isinstance(payload, dict):
                continue
            text = payload.get('display_text') or payload.get('content') or ''
            if event.get('event_name') == 'message.user' or payload.get('role') == 'user':
                active = isinstance(text, str) and ' '.join(text.split()) == ' '.join(document['prompt'].split())
                if active:
                    target = event.get('message_id') or payload.get('message_id')
                continue
            if event.get('event_name') != 'message.assistant' and not (
                    event.get('event_name') == 'delta.presentation' and payload.get('kind') == 'file'):
                continue
            refs = markdown_resources(event)
            if filename is not None:
                candidates.update(ref for ref in refs if PurePosixPath(ref).name == filename)
            elif active:
                reply_to = event.get('reply_to_message_id') or payload.get('reply_to_message_id')
                if not reply_to or reply_to == target or (isinstance(text, str) and any(link in text for link in links)):
                    candidates.update(refs)
        if len(candidates) > 5:
            raise ValueError('too many Markdown artifacts; select an exact filename')
        files = []
        for ref in sorted(candidates):
            raw = gateway.request('markdown.read', body={'ref': ref}, timeout=30)
            if not isinstance(raw, bytes) or len(raw) > 1_000_000:
                raise ValueError('Markdown exceeds the byte limit')
            text = raw.decode('utf-8-sig')
            if '\x00' in text or not any(link in text for link in links):
                raise ValueError('artifact is not UTF-8 Markdown associated with the selected source')
            sha = hashlib.sha256(raw).hexdigest()
            dest = beneath(root, 'artifacts/' + request_id + '/' + sha + '.md')
            dest.parent.mkdir(parents=True, exist_ok=True)
            if dest.exists():
                if dest.read_bytes() != raw:
                    raise ValueError('existing artifact differs; no overwrite allowed')
            else:
                with dest.open('xb') as output:
                    output.write(raw)
            metadata = {'request_id': request_id, 'source': document['source'],
                        'remote_ref': ref, 'original_filename': PurePosixPath(ref).name,
                        'sha256': sha, 'bytes': len(raw), 'provenance': 'Muse generated Markdown; not creator original skill',
                        'source_association': 'explicit selected filename and source link' if filename else 'selected request window and source link',
                        'content_verified': False, 'skill_installed': False}
            sidecar = beneath(root, 'artifacts/' + request_id + '/' + sha + '.json')
            if not sidecar.exists():
                with sidecar.open('x', encoding='utf-8') as output:
                    json.dump(metadata, output, indent=2)
            files.append({'path': str(dest), 'original_filename': metadata['original_filename'],
                          'sha256': sha, 'bytes': len(raw), 'content_verified': False})
        return {'files': files, 'state': 'saved' if files else 'no-linked-markdown-in-recent-history',
                'note': 'Original bytes preserved. Untrusted report; no skill created or installed. No task sent.'}
    finally:
        gateway.close()
