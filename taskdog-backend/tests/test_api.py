"""
Backend API tests for TaskDog v1.
Uses unittest + Flask test_client. No external services required.
Run with: cd taskdog-backend && venv/bin/python -m pytest tests/ -v
   or:   venv/bin/python tests/test_api.py
"""
import os
import sys
import json
import tempfile
import unittest
from unittest.mock import patch, MagicMock

# Ensure backend root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Use a temp database so tests don't touch the real one
TEST_DB = tempfile.mktemp(suffix='.db')
os.environ['DATABASE_PATH'] = TEST_DB

import app as app_module  # noqa: E402
import models.database as db  # noqa: E402
from app import app  # noqa: E402


class TestHealth(unittest.TestCase):
    def test_health_returns_ok(self):
        client = app.test_client()
        res = client.get('/health')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data['status'], 'ok')
        self.assertIn('timestamp', data)


class TestRoot(unittest.TestCase):
    def test_root_returns_metadata(self):
        client = app.test_client()
        res = client.get('/')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertIn('message', data)
        self.assertEqual(data['version'], '1.0.0')


class TestBridgeStatus(unittest.TestCase):
    @patch('routes.tasks.is_bridge_process_running', return_value=False)
    @patch('routes.tasks.is_port_open', return_value=False)
    def test_offline(self, mock_port, mock_proc):
        client = app.test_client()
        res = client.get('/api/bridge/status')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data['status'], 'offline')
        self.assertFalse(data['connected'])

    @patch('routes.tasks.is_bridge_process_running', return_value=True)
    @patch('routes.tasks.is_port_open', return_value=False)
    def test_pairing(self, mock_port, mock_proc):
        client = app.test_client()
        res = client.get('/api/bridge/status')
        data = res.get_json()
        self.assertEqual(data['status'], 'pairing')

    @patch('routes.tasks.is_bridge_process_running', return_value=True)
    @patch('routes.tasks.is_port_open', return_value=True)
    def test_connected(self, mock_port, mock_proc):
        client = app.test_client()
        res = client.get('/api/bridge/status')
        data = res.get_json()
        self.assertEqual(data['status'], 'connected')
        self.assertTrue(data['connected'])


class TestDatabaseSchema(unittest.TestCase):
    def setUp(self):
        # Fresh DB for each test
        if os.path.exists(TEST_DB):
            os.remove(TEST_DB)
        db.init_db(force=True)

    def test_all_tables_exist(self):
        conn = db.get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = {r[0] for r in cur.fetchall()}
        conn.close()
        self.assertIn('whitelisted_groups', tables)
        self.assertIn('themes', tables)
        self.assertIn('tasks', tables)
        self.assertIn('nudge_history', tables)
        self.assertIn('chat_classifications', tables)

    def test_init_db_is_idempotent(self):
        # Calling twice should not raise
        db.init_db(force=False)
        db.init_db(force=False)


class TestWhitelistedGroups(unittest.TestCase):
    def setUp(self):
        if os.path.exists(TEST_DB):
            os.remove(TEST_DB)
        db.init_db(force=True)

    def test_save_and_get(self):
        groups = [
            {'jid': 'a@g.us', 'name': 'Group A', 'category': 'Work', 'tldr': 'Stuff'},
            {'jid': 'b@g.us', 'name': 'Group B', 'category': 'Personal', 'tldr': 'Fam'},
        ]
        db.save_whitelisted_groups(groups)
        result = db.get_whitelisted_groups()
        self.assertEqual(len(result), 2)
        names = {g['name'] for g in result}
        self.assertEqual(names, {'Group A', 'Group B'})

    def test_save_upserts(self):
        db.save_whitelisted_groups([{'jid': 'a@g.us', 'name': 'Old', 'category': 'Work', 'tldr': ''}])
        db.save_whitelisted_groups([{'jid': 'a@g.us', 'name': 'New', 'category': 'Work', 'tldr': 'X'}])
        result = db.get_whitelisted_groups()
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['name'], 'New')


