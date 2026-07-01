"""
TaskDog v2 — Integration tests.

Covers database CRUD, setup routes, pipeline routes (with mocked Gemini),
and dashboard endpoints.

Run with:
    cd taskdog-backend
    DATABASE_PATH_V2=$(mktemp) venv/bin/python -m unittest tests.test_v2 -v
"""
import os
import sys
import json
import tempfile
import unittest
from unittest.mock import patch, MagicMock

# Ensure backend root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Use temp databases so tests don't touch real ones
TEST_DB_V2 = tempfile.mktemp(suffix='.db')
TEST_DB_V1 = tempfile.mktemp(suffix='.db')
os.environ['DATABASE_PATH_V2'] = TEST_DB_V2
os.environ['DATABASE_PATH'] = TEST_DB_V1

# Import after setting env vars
import models.database_v2 as db2  # noqa: E402
from models.database_v2 import (  # noqa: E402
    init_db_v2, insert_groups, get_groups, get_group,
    insert_tasks, get_tasks_by_group, get_task, get_all_tasks,
    get_dashboard_stats, update_task_status, update_task_importance,
    update_task_progress, update_task_deep_dive, get_tasks_for_refresh,
    insert_task_messages, get_task_messages, record_followup,
    get_followup_history, update_group_refreshed_at,
)
from app import app  # noqa: E402


