"""
TaskDog v2 — Onboarding Flow Tests (Exhaustive Reliability Suite).

Covers the full first-time-user journey:
  Gate A: API Key validation (health, validate-key)
  Gate B: WhatsApp Bridge (bridge status, QR, service states)
  Gate C: Group Whitelisting

Run with:
    cd taskdog-backend
    DATABASE_PATH_V2=$(mktemp) DATABASE_PATH=$(mktemp) venv/bin/python -m pytest tests.test_onboarding -v
  Or with unittest:
    DATABASE_PATH_V2=$(mktemp) DATABASE_PATH=$(mktemp) venv/bin/python -m unittest tests.test_onboarding -v
"""
import os
import sys
import json
import tempfile
import unittest
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

TEST_DB_V2 = tempfile.mktemp(suffix='.db')
TEST_DB_V1 = tempfile.mktemp(suffix='.db')
os.environ['DATABASE_PATH_V2'] = TEST_DB_V2
os.environ['DATABASE_PATH'] = TEST_DB_V1

import models.database_v2 as db2
from models.database_v2 import (
    init_db_v2, insert_groups, get_groups, get_group,
    insert_tasks, get_tasks_by_group,
)
from app import app


# ══════════════════════════════════════════════════════════════════════
# Gate A — Health & API Key Validation
# ══════════════════════════════════════════════════════════════════════

class TestHealthEndpoint(unittest.TestCase):
    """GET /api/health — the entry point for the frontend phase router."""

    @classmethod
    def setUpClass(cls):
        init_db_v2()
        app.config['TESTING'] = True

    def setUp(self):
        self.client = app.test_client()

    def test_health_returns_200(self):
        """Health endpoint should always return 200 OK."""
        res = self.client.get('/api/health')
        self.assertEqual(res.status_code, 200)

    def test_health_has_required_fields(self):
        """Health must include gemini_key_set, gemini_key_preview, bridge_status."""
        res = self.client.get('/api/health')
        data = res.get_json()
        self.assertIn('ok', data)
        self.assertTrue(data['ok'])
        self.assertIn('gemini_key_set', data)
        self.assertIn('gemini_key_preview', data)
        self.assertIn('bridge_status', data)

    def test_health_gemini_key_set_detects_key(self):
        """When GEMINI_API_KEY is set, gemini_key_set must be True."""
        with patch.dict(os.environ, {'GEMINI_API_KEY': 'AIzaSyTestKey123'}, clear=False):
            res = self.client.get('/api/health')
            data = res.get_json()
            self.assertTrue(data['gemini_key_set'])

    def test_health_gemini_key_set_detects_empty(self):
        """When GEMINI_API_KEY is empty, gemini_key_set must be False."""
        with patch.dict(os.environ, {'GEMINI_API_KEY': ''}, clear=False):
            res = self.client.get('/api/health')
            data = res.get_json()
            self.assertFalse(data['gemini_key_set'])

    def test_health_gemini_key_set_detects_missing(self):
        """When GEMINI_API_KEY is not in env, gemini_key_set must be False."""
        with patch.dict(os.environ, {}, clear=True):
            # Re-add essential env vars for DB paths
            res = self.client.get('/api/health')
            data = res.get_json()
            self.assertFalse(data['gemini_key_set'])

    def test_health_gemini_preview_masks_key(self):
        """Preview should show first 4 + last 3 chars only."""
        with patch.dict(os.environ, {'GEMINI_API_KEY': 'AIzaSySecretKey123'}, clear=False):
            res = self.client.get('/api/health')
            data = res.get_json()
            self.assertEqual(data['gemini_key_preview'], 'AIza…123')

    def test_health_bridge_status_is_string(self):
        """bridge_status must be one of: connected, pairing, offline."""
        res = self.client.get('/api/health')
        data = res.get_json()
        self.assertIn(data['bridge_status'], ('connected', 'pairing', 'offline'))

    @patch('routes.setup._is_port_open')
    @patch('routes.setup._is_bridge_process_running')
    def test_health_bridge_offline(self, mock_proc, mock_port):
        """When no bridge running, status should be 'offline'."""
        mock_port.return_value = False
        mock_proc.return_value = False
        res = self.client.get('/api/health')
        data = res.get_json()
        self.assertEqual(data['bridge_status'], 'offline')

    @patch('routes.setup._is_port_open')
    def test_health_bridge_pairing(self, mock_port):
        """When port is open but not authenticated, status should be 'pairing'."""
        mock_port.return_value = True
        with patch('routes.setup.requests.get') as mock_get:
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.json.return_value = {'connected': False}
            mock_get.return_value = mock_resp
            res = self.client.get('/api/health')
            data = res.get_json()
            self.assertEqual(data['bridge_status'], 'pairing')

    @patch('routes.setup._is_port_open')
    def test_health_bridge_connected(self, mock_port):
        """When port is open and authenticated, status should be 'connected'."""
        mock_port.return_value = True
        with patch('routes.setup.requests.get') as mock_get:
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.json.return_value = {'connected': True}
            mock_get.return_value = mock_resp
            res = self.client.get('/api/health')
            data = res.get_json()
            self.assertEqual(data['bridge_status'], 'connected')