class TestTasks(unittest.TestCase):
    def setUp(self):
        if os.path.exists(TEST_DB):
            os.remove(TEST_DB)
        db.init_db(force=True)
        # Seed: 1 group, 1 theme, 3 tasks
        db.save_whitelisted_groups([
            {'jid': 'g1@g.us', 'name': 'Group 1', 'category': 'Work', 'tldr': 'Q3 planning'}
        ])
        themes = [{
            'name': 'Theme 1',
            'description': 'Desc',
            'tasks': [
                {
                    'title': 'Task A',
                    'status': 'not started',
                    'context': 'ctx A',
                    'assignee': 'Alice',
                    'suggested_responses': {
                        'concise': 'cA',
                        'moderate': 'mA',
                        'with_context': 'wA',
                    },
                },
                {
                    'title': 'Task B',
                    'status': 'pending',
                    'context': 'ctx B',
                    'assignee': 'Bob',
                    'suggested_responses': {
                        'concise': 'cB',
                        'moderate': 'mB',
                        'with_context': 'wB',
                    },
                },
                {
                    'title': 'Task C',
                    'status': 'done',
                    'context': 'ctx C',
                    'assignee': 'Cara',
                    'suggested_responses': {
                        'concise': 'cC',
                        'moderate': 'mC',
                        'with_context': 'wC',
                    },
                },
            ],
        }]
        db.save_extracted_themes_and_tasks('g1@g.us', themes)

    def test_tasks_loaded_with_joins(self):
        tasks = db.get_kanban_tasks()
        self.assertEqual(len(tasks), 3)
        titles = {t['title'] for t in tasks}
        self.assertEqual(titles, {'Task A', 'Task B', 'Task C'})
        for t in tasks:
            self.assertEqual(t['group_name'], 'Group 1')
            self.assertEqual(t['theme_name'], 'Theme 1')
            self.assertEqual(t['group_jid'], 'g1@g.us')
            self.assertIn('suggested_responses', t)
            self.assertIn('concise', t['suggested_responses'])

    def test_update_task_status(self):
        tasks = db.get_kanban_tasks()
        target = next(t for t in tasks if t['title'] == 'Task A')
        self.assertEqual(target['status'], 'not started')
        db.update_task_status(target['id'], 'done')
        tasks = db.get_kanban_tasks()
        target = next(t for t in tasks if t['title'] == 'Task A')
        self.assertEqual(target['status'], 'done')

    def test_invalid_status_rejected_by_route(self):
        # Status validation happens at the route level (returns 400)
        client = app.test_client()
        res = client.post('/api/tasks/update_status', json={'task_id': 'x', 'status': 'BOGUS'})
        self.assertEqual(res.status_code, 400)

    def test_db_update_status_silently_no_op_for_missing(self):
        # DB layer should not raise for missing task_id
        db.update_task_status('non-existent-id', 'done')

    def test_filter_by_group(self):
        # Add a second group with no tasks
        db.save_whitelisted_groups([{'jid': 'g2@g.us', 'name': 'G2', 'category': 'Personal', 'tldr': ''}])
        all_tasks = db.get_kanban_tasks()
        g1_tasks = db.get_kanban_tasks('g1@g.us')
        g2_tasks = db.get_kanban_tasks('g2@g.us')
        self.assertEqual(len(all_tasks), 3)
        self.assertEqual(len(g1_tasks), 3)
        self.assertEqual(len(g2_tasks), 0)

    def test_stats(self):
        stats = db.get_tasks_stats()
        self.assertEqual(stats['not_started'], 1)
        self.assertEqual(stats['pending'], 1)
        self.assertEqual(stats['done'], 1)
        self.assertEqual(stats['total'], 3)


class TestNudgeHistory(unittest.TestCase):
    def setUp(self):
        if os.path.exists(TEST_DB):
            os.remove(TEST_DB)
        db.init_db(force=True)
        db.save_whitelisted_groups([{'jid': 'g1@g.us', 'name': 'G', 'category': 'Work', 'tldr': ''}])
        db.save_extracted_themes_and_tasks('g1@g.us', [{
            'name': 'T', 'description': '',
            'tasks': [{
                'title': 'X', 'status': 'not started', 'context': '', 'assignee': '',
                'suggested_responses': {'concise': 'c', 'moderate': 'm', 'with_context': 'w'},
            }],
        }])

    def test_record_nudge(self):
        tasks = db.get_kanban_tasks()
        tid = tasks[0]['id']
        db.record_nudge(tid, 'hello', 'g1@g.us')
        history = db.get_nudge_history()
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0]['sent_text'], 'hello')
        self.assertEqual(history[0]['task_title'], 'X')
        self.assertEqual(history[0]['group_name'], 'G')


class TestGetTasksEndpoint(unittest.TestCase):
    def setUp(self):
        if os.path.exists(TEST_DB):
            os.remove(TEST_DB)
        db.init_db(force=True)

    def test_get_tasks_empty(self):
        client = app.test_client()
        res = client.get('/api/tasks')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data['ok'])
        self.assertEqual(data['tasks'], [])
        self.assertEqual(data['stats']['total'], 0)

    def test_update_status_endpoint_missing_id(self):
        client = app.test_client()
        res = client.post('/api/tasks/update_status', json={'status': 'pending'})
        self.assertEqual(res.status_code, 400)

    def test_update_status_endpoint_no_body(self):
        client = app.test_client()
        res = client.post('/api/tasks/update_status', json={})
        self.assertEqual(res.status_code, 400)


class TestGroupsEndpoint(unittest.TestCase):
    def setUp(self):
        if os.path.exists(TEST_DB):
            os.remove(TEST_DB)
        db.init_db(force=True)

    def test_get_groups_empty(self):
        client = app.test_client()
        res = client.get('/api/groups')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data['groups'], [])

    def test_get_groups_after_seed(self):
        db.save_whitelisted_groups([{'jid': 'x@g.us', 'name': 'X', 'category': 'Work', 'tldr': ''}])
        client = app.test_client()
        res = client.get('/api/groups')
        data = res.get_json()
        self.assertEqual(len(data['groups']), 1)
        self.assertEqual(data['groups'][0]['name'], 'X')