class TestDatabaseV2(unittest.TestCase):
    """Test v2 database schema + CRUD functions."""

    @classmethod
    def setUpClass(cls):
        init_db_v2()

    def setUp(self):
        # Clean tables before each test
        conn = db2.get_db_connection_v2()
        conn.execute("DELETE FROM followup_history")
        conn.execute("DELETE FROM task_messages")
        conn.execute("DELETE FROM tasks")
        conn.execute("DELETE FROM groups")
        conn.commit()
        conn.close()

    def test_init_db_creates_tables(self):
        """All 4 tables should exist."""
        conn = db2.get_db_connection_v2()
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = {r[0] for r in cursor.fetchall()}
        conn.close()
        self.assertIn('groups', tables)
        self.assertIn('tasks', tables)
        self.assertIn('task_messages', tables)
        self.assertIn('followup_history', tables)

    def test_insert_and_get_groups(self):
        insert_groups(
            ['jid1@g.us', 'jid2@g.us'],
            ['Group One', 'Group Two'],
            ['Work', 'Personal'],
            ['TLDR 1', 'TLDR 2'],
        )
        groups = get_groups()
        self.assertEqual(len(groups), 2)
        g = get_group('jid1@g.us')
        self.assertEqual(g['name'], 'Group One')
        self.assertEqual(g['category'], 'Work')

    def test_insert_and_get_tasks(self):
        insert_groups(['test@g.us'], ['Test Group'], ['Work'], ['TLDR'])
        tasks = insert_tasks([
            {'title': 'Task A', 'status': 'active', 'importance': 4,
             'assignee': 'Priya', 'context': 'Do X', 'people': []},
            {'title': 'Task B', 'status': 'completed', 'importance': 2,
             'assignee': 'Rahul', 'context': 'Done Y', 'people': []},
        ], 'test@g.us')
        self.assertEqual(len(tasks), 2)
        # Each should have a UUID id
        self.assertTrue(all(len(t['id']) > 10 for t in tasks))

        by_group = get_tasks_by_group('test@g.us')
        self.assertEqual(len(by_group), 2)
        # Sorted by importance DESC
        self.assertEqual(by_group[0]['title'], 'Task A')

    def test_update_task_status(self):
        insert_groups(['test@g.us'], ['Test'], ['Work'], [''])
        tasks = insert_tasks([
            {'title': 'Task', 'status': 'active', 'importance': 3,
             'assignee': 'X', 'context': '', 'people': []},
        ], 'test@g.us')
        task_id = tasks[0]['id']

        update_task_status(task_id, 'completed')
        task = get_task(task_id)
        self.assertEqual(task['status'], 'completed')

    def test_update_task_importance(self):
        insert_groups(['test@g.us'], ['Test'], ['Work'], [''])
        tasks = insert_tasks([
            {'title': 'Task', 'status': 'active', 'importance': 3,
             'assignee': 'X', 'context': '', 'people': []},
        ], 'test@g.us')
        task_id = tasks[0]['id']

        update_task_importance(task_id, 5)
        task = get_task(task_id)
        self.assertEqual(task['importance'], 5)

    def test_update_task_progress(self):
        insert_groups(['test@g.us'], ['Test'], ['Work'], [''])
        tasks = insert_tasks([
            {'title': 'Task', 'status': 'active', 'importance': 3,
             'assignee': 'X', 'context': '', 'people': []},
        ], 'test@g.us')
        task_id = tasks[0]['id']

        update_task_progress(task_id, "Priya shared updates")
        update_task_progress(task_id, "Rahul reviewed")
        task = get_task(task_id)
        self.assertEqual(len(task['progress_log']), 2)
        self.assertEqual(task['progress_log'][0]['summary'], "Priya shared updates")
        self.assertEqual(task['progress_log'][1]['summary'], "Rahul reviewed")

    def test_deep_dive_update(self):
        insert_groups(['test@g.us'], ['Test'], ['Work'], [''])
        tasks = insert_tasks([
            {'title': 'Task', 'status': 'active', 'importance': 3,
             'assignee': 'X', 'context': '', 'people': []},
        ], 'test@g.us')
        task_id = tasks[0]['id']

        update_task_deep_dive(
            task_id,
            wiki="## Wiki\nContent",
            people=[{'name': 'Priya', 'role': 'assignee', 'jid': '123@s.w'}],
            progress_log=[{'date': '2026-06-20', 'summary': 'Started'}],
            blockers=[{'description': 'Waiting', 'raised_by': 'Priya', 'date': '2026-06-20'}],
            decisions=[{'description': 'Go ahead', 'made_by': 'Sam', 'date': '2026-06-20'}],
            importance=5,
        )
        task = get_task(task_id)
        self.assertEqual(task['wiki'], "## Wiki\nContent")
        self.assertEqual(len(task['people']), 1)
        self.assertEqual(task['people'][0]['name'], 'Priya')
        self.assertEqual(task['importance'], 5)
        self.assertIsNotNone(task['last_deep_dived_at'])

    def test_dashboard_stats(self):
        insert_groups(['test@g.us'], ['Test'], ['Work'], [''])
        insert_tasks([
            {'title': 'T1', 'status': 'active', 'importance': 5, 'assignee': '', 'context': '', 'people': []},
            {'title': 'T2', 'status': 'active', 'importance': 3, 'assignee': '', 'context': '', 'people': []},
            {'title': 'T3', 'status': 'completed', 'importance': 2, 'assignee': '', 'context': '', 'people': []},
            {'title': 'T4', 'status': 'archived', 'importance': 1, 'assignee': '', 'context': '', 'people': []},
        ], 'test@g.us')
        stats = get_dashboard_stats()
        self.assertEqual(stats['active'], 2)
        self.assertEqual(stats['completed'], 1)
        self.assertEqual(stats['archived'], 1)
        self.assertEqual(stats['total'], 4)
        self.assertEqual(stats['high_priority'], 1)

    def test_task_messages(self):
        insert_groups(['test@g.us'], ['Test'], ['Work'], [''])
        tasks = insert_tasks([
            {'title': 'Task', 'status': 'active', 'importance': 3,
             'assignee': '', 'context': '', 'people': []},
        ], 'test@g.us')
        task_id = tasks[0]['id']

        insert_task_messages(task_id, [
            {'message_content': 'Hey', 'sender_name': 'Sam', 'message_time': '2026-06-15', 'relevance': 0.9},
            {'message_content': 'Hi', 'sender_name': 'Priya', 'message_time': '2026-06-16', 'relevance': 0.8},
        ])
        msgs = get_task_messages(task_id)
        self.assertEqual(len(msgs), 2)

    def test_followup_history(self):
        insert_groups(['test@g.us'], ['Test'], ['Work'], [''])
        tasks = insert_tasks([
            {'title': 'Task', 'status': 'active', 'importance': 3,
             'assignee': '', 'context': '', 'people': []},
        ], 'test@g.us')
        task_id = tasks[0]['id']

        record_followup(task_id, 'Can you update?', 'test@g.us')
        record_followup(task_id, 'Following up', 'test@g.us')
        hist = get_followup_history()
        self.assertEqual(len(hist), 2)

    def test_get_tasks_for_refresh(self):
        insert_groups(['test@g.us'], ['Test'], ['Work'], [''])
        insert_tasks([
            {'title': 'T1', 'status': 'active', 'importance': 4, 'assignee': 'A', 'context': 'C', 'people': []},
            {'title': 'T2', 'status': 'completed', 'importance': 2, 'assignee': 'B', 'context': 'D', 'people': []},
        ], 'test@g.us')
        refresh_data = get_tasks_for_refresh('test@g.us')
        self.assertEqual(len(refresh_data), 2)
        # Each should have id, title, status, importance, assignee, context
        for t in refresh_data:
            self.assertIn('id', t)
            self.assertIn('title', t)
            self.assertIn('status', t)


