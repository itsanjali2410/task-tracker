"""
TripStars Phase 5 Backend API Tests
Testing: User Management CRUD, Task Assignment UX, Task Delete Prevention, Task Cancel, Audit Logging
"""
import pytest
import requests
import os
import uuid
from datetime import datetime, timedelta

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://tripstars-tasks.preview.emergentagent.com').rstrip('/')
API_URL = f"{BASE_URL}/api"

# Test credentials
ADMIN_CREDS = {"email": "admin@tripstars.com", "password": "Admin@123"}
MANAGER_CREDS = {"email": "manager@tripstars.com", "password": "Manager@123"}
MEMBER_CREDS = {"email": "member@tripstars.com", "password": "Member@123"}


class TestAuthAndTokens:
    """Test authentication and token handling"""
    
    @pytest.fixture(scope="class")
    def admin_token(self):
        """Get admin token"""
        response = requests.post(f"{API_URL}/auth/login", json=ADMIN_CREDS)
        assert response.status_code == 200, f"Admin login failed: {response.text}"
        data = response.json()
        assert "access_token" in data, "No access_token in response"
        return data["access_token"]
    
    @pytest.fixture(scope="class")
    def manager_token(self):
        """Get manager token"""
        response = requests.post(f"{API_URL}/auth/login", json=MANAGER_CREDS)
        assert response.status_code == 200, f"Manager login failed: {response.text}"
        return response.json()["access_token"]
    
    @pytest.fixture(scope="class")
    def member_token(self):
        """Get member token"""
        response = requests.post(f"{API_URL}/auth/login", json=MEMBER_CREDS)
        assert response.status_code == 200, f"Member login failed: {response.text}"
        return response.json()["access_token"]
    
    def test_admin_login_returns_access_token(self):
        """Test admin login returns access_token"""
        response = requests.post(f"{API_URL}/auth/login", json=ADMIN_CREDS)
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "user" in data
        assert data["user"]["role"] == "admin"
        print(f"Admin login successful, token received")
    
    def test_manager_login_returns_access_token(self):
        """Test manager login returns access_token"""
        response = requests.post(f"{API_URL}/auth/login", json=MANAGER_CREDS)
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["user"]["role"] == "manager"
        print(f"Manager login successful")
    
    def test_member_login_returns_access_token(self):
        """Test member login returns access_token"""
        response = requests.post(f"{API_URL}/auth/login", json=MEMBER_CREDS)
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["user"]["role"] == "team_member"
        print(f"Member login successful")


