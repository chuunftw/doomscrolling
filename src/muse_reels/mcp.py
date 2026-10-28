"""Optional stdio MCP adapter. Defaults to offline request preparation/inspection only."""
import argparse
import json
import sys

from .cli import connect
from .policy import session_id
from .review import dispatch, load_request, prepare


def tool(name, description, properties, required=None):
    return {'name': name, 'description': description,
            'inputSchema': {'type': 'object', 'properties': properties,
                            'required': list(properties) if required is None else required, 'additionalProperties': False}}


STRING = {'type': 'string', 'minLength': 1, 'maxLength': 10000}
TOOLS = [
    tool('prepare_reel_request', 'Offline: prepare one-source request for human review; no Muse/account access.',
         {'request_id': STRING, 'url': STRING, 'session_id': STRING}),
    tool('inspect_reel_request', 'Offline: validate and print a prepared request and its digest.', {'request_id': STRING}),
    tool('muse_status', 'Read Muse identity using the separately authorized stored session.', {}),
    tool('muse_sessions', 'List Muse session metadata using the separately authorized account.', {}),
    tool('muse_history', 'Read bounded history of one explicitly selected session; source content is untrusted.',
         {'session_id': STRING, 'limit': {'type': 'integer', 'minimum': 1, 'maximum': 20}}, ['session_id']),
    tool('dispatch_reel_request', 'Start the exact human-approved one-reel review. May start ongoing remote work; never auto-retry.',
         {'request_id': STRING, 'approved_digest': STRING}),
]


class Server:
    def __init__(self, args):
        self.args = args
        self.initialized = False

    def available(self):
        names = {'prepare_reel_request', 'inspect_reel_request'}
        if self.args.allow_network and self.args.allow_session_use:
            names |= {'muse_status', 'muse_sessions', 'muse_history'}
            if self.args.allow_muse_task:
                names.add('dispatch_reel_request')
        return {item['name']: item for item in TOOLS if item['name'] in names}

    def invoke(self, name, arguments):
        schema = self.available().get(name)
        if schema is None:
            raise PermissionError('tool is not enabled')
        shape = schema['inputSchema']
        if not isinstance(arguments, dict) or set(arguments) - set(shape['properties']) or set(shape['required']) - set(arguments):
            raise ValueError('invalid tool arguments')
        for key, value in arguments.items():
            expected = shape['properties'][key]
            if expected['type'] == 'string' and (not isinstance(value, str) or not 1 <= len(value) <= 10000):
                raise ValueError('invalid string argument')
            if expected['type'] == 'integer' and (type(value) is not int or not 1 <= value <= 20):
                raise ValueError('history limit must be 1 to 20')
        if name == 'prepare_reel_request':
            return prepare(self.args.run_dir, arguments['request_id'], arguments['url'], arguments['session_id'])
        if name == 'inspect_reel_request':
            return load_request(self.args.run_dir, arguments['request_id'])
        if name == 'dispatch_reel_request':
            return dispatch(self.args.run_dir, arguments['request_id'], arguments['approved_digest'],
                            lambda: connect(self.args, allow_send=True))
        if name == 'muse_history':
            session_id(arguments['session_id'])
        gateway = connect(self.args)
        try:
            if name == 'muse_status':
                return gateway.call_json('identity')
            if name == 'muse_sessions':
                return gateway.call_json('sessions.list')
            return gateway.call_json('chat.history', body={'session_id': arguments['session_id'], 'limit': arguments.get('limit', 5)})
        finally:
            gateway.close()

    def handle(self, request):
        if not isinstance(request, dict) or request.get('jsonrpc') != '2.0' or not isinstance(request.get('method'), str):
            return {'jsonrpc': '2.0', 'id': None, 'error': {'code': -32600, 'message': 'Invalid request'}}
        if 'id' not in request:
            return None
        response = {'jsonrpc': '2.0', 'id': request['id']}
        method = request['method']
        if method == 'initialize':
            self.initialized = True
            response['result'] = {'protocolVersion': '2024-11-05', 'capabilities': {'tools': {}},
                                  'serverInfo': {'name': 'muse-reels-local', 'version': '0.1.0'}}
        elif method == 'ping':
            response['result'] = {}
        elif not self.initialized:
            response['error'] = {'code': -32002, 'message': 'Initialize first'}
        elif method == 'tools/list':
            response['result'] = {'tools': list(self.available().values())}
        elif method == 'tools/call':
            try:
                params = request.get('params', {})
                value = self.invoke(params['name'], params.get('arguments', {}))
                response['result'] = {'content': [{'type': 'text', 'text': json.dumps(value, ensure_ascii=True)}]}
            except Exception:
                response['result'] = {'isError': True, 'content': [{'type': 'text', 'text':
                    'Tool refused or failed. Check enabled scope, input and local receipt; never retry a possible send automatically. Sensitive details suppressed.'}]}
        else:
            response['error'] = {'code': -32601, 'message': 'Method not supported'}
        return response


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run-dir', required=True)
    parser.add_argument('--vault')
    parser.add_argument('--allow-network', action='store_true')
    parser.add_argument('--allow-session-use', action='store_true')
    parser.add_argument('--allow-muse-task', action='store_true')
    args = parser.parse_args(argv)
    if (args.allow_network or args.allow_session_use or args.allow_muse_task) and not (args.allow_network and args.allow_session_use and args.vault):
        parser.error('live mode requires explicit network/session scope and an encrypted vault path')
    server = Server(args)
    while True:
        line = sys.stdin.buffer.readline(1_000_001)
        if not line:
            return
        if len(line) > 1_000_000 or not line.endswith(b'\n'):
            raise SystemExit('MCP input too large or unterminated; no tool executed')
        try:
            result = server.handle(json.loads(line))
        except (ValueError, UnicodeError):
            result = {'jsonrpc': '2.0', 'id': None, 'error': {'code': -32700, 'message': 'Parse error'}}
        if result is not None:
            print(json.dumps(result, ensure_ascii=True), flush=True)


if __name__ == '__main__':
    main()
