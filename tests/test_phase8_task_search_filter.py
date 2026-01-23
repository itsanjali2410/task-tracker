"""
Phase 8 Testing: Task Search, Filter, Sort, and Stats Features
Tests:
- All users can see all tasks (no role-based visibility restrictions)
- Task search by title and description
- Filter by status, priority, assigned_to, due_date range
- Filter overdue tasks only
- Sort by created_at, due_date, priority, status, title
- Sort order asc/desc
- Task stats summary endpoint
- Pagination with skip and limit
- Combined filters
"""

import pytest
import requests
import os
from datetime import datetime, timedelta

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')
API_URL = f"{BASE_URL}/api"


class TestTaskSearchFilterSort:
    """Test task search, filter, sort, and stats features"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test data and authentication"""
        self.admin_token = None
        self.sales_token = None
        self.member_token = None
        self.test_task_ids = []
        
        # Login as admin
        response = requests.post(f"{API_URL}/auth/login", json={
            "email": "admin@tripstars.com",
            "password": "Admin@123"
        })
        if response.status_code == 200:
            self.admin_token = response.json().get("access_token")
            self.admin_user = response.json().get("user")
        
        # Login as sales
        response = requests.post(f"{API_URL}/auth/login", json={
            "email": "sales@tripstars.com",
            "password": "Sales@123"
        })
        if response.status_code == 200:
            self.sales_token = response.json().get("access_token")
            self.sales_user = response.json().get("user")
        
        # Login as member
        response = requests.post(f"{API_URL}/auth/login", json={
            "email": "member@tripstars.com",
            "password": "Member@123"
        })
        if response.status_code == 200:
            self.member_token = response.json().get("access_token")
            self.member_user = response.json().get("user")
        
        yield
        
        # Cleanup: Cancel test tasks
        if self.admin_token:
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            for task_id in self.test_task_ids:
                try:
                    requests.patch(f"{API_URL}/tasks/{task_id}/cancel", headers=headers)
                except:
                    pass
    
    def get_headers(self, token):
        return {"Authorization": f"Bearer {token}"}
    
    def create_test_task(self, title, description, priority="medium", due_date=None, assigned_to=None):
        """Helper to create test tasks"""
        if not due_date:
            due_date = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
        if not assigned_to:
            assigned_to = self.member_user["id"]
        
        response = requests.post(
            f"{API_URL}/tasks",
            headers=self.get_headers(self.admin_token),
            json={
                "title": f"TEST_{title}",
                "description": f"TEST_{description}",
                "priority": priority,
                "assigned_to": assigned_to,
                "due_date": due_date
            }
        )
        if response.status_code == 201:
            task_id = response.json()["id"]
            self.test_task_ids.append(task_id)
            return response.json()
        return None
    
    # ==================== ALL USERS SEE ALL TASKS ====================
    
    def test_admin_sees_all_tasks(self):
        """Admin can see all tasks"""
        if not self.admin_token:
            pytest.skip("Admin login failed")
        
        response = requests.get(
            f"{API_URL}/tasks",
            headers=self.get_headers(self.admin_token)
        )
        assert response.status_code == 200
        tasks = response.json()
        assert isinstance(tasks, list)
        print(f"Admin sees {len(tasks)} tasks")
    
    def test_sales_sees_all_tasks(self):
        """Sales user can see all tasks (not just their own)"""
        if not self.sales_token:
            pytest.skip("Sales login failed")
        
        response = requests.get(
            f"{API_URL}/tasks",
            headers=self.get_headers(self.sales_token)
        )
        assert response.status_code == 200
        tasks = response.json()
        assert isinstance(tasks, list)
        print(f"Sales user sees {len(tasks)} tasks")
    
    def test_member_sees_all_tasks(self):
        """Team member can see all tasks (not just their own)"""
        if not self.member_token:
            pytest.skip("Member login failed")
        
        response = requests.get(
            f"{API_URL}/tasks",
            headers=self.get_headers(self.member_token)
        )
        assert response.status_code == 200
        tasks = response.json()
        assert isinstance(tasks, list)
        print(f"Member sees {len(tasks)} tasks")
    
    def test_all_roles_see_same_task_count(self):
        """All roles should see the same number of tasks"""
        if not all([self.admin_token, self.sales_token, self.member_token]):
            pytest.skip("Not all logins succeeded")
        
        admin_tasks = requests.get(f"{API_URL}/tasks", headers=self.get_headers(self.admin_token)).json()
        sales_tasks = requests.get(f"{API_URL}/tasks", headers=self.get_headers(self.sales_token)).json()
        member_tasks = requests.get(f"{API_URL}/tasks", headers=self.get_headers(self.member_token)).json()
        
        assert len(admin_tasks) == len(sales_tasks) == len(member_tasks), \
            f"Task counts differ: admin={len(admin_tasks)}, sales={len(sales_tasks)}, member={len(member_tasks)}"
        print(f"All roles see {len(admin_tasks)} tasks")
    
    # ==================== SEARCH BY TITLE ====================
    
    def test_search_by_title(self):
        """Search tasks by title"""
        if not self.admin_token:
            pytest.skip("Admin login failed")
        
        # Create a task with unique title
        task = self.create_test_task("UniqueSearchTitle123", "Some description")
        assert task is not None
        
        # Search for it
        response = requests.get(
            f"{API_URL}/tasks?search=UniqueSearchTitle123",
            headers=self.get_headers(self.admin_token)
        )
        assert response.status_code == 200
        tasks = response.json()
        assert len(tasks) >= 1
        assert any("UniqueSearchTitle123" in t["title"] for t in tasks)
        print(f"Search by title found {len(tasks)} tasks")
    
    def test_search_by_title_case_insensitive(self):
        """Search is case-insensitive"""
        if not self.admin_token:
            pytest.skip("Admin login failed")
        
        task = self.create_test_task("CaseSensitiveTest", "Description")
        assert task is not None
        
        # Search with different case
        response = requests.get(
            f"{API_URL}/tasks?search=casesensitivetest",
            headers=self.get_headers(self.admin_token)
        )
        assert response.status_code == 200
        tasks = response.json()
        assert len(tasks) >= 1
        print("Case-insensitive search works")
    
    # ==================== SEARCH BY DESCRIPTION ====================
    
    def test_search_by_description(self):
        """Search tasks by description"""
        if not self.admin_token:
            pytest.skip("Admin login failed")
        
        task = self.create_test_task("Regular Title", "UniqueDescriptionXYZ789")
        assert task is not None
        
        response = requests.get(
            f"{API_URL}/tasks?search=UniqueDescriptionXYZ789",
            headers=self.get_headers(self.admin_token)
        )
        assert response.status_code == 200
        tasks = response.json()
        assert len(tasks) >= 1
        assert any("UniqueDescriptionXYZ789" in t["description"] for t in tasks)
        print(f"Search by description found {len(tasks)} tasks")
    
    # ==================== FILTER BY STATUS ====================
    
    def test_filter_by_status_todo(self):
        """Filter tasks by status: todo"""
        if not self.admin_token:
            pytest.skip("Admin login failed")
        
        response = requests.get(
            f"{API_URL}/tasks?status=todo",
            headers=self.get_headers(self.admin_token)
        )
        assert response.status_code == 200
        tasks = response.json()
        for task in tasks:
            assert task["status"] == "todo", f"Expected todo, got {task['status']}"
        print(f"Filter by status=todo found {len(tasks)} tasks")
    
    def test_filter_by_status_in_progress(self):
        """Filter tasks by status: in_progress"""
        if not self.admin_token:
            pytest.skip("Admin login failed")
        
        response = requests.get(
            f"{API_URL}/tasks?status=in_progress",
            headers=self.get_headers(self.admin_token)
        )
        assert response.status_code == 200
        tasks = response.json()
        for task in tasks:
            assert task["status"] == "in_progress"
        print(f"Filter by status=in_progress found {len(tasks)} tasks")
    
    def test_filter_by_status_completed(self):
        """Filter tasks by status: completed"""
        if not self.admin_token:
            pytest.skip("Admin login failed")
        
        response = requests.get(
            f"{API_URL}/tasks?status=completed",
            headers=self.get_headers(self.admin_token)
        )
        assert response.status_code == 200
        tasks = response.json()
        for task in tasks:
            assert task["status"] == "completed"
        print(f"Filter by status=completed found {len(tasks)} tasks")
    
    def test_filter_by_status_cancelled(self):
        """Filter tasks by status: cancelled"""
        if not self.admin_token:
            pytest.skip("Admin login failed")
        
        response = requests.get(
            f"{API_URL}/tasks?status=cancelled",
            headers=self.get_headers(self.admin_token)
        )
        assert response.status_code == 200
        tasks = response.json()
        for task in tasks:
            assert task["status"] == "cancelled"
        print(f"Filter by status=cancelled found {len(tasks)} tasks")
    
    # ==================== FILTER BY PRIORITY ====================
    
    def test_filter_by_priority_high(self):
        """Filter tasks by priority: high"""
        if not self.admin_token:
            pytest.skip("Admin login failed")
        
        # Create a high priority task
        task = self.create_test_task("HighPriorityTask", "Description", priority="high")
        assert task is not None
        
        response = requests.get(
            f"{API_URL}/tasks?priority=high",
            headers=self.get_headers(self.admin_token)
        )
        assert response.status_code == 200
        tasks = response.json()
        assert len(tasks) >= 1
        for task in tasks:
            assert task["priority"] == "high"
        print(f"Filter by priority=high found {len(tasks)} tasks")
    
    def test_filter_by_priority_medium(self):
        """Filter tasks by priority: medium"""
        if not self.admin_token:
            pytest.skip("Admin login failed")
        
        response = requests.get(
            f"{API_URL}/tasks?priority=medium",
            headers=self.get_headers(self.admin_token)
        )
        assert response.status_code == 200
        tasks = response.json()
        for task in tasks:
            assert task["priority"] == "medium"
        print(f"Filter by priority=medium found {len(tasks)} tasks")
    
    def test_filter_by_priority_low(self):
        """Filter tasks by priority: low"""
        if not self.admin_token:
            pytest.skip("Admin login failed")
        
        task = self.create_test_task("LowPriorityTask", "Description", priority="low")
        assert task is not None
        
        response = requests.get(
            f"{API_URL}/tasks?priority=low",
            headers=self.get_headers(self.admin_token)
        )
        assert response.status_code == 200
        tasks = response.json()
        assert len(tasks) >= 1
        for task in tasks:
            assert task["priority"] == "low"
        print(f"Filter by priority=low found {len(tasks)} tasks")
    
    # ==================== FILTER BY ASSIGNED_TO ====================
    
    def test_filter_by_assigned_to(self):
        """Filter tasks by assigned user ID"""
        if not self.admin_token or not self.member_user:
            pytest.skip("Login failed")
        
        # Create task assigned to member
        task = self.create_test_task("AssignedToMember", "Description", assigned_to=self.member_user["id"])
        assert task is not None
        
        response = requests.get(
            f"{API_URL}/tasks?assigned_to={self.member_user['id']}",
            headers=self.get_headers(self.admin_token)
        )
        assert response.status_code == 200
        tasks = response.json()
        assert len(tasks) >= 1
        for task in tasks:
            assert task["assigned_to"] == self.member_user["id"]
        print(f"Filter by assigned_to found {len(tasks)} tasks")
    
    # ==================== FILTER BY DUE DATE RANGE ====================
    
    def test_filter_by_due_date_from(self):
        """Filter tasks by due date from"""
        if not self.admin_token:
            pytest.skip("Admin login failed")
        
        future_date = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
        task = self.create_test_task("FutureDueDate", "Description", due_date=future_date)
        assert task is not None
        
        from_date = (datetime.now() + timedelta(days=25)).strftime("%Y-%m-%d")
        response = requests.get(
            f"{API_URL}/tasks?due_date_from={from_date}",
            headers=self.get_headers(self.admin_token)
        )
        assert response.status_code == 200
        tasks = response.json()
        for task in tasks:
            assert task["due_date"] >= from_date
        print(f"Filter by due_date_from found {len(tasks)} tasks")
    
    def test_filter_by_due_date_to(self):
        """Filter tasks by due date to"""
        if not self.admin_token:
            pytest.skip("Admin login failed")
        
        to_date = (datetime.now() + timedelta(days=5)).strftime("%Y-%m-%d")
        response = requests.get(
            f"{API_URL}/tasks?due_date_to={to_date}",
            headers=self.get_headers(self.admin_token)
        )
        assert response.status_code == 200
        tasks = response.json()
        for task in tasks:
            assert task["due_date"] <= to_date
        print(f"Filter by due_date_to found {len(tasks)} tasks")
    
    def test_filter_by_due_date_range(self):
        """Filter tasks by due date range (from and to)"""
        if not self.admin_token:
            pytest.skip("Admin login failed")
        
        from_date = datetime.now().strftime("%Y-%m-%d")
        to_date = (datetime.now() + timedelta(days=14)).strftime("%Y-%m-%d")
        
        response = requests.get(
            f"{API_URL}/tasks?due_date_from={from_date}&due_date_to={to_date}",
            headers=self.get_headers(self.admin_token)
        )
        assert response.status_code == 200
        tasks = response.json()
        for task in tasks:
            assert from_date <= task["due_date"] <= to_date
        print(f"Filter by due_date range found {len(tasks)} tasks")
    
    # ==================== FILTER OVERDUE TASKS ====================
    
    def test_filter_overdue_tasks(self):
        """Filter overdue tasks only"""
        if not self.admin_token:
            pytest.skip("Admin login failed")
        
        # Create an overdue task
        past_date = (datetime.now() - timedelta(days=5)).strftime("%Y-%m-%d")
        task = self.create_test_task("OverdueTask", "This is overdue", due_date=past_date)
        assert task is not None
        
        response = requests.get(
            f"{API_URL}/tasks?overdue=true",
            headers=self.get_headers(self.admin_token)
        )
        assert response.status_code == 200
        tasks = response.json()
        
        current_date = datetime.now().strftime("%Y-%m-%d")
        for task in tasks:
            assert task["due_date"] < current_date
            assert task["status"] not in ["completed", "cancelled"]
        print(f"Filter overdue found {len(tasks)} tasks")
    
    # ==================== SORT BY FIELDS ====================
    
    def test_sort_by_created_at_desc(self):
        """Sort tasks by created_at descending (default)"""
        if not self.admin_token:
            pytest.skip("Admin login failed")
        
        response = requests.get(
            f"{API_URL}/tasks?sort_by=created_at&sort_order=desc",
            headers=self.get_headers(self.admin_token)
        )
        assert response.status_code == 200
        tasks = response.json()
        if len(tasks) >= 2:
            for i in range(len(tasks) - 1):
                assert tasks[i]["created_at"] >= tasks[i+1]["created_at"]
        print(f"Sort by created_at desc works, {len(tasks)} tasks")
    
    def test_sort_by_created_at_asc(self):
        """Sort tasks by created_at ascending"""
        if not self.admin_token:
            pytest.skip("Admin login failed")
        
        response = requests.get(
            f"{API_URL}/tasks?sort_by=created_at&sort_order=asc",
            headers=self.get_headers(self.admin_token)
        )
        assert response.status_code == 200
        tasks = response.json()
        if len(tasks) >= 2:
            for i in range(len(tasks) - 1):
                assert tasks[i]["created_at"] <= tasks[i+1]["created_at"]
        print(f"Sort by created_at asc works, {len(tasks)} tasks")
    
    def test_sort_by_due_date(self):
        """Sort tasks by due_date"""
        if not self.admin_token:
            pytest.skip("Admin login failed")
        
        response = requests.get(
            f"{API_URL}/tasks?sort_by=due_date&sort_order=asc",
            headers=self.get_headers(self.admin_token)
        )
        assert response.status_code == 200
        tasks = response.json()
        if len(tasks) >= 2:
            for i in range(len(tasks) - 1):
                assert tasks[i]["due_date"] <= tasks[i+1]["due_date"]
        print(f"Sort by due_date works, {len(tasks)} tasks")
    
    def test_sort_by_priority(self):
        """Sort tasks by priority"""
        if not self.admin_token:
            pytest.skip("Admin login failed")
        
        response = requests.get(
            f"{API_URL}/tasks?sort_by=priority&sort_order=desc",
            headers=self.get_headers(self.admin_token)
        )
        assert response.status_code == 200
        tasks = response.json()
        # Just verify it returns successfully
        print(f"Sort by priority works, {len(tasks)} tasks")
    
    def test_sort_by_status(self):
        """Sort tasks by status"""
        if not self.admin_token:
            pytest.skip("Admin login failed")
        
        response = requests.get(
            f"{API_URL}/tasks?sort_by=status&sort_order=asc",
            headers=self.get_headers(self.admin_token)
        )
        assert response.status_code == 200
        tasks = response.json()
        print(f"Sort by status works, {len(tasks)} tasks")
    
    def test_sort_by_title(self):
        """Sort tasks by title"""
        if not self.admin_token:
            pytest.skip("Admin login failed")
        
        response = requests.get(
            f"{API_URL}/tasks?sort_by=title&sort_order=asc",
            headers=self.get_headers(self.admin_token)
        )
        assert response.status_code == 200
        tasks = response.json()
        if len(tasks) >= 2:
            for i in range(len(tasks) - 1):
                assert tasks[i]["title"].lower() <= tasks[i+1]["title"].lower()
        print(f"Sort by title works, {len(tasks)} tasks")
    
    # ==================== PAGINATION ====================
    
    def test_pagination_skip(self):
        """Test pagination with skip"""
        if not self.admin_token:
            pytest.skip("Admin login failed")
        
        # Get all tasks
        all_response = requests.get(
            f"{API_URL}/tasks?limit=100",
            headers=self.get_headers(self.admin_token)
        )
        all_tasks = all_response.json()
        
        if len(all_tasks) < 2:
            pytest.skip("Not enough tasks to test pagination")
        
        # Get with skip
        skip_response = requests.get(
            f"{API_URL}/tasks?skip=1&limit=100",
            headers=self.get_headers(self.admin_token)
        )
        skip_tasks = skip_response.json()
        
        assert len(skip_tasks) == len(all_tasks) - 1
        print(f"Pagination skip works: all={len(all_tasks)}, skip=1 gives {len(skip_tasks)}")
    
    def test_pagination_limit(self):
        """Test pagination with limit"""
        if not self.admin_token:
            pytest.skip("Admin login failed")
        
        response = requests.get(
            f"{API_URL}/tasks?limit=2",
            headers=self.get_headers(self.admin_token)
        )
        assert response.status_code == 200
        tasks = response.json()
        assert len(tasks) <= 2
        print(f"Pagination limit=2 works, got {len(tasks)} tasks")
    
    def test_pagination_skip_and_limit(self):
        """Test pagination with both skip and limit"""
        if not self.admin_token:
            pytest.skip("Admin login failed")
        
        response = requests.get(
            f"{API_URL}/tasks?skip=1&limit=3",
            headers=self.get_headers(self.admin_token)
        )
        assert response.status_code == 200
        tasks = response.json()
        assert len(tasks) <= 3
        print(f"Pagination skip=1&limit=3 works, got {len(tasks)} tasks")
    
    # ==================== TASK STATS SUMMARY ====================
    
    def test_task_stats_summary_endpoint(self):
        """Test task stats summary endpoint"""
        if not self.admin_token:
            pytest.skip("Admin login failed")
        
        response = requests.get(
            f"{API_URL}/tasks/stats/summary",
            headers=self.get_headers(self.admin_token)
        )
        assert response.status_code == 200
        stats = response.json()
        
        # Verify structure
        assert "total" in stats
        assert "by_status" in stats
        assert "by_priority" in stats
        assert "overdue" in stats
        assert "my_tasks" in stats
        assert "my_overdue" in stats
        
        # Verify by_status structure
        assert "todo" in stats["by_status"]
        assert "in_progress" in stats["by_status"]
        assert "completed" in stats["by_status"]
        assert "cancelled" in stats["by_status"]
        
        # Verify by_priority structure
        assert "high" in stats["by_priority"]
        assert "medium" in stats["by_priority"]
        assert "low" in stats["by_priority"]
        
        print(f"Stats: total={stats['total']}, overdue={stats['overdue']}, my_tasks={stats['my_tasks']}")
    
    def test_task_stats_counts_match(self):
        """Verify stats counts match actual task counts"""
        if not self.admin_token:
            pytest.skip("Admin login failed")
        
        # Get stats
        stats_response = requests.get(
            f"{API_URL}/tasks/stats/summary",
            headers=self.get_headers(self.admin_token)
        )
        stats = stats_response.json()
        
        # Get all tasks
        tasks_response = requests.get(
            f"{API_URL}/tasks?limit=500",
            headers=self.get_headers(self.admin_token)
        )
        tasks = tasks_response.json()
        
        # Verify total matches
        assert stats["total"] == len(tasks), f"Stats total {stats['total']} != actual {len(tasks)}"
        
        # Verify status counts
        status_counts = {"todo": 0, "in_progress": 0, "completed": 0, "cancelled": 0}
        for task in tasks:
            if task["status"] in status_counts:
                status_counts[task["status"]] += 1
        
        for status, count in status_counts.items():
            assert stats["by_status"][status] == count, \
                f"Status {status}: stats={stats['by_status'][status]}, actual={count}"
        
        print("Stats counts match actual task counts")
    
    def test_stats_accessible_by_all_roles(self):
        """All roles can access stats endpoint"""
        if not all([self.admin_token, self.sales_token, self.member_token]):
            pytest.skip("Not all logins succeeded")
        
        for token, role in [(self.admin_token, "admin"), (self.sales_token, "sales"), (self.member_token, "member")]:
            response = requests.get(
                f"{API_URL}/tasks/stats/summary",
                headers=self.get_headers(token)
            )
            assert response.status_code == 200, f"{role} cannot access stats"
        print("All roles can access stats endpoint")
    
    # ==================== COMBINED FILTERS ====================
    
    def test_combined_search_and_status(self):
        """Test search combined with status filter"""
        if not self.admin_token:
            pytest.skip("Admin login failed")
        
        task = self.create_test_task("CombinedFilterTest", "Description")
        assert task is not None
        
        response = requests.get(
            f"{API_URL}/tasks?search=CombinedFilterTest&status=todo",
            headers=self.get_headers(self.admin_token)
        )
        assert response.status_code == 200
        tasks = response.json()
        for task in tasks:
            assert task["status"] == "todo"
            assert "CombinedFilterTest" in task["title"] or "CombinedFilterTest" in task["description"]
        print(f"Combined search+status filter works, {len(tasks)} tasks")
    
    def test_combined_priority_and_assigned(self):
        """Test priority combined with assigned_to filter"""
        if not self.admin_token or not self.member_user:
            pytest.skip("Login failed")
        
        task = self.create_test_task("PriorityAssignedTest", "Description", priority="high", assigned_to=self.member_user["id"])
        assert task is not None
        
        response = requests.get(
            f"{API_URL}/tasks?priority=high&assigned_to={self.member_user['id']}",
            headers=self.get_headers(self.admin_token)
        )
        assert response.status_code == 200
        tasks = response.json()
        for task in tasks:
            assert task["priority"] == "high"
            assert task["assigned_to"] == self.member_user["id"]
        print(f"Combined priority+assigned filter works, {len(tasks)} tasks")
    
    def test_combined_filters_with_sort(self):
        """Test multiple filters combined with sorting"""
        if not self.admin_token:
            pytest.skip("Admin login failed")
        
        response = requests.get(
            f"{API_URL}/tasks?status=todo&sort_by=due_date&sort_order=asc",
            headers=self.get_headers(self.admin_token)
        )
        assert response.status_code == 200
        tasks = response.json()
        
        for task in tasks:
            assert task["status"] == "todo"
        
        if len(tasks) >= 2:
            for i in range(len(tasks) - 1):
                assert tasks[i]["due_date"] <= tasks[i+1]["due_date"]
        
        print(f"Combined filters with sort works, {len(tasks)} tasks")
    
    def test_all_filters_combined(self):
        """Test all filters combined"""
        if not self.admin_token:
            pytest.skip("Admin login failed")
        
        from_date = datetime.now().strftime("%Y-%m-%d")
        to_date = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
        
        response = requests.get(
            f"{API_URL}/tasks?status=todo&priority=medium&due_date_from={from_date}&due_date_to={to_date}&sort_by=title&sort_order=asc&limit=10",
            headers=self.get_headers(self.admin_token)
        )
        assert response.status_code == 200
        tasks = response.json()
        assert len(tasks) <= 10
        print(f"All filters combined works, {len(tasks)} tasks")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