class TestSetupRoutes(unittest.TestCase):
    """Test setup/health endpoints."""

    @classmethod
    def setUpClass(cls):
        init_db_v2()
        app.config['TESTING'] = True

    def setUp(self):
        self.client = app.test_client()

    def test_health_endpoint(self):
        res = self.client.get('/api/health')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertIn('gemini_key_set', data)
        self.assertIn('bridge_status', data)

    @patch('routes.setup.requests.get')
    def test_validate_key_valid(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_get.return_value = mock_resp

        res = self.client.post('/api/setup/validate-key',
                               json={'key': 'AIzaSyTestKey123'})
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data['ok'])
        self.assertIn('preview', data)

    @patch('routes.setup.requests.get')
    def test_validate_key_invalid(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.status_code = 403
        mock_get.return_value = mock_resp

        res = self.client.post('/api/setup/validate-key',
                               json={'key': 'invalid_key'})
        data = res.get_json()
        self.assertFalse(data['ok'])
        self.assertIn('error', data)

    def test_validate_key_missing(self):
        res = self.client.post('/api/setup/validate-key', json={})
        self.assertEqual(res.status_code, 400)


class TestDashboardRoutes(unittest.TestCase):
    """Test dashboard routes."""

    @classmethod
    def setUpClass(cls):
        init_db_v2()
        app.config['TESTING'] = True

    def setUp(self):
        self.client = app.test_client()
        # Clean and seed
        conn = db2.get_db_connection_v2()
        conn.execute("DELETE FROM followup_history")
        conn.execute("DELETE FROM task_messages")
        conn.execute("DELETE FROM tasks")
        conn.execute("DELETE FROM groups")
        conn.commit()
        conn.close()

        insert_groups(['dash@g.us'], ['Dash Group'], ['Work'], ['TLDR'])
        self.task_list = insert_tasks([
            {'title': 'High Priority Task', 'status': 'active', 'importance': 5,
             'assignee': 'Priya', 'context': 'Important', 'people': []},
            {'title': 'Low Priority Task', 'status': 'active', 'importance': 2,
             'assignee': 'Rahul', 'context': 'Minor', 'people': []},
            {'title': 'Done Task', 'status': 'completed', 'importance': 3,
             'assignee': 'Sam', 'context': 'Finished', 'people': []},
        ], 'dash@g.us')

    def test_dashboard_returns_tasks_sorted(self):
        res = self.client.get('/api/dashboard')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data['ok'])
        self.assertEqual(len(data['tasks']), 3)
        # Sorted by importance DESC
        self.assertEqual(data['tasks'][0]['title'], 'High Priority Task')
        self.assertEqual(data['tasks'][0]['importance'], 5)

    def test_dashboard_stats(self):
        res = self.client.get('/api/dashboard')
        data = res.get_json()
        stats = data['stats']
        self.assertEqual(stats['active'], 2)
        self.assertEqual(stats['completed'], 1)
        self.assertEqual(stats['total'], 3)
        self.assertEqual(stats['high_priority'], 1)

    def test_dashboard_filter_by_group(self):
        res = self.client.get('/api/dashboard?group_jid=dash@g.us')
        data = res.get_json()
        self.assertEqual(len(data['tasks']), 3)

    def test_task_detail(self):
        task_id = self.task_list[0]['id']
        res = self.client.get(f'/api/tasks/{task_id}')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data['task']['title'], 'High Priority Task')

    def test_task_detail_not_found(self):
        res = self.client.get('/api/tasks/nonexistent-id')
        self.assertEqual(res.status_code, 404)

    def test_update_task_status(self):
        task_id = self.task_list[0]['id']
        res = self.client.patch(f'/api/tasks/{task_id}',
                                json={'status': 'completed'})
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data['ok'])

        # Verify
        task = get_task(task_id)
        self.assertEqual(task['status'], 'completed')

    def test_update_task_importance(self):
        task_id = self.task_list[0]['id']
        res = self.client.patch(f'/api/tasks/{task_id}',
                                json={'importance': 1})
        self.assertEqual(res.status_code, 200)
        task = get_task(task_id)
        self.assertEqual(task['importance'], 1)

    def test_update_task_invalid_status(self):
        task_id = self.task_list[0]['id']
        res = self.client.patch(f'/api/tasks/{task_id}',
                                json={'status': 'invalid'})
        self.assertEqual(res.status_code, 400)

    def test_update_task_invalid_importance(self):
        task_id = self.task_list[0]['id']
        res = self.client.patch(f'/api/tasks/{task_id}',
                                json={'importance': 99})
        self.assertEqual(res.status_code, 400)

    def test_task_messages(self):
        task_id = self.task_list[0]['id']
        insert_task_messages(task_id, [
            {'message_content': 'Test msg', 'sender_name': 'Sam',
             'message_time': '2026-06-15', 'relevance': 0.9},
        ])
        res = self.client.get(f'/api/tasks/{task_id}/messages')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(len(data['messages']), 1)


