"""
Phase 9 Testing: Authorization Fix for Comments and Attachments
Tests the fix for 'Failed to fetch task details' error when viewing tasks not assigned to user.

Key fixes tested:
1. All users can view all tasks
2. All users can view comments on any task
3. All users can add comments on any task
4. All users can view attachments on any task
5. Case-insensitive title sorting
"""

import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
CREDENTIALS = {
    "admin": {"email": "admin@tripstars.com", "password": "Admin@123"},
    "manager": {"email": "manager@tripstars.com", "password": "Manager@123"},
    "member": {"email": "member@tripstars.com", "password": "Member@123"}
}

# User IDs from the test request
USER_IDS = {
    "admin": "9349d6c2-5509-4560-907b-b09d9700c9db",
    "manager": "3ce88087-bc7c-4e77-af9f-2453f6ac3443",
    "member": "c2f0c397-f3e6-47fa-bcac-f1106b052dee"
}


class TestAuthorizationFix:
    """Test authorization fixes for comments and attachments"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test session"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        self.tokens = {}
        self.created_task_id = None
        self.created_comment_id = None
        
    def login(self, role):
        """Login and get token for a specific role"""
        if role in self.tokens:
            self.session.headers.update({"Authorization": f"Bearer {self.tokens[role]}"})
            return self.tokens[role]
            
        creds = CREDENTIALS[role]
        response = self.session.post(f"{BASE_URL}/api/auth/login", json=creds)
        assert response.status_code == 200, f"Login failed for {role}: {response.text}"
        token = response.json().get("access_token")
        self.tokens[role] = token
        self.session.headers.update({"Authorization": f"Bearer {token}"})
        return token
    
    # ==================== TASK CREATION TESTS ====================
    
    def test_admin_can_create_task(self):
        """Admin should be able to create tasks"""
        self.login("admin")
        task_data = {
            "title": f"TEST_Admin_Task_{uuid.uuid4().hex[:8]}",
            "description": "Task created by admin for testing",
            "priority": "high",
            "assigned_to": USER_IDS["member"],
            "due_date": "2026-02-15"
        }
        response = self.session.post(f"{BASE_URL}/api/tasks", json=task_data)
        assert response.status_code == 201, f"Admin task creation failed: {response.text}"
        data = response.json()
        assert data["title"] == task_data["title"]
        assert data["assigned_to"] == USER_IDS["member"]
        print(f"PASS: Admin created task {data['id']}")
        
    def test_manager_can_create_task(self):
        """Manager should be able to create tasks"""
        self.login("manager")
        task_data = {
            "title": f"TEST_Manager_Task_{uuid.uuid4().hex[:8]}",
            "description": "Task created by manager for testing",
            "priority": "medium",
            "assigned_to": USER_IDS["admin"],
            "due_date": "2026-02-20"
        }
        response = self.session.post(f"{BASE_URL}/api/tasks", json=task_data)
        assert response.status_code == 201, f"Manager task creation failed: {response.text}"
        data = response.json()
        assert data["title"] == task_data["title"]
        print(f"PASS: Manager created task {data['id']}")
        
    def test_member_can_create_task(self):
        """Team member should be able to create tasks"""
        self.login("member")
        task_data = {
            "title": f"TEST_Member_Task_{uuid.uuid4().hex[:8]}",
            "description": "Task created by team member for testing",
            "priority": "low",
            "assigned_to": USER_IDS["manager"],  # Member can assign to manager
            "due_date": "2026-02-25"
        }
        response = self.session.post(f"{BASE_URL}/api/tasks", json=task_data)
        assert response.status_code == 201, f"Member task creation failed: {response.text}"
        data = response.json()
        assert data["title"] == task_data["title"]
        print(f"PASS: Team member created task {data['id']}")
        
    def test_member_cannot_assign_to_admin(self):
        """Team member should NOT be able to assign tasks to admin"""
        self.login("member")
        task_data = {
            "title": f"TEST_Invalid_Task_{uuid.uuid4().hex[:8]}",
            "description": "This should fail",
            "priority": "low",
            "assigned_to": USER_IDS["admin"],  # Member cannot assign to admin
            "due_date": "2026-02-25"
        }
        response = self.session.post(f"{BASE_URL}/api/tasks", json=task_data)
        assert response.status_code == 403, f"Expected 403, got {response.status_code}"
        print("PASS: Team member correctly blocked from assigning to admin")
    
    # ==================== TASK VIEWING TESTS ====================
    
    def test_all_users_see_all_tasks(self):
        """All users should see all tasks"""
        task_counts = {}
        
        for role in ["admin", "manager", "member"]:
            self.login(role)
            response = self.session.get(f"{BASE_URL}/api/tasks")
            assert response.status_code == 200, f"{role} failed to get tasks: {response.text}"
            task_counts[role] = len(response.json())
            print(f"{role.capitalize()} sees {task_counts[role]} tasks")
        
        # All users should see the same number of tasks
        assert task_counts["admin"] == task_counts["manager"] == task_counts["member"], \
            f"Task counts differ: {task_counts}"
        print(f"PASS: All users see same {task_counts['admin']} tasks")
    
    # ==================== TASK DETAIL WITH COMMENTS/ATTACHMENTS ====================
    
    def test_member_can_view_task_not_assigned_to_them(self):
        """Team member should be able to view task details for tasks not assigned to them"""
        # First, admin creates a task assigned to manager
        self.login("admin")
        task_data = {
            "title": f"TEST_ViewTest_{uuid.uuid4().hex[:8]}",
            "description": "Task for view testing",
            "priority": "high",
            "assigned_to": USER_IDS["manager"],  # Assigned to manager, not member
            "due_date": "2026-03-01"
        }
        create_response = self.session.post(f"{BASE_URL}/api/tasks", json=task_data)
        assert create_response.status_code == 201
        task_id = create_response.json()["id"]
        self.created_task_id = task_id
        
        # Now member tries to view this task
        self.login("member")
        view_response = self.session.get(f"{BASE_URL}/api/tasks/{task_id}")
        assert view_response.status_code == 200, f"Member failed to view task: {view_response.text}"
        
        task = view_response.json()
        assert task["id"] == task_id
        assert task["assigned_to"] == USER_IDS["manager"]
        print(f"PASS: Member can view task {task_id} assigned to manager")
        
        return task_id
    
    def test_member_can_view_comments_on_any_task(self):
        """Team member should be able to view comments on tasks not assigned to them"""
        # Create task assigned to manager
        self.login("admin")
        task_data = {
            "title": f"TEST_CommentView_{uuid.uuid4().hex[:8]}",
            "description": "Task for comment view testing",
            "priority": "medium",
            "assigned_to": USER_IDS["manager"],
            "due_date": "2026-03-05"
        }
        create_response = self.session.post(f"{BASE_URL}/api/tasks", json=task_data)
        assert create_response.status_code == 201
        task_id = create_response.json()["id"]
        
        # Admin adds a comment
        comment_response = self.session.post(f"{BASE_URL}/api/comments", json={
            "task_id": task_id,
            "content": "Admin comment for testing"
        })
        assert comment_response.status_code == 201
        
        # Member tries to view comments - THIS WAS THE BUG
        self.login("member")
        comments_response = self.session.get(f"{BASE_URL}/api/comments/task/{task_id}")
        assert comments_response.status_code == 200, \
            f"Member failed to view comments: {comments_response.text}"
        
        comments = comments_response.json()
        assert len(comments) >= 1
        print(f"PASS: Member can view {len(comments)} comments on task not assigned to them")
        
        return task_id
    
    def test_member_can_add_comment_on_any_task(self):
        """Team member should be able to add comments on tasks not assigned to them"""
        # Create task assigned to admin
        self.login("admin")
        task_data = {
            "title": f"TEST_CommentAdd_{uuid.uuid4().hex[:8]}",
            "description": "Task for comment add testing",
            "priority": "low",
            "assigned_to": USER_IDS["admin"],  # Assigned to admin
            "due_date": "2026-03-10"
        }
        create_response = self.session.post(f"{BASE_URL}/api/tasks", json=task_data)
        assert create_response.status_code == 201
        task_id = create_response.json()["id"]
        
        # Member tries to add a comment - THIS WAS THE BUG
        self.login("member")
        comment_data = {
            "task_id": task_id,
            "content": f"Member comment on admin's task - {uuid.uuid4().hex[:8]}"
        }
        comment_response = self.session.post(f"{BASE_URL}/api/comments", json=comment_data)
        assert comment_response.status_code == 201, \
            f"Member failed to add comment: {comment_response.text}"
        
        comment = comment_response.json()
        assert comment["content"] == comment_data["content"]
        assert comment["user_id"] == USER_IDS["member"]
        print(f"PASS: Member added comment on task assigned to admin")
        
        return task_id
    
    def test_member_can_view_attachments_on_any_task(self):
        """Team member should be able to view attachments on tasks not assigned to them"""
        # Create task assigned to manager
        self.login("admin")
        task_data = {
            "title": f"TEST_AttachView_{uuid.uuid4().hex[:8]}",
            "description": "Task for attachment view testing",
            "priority": "high",
            "assigned_to": USER_IDS["manager"],
            "due_date": "2026-03-15"
        }
        create_response = self.session.post(f"{BASE_URL}/api/tasks", json=task_data)
        assert create_response.status_code == 201
        task_id = create_response.json()["id"]
        
        # Member tries to view attachments - THIS WAS THE BUG
        self.login("member")
        attachments_response = self.session.get(f"{BASE_URL}/api/attachments/task/{task_id}")
        assert attachments_response.status_code == 200, \
            f"Member failed to view attachments: {attachments_response.text}"
        
        attachments = attachments_response.json()
        print(f"PASS: Member can view attachments on task not assigned to them ({len(attachments)} attachments)")
        
        return task_id
    
    def test_full_task_detail_flow_for_member(self):
        """
        Test the full task detail page flow for a member viewing a task not assigned to them.
        This simulates what the frontend does when loading TaskDetail.js
        """
        # Create task assigned to admin
        self.login("admin")
        task_data = {
            "title": f"TEST_FullFlow_{uuid.uuid4().hex[:8]}",
            "description": "Task for full flow testing",
            "priority": "high",
            "assigned_to": USER_IDS["admin"],
            "due_date": "2026-03-20"
        }
        create_response = self.session.post(f"{BASE_URL}/api/tasks", json=task_data)
        assert create_response.status_code == 201
        task_id = create_response.json()["id"]
        
        # Add a comment as admin
        self.session.post(f"{BASE_URL}/api/comments", json={
            "task_id": task_id,
            "content": "Admin's comment"
        })
        
        # Now member loads the task detail page (simulating Promise.all in frontend)
        self.login("member")
        
        # These 3 calls happen in parallel in TaskDetail.js
        task_response = self.session.get(f"{BASE_URL}/api/tasks/{task_id}")
        comments_response = self.session.get(f"{BASE_URL}/api/comments/task/{task_id}")
        attachments_response = self.session.get(f"{BASE_URL}/api/attachments/task/{task_id}")
        
        # All should succeed - this was the bug
        assert task_response.status_code == 200, f"Task fetch failed: {task_response.text}"
        assert comments_response.status_code == 200, f"Comments fetch failed: {comments_response.text}"
        assert attachments_response.status_code == 200, f"Attachments fetch failed: {attachments_response.text}"
        
        task = task_response.json()
        comments = comments_response.json()
        attachments = attachments_response.json()
        
        print(f"PASS: Full task detail flow works for member")
        print(f"  - Task: {task['title']}")
        print(f"  - Comments: {len(comments)}")
        print(f"  - Attachments: {len(attachments)}")
        
        return task_id
    
    # ==================== SORTING TESTS ====================
    
    def test_case_insensitive_title_sorting(self):
        """Test that title sorting is case-insensitive"""
        self.login("admin")
        
        # Create tasks with mixed case titles
        test_titles = [
            f"aaa_test_{uuid.uuid4().hex[:4]}",
            f"AAA_test_{uuid.uuid4().hex[:4]}",
            f"Bbb_test_{uuid.uuid4().hex[:4]}",
            f"bbb_test_{uuid.uuid4().hex[:4]}"
        ]
        
        created_ids = []
        for title in test_titles:
            response = self.session.post(f"{BASE_URL}/api/tasks", json={
                "title": title,
                "description": "Sort test task",
                "priority": "low",
                "assigned_to": USER_IDS["member"],
                "due_date": "2026-04-01"
            })
            if response.status_code == 201:
                created_ids.append(response.json()["id"])
        
        # Get tasks sorted by title ascending
        response = self.session.get(f"{BASE_URL}/api/tasks?sort_by=title&sort_order=asc")
        assert response.status_code == 200
        
        tasks = response.json()
        titles = [t["title"] for t in tasks]
        
        # Check that lowercase 'a' and uppercase 'A' are grouped together
        # With case-insensitive sorting, 'aaa' and 'AAA' should be adjacent
        print(f"First 10 titles (sorted): {titles[:10]}")
        
        # Verify sorting is case-insensitive by checking order
        titles_lower = [t.lower() for t in titles]
        assert titles_lower == sorted(titles_lower), "Title sorting should be case-insensitive"
        print("PASS: Title sorting is case-insensitive")
    
    # ==================== FILTER TESTS ====================
    
    def test_filter_by_status(self):
        """Test filtering tasks by status"""
        self.login("admin")
        
        for status in ["todo", "in_progress", "completed"]:
            response = self.session.get(f"{BASE_URL}/api/tasks?status={status}")
            assert response.status_code == 200
            tasks = response.json()
            for task in tasks:
                assert task["status"] == status, f"Expected status {status}, got {task['status']}"
            print(f"PASS: Filter by status={status} returns {len(tasks)} tasks")
    
    def test_filter_by_priority(self):
        """Test filtering tasks by priority"""
        self.login("admin")
        
        for priority in ["high", "medium", "low"]:
            response = self.session.get(f"{BASE_URL}/api/tasks?priority={priority}")
            assert response.status_code == 200
            tasks = response.json()
            for task in tasks:
                assert task["priority"] == priority, f"Expected priority {priority}, got {task['priority']}"
            print(f"PASS: Filter by priority={priority} returns {len(tasks)} tasks")
    
    def test_filter_by_assigned_to(self):
        """Test filtering tasks by assigned user"""
        self.login("admin")
        
        response = self.session.get(f"{BASE_URL}/api/tasks?assigned_to={USER_IDS['member']}")
        assert response.status_code == 200
        tasks = response.json()
        for task in tasks:
            assert task["assigned_to"] == USER_IDS["member"]
        print(f"PASS: Filter by assigned_to returns {len(tasks)} tasks")
    
    def test_search_by_title(self):
        """Test searching tasks by title"""
        self.login("admin")
        
        # Create a task with unique title
        unique_term = f"SEARCHTEST_{uuid.uuid4().hex[:8]}"
        self.session.post(f"{BASE_URL}/api/tasks", json={
            "title": f"Task with {unique_term} in title",
            "description": "Search test",
            "priority": "medium",
            "assigned_to": USER_IDS["member"],
            "due_date": "2026-04-15"
        })
        
        # Search for it
        response = self.session.get(f"{BASE_URL}/api/tasks?search={unique_term}")
        assert response.status_code == 200
        tasks = response.json()
        assert len(tasks) >= 1
        assert any(unique_term in t["title"] for t in tasks)
        print(f"PASS: Search by title found {len(tasks)} tasks")
    
    def test_task_stats_summary(self):
        """Test task stats summary endpoint"""
        self.login("admin")
        
        response = self.session.get(f"{BASE_URL}/api/tasks/stats/summary")
        assert response.status_code == 200
        
        stats = response.json()
        assert "total" in stats
        assert "by_status" in stats
        assert "by_priority" in stats
        assert "overdue" in stats
        assert "my_tasks" in stats
        
        print(f"PASS: Stats summary - Total: {stats['total']}, Overdue: {stats['overdue']}")


class TestCleanup:
    """Cleanup test data"""
    
    def test_cleanup_test_tasks(self):
        """Cancel all TEST_ prefixed tasks"""
        session = requests.Session()
        session.headers.update({"Content-Type": "application/json"})
        
        # Login as admin
        response = session.post(f"{BASE_URL}/api/auth/login", json=CREDENTIALS["admin"])
        if response.status_code != 200:
            pytest.skip("Could not login for cleanup")
        
        token = response.json().get("access_token")
        session.headers.update({"Authorization": f"Bearer {token}"})
        
        # Get all tasks
        response = session.get(f"{BASE_URL}/api/tasks?search=TEST_")
        if response.status_code != 200:
            pytest.skip("Could not fetch tasks for cleanup")
        
        tasks = response.json()
        cancelled = 0
        
        for task in tasks:
            if task["title"].startswith("TEST_") and task["status"] != "cancelled":
                cancel_response = session.patch(f"{BASE_URL}/api/tasks/{task['id']}/cancel")
                if cancel_response.status_code == 200:
                    cancelled += 1
        
        print(f"Cleanup: Cancelled {cancelled} test tasks")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
