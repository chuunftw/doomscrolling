"""Offline by default. No installer, updater, browser access, cookie export or generic send."""
import argparse
import getpass
import json
import sys
import warnings
from pathlib import Path

from . import __version__
from .policy import session_id
from .review import check_request, dispatch, load_request, prepare
from .storage import load_cookie, save_cookie


def connect(args, allow_send=False):
    if not args.allow_network or not args.allow_session_use:
        raise PermissionError('account access requires --allow-network and --allow-session-use')
    # No account/credential work at import or help time; no implicit dependency installation.
    from .gateway import Gateway
    return Gateway(load_cookie(args.vault), allow_send=allow_send)


def emit(value):
    print(json.dumps(value, indent=2, ensure_ascii=True))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--version', action='version', version=__version__)
    sub = parser.add_subparsers(dest='mode', required=True)
    stage = sub.add_parser('prepare', help='write a one-source request for review; no account use')
    stage.add_argument('url')
    stage.add_argument('--session', required=True)
    stage.add_argument('--id', required=True)
    stage.add_argument('--run-dir', required=True)
    inspect = sub.add_parser('inspect', help='validate and print a prepared request')
    inspect.add_argument('--id', required=True)
    inspect.add_argument('--run-dir', required=True)
    auth = sub.add_parser('auth-store', help='user-entered hatch_sess value, Windows DPAPI; no browser automation')
    auth.add_argument('--vault', required=True)
    auth.add_argument('--allow-credential-storage', action='store_true')
    auth.add_argument('--replace', action='store_true')
    for mode in ('status', 'sessions', 'history', 'check', 'dispatch'):
        child = sub.add_parser(mode)
        child.add_argument('--vault', required=True)
        child.add_argument('--allow-network', action='store_true')
        child.add_argument('--allow-session-use', action='store_true')
        if mode == 'history':
            child.add_argument('--session', required=True)
            child.add_argument('--limit', type=int, default=5)
        if mode in ('check', 'dispatch'):
            child.add_argument('--run-dir', required=True)
            child.add_argument('--id', required=True)
        if mode == 'dispatch':
            child.add_argument('--approve', required=True, help='exact reviewed request digest')
            child.add_argument('--allow-muse-task', action='store_true')
    args = parser.parse_args(argv)
    try:
        if args.mode == 'prepare':
            return emit(prepare(args.run_dir, args.id, args.url, args.session))
        if args.mode == 'inspect':
            return emit(load_request(args.run_dir, args.id))
        if args.mode == 'auth-store':
            if not args.allow_credential_storage:
                raise PermissionError('credential storage needs --allow-credential-storage and user entry')
            if Path(args.vault).exists() and not args.replace:
                raise FileExistsError('encrypted credential exists; explicit --replace required')
            if not sys.stdin.isatty() or not sys.stderr.isatty():
                raise PermissionError('credential entry must run personally in an interactive terminal; piped input is disabled')
            with warnings.catch_warnings():
                warnings.simplefilter('error', getpass.GetPassWarning)
                secret = getpass.getpass('Enter only your Muse hatch_sess value locally (never paste it into chat): ')
            save_cookie(args.vault, secret, overwrite=args.replace)
            return emit({'stored': 'Windows user-bound encrypted credential; no plaintext backup'})
        if not args.allow_network or not args.allow_session_use:
            raise PermissionError('account access disabled; explicit --allow-network and --allow-session-use required')
        if args.mode == 'check':
            return emit(check_request(args.run_dir, args.id, lambda: connect(args)))
        if args.mode == 'dispatch':
            if not args.allow_muse_task:
                raise PermissionError('dispatch needs explicit --allow-muse-task after review')
            return emit(dispatch(args.run_dir, args.id, args.approve, lambda: connect(args, allow_send=True)))
        if args.mode == 'history':
            session_id(args.session)
            if not 1 <= args.limit <= 20:
                raise ValueError('history limit must be 1 to 20')
        gateway = connect(args)
        try:
            if args.mode == 'status':
                return emit(gateway.call_json('identity'))
            if args.mode == 'sessions':
                return emit(gateway.call_json('sessions.list'))
            return emit(gateway.call_json('chat.history', body={'session_id': args.session, 'limit': args.limit}))
        finally:
            gateway.close()
    except (PermissionError, ValueError, FileExistsError, FileNotFoundError) as error:
        parser.exit(2, str(error) + '\n')
    except ImportError:
        parser.exit(3, 'Live dependencies are missing; nothing installed and no account accessed. See README.\n')
    except Exception:
        parser.exit(4, 'Operation failed; sensitive details suppressed. Inspect local receipts before any retry.\n')