class TestExtractEndpoint(unittest.TestCase):
    def setUp(self):
        if os.path.exists(TEST_DB):
            os.remove(TEST_DB)
        db.init_db(force=True)

    def test_extract_requires_chats(self):
        client = app.test_client()
        res = client.post('/api/tasks/extract', json={'chats': []})
        self.assertEqual(res.status_code, 400)
        self.assertFalse(res.get_json()['ok'])


class TestGeminiClient(unittest.TestCase):
    def setUp(self):
        from utils import gemini_client
        self.client = gemini_client

    def test_fallback_when_no_api_key(self):
        with patch.object(self.client, 'GEMINI_API_KEY', None):
            result = self.client.classify_chat('Test', [{'sender': 'a', 'content': 'b'}])
            self.assertEqual(result['category'], 'Personal')
            result2 = self.client.extract_tasks('Test', [{'sender': 'a', 'content': 'b'}])
            self.assertEqual(result2['themes'], [])

    def test_classify_parses_valid_response(self):
        mock_response = {'candidates': [{'content': {'parts': [{'text': json.dumps({
            'category': 'Work',
            'tldr': 'Test summary',
        })}]}}]}
        with patch.object(self.client, 'GEMINI_API_KEY', 'fake'), \
             patch.object(self.client.requests, 'post') as mock_post:
            mock_post.return_value.json.return_value = mock_response
            mock_post.return_value.raise_for_status = MagicMock()
            result = self.client.classify_chat('Test', [{'sender': 'a', 'content': 'b'}])
            self.assertEqual(result['category'], 'Work')
            self.assertEqual(result['tldr'], 'Test summary')

    def test_classify_handles_invalid_category(self):
        mock_response = {'candidates': [{'content': {'parts': [{'text': json.dumps({
            'category': 'BOGUS',
            'tldr': 'x',
        })}]}}]}
        with patch.object(self.client, 'GEMINI_API_KEY', 'fake'), \
             patch.object(self.client.requests, 'post') as mock_post:
            mock_post.return_value.json.return_value = mock_response
            mock_post.return_value.raise_for_status = MagicMock()
            result = self.client.classify_chat('Test', [{'sender': 'a', 'content': 'b'}])
            self.assertEqual(result['category'], 'Personal')