class TestValidateKeyEndpoint(unittest.TestCase):
    """POST /api/setup/validate-key — Gate A key validation."""

    @classmethod
    def setUpClass(cls):
        app.config['TESTING'] = True

    def setUp(self):
        self.client = app.test_client()

    @patch('routes.setup.requests.get')
    def test_validate_key_valid(self, mock_get):
        """Valid key should return ok=True with preview."""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_get.return_value = mock_resp

        res = self.client.post('/api/setup/validate-key',
                               json={'key': 'AIzaSyValidKey123'})
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data['ok'])
        self.assertEqual(data['preview'], 'AIza…123')

    @patch('routes.setup.requests.get')
    def test_validate_key_invalid_403(self, mock_get):
        """Invalid key (403) should return ok=False with error."""
        mock_resp = MagicMock()
        mock_resp.status_code = 403
        mock_get.return_value = mock_resp

        res = self.client.post('/api/setup/validate-key',
                               json={'key': 'bogus-key'})
        data = res.get_json()
        self.assertFalse(data['ok'])
        self.assertIn('error', data)

    @patch('routes.setup.requests.get')
    def test_validate_key_invalid_401(self, mock_get):
        """Unauthorized key (401) should return ok=False."""
        mock_resp = MagicMock()
        mock_resp.status_code = 401
        mock_get.return_value = mock_resp

        res = self.client.post('/api/setup/validate-key',
                               json={'key': 'bogus-key-401'})
        data = res.get_json()
        self.assertFalse(data['ok'])

    def test_validate_key_missing(self):
        """Empty request body should return 400."""
        res = self.client.post('/api/setup/validate-key', json={})
        self.assertEqual(res.status_code, 400)

    def test_validate_key_empty_string(self):
        """Empty key string should return 400."""
        res = self.client.post('/api/setup/validate-key',
                               json={'key': ''})
        self.assertEqual(res.status_code, 400)

    def test_validate_key_whitespace_only(self):
        """Whitespace-only key should return 400."""
        res = self.client.post('/api/setup/validate-key',
                               json={'key': '   '})
        self.assertEqual(res.status_code, 400)

    def test_validate_key_no_json_body(self):
        """No JSON body at all should return 400."""
        res = self.client.post('/api/setup/validate-key')
        self.assertEqual(res.status_code, 400)

    def test_validate_key_very_short(self):
        """Very short key (less than 10 chars stripped) should still be validated by Gemini."""
        with patch('routes.setup.requests.get') as mock_get:
            mock_resp = MagicMock()
            mock_resp.status_code = 403
            mock_get.return_value = mock_resp
            res = self.client.post('/api/setup/validate-key',
                                   json={'key': 'abc'})
            data = res.get_json()
            self.assertFalse(data['ok'])

    @patch('routes.setup.requests.get')
    def test_validate_key_timeout(self, mock_get):
        """Gemini timeout should return 504."""
        import requests as real_requests
        mock_get.side_effect = real_requests.exceptions.Timeout('timed out')

        res = self.client.post('/api/setup/validate-key',
                               json={'key': 'AIzaSyTimeoutKey1'})
        self.assertEqual(res.status_code, 504)
        data = res.get_json()
        self.assertIn('timed out', data['error'])

    @patch('routes.setup.requests.get')
    def test_validate_key_network_error(self, mock_get):
        """Network error should return 502."""
        import requests as real_requests
        mock_get.side_effect = real_requests.exceptions.ConnectionError('no network')

        res = self.client.post('/api/setup/validate-key',
                               json={'key': 'AIzaSyNetworkFail'})
        self.assertEqual(res.status_code, 502)
        data = res.get_json()
        self.assertIn('Request failed', data['error'])

    def test_validate_key_unicode_in_key(self):
        """Unicode characters in the key should be handled."""
        res = self.client.post('/api/setup/validate-key',
                               json={'key': 'AIzaSy\u2603Snowman'})
        self.assertIn(res.status_code, (200, 400, 502, 504))

    def test_validate_key_preview_short_key(self):
        """Keys shorter than 8 chars should return empty preview."""
        with patch('routes.setup.requests.get') as mock_get:
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_get.return_value = mock_resp
            res = self.client.post('/api/setup/validate-key',
                                   json={'key': 'short'})
            data = res.get_json()
            self.assertEqual(data['preview'], '')

    @patch('routes.setup.requests.get')
    def test_key_preview_format(self, mock_get):
        """Preview should always be first 4 + '…' + last 3."""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_get.return_value = mock_resp

        res = self.client.post('/api/setup/validate-key',
                               json={'key': 'AIzaSyABCDEFGHIJKLMNOPQRSTUVWXYZ'})
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data['preview'], 'AIza…XYZ')

    def test_validate_key_special_chars(self):
        """Keys with special characters should not crash."""
        res = self.client.post('/api/setup/validate-key',
                               json={'key': 'key with spaces !@#$%'})
        self.assertIn(res.status_code, (200, 400, 502, 504))