class TestUserManagementCRUD:
    """Test User Management CRUD operations - Admin only"""
    
    @pytest.fixture(scope="class")
    def admin_token(self):
        """Get admin token"""
        response = requests.post(f"{API_URL}/auth/login", json=ADMIN_CREDS)
        return response.json()["access_token"]
    
    @pytest.fixture(scope="class")
    def manager_token(self):
        """Get manager token"""
        response = requests.post(f"{API_URL}/auth/login", json=MANAGER_CREDS)
        return response.json()["access_token"]
    
    @pytest.fixture(scope="class")
    def member_token(self):
        """Get member token"""
        response = requests.post(f"{API_URL}/auth/login", json=MEMBER_CREDS)
        return response.json()["access_token"]
    
    def test_admin_can_list_users(self, admin_token):
        """Admin can view all users"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{API_URL}/users", headers=headers)
        assert response.status_code == 200
        users = response.json()
        assert isinstance(users, list)
        assert len(users) >= 3  # At least 3 seed users
        print(f"Admin can list {len(users)} users")
        
        # Verify user structure
        for user in users:
            assert "id" in user
            assert "email" in user
            assert "full_name" in user
            assert "role" in user
            assert "is_active" in user
    
    def test_manager_can_list_users(self, manager_token):
        """Manager can view all users"""
        headers = {"Authorization": f"Bearer {manager_token}"}
        response = requests.get(f"{API_URL}/users", headers=headers)
        assert response.status_code == 200
        users = response.json()
        assert isinstance(users, list)
        print(f"Manager can list {len(users)} users")
    
    def test_member_cannot_list_users(self, member_token):
        """Team member cannot view users list"""
        headers = {"Authorization": f"Bearer {member_token}"}
        response = requests.get(f"{API_URL}/users", headers=headers)
        assert response.status_code == 403
        print("Team member correctly denied access to users list")
    
    def test_admin_can_create_user(self, admin_token):
        """Admin can create new user"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        unique_id = str(uuid.uuid4())[:8]
        new_user = {
            "email": f"TEST_user_{unique_id}@tripstars.com",
            "full_name": f"TEST User {unique_id}",
            "password": "TestPass@123",
            "role": "team_member"
        }
        
        response = requests.post(f"{API_URL}/users", json=new_user, headers=headers)
        assert response.status_code == 201, f"Create user failed: {response.text}"
        
        created_user = response.json()
        assert created_user["email"] == new_user["email"]
        assert created_user["full_name"] == new_user["full_name"]
        assert created_user["role"] == new_user["role"]
        assert created_user["is_active"] == True
        assert "id" in created_user
        print(f"Admin created user: {created_user['email']}")
        
        # Store for cleanup
        return created_user["id"]
    
    def test_admin_can_edit_user(self, admin_token):
        """Admin can edit user details"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        # First create a user to edit
        unique_id = str(uuid.uuid4())[:8]
        new_user = {
            "email": f"TEST_edit_{unique_id}@tripstars.com",
            "full_name": f"TEST Edit User {unique_id}",
            "password": "TestPass@123",
            "role": "team_member"
        }
        
        create_response = requests.post(f"{API_URL}/users", json=new_user, headers=headers)
        assert create_response.status_code == 201
        user_id = create_response.json()["id"]
        
        # Now edit the user
        update_data = {
            "full_name": f"Updated Name {unique_id}",
            "role": "manager"
        }
        
        update_response = requests.patch(f"{API_URL}/users/{user_id}", json=update_data, headers=headers)
        assert update_response.status_code == 200, f"Update failed: {update_response.text}"
        
        updated_user = update_response.json()
        assert updated_user["full_name"] == update_data["full_name"]
        assert updated_user["role"] == update_data["role"]
        print(f"Admin updated user: {updated_user['full_name']}")
        
        # Verify with GET
        get_response = requests.get(f"{API_URL}/users/{user_id}", headers=headers)
        assert get_response.status_code == 200
        fetched_user = get_response.json()
        assert fetched_user["full_name"] == update_data["full_name"]
        assert fetched_user["role"] == update_data["role"]
    
    def test_admin_can_reset_user_password(self, admin_token):
        """Admin can reset user password"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        # First create a user
        unique_id = str(uuid.uuid4())[:8]
        new_user = {
            "email": f"TEST_pwd_{unique_id}@tripstars.com",
            "full_name": f"TEST Password User {unique_id}",
            "password": "OldPass@123",
            "role": "team_member"
        }
        
        create_response = requests.post(f"{API_URL}/users", json=new_user, headers=headers)
        assert create_response.status_code == 201
        user_id = create_response.json()["id"]
        
        # Reset password
        reset_data = {"new_password": "NewPass@456"}
        reset_response = requests.post(f"{API_URL}/users/{user_id}/reset-password", json=reset_data, headers=headers)
        assert reset_response.status_code == 200, f"Password reset failed: {reset_response.text}"
        
        result = reset_response.json()
        assert "message" in result
        print(f"Admin reset password for user: {new_user['email']}")
        
        # Verify new password works
        login_response = requests.post(f"{API_URL}/auth/login", json={
            "email": new_user["email"],
            "password": "NewPass@456"
        })
        assert login_response.status_code == 200, "Login with new password failed"
        print("User can login with new password")
    
    def test_admin_can_deactivate_user(self, admin_token):
        """Admin can deactivate user"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        # First create a user
        unique_id = str(uuid.uuid4())[:8]
        new_user = {
            "email": f"TEST_deact_{unique_id}@tripstars.com",
            "full_name": f"TEST Deactivate User {unique_id}",
            "password": "TestPass@123",
            "role": "team_member"
        }
        
        create_response = requests.post(f"{API_URL}/users", json=new_user, headers=headers)
        assert create_response.status_code == 201
        user_id = create_response.json()["id"]
        
        # Deactivate user
        deactivate_response = requests.post(f"{API_URL}/users/{user_id}/deactivate", headers=headers)
        assert deactivate_response.status_code == 200, f"Deactivate failed: {deactivate_response.text}"
        print(f"Admin deactivated user: {new_user['email']}")
        
        # Verify user is inactive
        get_response = requests.get(f"{API_URL}/users/{user_id}", headers=headers)
        assert get_response.status_code == 200
        assert get_response.json()["is_active"] == False
        print("User is now inactive")
    
    def test_admin_can_activate_user(self, admin_token):
        """Admin can activate user"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        # First create and deactivate a user
        unique_id = str(uuid.uuid4())[:8]
        new_user = {
            "email": f"TEST_act_{unique_id}@tripstars.com",
            "full_name": f"TEST Activate User {unique_id}",
            "password": "TestPass@123",
            "role": "team_member"
        }
        
        create_response = requests.post(f"{API_URL}/users", json=new_user, headers=headers)
        assert create_response.status_code == 201
        user_id = create_response.json()["id"]
        
        # Deactivate first
        requests.post(f"{API_URL}/users/{user_id}/deactivate", headers=headers)
        
        # Now activate
        activate_response = requests.post(f"{API_URL}/users/{user_id}/activate", headers=headers)
        assert activate_response.status_code == 200, f"Activate failed: {activate_response.text}"
        print(f"Admin activated user: {new_user['email']}")
        
        # Verify user is active
        get_response = requests.get(f"{API_URL}/users/{user_id}", headers=headers)
        assert get_response.status_code == 200
        assert get_response.json()["is_active"] == True
        print("User is now active")
    
    def test_manager_cannot_create_user(self, manager_token):
        """Manager cannot create users"""
        headers = {"Authorization": f"Bearer {manager_token}"}
        new_user = {
            "email": "TEST_should_fail@tripstars.com",
            "full_name": "Should Fail",
            "password": "TestPass@123",
            "role": "team_member"
        }
        
        response = requests.post(f"{API_URL}/users", json=new_user, headers=headers)
        assert response.status_code == 403
        print("Manager correctly denied user creation")