class TestClassificationCache(unittest.TestCase):
    """Coverage for the chat_classifications cache used by /api/chats/classify."""

    def setUp(self):
        if os.path.exists(TEST_DB):
            os.remove(TEST_DB)
        db.init_db(force=True)

    def test_upsert_and_get_bulk(self):
        db.upsert_classification('a@g.us', 'Group A', 'Work', 'TLDR A')
        db.upsert_classification('b@g.us', 'Group B', 'Personal', 'TLDR B')
        cached = db.get_cached_classifications_for_jids(['a@g.us', 'b@g.us', 'missing@g.us'])
        self.assertEqual(set(cached.keys()), {'a@g.us', 'b@g.us'})
        self.assertEqual(cached['a@g.us']['category'], 'Work')
        self.assertEqual(cached['b@g.us']['tldr'], 'TLDR B')

    def test_upsert_overwrites_existing(self):
        db.upsert_classification('a@g.us', 'Group A', 'Work', 'old')
        db.upsert_classification('a@g.us', 'Group A', 'Personal', 'new')
        cached = db.get_cached_classifications_for_jids(['a@g.us'])
        self.assertEqual(cached['a@g.us']['category'], 'Personal')
        self.assertEqual(cached['a@g.us']['tldr'], 'new')

    def test_upsert_normalises_legacy_others_to_personal(self):
        db.upsert_classification('a@g.us', 'Group A', 'Others', 'old')
        cached = db.get_cached_classifications_for_jids(['a@g.us'])
        self.assertEqual(cached['a@g.us']['category'], 'Personal')

    def test_whitelisted_jids_set(self):
        self.assertEqual(db.get_whitelisted_jids(), set())
        db.save_whitelisted_groups([
            {'jid': 'w1@g.us', 'name': 'W1', 'category': 'Work', 'tldr': ''},
            {'jid': 'w2@g.us', 'name': 'W2', 'category': 'Personal', 'tldr': ''},
        ])
        self.assertEqual(db.get_whitelisted_jids(), {'w1@g.us', 'w2@g.us'})
        self.assertTrue(db.is_jid_whitelisted('w1@g.us'))
        self.assertFalse(db.is_jid_whitelisted('nope@g.us'))

    def test_force_flag_bypasses_cache(self):
        """The classify route should hit Gemini when force=true, even if a
        cached row exists, and return from_cache=False for every chat."""
        # Pre-seed the cache with a value different from what Gemini returns.
        db.upsert_classification('a@g.us', 'Group A', 'Work', 'cached TLDR')

        mock_response = {'candidates': [{'content': {'parts': [{'text': json.dumps({
            'category': 'Personal', 'tldr': 'fresh TLDR'
        })}]}}]}

        with patch('routes.tasks.fetch_top_chats', return_value=[
            {'jid': 'a@g.us', 'name': 'Group A', 'last_message_time': 'x'},
        ]), \
             patch('routes.tasks.fetch_chat_messages', return_value=[
                 {'sender': 's', 'content': 'c'}
             ]), \
             patch('routes.tasks.get_whitelisted_jids', return_value=set()), \
             patch('utils.gemini_client.GEMINI_API_KEY', 'fake'), \
             patch('utils.gemini_client.requests.post') as mock_post:
            mock_post.return_value.json.return_value = mock_response
            mock_post.return_value.raise_for_status = MagicMock()

            client = app.test_client()
            res = client.post('/api/chats/classify?force=true')
            self.assertEqual(res.status_code, 200)
            data = res.get_json()
            self.assertEqual(data['cached_count'], 0)
            self.assertEqual(data['new_count'], 1)
            self.assertEqual(data['chats'][0]['tldr'], 'fresh TLDR')
            self.assertEqual(data['chats'][0]['category'], 'Personal')
            self.assertFalse(data['chats'][0]['from_cache'])

    def test_cache_hit_skips_gemini(self):
        """When the cache has a row, the route must NOT call Gemini."""
        db.upsert_classification('a@g.us', 'Group A', 'Work', 'cached TLDR')

        with patch('routes.tasks.fetch_top_chats', return_value=[
            {'jid': 'a@g.us', 'name': 'Group A', 'last_message_time': 'x'},
        ]), \
             patch('routes.tasks.fetch_chat_messages') as mock_msgs, \
             patch('routes.tasks.get_whitelisted_jids', return_value=set()), \
             patch('routes.tasks.get_cached_classifications_for_jids', wraps=db.get_cached_classifications_for_jids) as mock_cache, \
             patch('utils.gemini_client.classify_chat') as mock_classify:
            client = app.test_client()
            res = client.post('/api/chats/classify')
            self.assertEqual(res.status_code, 200)
            data = res.get_json()
            self.assertEqual(data['cached_count'], 1)
            self.assertEqual(data['new_count'], 0)
            self.assertTrue(data['chats'][0]['from_cache'])
            self.assertEqual(data['chats'][0]['category'], 'Work')
            self.assertEqual(data['chats'][0]['tldr'], 'cached TLDR')
            # Gemini must not have been called.
            mock_classify.assert_not_called()
            mock_msgs.assert_not_called()
            mock_cache.assert_called_once()

    def test_response_includes_is_whitelisted(self):
        db.upsert_classification('a@g.us', 'Group A', 'Work', 'TLDR A')
        db.save_whitelisted_groups([
            {'jid': 'a@g.us', 'name': 'Group A', 'category': 'Work', 'tldr': 'TLDR A'},
        ])
        with patch('routes.tasks.fetch_top_chats', return_value=[
            {'jid': 'a@g.us', 'name': 'Group A', 'last_message_time': 'x'},
        ]), \
             patch('routes.tasks.get_whitelisted_jids', wraps=db.get_whitelisted_jids), \
             patch('routes.tasks.get_cached_classifications_for_jids', wraps=db.get_cached_classifications_for_jids):
            client = app.test_client()
            res = client.post('/api/chats/classify')
            data = res.get_json()
            self.assertTrue(data['chats'][0]['is_whitelisted'])


class TestUpdateCategoryEndpoint(unittest.TestCase):
    """Coverage for POST /api/chats/classify/update_category (drag-and-drop)."""

    def setUp(self):
        if os.path.exists(TEST_DB):
            os.remove(TEST_DB)
        db.init_db(force=True)

    def _post(self, jid, category):
        client = app.test_client()
        return client.post('/api/chats/classify/update_category', json={
            'jid': jid, 'category': category,
        })

    def test_updates_existing_cache_row(self):
        db.upsert_classification('a@g.us', 'Group A', 'Work', 'TLDR A')
        res = self._post('a@g.us', 'Personal')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data['ok'])
        self.assertTrue(data['updated'])
        cached = db.get_cached_classifications_for_jids(['a@g.us'])
        self.assertEqual(cached['a@g.us']['category'], 'Personal')
        self.assertEqual(cached['a@g.us']['tldr'], 'TLDR A')  # tldr untouched

    def test_normalises_invalid_value_to_personal(self):
        db.upsert_classification('a@g.us', 'Group A', 'Work', 'x')
        res = self._post('a@g.us', 'BOGUS')
        self.assertEqual(res.status_code, 400)  # rejected at the route

        # But the model-level helper normalises anyway:
        db.update_classification_category('a@g.us', 'Others')
        cached = db.get_cached_classifications_for_jids(['a@g.us'])
        self.assertEqual(cached['a@g.us']['category'], 'Personal')

    def test_rejects_missing_jid(self):
        client = app.test_client()
        res = client.post('/api/chats/classify/update_category', json={'category': 'Work'})
        self.assertEqual(res.status_code, 400)
        self.assertFalse(res.get_json()['ok'])

    def test_rejects_missing_category(self):
        client = app.test_client()
        res = client.post('/api/chats/classify/update_category', json={'jid': 'a@g.us'})
        self.assertEqual(res.status_code, 400)

    def test_defensive_insert_when_no_cache_row(self):
        # No prior upsert — the helper should still succeed and create a row.
        ok = db.update_classification_category('new@g.us', 'Personal')
        self.assertTrue(ok)
        cached = db.get_cached_classifications_for_jids(['new@g.us'])
        self.assertEqual(cached['new@g.us']['category'], 'Personal')