# ══════════════════════════════════════════════════════════════════════
# Gate B — Bridge Status & QR (relies on v1 routes)
# ══════════════════════════════════════════════════════════════════════

class TestBridgeStatusEndpoint(unittest.TestCase):
    """GET /api/bridge/status and GET /api/bridge/qr."""

    @classmethod
    def setUpClass(cls):
        app.config['TESTING'] = True

    def setUp(self):
        self.client = app.test_client()

    def test_bridge_status_returns_200(self):
        """Bridge status should always return 200."""
        with patch('routes.tasks.is_port_open', return_value=False):
            with patch('routes.tasks.is_bridge_process_running', return_value=False):
                res = self.client.get('/api/bridge/status')
                self.assertEqual(res.status_code, 200)

    @patch('routes.tasks.is_port_open')
    @patch('routes.tasks.is_bridge_process_running')
    def test_bridge_status_offline(self, mock_proc, mock_port):
        """Both port closed and process not running = offline."""
        mock_port.return_value = False
        mock_proc.return_value = False
        res = self.client.get('/api/bridge/status')
        data = res.get_json()
        self.assertEqual(data['status'], 'offline')
        self.assertFalse(data['connected'])

    @patch('routes.tasks.is_port_open')
    def test_bridge_status_pairing_via_port(self, mock_port):
        """Port open but not authenticated = pairing."""
        mock_port.return_value = True
        with patch('requests.get') as mock_get:
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.json.return_value = {'connected': False}
            mock_get.return_value = mock_resp
            res = self.client.get('/api/bridge/status')
            data = res.get_json()
            self.assertEqual(data['status'], 'pairing')
            self.assertFalse(data['connected'])

    @patch('routes.tasks.is_port_open')
    @patch('routes.tasks.is_bridge_process_running')
    def test_bridge_status_pairing_via_process(self, mock_proc, mock_port):
        """Port closed but process running = pairing."""
        mock_port.return_value = False
        mock_proc.return_value = True
        res = self.client.get('/api/bridge/status')
        data = res.get_json()
        self.assertEqual(data['status'], 'pairing')
        self.assertFalse(data['connected'])

    @patch('routes.tasks.is_port_open')
    def test_bridge_status_connected(self, mock_port):
        """Port open and authenticated = connected."""
        mock_port.return_value = True
        with patch('requests.get') as mock_get:
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.json.return_value = {'connected': True}
            mock_get.return_value = mock_resp

            res = self.client.get('/api/bridge/status')
            data = res.get_json()
            self.assertEqual(data['status'], 'connected')
            self.assertTrue(data['connected'])

    @patch('routes.tasks.is_port_open')
    def test_bridge_status_port_open_but_error(self, mock_port):
        """Port open but bridge returns error = falls back to pairing."""
        mock_port.return_value = True
        with patch('requests.get', side_effect=Exception('refused')):
            res = self.client.get('/api/bridge/status')
            data = res.get_json()
            self.assertEqual(data['status'], 'pairing')

    def test_bridge_qr_offline(self):
        """QR endpoint when bridge is offline."""
        with patch('routes.tasks.is_port_open', return_value=False):
            res = self.client.get('/api/bridge/qr')
            data = res.get_json()
            self.assertEqual(data['event'], 'offline')
            self.assertEqual(data['qr'], '')

    @patch('routes.tasks.is_port_open')
    def test_bridge_qr_code_available(self, mock_port):
        """QR endpoint returns code when bridge is in pairing mode."""
        mock_port.return_value = True
        with patch('requests.get') as mock_get:
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.json.return_value = {'qr_raw': 'fake-qr-string', 'event': 'code'}
            mock_get.return_value = mock_resp

            res = self.client.get('/api/bridge/qr')
            data = res.get_json()
            self.assertEqual(data['event'], 'code')
            self.assertEqual(data['qr_raw'], 'fake-qr-string')

    @patch('routes.tasks.is_port_open')
    def test_bridge_qr_error_handling(self, mock_port):
        """QR endpoint handles bridge errors gracefully."""
        mock_port.return_value = True
        with patch('requests.get', side_effect=Exception('timeout')):
            res = self.client.get('/api/bridge/qr')
            data = res.get_json()
            self.assertEqual(data['event'], 'error')


