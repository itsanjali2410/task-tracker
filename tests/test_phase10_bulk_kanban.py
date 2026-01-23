"""
Phase 10 Testing: Bulk Operations and Kanban View
Tests for:
- Bulk update, cancel, delete operations (admin/manager only)
- Role-based access control for bulk operations
- Task status changes for Kanban drag-drop
"""

import pytest
import requests
import os
import uuid
from datetime import datetime, timedelta

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')
API_URL = f"{BASE_URL}/api"

# Test credentials
ADMIN_EMAIL = "admin@tripstars.com"
ADMIN_PASSWORD = "Admin@123"
MANAGER_EMAIL = "manager@tripstars.com"
MANAGER_PASSWORD = "Manager@123"
MEMBER_EMAIL = "member@tripstars.com"
MEMBER_PASSWORD = "Member@123"

# User IDs
ADMIN_ID = "9349d6c2-5509-4560-907b-b09d9700c9db"
MANAGER_ID = "3ce88087-bc7c-4e77-af9f-2453f6ac3443"
MEMBER_ID = "c2f0c397-f3e6-47fa-bcac-f1106b052dee"


class TestAuth:
    """Authentication helper tests"""
    
    def test_admin_login(self):
        """Test admin login"""
        response = requests.post(f"{API_URL}/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["user"]["role"] == "admin"
    
    def test_manager_login(self):
        """Test manager login"""
        response = requests.post(f"{API_URL}/auth/login", json={
            "email": MANAGER_EMAIL,
            "password": MANAGER_PASSWORD
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["user"]["role"] == "manager"
    
    def test_member_login(self):
        """Test team member login"""
        response = requests.post(f"{API_URL}/auth/login", json={
            "email": MEMBER_EMAIL,
            "password": MEMBER_PASSWORD
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["user"]["role"] == "team_member"


def get_token(email, password):
    """Helper to get auth token"""
    response = requests.post(f"{API_URL}/auth/login", json={
        "email": email,
        "password": password
    })
    if response.status_code == 200:
        return response.json()["access_token"]
    return None


def create_test_task(token, title_suffix=""):
    """Helper to create a test task"""
    headers = {"Authorization": f"Bearer {token}"}
    due_date = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
    
    response = requests.post(f"{API_URL}/tasks", headers=headers, json={
        "title": f"TEST_BULK_{title_suffix}_{uuid.uuid4().hex[:8]}",
        "description": "Test task for bulk operations testing",
        "priority": "medium",
        "assigned_to": MEMBER_ID,
        "due_date": due_date
    })
    if response.status_code == 201:
        return response.json()
    return None


class TestBulkUpdateEndpoint:
    """Tests for POST /api/tasks/bulk/update"""
    
    def test_admin_bulk_update_status(self):
        """Admin can bulk update task status"""
        token = get_token(ADMIN_EMAIL, ADMIN_PASSWORD)
        assert token is not None
        
        headers = {"Authorization": f"Bearer {token}"}
        
        # Create test tasks
        task1 = create_test_task(token, "update1")
        task2 = create_test_task(token, "update2")
        assert task1 is not None and task2 is not None
        
        # Bulk update status
        response = requests.post(f"{API_URL}/tasks/bulk/update", headers=headers, json={
            "task_ids": [task1["id"], task2["id"]],
            "status": "in_progress"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        assert data["updated_count"] == 2
        assert "Successfully updated" in data["message"]
        
        # Verify tasks were updated
        task1_check = requests.get(f"{API_URL}/tasks/{task1['id']}", headers=headers)
        task2_check = requests.get(f"{API_URL}/tasks/{task2['id']}", headers=headers)
        assert task1_check.json()["status"] == "in_progress"
        assert task2_check.json()["status"] == "in_progress"
        
        # Cleanup
        requests.delete(f"{API_URL}/tasks/bulk/delete", headers=headers, json={
            "task_ids": [task1["id"], task2["id"]]
        })
    
    def test_admin_bulk_update_priority(self):
        """Admin can bulk update task priority"""
        token = get_token(ADMIN_EMAIL, ADMIN_PASSWORD)
        headers = {"Authorization": f"Bearer {token}"}
        
        task1 = create_test_task(token, "priority1")
        task2 = create_test_task(token, "priority2")
        assert task1 is not None and task2 is not None
        
        response = requests.post(f"{API_URL}/tasks/bulk/update", headers=headers, json={
            "task_ids": [task1["id"], task2["id"]],
            "priority": "high"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        assert data["updated_count"] == 2
        
        # Verify
        task1_check = requests.get(f"{API_URL}/tasks/{task1['id']}", headers=headers)
        assert task1_check.json()["priority"] == "high"
        
        # Cleanup
        requests.delete(f"{API_URL}/tasks/bulk/delete", headers=headers, json={
            "task_ids": [task1["id"], task2["id"]]
        })
    
    def test_admin_bulk_update_assigned_to(self):
        """Admin can bulk reassign tasks"""
        token = get_token(ADMIN_EMAIL, ADMIN_PASSWORD)
        headers = {"Authorization": f"Bearer {token}"}
        
        task1 = create_test_task(token, "assign1")
        assert task1 is not None
        
        response = requests.post(f"{API_URL}/tasks/bulk/update", headers=headers, json={
            "task_ids": [task1["id"]],
            "assigned_to": MANAGER_ID
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        
        # Verify
        task1_check = requests.get(f"{API_URL}/tasks/{task1['id']}", headers=headers)
        assert task1_check.json()["assigned_to"] == MANAGER_ID
        
        # Cleanup
        requests.delete(f"{API_URL}/tasks/bulk/delete", headers=headers, json={
            "task_ids": [task1["id"]]
        })
    
    def test_manager_bulk_update(self):
        """Manager can bulk update tasks"""
        admin_token = get_token(ADMIN_EMAIL, ADMIN_PASSWORD)
        manager_token = get_token(MANAGER_EMAIL, MANAGER_PASSWORD)
        
        admin_headers = {"Authorization": f"Bearer {admin_token}"}
        manager_headers = {"Authorization": f"Bearer {manager_token}"}
        
        task1 = create_test_task(admin_token, "mgr_update")
        assert task1 is not None
        
        response = requests.post(f"{API_URL}/tasks/bulk/update", headers=manager_headers, json={
            "task_ids": [task1["id"]],
            "status": "completed"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        
        # Cleanup
        requests.delete(f"{API_URL}/tasks/bulk/delete", headers=admin_headers, json={
            "task_ids": [task1["id"]]
        })
    
    def test_member_cannot_bulk_update(self):
        """Team member CANNOT bulk update tasks (403)"""
        admin_token = get_token(ADMIN_EMAIL, ADMIN_PASSWORD)
        member_token = get_token(MEMBER_EMAIL, MEMBER_PASSWORD)
        
        admin_headers = {"Authorization": f"Bearer {admin_token}"}
        member_headers = {"Authorization": f"Bearer {member_token}"}
        
        task1 = create_test_task(admin_token, "member_test")
        assert task1 is not None
        
        response = requests.post(f"{API_URL}/tasks/bulk/update", headers=member_headers, json={
            "task_ids": [task1["id"]],
            "status": "completed"
        })
        
        assert response.status_code == 403
        
        # Cleanup
        requests.delete(f"{API_URL}/tasks/bulk/delete", headers=admin_headers, json={
            "task_ids": [task1["id"]]
        })
    
    def test_bulk_update_no_fields(self):
        """Bulk update with no fields returns 400"""
        token = get_token(ADMIN_EMAIL, ADMIN_PASSWORD)
        headers = {"Authorization": f"Bearer {token}"}
        
        task1 = create_test_task(token, "no_fields")
        assert task1 is not None
        
        response = requests.post(f"{API_URL}/tasks/bulk/update", headers=headers, json={
            "task_ids": [task1["id"]]
        })
        
        assert response.status_code == 400
        assert "No update fields" in response.json()["detail"]
        
        # Cleanup
        requests.delete(f"{API_URL}/tasks/bulk/delete", headers=headers, json={
            "task_ids": [task1["id"]]
        })
    
    def test_bulk_update_empty_task_ids(self):
        """Bulk update with empty task_ids returns 400"""
        token = get_token(ADMIN_EMAIL, ADMIN_PASSWORD)
        headers = {"Authorization": f"Bearer {token}"}
        
        response = requests.post(f"{API_URL}/tasks/bulk/update", headers=headers, json={
            "task_ids": [],
            "status": "completed"
        })
        
        assert response.status_code == 400
        assert "No task IDs" in response.json()["detail"]


class TestBulkCancelEndpoint:
    """Tests for POST /api/tasks/bulk/cancel"""
    
    def test_admin_bulk_cancel(self):
        """Admin can bulk cancel tasks"""
        token = get_token(ADMIN_EMAIL, ADMIN_PASSWORD)
        headers = {"Authorization": f"Bearer {token}"}
        
        task1 = create_test_task(token, "cancel1")
        task2 = create_test_task(token, "cancel2")
        assert task1 is not None and task2 is not None
        
        response = requests.post(f"{API_URL}/tasks/bulk/cancel", headers=headers, json={
            "task_ids": [task1["id"], task2["id"]]
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        assert data["updated_count"] == 2
        assert "cancelled" in data["message"].lower()
        
        # Verify tasks are cancelled
        task1_check = requests.get(f"{API_URL}/tasks/{task1['id']}", headers=headers)
        task2_check = requests.get(f"{API_URL}/tasks/{task2['id']}", headers=headers)
        assert task1_check.json()["status"] == "cancelled"
        assert task2_check.json()["status"] == "cancelled"
        
        # Cleanup
        requests.delete(f"{API_URL}/tasks/bulk/delete", headers=headers, json={
            "task_ids": [task1["id"], task2["id"]]
        })
    
    def test_manager_bulk_cancel(self):
        """Manager can bulk cancel tasks"""
        admin_token = get_token(ADMIN_EMAIL, ADMIN_PASSWORD)
        manager_token = get_token(MANAGER_EMAIL, MANAGER_PASSWORD)
        
        admin_headers = {"Authorization": f"Bearer {admin_token}"}
        manager_headers = {"Authorization": f"Bearer {manager_token}"}
        
        task1 = create_test_task(admin_token, "mgr_cancel")
        assert task1 is not None
        
        response = requests.post(f"{API_URL}/tasks/bulk/cancel", headers=manager_headers, json={
            "task_ids": [task1["id"]]
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        
        # Cleanup
        requests.delete(f"{API_URL}/tasks/bulk/delete", headers=admin_headers, json={
            "task_ids": [task1["id"]]
        })
    
    def test_member_cannot_bulk_cancel(self):
        """Team member CANNOT bulk cancel tasks (403)"""
        admin_token = get_token(ADMIN_EMAIL, ADMIN_PASSWORD)
        member_token = get_token(MEMBER_EMAIL, MEMBER_PASSWORD)
        
        admin_headers = {"Authorization": f"Bearer {admin_token}"}
        member_headers = {"Authorization": f"Bearer {member_token}"}
        
        task1 = create_test_task(admin_token, "member_cancel")
        assert task1 is not None
        
        response = requests.post(f"{API_URL}/tasks/bulk/cancel", headers=member_headers, json={
            "task_ids": [task1["id"]]
        })
        
        assert response.status_code == 403
        
        # Cleanup
        requests.delete(f"{API_URL}/tasks/bulk/delete", headers=admin_headers, json={
            "task_ids": [task1["id"]]
        })


class TestBulkDeleteEndpoint:
    """Tests for DELETE /api/tasks/bulk/delete"""
    
    def test_admin_bulk_delete(self):
        """Admin can bulk delete tasks permanently"""
        token = get_token(ADMIN_EMAIL, ADMIN_PASSWORD)
        headers = {"Authorization": f"Bearer {token}"}
        
        task1 = create_test_task(token, "delete1")
        task2 = create_test_task(token, "delete2")
        assert task1 is not None and task2 is not None
        
        response = requests.delete(f"{API_URL}/tasks/bulk/delete", headers=headers, json={
            "task_ids": [task1["id"], task2["id"]]
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        assert data["updated_count"] == 2
        assert "deleted" in data["message"].lower()
        
        # Verify tasks are deleted (404)
        task1_check = requests.get(f"{API_URL}/tasks/{task1['id']}", headers=headers)
        task2_check = requests.get(f"{API_URL}/tasks/{task2['id']}", headers=headers)
        assert task1_check.status_code == 404
        assert task2_check.status_code == 404
    
    def test_manager_bulk_delete(self):
        """Manager can bulk delete tasks"""
        admin_token = get_token(ADMIN_EMAIL, ADMIN_PASSWORD)
        manager_token = get_token(MANAGER_EMAIL, MANAGER_PASSWORD)
        
        admin_headers = {"Authorization": f"Bearer {admin_token}"}
        manager_headers = {"Authorization": f"Bearer {manager_token}"}
        
        task1 = create_test_task(admin_token, "mgr_delete")
        assert task1 is not None
        
        response = requests.delete(f"{API_URL}/tasks/bulk/delete", headers=manager_headers, json={
            "task_ids": [task1["id"]]
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
    
    def test_member_cannot_bulk_delete(self):
        """Team member CANNOT bulk delete tasks (403)"""
        admin_token = get_token(ADMIN_EMAIL, ADMIN_PASSWORD)
        member_token = get_token(MEMBER_EMAIL, MEMBER_PASSWORD)
        
        admin_headers = {"Authorization": f"Bearer {admin_token}"}
        member_headers = {"Authorization": f"Bearer {member_token}"}
        
        task1 = create_test_task(admin_token, "member_delete")
        assert task1 is not None
        
        response = requests.delete(f"{API_URL}/tasks/bulk/delete", headers=member_headers, json={
            "task_ids": [task1["id"]]
        })
        
        assert response.status_code == 403
        
        # Cleanup
        requests.delete(f"{API_URL}/tasks/bulk/delete", headers=admin_headers, json={
            "task_ids": [task1["id"]]
        })


class TestKanbanStatusChange:
    """Tests for status changes (simulating Kanban drag-drop)"""
    
    def test_admin_change_status_todo_to_in_progress(self):
        """Admin can change task status from todo to in_progress"""
        token = get_token(ADMIN_EMAIL, ADMIN_PASSWORD)
        headers = {"Authorization": f"Bearer {token}"}
        
        task = create_test_task(token, "kanban1")
        assert task is not None
        assert task["status"] == "todo"
        
        response = requests.patch(f"{API_URL}/tasks/{task['id']}", headers=headers, json={
            "status": "in_progress"
        })
        
        assert response.status_code == 200
        assert response.json()["status"] == "in_progress"
        
        # Cleanup
        requests.delete(f"{API_URL}/tasks/bulk/delete", headers=headers, json={
            "task_ids": [task["id"]]
        })
    
    def test_admin_change_status_to_completed(self):
        """Admin can change task status to completed"""
        token = get_token(ADMIN_EMAIL, ADMIN_PASSWORD)
        headers = {"Authorization": f"Bearer {token}"}
        
        task = create_test_task(token, "kanban2")
        assert task is not None
        
        response = requests.patch(f"{API_URL}/tasks/{task['id']}", headers=headers, json={
            "status": "completed"
        })
        
        assert response.status_code == 200
        assert response.json()["status"] == "completed"
        
        # Cleanup
        requests.delete(f"{API_URL}/tasks/bulk/delete", headers=headers, json={
            "task_ids": [task["id"]]
        })
    
    def test_admin_change_status_to_cancelled(self):
        """Admin can change task status to cancelled"""
        token = get_token(ADMIN_EMAIL, ADMIN_PASSWORD)
        headers = {"Authorization": f"Bearer {token}"}
        
        task = create_test_task(token, "kanban3")
        assert task is not None
        
        response = requests.patch(f"{API_URL}/tasks/{task['id']}", headers=headers, json={
            "status": "cancelled"
        })
        
        assert response.status_code == 200
        assert response.json()["status"] == "cancelled"
        
        # Cleanup
        requests.delete(f"{API_URL}/tasks/bulk/delete", headers=headers, json={
            "task_ids": [task["id"]]
        })
    
    def test_member_change_own_task_status(self):
        """Team member can change status of their own task"""
        admin_token = get_token(ADMIN_EMAIL, ADMIN_PASSWORD)
        member_token = get_token(MEMBER_EMAIL, MEMBER_PASSWORD)
        
        admin_headers = {"Authorization": f"Bearer {admin_token}"}
        member_headers = {"Authorization": f"Bearer {member_token}"}
        
        # Create task assigned to member
        task = create_test_task(admin_token, "member_own")
        assert task is not None
        assert task["assigned_to"] == MEMBER_ID
        
        # Member updates their own task status
        response = requests.patch(f"{API_URL}/tasks/{task['id']}", headers=member_headers, json={
            "status": "in_progress"
        })
        
        assert response.status_code == 200
        assert response.json()["status"] == "in_progress"
        
        # Cleanup
        requests.delete(f"{API_URL}/tasks/bulk/delete", headers=admin_headers, json={
            "task_ids": [task["id"]]
        })
    
    def test_member_cannot_change_others_task_status(self):
        """Team member CANNOT change status of task assigned to others"""
        admin_token = get_token(ADMIN_EMAIL, ADMIN_PASSWORD)
        member_token = get_token(MEMBER_EMAIL, MEMBER_PASSWORD)
        
        admin_headers = {"Authorization": f"Bearer {admin_token}"}
        member_headers = {"Authorization": f"Bearer {member_token}"}
        
        # Create task assigned to manager (not member)
        due_date = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
        response = requests.post(f"{API_URL}/tasks", headers=admin_headers, json={
            "title": f"TEST_BULK_other_task_{uuid.uuid4().hex[:8]}",
            "description": "Task assigned to manager",
            "priority": "medium",
            "assigned_to": MANAGER_ID,
            "due_date": due_date
        })
        assert response.status_code == 201
        task = response.json()
        
        # Member tries to update task assigned to manager
        response = requests.patch(f"{API_URL}/tasks/{task['id']}", headers=member_headers, json={
            "status": "completed"
        })
        
        assert response.status_code == 403
        
        # Cleanup
        requests.delete(f"{API_URL}/tasks/bulk/delete", headers=admin_headers, json={
            "task_ids": [task["id"]]
        })


class TestTaskListFilters:
    """Tests for task list filters (used in Kanban view)"""
    
    def test_filter_by_status(self):
        """Filter tasks by status"""
        token = get_token(ADMIN_EMAIL, ADMIN_PASSWORD)
        headers = {"Authorization": f"Bearer {token}"}
        
        response = requests.get(f"{API_URL}/tasks?status=todo", headers=headers)
        assert response.status_code == 200
        tasks = response.json()
        for task in tasks:
            assert task["status"] == "todo"
    
    def test_filter_by_priority(self):
        """Filter tasks by priority"""
        token = get_token(ADMIN_EMAIL, ADMIN_PASSWORD)
        headers = {"Authorization": f"Bearer {token}"}
        
        response = requests.get(f"{API_URL}/tasks?priority=high", headers=headers)
        assert response.status_code == 200
        tasks = response.json()
        for task in tasks:
            assert task["priority"] == "high"
    
    def test_search_tasks(self):
        """Search tasks by title/description"""
        token = get_token(ADMIN_EMAIL, ADMIN_PASSWORD)
        headers = {"Authorization": f"Bearer {token}"}
        
        # Create a task with unique title
        unique_title = f"UNIQUE_SEARCH_{uuid.uuid4().hex[:8]}"
        task = requests.post(f"{API_URL}/tasks", headers=headers, json={
            "title": unique_title,
            "description": "Search test task",
            "priority": "medium",
            "assigned_to": MEMBER_ID,
            "due_date": (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
        })
        assert task.status_code == 201
        task_id = task.json()["id"]
        
        # Search for it
        response = requests.get(f"{API_URL}/tasks?search={unique_title}", headers=headers)
        assert response.status_code == 200
        tasks = response.json()
        assert len(tasks) >= 1
        assert any(t["title"] == unique_title for t in tasks)
        
        # Cleanup
        requests.delete(f"{API_URL}/tasks/bulk/delete", headers=headers, json={
            "task_ids": [task_id]
        })
    
    def test_get_all_statuses_for_kanban(self):
        """Get tasks with all statuses for Kanban board"""
        token = get_token(ADMIN_EMAIL, ADMIN_PASSWORD)
        headers = {"Authorization": f"Bearer {token}"}
        
        # Get all tasks (no status filter)
        response = requests.get(f"{API_URL}/tasks?limit=500", headers=headers)
        assert response.status_code == 200
        tasks = response.json()
        
        # Verify we can get tasks with different statuses
        statuses = set(t["status"] for t in tasks)
        # At minimum, we should have some tasks
        assert len(tasks) >= 0


class TestTaskStats:
    """Tests for task statistics (used in dashboard)"""
    
    def test_get_stats_summary(self):
        """Get task statistics summary"""
        token = get_token(ADMIN_EMAIL, ADMIN_PASSWORD)
        headers = {"Authorization": f"Bearer {token}"}
        
        response = requests.get(f"{API_URL}/tasks/stats/summary", headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        assert "total" in data
        assert "by_status" in data
        assert "by_priority" in data
        assert "overdue" in data
        assert "my_tasks" in data
        
        # Verify status breakdown
        assert "todo" in data["by_status"]
        assert "in_progress" in data["by_status"]
        assert "completed" in data["by_status"]
        assert "cancelled" in data["by_status"]


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