class TestClassifyLimitParam(unittest.TestCase):
    """The classify routes accept a `limit` parameter (default 100)."""

    def setUp(self):
        if os.path.exists(TEST_DB):
            os.remove(TEST_DB)
        db.init_db(force=True)

    def test_default_limit_is_100(self):
        with patch('routes.tasks.fetch_top_chats', return_value=[]) as mock_fetch, \
             patch('routes.tasks.get_whitelisted_jids', return_value=set()):
            client = app.test_client()
            res = client.post('/api/chats/classify')
            self.assertEqual(res.status_code, 200)
            # Should have requested 100 chats.
            _, kwargs = mock_fetch.call_args
            self.assertEqual(kwargs.get('limit'), 100)

    def test_explicit_limit_in_body(self):
        with patch('routes.tasks.fetch_top_chats', return_value=[]) as mock_fetch, \
             patch('routes.tasks.get_whitelisted_jids', return_value=set()):
            client = app.test_client()
            res = client.post('/api/chats/classify', json={'limit': 25})
            self.assertEqual(res.status_code, 200)
            _, kwargs = mock_fetch.call_args
            self.assertEqual(kwargs.get('limit'), 25)

    def test_explicit_limit_via_query_string(self):
        with patch('routes.tasks.fetch_top_chats', return_value=[]) as mock_fetch, \
             patch('routes.tasks.get_whitelisted_jids', return_value=set()):
            client = app.test_client()
            res = client.post('/api/chats/classify?limit=50')
            self.assertEqual(res.status_code, 200)
            _, kwargs = mock_fetch.call_args
            self.assertEqual(kwargs.get('limit'), 50)

    def test_limit_is_capped(self):
        with patch('routes.tasks.fetch_top_chats', return_value=[]) as mock_fetch, \
             patch('routes.tasks.get_whitelisted_jids', return_value=set()):
            client = app.test_client()
            res = client.post('/api/chats/classify', json={'limit': 99999})
            self.assertEqual(res.status_code, 200)
            _, kwargs = mock_fetch.call_args
            self.assertEqual(kwargs.get('limit'), 500)  # hard cap


class TestClassifyStreamEndpoint(unittest.TestCase):
    """Coverage for the SSE streaming classify endpoint."""

    def setUp(self):
        if os.path.exists(TEST_DB):
            os.remove(TEST_DB)
        db.init_db(force=True)

    @staticmethod
    def _parse_sse(body):
        """Parse an SSE response body into a list of (event, data) tuples."""
        events = []
        for block in body.split('\n\n'):
            block = block.strip()
            if not block:
                continue
            event_name = 'message'
            data_str = ''
            for line in block.split('\n'):
                if line.startswith('event:'):
                    event_name = line[len('event:'):].strip()
                elif line.startswith('data:'):
                    data_str += line[len('data:'):].strip()
            if data_str:
                try:
                    events.append((event_name, json.loads(data_str)))
                except json.JSONDecodeError:
                    pass
        return events

    def test_emits_cached_chats_first_then_done(self):
        db.upsert_classification('a@g.us', 'Group A', 'Work', 'cached')
        db.upsert_classification('b@g.us', 'Group B', 'Personal', 'cached b')
        with patch('routes.tasks.fetch_top_chats', return_value=[
            {'jid': 'a@g.us', 'name': 'Group A', 'last_message_time': 'x'},
            {'jid': 'b@g.us', 'name': 'Group B', 'last_message_time': 'y'},
        ]), \
             patch('routes.tasks.get_whitelisted_jids', return_value=set()):
            client = app.test_client()
            res = client.post('/api/chats/classify/stream')
            self.assertEqual(res.status_code, 200)
            self.assertIn('text/event-stream', res.headers.get('Content-Type', ''))
            events = self._parse_sse(res.get_data(as_text=True))
        # 2 chat events + 1 meta + 1 done = 4
        self.assertEqual(len(events), 4)
        event_names = [e[0] for e in events]
        # Cached chats come first.
        self.assertEqual(event_names[0], 'chat')
        self.assertEqual(event_names[1], 'chat')
        # Then meta, then done.
        self.assertEqual(event_names[2], 'meta')
        self.assertEqual(event_names[3], 'done')
        meta_event = events[2][1]
        self.assertEqual(meta_event['total'], 2)
        self.assertEqual(meta_event['cached_count'], 2)
        self.assertEqual(meta_event['new_count'], 0)

    def test_uncached_chats_hit_gemini_and_are_emitted(self):
        # No cache rows — the single chat should go to Gemini and be emitted.
        mock_response = {'candidates': [{'content': {'parts': [{'text': json.dumps({
            'category': 'Personal', 'tldr': 'fresh'
        })}]}}]}
        with patch('routes.tasks.fetch_top_chats', return_value=[
            {'jid': 'a@g.us', 'name': 'Group A', 'last_message_time': 'x'},
        ]), \
             patch('routes.tasks.fetch_chat_messages', return_value=[
                 {'sender': 's', 'content': 'c'}
             ]), \
             patch('routes.tasks.get_whitelisted_jids', return_value=set()), \
             patch('utils.gemini_client.GEMINI_API_KEY', 'fake'), \
             patch('utils.gemini_client.requests.post') as mock_post:
            mock_post.return_value.json.return_value = mock_response
            mock_post.return_value.raise_for_status = MagicMock()
            client = app.test_client()
            res = client.post('/api/chats/classify/stream')
            self.assertEqual(res.status_code, 200)
            events = self._parse_sse(res.get_data(as_text=True))
        # Order: meta (no cached chats, so it's emitted first) → chat → done
        self.assertEqual(len(events), 3)
        self.assertEqual(events[0][0], 'meta')
        self.assertEqual(events[0][1]['total'], 1)
        self.assertEqual(events[0][1]['cached_count'], 0)
        self.assertEqual(events[0][1]['new_count'], 1)
        chat_event = events[1]
        self.assertEqual(chat_event[0], 'chat')
        self.assertEqual(chat_event[1]['category'], 'Personal')
        self.assertFalse(chat_event[1]['from_cache'])
        self.assertEqual(events[2][0], 'done')
        # And it should now be cached.
        cached = db.get_cached_classifications_for_jids(['a@g.us'])
        self.assertEqual(cached['a@g.us']['category'], 'Personal')

    def test_empty_chat_list_emits_meta_and_done(self):
        with patch('routes.tasks.fetch_top_chats', return_value=[]), \
             patch('routes.tasks.get_whitelisted_jids', return_value=set()):
            client = app.test_client()
            res = client.post('/api/chats/classify/stream')
            self.assertEqual(res.status_code, 200)
            events = self._parse_sse(res.get_data(as_text=True))
        self.assertEqual(len(events), 2)
        self.assertEqual(events[0][0], 'meta')
        self.assertEqual(events[0][1]['total'], 0)
        self.assertEqual(events[1][0], 'done')