# ══════════════════════════════════════════════════════════════════════
# Gate C — Group Whitelisting
# ══════════════════════════════════════════════════════════════════════

class TestGroupsWhitelistEndpoint(unittest.TestCase):
    """POST /api/groups/whitelist — save selected groups."""

    @classmethod
    def setUpClass(cls):
        init_db_v2()
        app.config['TESTING'] = True

    def setUp(self):
        self.client = app.test_client()
        conn = db2.get_db_connection_v2()
        conn.execute("DELETE FROM followup_history")
        conn.execute("DELETE FROM task_messages")
        conn.execute("DELETE FROM tasks")
        conn.execute("DELETE FROM groups")
        conn.commit()
        conn.close()

    @patch('routes.groups.fetch_top_chats')
    @patch('routes.groups.get_cached_classifications_for_jids')
    def test_whitelist_single_group(self, mock_cached, mock_fetch):
        """Whitelist one group with Work category."""
        mock_fetch.return_value = [
            {'jid': 'test-group@g.us', 'name': 'Test Group'},
        ]
        mock_cached.return_value = {
            'test-group@g.us': {'category': 'Work', 'tldr': 'Testing stuff'},
        }

        res = self.client.post('/api/groups/whitelist',
                               json={'jids': ['test-group@g.us']})
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data['ok'])
        self.assertEqual(data['count'], 1)

        groups = get_groups()
        self.assertEqual(len(groups), 1)
        self.assertEqual(groups[0]['name'], 'Test Group')
        self.assertEqual(groups[0]['category'], 'Work')

    @patch('routes.groups.fetch_top_chats')
    @patch('routes.groups.get_cached_classifications_for_jids')
    def test_whitelist_multiple_groups(self, mock_cached, mock_fetch):
        """Whitelist multiple groups."""
        mock_fetch.return_value = [
            {'jid': 'g1@g.us', 'name': 'Group 1'},
            {'jid': 'g2@g.us', 'name': 'Group 2'},
            {'jid': 'g3@g.us', 'name': 'Group 3'},
        ]
        mock_cached.return_value = {
            'g1@g.us': {'category': 'Work', 'tldr': 'Work stuff'},
            'g2@g.us': {'category': 'Personal', 'tldr': 'Personal stuff'},
            'g3@g.us': {'category': 'Work', 'tldr': 'More work'},
        }

        res = self.client.post('/api/groups/whitelist',
                               json={'jids': ['g1@g.us', 'g2@g.us', 'g3@g.us']})
        data = res.get_json()
        self.assertTrue(data['ok'])
        self.assertEqual(data['count'], 3)
        self.assertEqual(len(get_groups()), 3)

    def test_whitelist_empty_jids(self):
        """Empty jids list should return 400."""
        res = self.client.post('/api/groups/whitelist', json={'jids': []})
        self.assertEqual(res.status_code, 400)

    def test_whitelist_no_jids_key(self):
        """Missing jids key should return 400."""
        res = self.client.post('/api/groups/whitelist', json={})
        self.assertEqual(res.status_code, 400)

    def test_whitelist_no_body(self):
        """No request body should return 400."""
        res = self.client.post('/api/groups/whitelist')
        self.assertEqual(res.status_code, 400)

    @patch('routes.groups.fetch_top_chats')
    @patch('routes.groups.get_cached_classifications_for_jids')
    def test_whitelist_default_category_personal(self, mock_cached, mock_fetch):
        """Groups without cached classification default to 'Personal'."""
        mock_fetch.return_value = [
            {'jid': 'uncached@g.us', 'name': 'Unknown Group'},
        ]
        mock_cached.return_value = {}  # No cached data

        res = self.client.post('/api/groups/whitelist',
                               json={'jids': ['uncached@g.us']})
        self.assertTrue(res.get_json()['ok'])
        group = get_group('uncached@g.us')
        self.assertEqual(group['category'], 'Personal')

    @patch('routes.groups.fetch_top_chats')
    @patch('routes.groups.get_cached_classifications_for_jids')
    def test_whitelist_overwrite_updates_group(self, mock_cached, mock_fetch):
        """Whitelisting same JID again should update name/category/tldr."""
        mock_fetch.return_value = [
            {'jid': 'update-me@g.us', 'name': 'Updated Name'},
        ]
        mock_cached.return_value = {
            'update-me@g.us': {'category': 'Work', 'tldr': 'Updated TLDR'},
        }

        # Insert first
        insert_groups(['update-me@g.us'], ['Old Name'], ['Personal'], ['Old TLDR'])
        group = get_group('update-me@g.us')
        self.assertEqual(group['name'], 'Old Name')

        # Whitelist again
        res = self.client.post('/api/groups/whitelist',
                               json={'jids': ['update-me@g.us']})
        self.assertTrue(res.get_json()['ok'])
        group = get_group('update-me@g.us')
        self.assertEqual(group['name'], 'Updated Name')
        self.assertEqual(group['category'], 'Work')

    @patch('routes.groups.fetch_top_chats')
    @patch('routes.groups.get_cached_classifications_for_jids')
    def test_whitelist_removes_deselected_groups(self, mock_cached, mock_fetch):
        """Groups not in the new jids list should be deleted (cascade)."""
        insert_groups(
            ['keep@g.us', 'remove@g.us'],
            ['Keep', 'Remove'],
            ['Work', 'Personal'],
            ['', ''],
        )
        self.assertEqual(len(get_groups()), 2)

        mock_fetch.return_value = [
            {'jid': 'keep@g.us', 'name': 'Keep'},
        ]
        mock_cached.return_value = {}

        res = self.client.post('/api/groups/whitelist',
                               json={'jids': ['keep@g.us']})
        self.assertTrue(res.get_json()['ok'])
        groups = get_groups()
        self.assertEqual(len(groups), 1)
        self.assertEqual(groups[0]['jid'], 'keep@g.us')

    @patch('routes.groups.fetch_top_chats')
    @patch('routes.groups.get_cached_classifications_for_jids')
    def test_whitelist_fallback_name_from_jid(self, mock_cached, mock_fetch):
        """If chat name not in bridge, falls back to JID username."""
        mock_fetch.return_value = []  # No chats found
        mock_cached.return_value = {}

        res = self.client.post('/api/groups/whitelist',
                               json={'jids': ['123456789@s.whatsapp.net']})
        self.assertTrue(res.get_json()['ok'])
        group = get_group('123456789@s.whatsapp.net')
        self.assertEqual(group['name'], '123456789')

    @patch('routes.groups.fetch_top_chats')
    @patch('routes.groups.get_cached_classifications_for_jids')
    def test_whitelist_invalid_category_normalized(self, mock_cached, mock_fetch):
        """Categories not 'Work' or 'Personal' are normalized to 'Personal'."""
        mock_fetch.return_value = [
            {'jid': 'bad-cat@g.us', 'name': 'Bad Cat'},
        ]
        mock_cached.return_value = {
            'bad-cat@g.us': {'category': 'InvalidCategory', 'tldr': 'Hmm'},
        }

        res = self.client.post('/api/groups/whitelist',
                               json={'jids': ['bad-cat@g.us']})
        self.assertTrue(res.get_json()['ok'])
        group = get_group('bad-cat@g.us')
        self.assertEqual(group['category'], 'Personal')