class TestDiscoveryRoute(unittest.TestCase):
    """Test discovery pipeline route with mocked Gemini."""

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
        insert_groups(['disc@g.us'], ['Disc Group'], ['Work'], ['TLDR'])

    @patch('routes.pipeline.fetch_chat_messages_since')
    @patch('routes.pipeline.discover_tasks')
    def test_discover_saves_tasks(self, mock_discover, mock_fetch):
        mock_fetch.return_value = [
            {'sender': 'Sam', 'content': 'Do the thing', 'timestamp': '2026-06-15', 'is_from_me': False},
        ]
        mock_discover.return_value = {
            'tasks': [
                {
                    'title': 'Test Task',
                    'status': 'active',
                    'importance': 4,
                    'assignee': 'Priya',
                    'context': 'Do the thing',
                    'people': [{'name': 'Priya', 'role': 'assignee'}],
                    'suggested_responses': {
                        'concise': 'Hi',
                        'moderate': 'Hi there',
                        'with_context': 'Hi with context',
                    },
                    'relevant_message_indices': [0],
                }
            ]
        }

        res = self.client.post('/api/pipeline/discover',
                               json={'group_jids': ['disc@g.us']})
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data['ok'])
        self.assertEqual(data['summary']['total_tasks_found'], 1)

        # Verify task saved to DB
        tasks = get_tasks_by_group('disc@g.us')
        self.assertEqual(len(tasks), 1)
        self.assertEqual(tasks[0]['title'], 'Test Task')

        # Verify messages saved
        msgs = get_task_messages(tasks[0]['id'])
        self.assertEqual(len(msgs), 1)

    @patch('routes.pipeline.fetch_chat_messages_since')
    def test_discover_no_messages(self, mock_fetch):
        mock_fetch.return_value = []
        res = self.client.post('/api/pipeline/discover',
                               json={'group_jids': ['disc@g.us']})
        data = res.get_json()
        self.assertEqual(data['results'][0]['status'], 'no_messages')


class TestDeepDiveRoute(unittest.TestCase):
    """Test deep-dive pipeline route with mocked Gemini."""

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
        insert_groups(['dd@g.us'], ['DD Group'], ['Work'], ['TLDR'])
        self.tasks = insert_tasks([
            {'title': 'Deep Dive Task', 'status': 'active', 'importance': 3,
             'assignee': 'Priya', 'context': 'Some context', 'people': []},
        ], 'dd@g.us')

    @patch('routes.pipeline.fetch_chat_messages_since')
    @patch('routes.pipeline.deep_dive_task')
    def test_deep_dive_saves_wiki(self, mock_dd, mock_fetch):
        mock_fetch.return_value = [
            {'sender': 'Sam', 'content': 'Discuss task', 'timestamp': '2026-06-10', 'is_from_me': False},
        ]
        mock_dd.return_value = {
            'wiki': '## Task Wiki\n\nThis is the wiki content.',
            'people': [{'name': 'Priya', 'role': 'assignee', 'jid': '123@s.w'}],
            'progress_log': [{'date': '2026-06-10', 'summary': 'Started discussion'}],
            'blockers': [{'description': 'Waiting', 'raised_by': 'Priya', 'date': '2026-06-10'}],
            'decisions': [{'description': 'Go ahead', 'made_by': 'Sam', 'date': '2026-06-10'}],
            'importance': 5,
        }

        task_id = self.tasks[0]['id']
        res = self.client.post('/api/pipeline/deep-dive',
                               json={'task_id': task_id})
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data['ok'])
        self.assertIn('wiki', data['task'])
        self.assertEqual(data['task']['importance'], 5)

        # Verify saved to DB
        task = get_task(task_id)
        self.assertEqual(task['wiki'], '## Task Wiki\n\nThis is the wiki content.')
        self.assertEqual(len(task['people']), 1)
        self.assertIsNotNone(task['last_deep_dived_at'])

    def test_deep_dive_task_not_found(self):
        res = self.client.post('/api/pipeline/deep-dive',
                               json={'task_id': 'nonexistent'})
        self.assertEqual(res.status_code, 404)

    def test_deep_dive_missing_task_id(self):
        res = self.client.post('/api/pipeline/deep-dive', json={})
        self.assertEqual(res.status_code, 400)


if __name__ == '__main__':
    unittest.main()