class TestExtractDetailedResponse(unittest.TestCase):
    """Verify the /tasks/extract route surfaces per-chat status so the UI
    can show the user what actually happened for each group."""

    def setUp(self):
        # Fresh DB per test
        if os.path.exists(TEST_DB):
            os.remove(TEST_DB)
        db.init_db(force=True)

    def _post(self, client, chats):
        return client.post('/api/tasks/extract', json={'chats': chats})

    def test_response_shape_with_mixed_outcomes(self):
        """Mix of ok / no_messages / gemini_failed must all show up in
        the details array with the right status field."""
        chats = [
            {'jid': 'ok@g.us',         'name': 'OK Group'},
            {'jid': 'empty@g.us',      'name': 'Empty Group'},
            {'jid': 'gemfail@g.us',    'name': 'Gemini Group'},
        ]

        with patch('routes.tasks.fetch_chat_messages_since') as m_fetch, \
             patch('routes.tasks.extract_tasks') as m_extract, \
             patch('routes.tasks.save_extracted_themes_and_tasks') as m_save:
            def fetch(jid, days=30):
                return [] if jid == 'empty@g.us' else [{'sender': 'a', 'content': 'hi', 'is_from_me': False}]
            m_fetch.side_effect = fetch

            def extract(name, messages):
                # gemfail@g.us simulates a Gemini error
                if 'Gemini' in name:
                    return {'themes': [], 'error': 'Gemini timed out'}
                return {
                    'themes': [{
                        'name': 't1', 'description': 'd1',
                        'tasks': [{'title': 'A', 'status': 'pending', 'context': '', 'assignee': 'x',
                                   'suggested_responses': {'concise': '', 'moderate': '', 'with_context': ''}}],
                    }],
                }
            m_extract.side_effect = extract

            client = app.test_client()
            res = self._post(client, chats)
        self.assertEqual(res.status_code, 200)
        body = res.get_json()
        self.assertTrue(body['ok'])
        self.assertEqual(body['total'], 3)
        self.assertEqual(body['processed'], 1)
        self.assertEqual(body['no_messages'], 1)
        self.assertEqual(body['gemini_failed'], 1)
        self.assertEqual(body['save_failed'], 0)

        details = {d['jid']: d for d in body['details']}
        self.assertEqual(details['ok@g.us']['status'], 'ok')
        self.assertEqual(details['ok@g.us']['task_count'], 1)
        self.assertEqual(details['empty@g.us']['status'], 'no_messages')
        self.assertEqual(details['gemfail@g.us']['status'], 'gemini_failed')

    def test_gemini_failure_is_reported_per_chat(self):
        """When extract_tasks returns an error dict, that chat must be
        marked gemini_failed — not silently dropped."""
        with patch('routes.tasks.fetch_chat_messages_since', return_value=[{'sender': 'a', 'content': 'hi', 'is_from_me': False}]), \
             patch('routes.tasks.extract_tasks', return_value={'themes': [], 'error': 'Gemini 503'}), \
             patch('routes.tasks.save_extracted_themes_and_tasks') as m_save:
            client = app.test_client()
            res = self._post(client, [{'jid': 'x@g.us', 'name': 'X'}])
        body = res.get_json()
        self.assertEqual(body['processed'], 0)
        self.assertEqual(body['gemini_failed'], 1)
        self.assertEqual(body['details'][0]['status'], 'gemini_failed')
        # save should NOT be called for failed Gemini
        m_save.assert_not_called()

    def test_save_failure_is_reported(self):
        """When themes come back but save throws, status=save_failed and
        the theme_count is still reported."""
        with patch('routes.tasks.fetch_chat_messages_since', return_value=[{'sender': 'a', 'content': 'hi', 'is_from_me': False}]), \
             patch('routes.tasks.extract_tasks', return_value={'themes': [{'name': 't', 'description': 'd', 'tasks': []}]}), \
             patch('routes.tasks.save_extracted_themes_and_tasks', side_effect=RuntimeError('db locked')):
            client = app.test_client()
            res = self._post(client, [{'jid': 'x@g.us', 'name': 'X'}])
        body = res.get_json()
        self.assertEqual(body['processed'], 0)
        self.assertEqual(body['save_failed'], 1)
        self.assertEqual(body['details'][0]['status'], 'save_failed')
        self.assertIn('db locked', body['details'][0]['error'])

    def test_concurrent_processing(self):
        """Process 5 chats with mocked sleeps to verify the executor runs
        in parallel (completes much faster than serial)."""
        import time
        chats = [{'jid': f'g{i}@g.us', 'name': f'G{i}'} for i in range(5)]

        def slow_extract(name, messages):
            time.sleep(0.4)
            return {'themes': [{'name': 't', 'description': 'd', 'tasks': []}]}

        with patch('routes.tasks.fetch_chat_messages_since', return_value=[{'sender': 'a', 'content': 'hi', 'is_from_me': False}]), \
             patch('routes.tasks.extract_tasks', side_effect=slow_extract), \
             patch('routes.tasks.save_extracted_themes_and_tasks'):
            t0 = time.time()
            client = app.test_client()
            res = self._post(client, chats)
            elapsed = time.time() - t0
        self.assertEqual(res.status_code, 200)
        body = res.get_json()
        self.assertEqual(body['processed'], 5)
        # 3 workers * 0.4s ≈ 0.7s wall time; serial would be 2.0s.
        # Allow generous margin for CI noise.
        self.assertLess(elapsed, 1.6,
                        f'Expected parallel execution (<1.6s), got {elapsed:.2f}s')