class TestGroupsListEndpoint(unittest.TestCase):
    """GET /api/groups — list whitelisted groups with task counts."""

    @classmethod
    def setUpClass(cls):
        init_db_v2()
        app.config['TESTING'] = True

    def setUp(self):
        self.client = app.test_client()
        conn = db2.get_db_connection_v2()
        conn.execute("DELETE FROM followup_history")
        conn.execute("DELETE FROM task_messages")
        conn.execute("DELETE FROM tasks")
        conn.execute("DELETE FROM groups")
        conn.commit()
        conn.close()

    def test_groups_list_empty(self):
        """Empty groups list should return ok with empty array."""
        res = self.client.get('/api/groups')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data['ok'])
        self.assertEqual(len(data['groups']), 0)

    def test_groups_list_with_data(self):
        """Should return groups with task counts."""
        insert_groups(
            ['g1@g.us', 'g2@g.us'],
            ['Group 1', 'Group 2'],
            ['Work', 'Personal'],
            ['TLDR 1', 'TLDR 2'],
        )
        insert_tasks([
            {'title': 'T1', 'status': 'active', 'importance': 5,
             'assignee': '', 'context': '', 'people': []},
            {'title': 'T2', 'status': 'active', 'importance': 3,
             'assignee': '', 'context': '', 'people': []},
        ], 'g1@g.us')

        res = self.client.get('/api/groups')
        data = res.get_json()
        self.assertEqual(len(data['groups']), 2)
        # Find g1
        g1 = next(g for g in data['groups'] if g['jid'] == 'g1@g.us')
        self.assertEqual(g1['task_count'], 2)
        self.assertEqual(g1['active_count'], 2)
        g2 = next(g for g in data['groups'] if g['jid'] == 'g2@g.us')
        self.assertEqual(g2['task_count'], 0)

    def test_groups_list_fields(self):
        """Each group should have all required fields."""
        insert_groups(['test@g.us'], ['Test'], ['Work'], ['TLDR'])
        res = self.client.get('/api/groups')
        data = res.get_json()
        g = data['groups'][0]
        for field in ('jid', 'name', 'category', 'tldr', 'whitelisted_at',
                       'task_count', 'active_count', 'last_refreshed_at'):
            self.assertIn(field, g, f"Missing field: {field}")