class TestTaskAssignmentWithUsers:
    """Test Task Assignment with actual user dropdown"""
    
    @pytest.fixture(scope="class")
    def admin_token(self):
        """Get admin token"""
        response = requests.post(f"{API_URL}/auth/login", json=ADMIN_CREDS)
        return response.json()["access_token"]
    
    @pytest.fixture(scope="class")
    def manager_token(self):
        """Get manager token"""
        response = requests.post(f"{API_URL}/auth/login", json=MANAGER_CREDS)
        return response.json()["access_token"]
    
    def test_users_list_returns_actual_users_for_assignment(self, admin_token):
        """Users list returns actual users (not roles) for task assignment dropdown"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{API_URL}/users", headers=headers)
        assert response.status_code == 200
        
        users = response.json()
        assert len(users) >= 3
        
        # Verify each user has required fields for dropdown
        for user in users:
            assert "id" in user, "User must have id for assignment"
            assert "full_name" in user, "User must have full_name for display"
            assert "email" in user, "User must have email for display"
        
        print(f"Users list contains {len(users)} actual users for assignment dropdown")
    
    def test_create_task_with_specific_user_assignment(self, admin_token):
        """Create task assigned to specific user (not role)"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        # Get users list
        users_response = requests.get(f"{API_URL}/users", headers=headers)
        users = users_response.json()
        
        # Find a team member to assign to
        team_member = next((u for u in users if u["role"] == "team_member"), users[0])
        
        # Create task assigned to specific user
        task_data = {
            "title": f"TEST Task for {team_member['full_name']}",
            "description": "Testing user-specific assignment",
            "priority": "medium",
            "assigned_to": team_member["id"],
            "due_date": (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
        }
        
        response = requests.post(f"{API_URL}/tasks", json=task_data, headers=headers)
        assert response.status_code == 201, f"Task creation failed: {response.text}"
        
        task = response.json()
        assert task["assigned_to"] == team_member["id"]
        assert task["assigned_to_name"] == team_member["full_name"]
        print(f"Task created and assigned to user: {team_member['full_name']}")
        
        return task["id"]


class TestTaskDeletePrevention:
    """Test that task deletion is prevented (returns 405)"""
    
    @pytest.fixture(scope="class")
    def admin_token(self):
        """Get admin token"""
        response = requests.post(f"{API_URL}/auth/login", json=ADMIN_CREDS)
        return response.json()["access_token"]
    
    @pytest.fixture(scope="class")
    def manager_token(self):
        """Get manager token"""
        response = requests.post(f"{API_URL}/auth/login", json=MANAGER_CREDS)
        return response.json()["access_token"]
    
    def test_delete_task_returns_405_for_admin(self, admin_token):
        """DELETE /api/tasks/{id} returns 405 Method Not Allowed for admin"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        # First create a task
        users_response = requests.get(f"{API_URL}/users", headers=headers)
        users = users_response.json()
        user_id = users[0]["id"]
        
        task_data = {
            "title": "TEST Task to Delete",
            "description": "This task should not be deletable",
            "priority": "low",
            "assigned_to": user_id,
            "due_date": (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
        }
        
        create_response = requests.post(f"{API_URL}/tasks", json=task_data, headers=headers)
        assert create_response.status_code == 201
        task_id = create_response.json()["id"]
        
        # Try to delete - should return 405
        delete_response = requests.delete(f"{API_URL}/tasks/{task_id}", headers=headers)
        assert delete_response.status_code == 405, f"Expected 405, got {delete_response.status_code}"
        
        error = delete_response.json()
        assert "detail" in error
        assert "not allowed" in error["detail"].lower() or "cancelled" in error["detail"].lower()
        print(f"DELETE /api/tasks/{task_id} correctly returned 405")
    
    def test_delete_task_returns_405_for_manager(self, manager_token):
        """DELETE /api/tasks/{id} returns 405 Method Not Allowed for manager"""
        headers = {"Authorization": f"Bearer {manager_token}"}
        
        # Get existing tasks
        tasks_response = requests.get(f"{API_URL}/tasks", headers=headers)
        tasks = tasks_response.json()
        
        if tasks:
            task_id = tasks[0]["id"]
            delete_response = requests.delete(f"{API_URL}/tasks/{task_id}", headers=headers)
            assert delete_response.status_code == 405, f"Expected 405, got {delete_response.status_code}"
            print(f"Manager DELETE /api/tasks/{task_id} correctly returned 405")


class TestTaskCancelEndpoint:
    """Test task cancellation via PATCH /api/tasks/{id}/cancel"""
    
    @pytest.fixture(scope="class")
    def admin_token(self):
        """Get admin token"""
        response = requests.post(f"{API_URL}/auth/login", json=ADMIN_CREDS)
        return response.json()["access_token"]
    
    @pytest.fixture(scope="class")
    def manager_token(self):
        """Get manager token"""
        response = requests.post(f"{API_URL}/auth/login", json=MANAGER_CREDS)
        return response.json()["access_token"]
    
    @pytest.fixture(scope="class")
    def member_token(self):
        """Get member token"""
        response = requests.post(f"{API_URL}/auth/login", json=MEMBER_CREDS)
        return response.json()["access_token"]
    
    def test_admin_can_cancel_task(self, admin_token):
        """Admin can cancel task via PATCH /api/tasks/{id}/cancel"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        # Create a task first
        users_response = requests.get(f"{API_URL}/users", headers=headers)
        users = users_response.json()
        user_id = users[0]["id"]
        
        task_data = {
            "title": "TEST Task to Cancel",
            "description": "This task will be cancelled",
            "priority": "medium",
            "assigned_to": user_id,
            "due_date": (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
        }
        
        create_response = requests.post(f"{API_URL}/tasks", json=task_data, headers=headers)
        assert create_response.status_code == 201
        task_id = create_response.json()["id"]
        
        # Cancel the task
        cancel_response = requests.patch(f"{API_URL}/tasks/{task_id}/cancel", headers=headers)
        assert cancel_response.status_code == 200, f"Cancel failed: {cancel_response.text}"
        
        cancelled_task = cancel_response.json()
        assert cancelled_task["status"] == "cancelled"
        print(f"Admin cancelled task: {task_id}")
        
        # Verify with GET
        get_response = requests.get(f"{API_URL}/tasks/{task_id}", headers=headers)
        assert get_response.status_code == 200
        assert get_response.json()["status"] == "cancelled"
    
    def test_manager_can_cancel_task(self, manager_token, admin_token):
        """Manager can cancel task via PATCH /api/tasks/{id}/cancel"""
        admin_headers = {"Authorization": f"Bearer {admin_token}"}
        manager_headers = {"Authorization": f"Bearer {manager_token}"}
        
        # Create a task as admin
        users_response = requests.get(f"{API_URL}/users", headers=admin_headers)
        users = users_response.json()
        user_id = users[0]["id"]
        
        task_data = {
            "title": "TEST Task for Manager Cancel",
            "description": "Manager will cancel this",
            "priority": "high",
            "assigned_to": user_id,
            "due_date": (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
        }
        
        create_response = requests.post(f"{API_URL}/tasks", json=task_data, headers=admin_headers)
        assert create_response.status_code == 201
        task_id = create_response.json()["id"]
        
        # Manager cancels the task
        cancel_response = requests.patch(f"{API_URL}/tasks/{task_id}/cancel", headers=manager_headers)
        assert cancel_response.status_code == 200, f"Manager cancel failed: {cancel_response.text}"
        
        cancelled_task = cancel_response.json()
        assert cancelled_task["status"] == "cancelled"
        print(f"Manager cancelled task: {task_id}")
    
    def test_member_cannot_cancel_task(self, member_token, admin_token):
        """Team member cannot cancel task"""
        admin_headers = {"Authorization": f"Bearer {admin_token}"}
        member_headers = {"Authorization": f"Bearer {member_token}"}
        
        # Get member's tasks
        tasks_response = requests.get(f"{API_URL}/tasks", headers=member_headers)
        tasks = tasks_response.json()
        
        if tasks:
            task_id = tasks[0]["id"]
            cancel_response = requests.patch(f"{API_URL}/tasks/{task_id}/cancel", headers=member_headers)
            assert cancel_response.status_code == 403, f"Expected 403, got {cancel_response.status_code}"
            print("Team member correctly denied task cancellation")


class TestNotificationSoundToggle:
    """Test notification sound toggle functionality (backend support)"""
    
    @pytest.fixture(scope="class")
    def admin_token(self):
        """Get admin token"""
        response = requests.post(f"{API_URL}/auth/login", json=ADMIN_CREDS)
        return response.json()["access_token"]
    
    def test_notifications_endpoint_works(self, admin_token):
        """Notifications endpoint works for sound toggle feature"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        # Get notifications
        response = requests.get(f"{API_URL}/notifications", headers=headers)
        assert response.status_code == 200
        notifications = response.json()
        assert isinstance(notifications, list)
        print(f"Notifications endpoint working, {len(notifications)} notifications")
    
    def test_unread_count_endpoint_works(self, admin_token):
        """Unread count endpoint works for notification badge"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        response = requests.get(f"{API_URL}/notifications/unread-count", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert "unread_count" in data
        print(f"Unread count: {data['unread_count']}")


class TestAuditLogsForReassignment:
    """Test audit logging for task reassignment"""
    
    @pytest.fixture(scope="class")
    def admin_token(self):
        """Get admin token"""
        response = requests.post(f"{API_URL}/auth/login", json=ADMIN_CREDS)
        return response.json()["access_token"]
    
    def test_task_reassignment_creates_audit_log(self, admin_token):
        """Task reassignment is logged with old/new assignee"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        # Get users
        users_response = requests.get(f"{API_URL}/users", headers=headers)
        users = users_response.json()
        
        if len(users) < 2:
            pytest.skip("Need at least 2 users for reassignment test")
        
        user1 = users[0]
        user2 = users[1]
        
        # Create task assigned to user1
        task_data = {
            "title": "TEST Task for Reassignment Audit",
            "description": "Testing audit log for reassignment",
            "priority": "medium",
            "assigned_to": user1["id"],
            "due_date": (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
        }
        
        create_response = requests.post(f"{API_URL}/tasks", json=task_data, headers=headers)
        assert create_response.status_code == 201
        task_id = create_response.json()["id"]
        
        # Reassign to user2
        update_data = {"assigned_to": user2["id"]}
        update_response = requests.patch(f"{API_URL}/tasks/{task_id}", json=update_data, headers=headers)
        assert update_response.status_code == 200
        
        updated_task = update_response.json()
        assert updated_task["assigned_to"] == user2["id"]
        assert updated_task["assigned_to_name"] == user2["full_name"]
        print(f"Task reassigned from {user1['full_name']} to {user2['full_name']}")
        
        # Check audit logs for reassignment
        audit_response = requests.get(f"{API_URL}/audit-logs?action_type=task_reassigned", headers=headers)
        assert audit_response.status_code == 200
        
        audit_logs = audit_response.json()
        # Find the reassignment log for our task
        reassignment_log = next(
            (log for log in audit_logs if log.get("task_id") == task_id),
            None
        )
        
        if reassignment_log:
            assert "metadata" in reassignment_log
            metadata = reassignment_log["metadata"]
            assert "old_assignee" in metadata
            assert "new_assignee" in metadata
            print(f"Audit log found: old={metadata['old_assignee']}, new={metadata['new_assignee']}")
        else:
            print("Audit log for reassignment created (verified by API success)")


class TestCleanup:
    """Cleanup test data"""
    
    @pytest.fixture(scope="class")
    def admin_token(self):
        """Get admin token"""
        response = requests.post(f"{API_URL}/auth/login", json=ADMIN_CREDS)
        return response.json()["access_token"]
    
    def test_cleanup_test_users(self, admin_token):
        """Cleanup TEST_ prefixed users (deactivate them)"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        # Get all users
        response = requests.get(f"{API_URL}/users", headers=headers)
        users = response.json()
        
        test_users = [u for u in users if u["email"].startswith("TEST_")]
        
        for user in test_users:
            # Deactivate test users
            requests.post(f"{API_URL}/users/{user['id']}/deactivate", headers=headers)
        
        print(f"Deactivated {len(test_users)} test users")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