class TestExtractRetryLogic(unittest.TestCase):
    """Verify extract_tasks retries on transient failures."""

    def setUp(self):
        from utils import gemini_client
        self.client = gemini_client

    def test_retries_on_first_failure_then_succeeds(self):
        """Two failures followed by success on attempt 3 returns data."""
        call_count = {'n': 0}

        def flaky_call(prompt, response_schema=None, timeout=60):
            call_count['n'] += 1
            if call_count['n'] < 3:
                return None
            return {'themes': [{'name': 't', 'description': 'd', 'tasks': []}]}

        with patch.object(self.client, '_call_gemini', side_effect=flaky_call), \
             patch.object(self.client, 'GEMINI_API_KEY', 'fake-key'), \
             patch('time.sleep') as m_sleep, \
             patch.object(self.client, 'get_user_identity',
                          return_value={'push_name': 'me', 'jid': 'me@s'}):
            result = self.client.extract_tasks('G', [{'sender': 'a', 'content': 'b', 'is_from_me': False}])
        self.assertEqual(call_count['n'], 3)
        self.assertEqual(result['themes'][0]['name'], 't')
        # Backoff should have slept twice (1s, 2s) between retries
        self.assertEqual(m_sleep.call_count, 2)
        self.assertEqual(m_sleep.call_args_list[0].args, (1,))
        self.assertEqual(m_sleep.call_args_list[1].args, (2,))

    def test_returns_error_after_all_attempts_fail(self):
        """After 3 failed attempts, return themes=[] with error key."""
        with patch.object(self.client, '_call_gemini', return_value=None), \
             patch.object(self.client, 'GEMINI_API_KEY', 'fake-key'), \
             patch('time.sleep'), \
             patch.object(self.client, 'get_user_identity',
                          return_value={'push_name': 'me', 'jid': 'me@s'}):
            result = self.client.extract_tasks('G', [{'sender': 'a', 'content': 'b', 'is_from_me': False}])
        self.assertEqual(result['themes'], [])
        self.assertIn('error', result)

    def test_no_retry_on_immediate_success(self):
        """If the first attempt returns themes, no sleep should occur."""
        with patch.object(self.client, '_call_gemini', return_value={'themes': []}), \
             patch.object(self.client, 'GEMINI_API_KEY', 'fake-key'), \
             patch('time.sleep') as m_sleep, \
             patch.object(self.client, 'get_user_identity',
                          return_value={'push_name': 'me', 'jid': 'me@s'}):
            self.client.extract_tasks('G', [{'sender': 'a', 'content': 'b', 'is_from_me': False}])
        m_sleep.assert_not_called()