# ══════════════════════════════════════════════════════════════════════
# Database Integrity — ensure_group_exists + init
# ══════════════════════════════════════════════════════════════════════

class TestEnsureGroupExists(unittest.TestCase):
    """Test _ensure_group_exists() used by pipeline to prevent FK errors."""

    @classmethod
    def setUpClass(cls):
        init_db_v2()

    def setUp(self):
        conn = db2.get_db_connection_v2()
        conn.execute("DELETE FROM followup_history")
        conn.execute("DELETE FROM task_messages")
        conn.execute("DELETE FROM tasks")
        conn.execute("DELETE FROM groups")
        conn.commit()
        conn.close()

    def test_creates_missing_group(self):
        """Should auto-create a group that doesn't exist."""
        from routes.pipeline import _ensure_group_exists
        _ensure_group_exists('new-group@g.us', 'New Group')
        g = get_group('new-group@g.us')
        self.assertIsNotNone(g)
        self.assertEqual(g['name'], 'New Group')
        self.assertEqual(g['category'], 'Personal')

    def test_noop_for_existing_group(self):
        """Should not modify an existing group."""
        insert_groups(['existing@g.us'], ['Existing'], ['Work'], ['TLDR'])
        from routes.pipeline import _ensure_group_exists
        _ensure_group_exists('existing@g.us')
        g = get_group('existing@g.us')
        self.assertEqual(g['category'], 'Work')

    def test_fallback_name_from_jid(self):
        """When name is None, fallback to JID prefix."""
        from routes.pipeline import _ensure_group_exists
        _ensure_group_exists('123456789@g.us')
        g = get_group('123456789@g.us')
        self.assertEqual(g['name'], '123456789')

    def test_idempotent(self):
        """Calling multiple times should not error."""
        from routes.pipeline import _ensure_group_exists
        _ensure_group_exists('idem@g.us', 'Idem')
        _ensure_group_exists('idem@g.us', 'Idem Again')
        g = get_group('idem@g.us')
        self.assertEqual(g['name'], 'Idem')  # Should keep original


class TestDBInitOnFreshStart(unittest.TestCase):
    """Test that init_db_v2() can run multiple times without error."""

    def setUp(self):
        # Use a fresh temp DB each time
        self.tmp = tempfile.mktemp(suffix='.db')
        os.environ['DATABASE_PATH_V2'] = self.tmp
        # Re-import to pick up new path
        import importlib
        import models.database_v2 as db2_mod
        importlib.reload(db2_mod)

    def test_init_idempotent(self):
        """Running init_db_v2 twice should not error."""
        import models.database_v2 as db2_mod
        db2_mod.init_db_v2()
        db2_mod.init_db_v2()  # Should not raise

    def test_tables_created(self):
        """All 4 tables should exist after init."""
        import models.database_v2 as db2_mod
        db2_mod.init_db_v2()
        conn = db2_mod.get_db_connection_v2()
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = {r[0] for r in cursor.fetchall()}
        conn.close()
        for t in ('groups', 'tasks', 'task_messages', 'followup_history'):
            self.assertIn(t, tables)

    def test_indexes_created(self):
        """All indexes should exist after init."""
        import models.database_v2 as db2_mod
        db2_mod.init_db_v2()
        conn = db2_mod.get_db_connection_v2()
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='index'")
        indexes = {r[0] for r in cursor.fetchall()}
        conn.close()
        for idx in ('idx_tasks_group_jid', 'idx_tasks_status', 'idx_tasks_importance',
                     'idx_task_messages_task', 'idx_followup_task'):
            self.assertIn(idx, indexes)

    def tearDown(self):
        if os.path.exists(self.tmp):
            os.remove(self.tmp)


# ══════════════════════════════════════════════════════════════════════
# Phase Router Logic — app.js renderApp() equivalence
# ══════════════════════════════════════════════════════════════════════

class TestPhaseRoutingLogic(unittest.TestCase):
    """
    Tests for the phase routing logic that lives in app.js:renderApp().

    The logic is:
      healthV2() → if !gemini_key_set → APIKEY
                 → elif bridge_status != 'connected' → PAIRING
                 → elif api.getGroupsV2() has groups → DASHBOARD
                 → else → WHITELIST
    These tests validate the backend endpoints the frontend depends on
    for this decision tree.
    """

    # These are not real "unit tests" per se — they verify the data
    # contract between the backend health/group endpoints and the
    # frontend phase router.

    @classmethod
    def setUpClass(cls):
        init_db_v2()
        app.config['TESTING'] = True

    def setUp(self):
        self.client = app.test_client()
        conn = db2.get_db_connection_v2()
        conn.execute("DELETE FROM followup_history")
        conn.execute("DELETE FROM task_messages")
        conn.execute("DELETE FROM tasks")
        conn.execute("DELETE FROM groups")
        conn.commit()
        conn.close()

    def test_route_to_apikey_when_key_not_set(self):
        """Route 1: gemini_key_set=False → phase should be APIKEY."""
        with patch.dict(os.environ, {'GEMINI_API_KEY': ''}, clear=False):
            res = self.client.get('/api/health')
            data = res.get_json()
            self.assertFalse(data['gemini_key_set'])
            # Frontend: if !gemini_key_set → PHASE.APIKEY
            self.assertEqual(data['gemini_key_set'], False)

    @patch('routes.setup._is_port_open')
    def test_route_to_pairing_when_key_set_but_bridge_offline(self, mock_port):
        """Route 2: key_set=True + bridge != connected → phase should be PAIRING."""
        mock_port.return_value = False
        with patch('routes.setup._is_bridge_process_running', return_value=False):
            with patch.dict(os.environ, {'GEMINI_API_KEY': 'AIzaSyTest123'}, clear=False):
                res = self.client.get('/api/health')
                data = res.get_json()
                self.assertTrue(data['gemini_key_set'])
                self.assertNotEqual(data['bridge_status'], 'connected')
                # Frontend: if bridge_status != 'connected' → PHASE.PAIRING

    def test_route_to_whitelist_when_connected_but_no_groups(self):
        """Route 3: key_set + bridge connected + no groups → phase should be WHITELIST."""
        res = self.client.get('/api/groups')
        data = res.get_json()
        self.assertEqual(len(data['groups']), 0)
        # Frontend: if groups.length === 0 → PHASE.WHITELIST

    @patch('routes.groups.fetch_top_chats')
    @patch('routes.groups.get_cached_classifications_for_jids')
    def test_route_to_dashboard_when_connected_and_has_groups(self, mock_cached, mock_fetch):
        """Route 4: key_set + bridge connected + groups exist → phase should be DASHBOARD."""
        mock_fetch.return_value = [{'jid': 'test@g.us', 'name': 'Test'}]
        mock_cached.return_value = {'test@g.us': {'category': 'Work', 'tldr': 'Test'}}
        # Whitelist a group
        self.client.post('/api/groups/whitelist',
                         json={'jids': ['test@g.us']})

        res = self.client.get('/api/groups')
        data = res.get_json()
        self.assertGreater(len(data['groups']), 0)
        # Frontend: if groups.length > 0 → PHASE.DASHBOARD

    def test_phase_router_fallback_on_health_error(self):
        """
        The frontend has a .catch() fallback:
          healthV2().catch(() => { phase = PHASE.APIKEY })
        This test verifies /api/health is reliable enough to reach.
        """
        res = self.client.get('/api/health')
        self.assertEqual(res.status_code, 200)


# ══════════════════════════════════════════════════════════════════════
# Reset Endpoint — v1 /api/setup/reset
# ══════════════════════════════════════════════════════════════════════