class TestExtractStreamEndpoint(unittest.TestCase):
    """Verify the SSE stream emits one chat event per completed group."""

    def setUp(self):
        if os.path.exists(TEST_DB):
            os.remove(TEST_DB)
        db.init_db(force=True)

    @staticmethod
    def _parse_sse(body):
        events = []
        for block in body.split('\n\n'):
            block = block.strip()
            if not block:
                continue
            event_name = 'message'
            data_str = ''
            for line in block.split('\n'):
                if line.startswith('event:'):
                    event_name = line[len('event:'):].strip()
                elif line.startswith('data:'):
                    data_str += line[len('data:'):].strip()
            if data_str:
                try:
                    events.append((event_name, json.loads(data_str)))
                except json.JSONDecodeError:
                    pass
        return events

    @patch('routes.tasks.save_extracted_themes_and_tasks')
    @patch('routes.tasks.extract_tasks',
           return_value={'themes': [{'name': 't', 'description': 'd',
                                     'tasks': [{'title': 'A', 'status': 'pending'}]}]})
    @patch('routes.tasks.fetch_chat_messages_since',
           return_value=[{'sender': 'x', 'content': 'y', 'is_from_me': False}])
    def test_stream_emits_meta_chat_and_done(self, m_fetch, m_extract, m_save):
        """Stream must emit meta, one chat per group, then done."""
        chats = [
            {'jid': 'a@g.us', 'name': 'A', 'category': 'Work'},
            {'jid': 'b@g.us', 'name': 'B', 'category': 'Personal'},
        ]
        client = app.test_client()
        res = client.post('/api/tasks/extract/stream',
                          json={'chats': chats})
        self.assertEqual(res.status_code, 200)
        events = self._parse_sse(res.get_data(as_text=True))
        # meta + 2 chats + done
        self.assertEqual(events[0][0], 'meta')
        self.assertEqual(events[0][1]['total'], 2)
        chat_events = [e for e in events if e[0] == 'chat']
        self.assertEqual(len(chat_events), 2)
        for ev_name, ev_data in chat_events:
            self.assertEqual(ev_data['status'], 'ok')
            self.assertEqual(ev_data['task_count'], 1)
            self.assertIn('jid', ev_data)
            self.assertIn('name', ev_data)
        done = events[-1]
        self.assertEqual(done[0], 'done')
        self.assertTrue(done[1]['ok'])
        self.assertEqual(done[1]['processed'], 2)

    @patch('routes.tasks.save_extracted_themes_and_tasks')
    @patch('routes.tasks.fetch_chat_messages_since', return_value=[])
    def test_stream_emits_no_messages_status(self, m_fetch, m_save):
        """Chats with no 30d history must show up as no_messages events."""
        client = app.test_client()
        res = client.post('/api/tasks/extract/stream',
                          json={'chats': [{'jid': 'e@g.us', 'name': 'E'}]})
        events = self._parse_sse(res.get_data(as_text=True))
        chat = next(e for e in events if e[0] == 'chat')
        self.assertEqual(chat[1]['status'], 'no_messages')
        # Should NOT have hit Gemini
        m_save.assert_not_called()

    @patch('routes.tasks.save_extracted_themes_and_tasks')
    @patch('routes.tasks.extract_tasks',
           return_value={'themes': [], 'error': 'rate limit'})
    @patch('routes.tasks.fetch_chat_messages_since',
           return_value=[{'sender': 'x', 'content': 'y', 'is_from_me': False}])
    def test_stream_emits_gemini_failure(self, m_fetch, m_extract, m_save):
        """When extract_tasks returns an error, status=gemini_failed."""
        client = app.test_client()
        res = client.post('/api/tasks/extract/stream',
                          json={'chats': [{'jid': 'g@g.us', 'name': 'G'}]})
        events = self._parse_sse(res.get_data(as_text=True))
        chat = next(e for e in events if e[0] == 'chat')
        self.assertEqual(chat[1]['status'], 'gemini_failed')
        self.assertIn('rate limit', chat[1].get('error', ''))
        m_save.assert_not_called()

    def test_stream_rejects_empty_chats(self):
        client = app.test_client()
        res = client.post('/api/tasks/extract/stream', json={'chats': []})
        self.assertEqual(res.status_code, 400)
        self.assertFalse(res.get_json()['ok'])

    @patch('routes.tasks.fetch_chat_messages_since', return_value=[])
    def test_stream_response_headers_disable_buffering(self, m_fetch):
        """SSE responses must disable proxy buffering for real-time UX."""
        client = app.test_client()
        res = client.post('/api/tasks/extract/stream',
                          json={'chats': [{'jid': 'x@g.us', 'name': 'X'}]})
        self.assertEqual(res.status_code, 200)
        self.assertIn('text/event-stream', res.headers.get('Content-Type', ''))
        self.assertEqual(res.headers.get('X-Accel-Buffering'), 'no')


def tearDownModule():
    if os.path.exists(TEST_DB):
        try:
            os.remove(TEST_DB)
        except OSError:
            pass


if __name__ == '__main__':
    unittest.main(verbosity=2)