class TestResetEndpoint(unittest.TestCase):
    """POST /api/setup/reset — session reset used by Pairing.js logout."""

    @classmethod
    def setUpClass(cls):
        app.config['TESTING'] = True

    def setUp(self):
        self.client = app.test_client()

    def test_reset_endpoint_returns_ok(self):
        """Reset endpoint should return 200 with ok=True."""
        with patch('routes.tasks.subprocess.run') as mock_run:
            mock_proc = MagicMock()
            mock_proc.returncode = 0
            mock_run.return_value = mock_proc
            res = self.client.post('/api/setup/reset')
            self.assertEqual(res.status_code, 200)
            data = res.get_json()
            self.assertIn('ok', data)

    def test_reset_endpoint_kills_processes(self):
        """Reset should call pkill for wa-bridge."""
        with patch('routes.tasks.subprocess.run') as mock_run:
            mock_proc = MagicMock()
            mock_proc.returncode = 0
            mock_run.return_value = mock_proc
            self.client.post('/api/setup/reset')
            # Verify pkill was called
            pkill_calls = [c[0][0] for c in mock_run.call_args_list
                           if 'pkill' in str(c[0][0])]
            self.assertGreater(len(pkill_calls), 0)

    @patch('routes.tasks.subprocess.run')
    def test_reset_endpoint_purges_store_files(self, mock_run):
        """Reset should attempt to purge bridge store database files."""
        mock_proc = MagicMock()
        mock_proc.returncode = 0
        mock_run.return_value = mock_proc
        with patch('routes.tasks.glob.glob', return_value=['/fake/whatsapp.db', '/fake/messages.db']):
            with patch('routes.tasks.os.remove') as mock_remove:
                res = self.client.post('/api/setup/reset')
                self.assertEqual(res.status_code, 200)
                self.assertGreater(mock_remove.call_count, 0)

    @patch('routes.tasks.subprocess.run')
    def test_reset_endpoint_handles_exception(self, mock_run):
        """Reset should catch exceptions and return 500 with error."""
        mock_run.side_effect = Exception('Simulated reset failure')
        res = self.client.post('/api/setup/reset')
        self.assertEqual(res.status_code, 500)


# ══════════════════════════════════════════════════════════════════════
# Edge Cases — Concurrency, Rate Limits, Data Integrity
# ══════════════════════════════════════════════════════════════════════

class TestEdgeCases(unittest.TestCase):
    """Edge cases and stress scenarios for onboarding."""

    @classmethod
    def setUpClass(cls):
        init_db_v2()
        app.config['TESTING'] = True

    def setUp(self):
        self.client = app.test_client()
        conn = db2.get_db_connection_v2()
        conn.execute("DELETE FROM followup_history")
        conn.execute("DELETE FROM task_messages")
        conn.execute("DELETE FROM tasks")
        conn.execute("DELETE FROM groups")
        conn.commit()
        conn.close()

    @patch('routes.groups.fetch_top_chats')
    @patch('routes.groups.get_cached_classifications_for_jids')
    def test_whitelist_large_jid_list(self, mock_cached, mock_fetch):
        """Whitelisting 50 groups should succeed."""
        jids = [f'group-{i}@g.us' for i in range(50)]
        mock_fetch.return_value = [
            {'jid': j, 'name': f'Group {i}'} for i, j in enumerate(jids)
        ]
        mock_cached.return_value = {
            j: {'category': 'Work', 'tldr': f'TLDR {i}'}
            for i, j in enumerate(jids)
        }
        res = self.client.post('/api/groups/whitelist', json={'jids': jids})
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data['ok'])
        self.assertEqual(data['count'], 50)
        self.assertEqual(len(get_groups()), 50)

    @patch('routes.groups.fetch_top_chats')
    @patch('routes.groups.fetch_top_chats')
    @patch('routes.groups.get_cached_classifications_for_jids')
    def test_whitelist_duplicate_jids(self, mock_cached, mock_fetch1, mock_fetch2):
        """Duplicate JIDs in the request should be handled (upsert)."""
        mock_fetch1.return_value = [
            {'jid': 'dup@g.us', 'name': 'Duplicate'},
        ]
        mock_fetch2.return_value = mock_fetch1.return_value
        mock_cached.return_value = {
            'dup@g.us': {'category': 'Work', 'tldr': 'TLDR'},
        }
        res = self.client.post('/api/groups/whitelist',
                               json={'jids': ['dup@g.us', 'dup@g.us', 'dup@g.us']})
        self.assertTrue(res.get_json()['ok'])
        self.assertEqual(len(get_groups()), 1)

    def test_empty_task_list_in_dashboard(self):
        """Dashboard should return empty tasks with stats when no data."""
        res = self.client.get('/api/dashboard')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data['ok'])
        self.assertEqual(len(data['tasks']), 0)
        self.assertEqual(data['stats']['total'], 0)
        self.assertEqual(data['stats']['active'], 0)

    def test_404_on_invalid_endpoint(self):
        """Nonexistent endpoints should return 404."""
        res = self.client.get('/api/nonexistent')
        self.assertEqual(res.status_code, 404)

    def test_404_on_invalid_task_id(self):
        """Requesting a nonexistent task should return 404."""
        res = self.client.get('/api/tasks/nonexistent-id-12345')
        self.assertEqual(res.status_code, 404)


if __name__ == '__main__':
    unittest.main()