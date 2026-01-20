import requests
import sys
from datetime import datetime, timedelta
import json
import os
import tempfile

class TripStarsAPITester:
    def __init__(self, base_url="https://tripstars-tracker.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tokens = {}
        self.users = {}
        self.tasks = []
        self.comments = []
        self.attachments = []
        self.tests_run = 0
        self.tests_passed = 0

    def run_test(self, name, method, endpoint, expected_status, data=None, token=None):
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        if token:
            headers['Authorization'] = f'Bearer {token}'

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers)
            elif method == 'PATCH':
                response = requests.patch(url, json=data, headers=headers)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers)

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    return success, response.json()
                except:
                    return success, {}
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                try:
                    print(f"   Response: {response.json()}")
                except:
                    print(f"   Response: {response.text}")
                return False, {}

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}

    def test_root_endpoint(self):
        """Test root API endpoint"""
        success, response = self.run_test(
            "Root API Endpoint",
            "GET",
            "",
            200
        )
        return success

    def test_login_all_users(self):
        """Test login for all three seed users"""
        users_to_test = [
            {"email": "admin@tripstars.com", "password": "Admin@123", "role": "admin"},
            {"email": "manager@tripstars.com", "password": "Manager@123", "role": "manager"},
            {"email": "member@tripstars.com", "password": "Member@123", "role": "team_member"}
        ]
        
        all_passed = True
        for user_data in users_to_test:
            success, response = self.run_test(
                f"Login {user_data['role']} user",
                "POST",
                "auth/login",
                200,
                data={"email": user_data["email"], "password": user_data["password"]}
            )
            
            if success and 'access_token' in response:
                self.tokens[user_data['role']] = response['access_token']
                self.users[user_data['role']] = response['user']
                print(f"   Token stored for {user_data['role']}")
            else:
                all_passed = False
                
        return all_passed

    def test_auth_me(self):
        """Test /auth/me endpoint for all users"""
        all_passed = True
        for role, token in self.tokens.items():
            success, response = self.run_test(
                f"Get current user ({role})",
                "GET",
                "auth/me",
                200,
                token=token
            )
            if not success:
                all_passed = False
        return all_passed

    def test_user_management_admin(self):
        """Test user management endpoints (Admin only)"""
        admin_token = self.tokens.get('admin')
        if not admin_token:
            print("❌ No admin token available for user management tests")
            return False

        # Test get users
        success, users_response = self.run_test(
            "Get users (Admin)",
            "GET",
            "users",
            200,
            token=admin_token
        )
        
        if not success:
            return False

        # Test create user
        new_user_data = {
            "email": f"test_user_{datetime.now().strftime('%H%M%S')}@tripstars.com",
            "full_name": "Test User",
            "password": "TestPass123!",
            "role": "team_member"
        }
        
        success, create_response = self.run_test(
            "Create new user (Admin)",
            "POST",
            "users",
            201,
            data=new_user_data,
            token=admin_token
        )
        
        return success

    def test_user_management_unauthorized(self):
        """Test that non-admin users cannot access user management"""
        manager_token = self.tokens.get('manager')
        member_token = self.tokens.get('team_member')
        
        all_passed = True
        
        # Test manager cannot create users
        if manager_token:
            success, _ = self.run_test(
                "Create user (Manager - should fail)",
                "POST",
                "users",
                403,
                data={"email": "test@test.com", "full_name": "Test", "password": "pass", "role": "team_member"},
                token=manager_token
            )
            if not success:
                all_passed = False
        
        # Test team member cannot access users
        if member_token:
            success, _ = self.run_test(
                "Get users (Team Member - should fail)",
                "GET",
                "users",
                403,
                token=member_token
            )
            if not success:
                all_passed = False
                
        return all_passed

    def test_task_management(self):
        """Test task creation and management"""
        manager_token = self.tokens.get('manager')
        admin_token = self.tokens.get('admin')
        member_user = self.users.get('team_member')
        
        if not manager_token or not member_user:
            print("❌ Missing required tokens/users for task management tests")
            return False

        # Test task creation by manager
        task_data = {
            "title": "Test Task",
            "description": "This is a test task for API testing",
            "priority": "high",
            "assigned_to": member_user['id'],
            "due_date": (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d')
        }
        
        success, task_response = self.run_test(
            "Create task (Manager)",
            "POST",
            "tasks",
            201,
            data=task_data,
            token=manager_token
        )
        
        if success and 'id' in task_response:
            self.tasks.append(task_response)
            print(f"   Task created with ID: {task_response['id']}")
        else:
            return False

        # Test get all tasks (Manager)
        success, _ = self.run_test(
            "Get all tasks (Manager)",
            "GET",
            "tasks",
            200,
            token=manager_token
        )
        
        if not success:
            return False

        # Test team member cannot create tasks
        success, _ = self.run_test(
            "Create task (Team Member - should fail)",
            "POST",
            "tasks",
            403,
            data=task_data,
            token=self.tokens.get('team_member')
        )
        
        return success

    def test_task_status_update(self):
        """Test task status updates by team members"""
        member_token = self.tokens.get('team_member')
        
        if not member_token or not self.tasks:
            print("❌ Missing member token or no tasks available for status update test")
            return False

        task_id = self.tasks[0]['id']
        
        # Test status update
        success, _ = self.run_test(
            "Update task status (Team Member)",
            "PATCH",
            f"tasks/{task_id}",
            200,
            data={"status": "in_progress"},
            token=member_token
        )
        
        return success

    def test_stats_endpoint(self):
        """Test stats endpoint for all user roles"""
        all_passed = True
        
        for role, token in self.tokens.items():
            success, response = self.run_test(
                f"Get stats ({role})",
                "GET",
                "stats",
                200,
                token=token
            )
            
            if success:
                expected_keys = ['total_tasks', 'todo', 'in_progress', 'completed']
                if all(key in response for key in expected_keys):
                    print(f"   Stats response valid for {role}")
                else:
                    print(f"   ❌ Missing keys in stats response for {role}")
                    all_passed = False
            else:
                all_passed = False
                
        return all_passed

    def test_role_based_access(self):
        """Test role-based access control"""
        member_token = self.tokens.get('team_member')
        
        if not member_token:
            print("❌ No team member token for role-based access test")
            return False

        # Team member should only see their own tasks
        success, tasks_response = self.run_test(
            "Get tasks (Team Member - own tasks only)",
            "GET",
            "tasks",
            200,
            token=member_token
        )
        
        if success:
            member_id = self.users['team_member']['id']
            for task in tasks_response:
                if task['assigned_to'] != member_id:
                    print(f"   ❌ Team member can see task not assigned to them: {task['id']}")
                    return False
            print(f"   ✅ Team member only sees their own tasks ({len(tasks_response)} tasks)")
        
        return success

    def test_comments_api(self):
        """Test comments API endpoints"""
        member_token = self.tokens.get('team_member')
        admin_token = self.tokens.get('admin')
        
        if not member_token or not self.tasks:
            print("❌ Missing member token or no tasks available for comments test")
            return False

        task_id = self.tasks[0]['id']
        
        # Test create comment by team member (on their own task)
        comment_data = {
            "task_id": task_id,
            "content": "This is a test comment from team member"
        }
        
        success, comment_response = self.run_test(
            "Create comment (Team Member)",
            "POST",
            "comments",
            201,
            data=comment_data,
            token=member_token
        )
        
        if success and 'id' in comment_response:
            self.comments.append(comment_response)
            print(f"   Comment created with ID: {comment_response['id']}")
        else:
            return False

        # Test get comments for task
        success, comments_list = self.run_test(
            "Get comments for task",
            "GET",
            f"comments/task/{task_id}",
            200,
            token=member_token
        )
        
        if not success:
            return False

        # Test get specific comment
        comment_id = self.comments[0]['id']
        success, _ = self.run_test(
            "Get specific comment",
            "GET",
            f"comments/{comment_id}",
            200,
            token=member_token
        )
        
        if not success:
            return False

        # Test update comment (only author can update)
        success, _ = self.run_test(
            "Update comment (Author)",
            "PATCH",
            f"comments/{comment_id}",
            200,
            data={"content": "Updated comment content"},
            token=member_token
        )
        
        if not success:
            return False

        # Test admin can create comment on any task
        if admin_token:
            admin_comment_data = {
                "task_id": task_id,
                "content": "Admin comment on task"
            }
            
            success, admin_comment = self.run_test(
                "Create comment (Admin)",
                "POST",
                "comments",
                201,
                data=admin_comment_data,
                token=admin_token
            )
            
            if success and 'id' in admin_comment:
                self.comments.append(admin_comment)
            else:
                return False

        return True

    def test_comments_authorization(self):
        """Test comments authorization rules"""
        manager_token = self.tokens.get('manager')
        member_token = self.tokens.get('team_member')
        
        if not manager_token or not member_token or not self.tasks:
            print("❌ Missing tokens or tasks for comments authorization test")
            return False

        # Create a task assigned to manager (not team member)
        manager_user = self.users.get('manager')
        if not manager_user:
            return False

        task_data = {
            "title": "Manager Task for Comments Test",
            "description": "Task assigned to manager for testing comment permissions",
            "priority": "medium",
            "assigned_to": manager_user['id'],
            "due_date": (datetime.now() + timedelta(days=5)).strftime('%Y-%m-%d')
        }
        
        success, manager_task = self.run_test(
            "Create task for manager (Comments auth test)",
            "POST",
            "tasks",
            201,
            data=task_data,
            token=manager_token
        )
        
        if not success or 'id' not in manager_task:
            return False

        manager_task_id = manager_task['id']

        # Test team member cannot comment on task not assigned to them
        comment_data = {
            "task_id": manager_task_id,
            "content": "Team member trying to comment on manager's task"
        }
        
        success, _ = self.run_test(
            "Create comment on unassigned task (Team Member - should fail)",
            "POST",
            "comments",
            403,
            data=comment_data,
            token=member_token
        )
        
        return success

    def test_file_attachments_api(self):
        """Test file attachments API endpoints"""
        member_token = self.tokens.get('team_member')
        admin_token = self.tokens.get('admin')
        
        if not member_token or not self.tasks:
            print("❌ Missing member token or no tasks available for attachments test")
            return False

        task_id = self.tasks[0]['id']
        
        # Create a test file
        test_content = b"This is a test PDF file content for attachment testing"
        
        # Test file upload
        files = {'file': ('test_document.pdf', test_content, 'application/pdf')}
        
        url = f"{self.api_url}/attachments?task_id={task_id}"
        headers = {'Authorization': f'Bearer {member_token}'}
        
        self.tests_run += 1
        print(f"\n🔍 Testing Upload attachment (Team Member)...")
        
        try:
            response = requests.post(url, files=files, headers=headers)
            success = response.status_code == 201
            
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                attachment_response = response.json()
                self.attachments.append(attachment_response)
                print(f"   Attachment created with ID: {attachment_response['id']}")
            else:
                print(f"❌ Failed - Expected 201, got {response.status_code}")
                try:
                    print(f"   Response: {response.json()}")
                except:
                    print(f"   Response: {response.text}")
                return False
        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False

        # Test list attachments for task
        success, attachments_list = self.run_test(
            "List task attachments",
            "GET",
            f"attachments/task/{task_id}",
            200,
            token=member_token
        )
        
        if not success:
            return False

        # Test file validation - invalid file type
        invalid_files = {'file': ('test.txt', b"Invalid file type", 'text/plain')}
        
        self.tests_run += 1
        print(f"\n🔍 Testing Upload invalid file type (should fail)...")
        
        try:
            response = requests.post(url, files=invalid_files, headers=headers)
            success = response.status_code == 400
            
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code} (correctly rejected)")
            else:
                print(f"❌ Failed - Expected 400, got {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False

        # Test download attachment
        if self.attachments:
            attachment_id = self.attachments[0]['id']
            
            self.tests_run += 1
            print(f"\n🔍 Testing Download attachment...")
            
            try:
                download_url = f"{self.api_url}/attachments/{attachment_id}/download"
                response = requests.get(download_url, headers=headers)
                success = response.status_code == 200
                
                if success:
                    self.tests_passed += 1
                    print(f"✅ Passed - Status: {response.status_code}")
                    print(f"   Downloaded {len(response.content)} bytes")
                else:
                    print(f"❌ Failed - Expected 200, got {response.status_code}")
                    return False
            except Exception as e:
                print(f"❌ Failed - Error: {str(e)}")
                return False

        return True

    def test_attachments_authorization(self):
        """Test attachments authorization rules"""
        manager_token = self.tokens.get('manager')
        member_token = self.tokens.get('team_member')
        
        if not manager_token or not member_token or not self.tasks:
            print("❌ Missing tokens or tasks for attachments authorization test")
            return False

        # Create a task assigned to manager (not team member)
        manager_user = self.users.get('manager')
        if not manager_user:
            return False

        task_data = {
            "title": "Manager Task for Attachments Test",
            "description": "Task assigned to manager for testing attachment permissions",
            "priority": "medium",
            "assigned_to": manager_user['id'],
            "due_date": (datetime.now() + timedelta(days=5)).strftime('%Y-%m-%d')
        }
        
        success, manager_task = self.run_test(
            "Create task for manager (Attachments auth test)",
            "POST",
            "tasks",
            201,
            data=task_data,
            token=manager_token
        )
        
        if not success or 'id' not in manager_task:
            return False

        manager_task_id = manager_task['id']

        # Test team member cannot upload to task not assigned to them
        test_content = b"Unauthorized upload test"
        files = {'file': ('unauthorized.pdf', test_content, 'application/pdf')}
        
        url = f"{self.api_url}/attachments?task_id={manager_task_id}"
        headers = {'Authorization': f'Bearer {member_token}'}
        
        self.tests_run += 1
        print(f"\n🔍 Testing Upload to unassigned task (Team Member - should fail)...")
        
        try:
            response = requests.post(url, files=files, headers=headers)
            success = response.status_code == 403
            
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code} (correctly forbidden)")
            else:
                print(f"❌ Failed - Expected 403, got {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False

        return True

    def test_delete_attachment(self):
        """Test attachment deletion"""
        member_token = self.tokens.get('team_member')
        admin_token = self.tokens.get('admin')
        
        if not member_token or not self.attachments:
            print("❌ Missing member token or no attachments available for deletion test")
            return False

        attachment_id = self.attachments[0]['id']
        
        # Test delete attachment by uploader
        success, _ = self.run_test(
            "Delete attachment (Uploader)",
            "DELETE",
            f"attachments/{attachment_id}",
            204,
            token=member_token
        )
        
        return success

    def test_productivity_reports_api(self):
        """Test productivity reports API endpoints"""
        admin_token = self.tokens.get('admin')
        manager_token = self.tokens.get('manager')
        member_token = self.tokens.get('team_member')
        
        if not admin_token or not manager_token or not member_token:
            print("❌ Missing tokens for productivity reports test")
            return False

        # Test user productivity endpoint (Admin can view all)
        success, user_productivity = self.run_test(
            "Get user productivity (Admin)",
            "GET",
            "reports/user-productivity",
            200,
            token=admin_token
        )
        
        if not success:
            return False

        # Test user productivity endpoint (Manager can view all)
        success, _ = self.run_test(
            "Get user productivity (Manager)",
            "GET",
            "reports/user-productivity",
            200,
            token=manager_token
        )
        
        if not success:
            return False

        # Test user productivity endpoint (Team member can only view own)
        success, member_productivity = self.run_test(
            "Get user productivity (Team Member - own only)",
            "GET",
            "reports/user-productivity",
            200,
            token=member_token
        )
        
        if not success:
            return False

        # Verify team member only sees their own data
        if member_productivity:
            member_id = self.users['team_member']['id']
            for user_stat in member_productivity:
                if user_stat['user_id'] != member_id:
                    print(f"   ❌ Team member can see other user's productivity data")
                    return False
            print(f"   ✅ Team member only sees their own productivity data")

        # Test team overview endpoint (Admin only)
        success, team_overview = self.run_test(
            "Get team overview (Admin)",
            "GET",
            "reports/team-overview",
            200,
            token=admin_token
        )
        
        if not success:
            return False

        # Verify team overview structure
        if team_overview:
            expected_keys = ['total_users', 'total_tasks', 'total_completed', 'total_overdue', 'average_productivity_score', 'user_stats']
            if all(key in team_overview for key in expected_keys):
                print(f"   ✅ Team overview response has all required fields")
            else:
                print(f"   ❌ Missing keys in team overview response")
                return False

        # Test team overview endpoint (Manager can access)
        success, _ = self.run_test(
            "Get team overview (Manager)",
            "GET",
            "reports/team-overview",
            200,
            token=manager_token
        )
        
        if not success:
            return False

        # Test team overview endpoint (Team member should be forbidden)
        success, _ = self.run_test(
            "Get team overview (Team Member - should fail)",
            "GET",
            "reports/team-overview",
            403,
            token=member_token
        )
        
        return success

    def test_productivity_score_calculation(self):
        """Test productivity score calculation by completing tasks"""
        member_token = self.tokens.get('team_member')
        manager_token = self.tokens.get('manager')
        
        if not member_token or not manager_token:
            print("❌ Missing tokens for productivity score calculation test")
            return False

        member_user = self.users.get('team_member')
        if not member_user:
            return False

        # Create a task and complete it to test score calculation
        task_data = {
            "title": "Productivity Test Task",
            "description": "Task for testing productivity score calculation",
            "priority": "medium",
            "assigned_to": member_user['id'],
            "due_date": (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
        }
        
        success, test_task = self.run_test(
            "Create task for productivity test",
            "POST",
            "tasks",
            201,
            data=task_data,
            token=manager_token
        )
        
        if not success or 'id' not in test_task:
            return False

        test_task_id = test_task['id']

        # Complete the task (this should add completed_at timestamp)
        success, _ = self.run_test(
            "Complete task for productivity test",
            "PATCH",
            f"tasks/{test_task_id}",
            200,
            data={"status": "completed"},
            token=member_token
        )
        
        if not success:
            return False

        # Get updated productivity data
        success, updated_productivity = self.run_test(
            "Get updated productivity after completion",
            "GET",
            f"reports/user-productivity?user_id={member_user['id']}",
            200,
            token=manager_token
        )
        
        if success and updated_productivity:
            user_stat = updated_productivity[0]
            print(f"   ✅ Productivity score: {user_stat['productivity_score']}")
            print(f"   ✅ Tasks completed: {user_stat['tasks_completed']}")
            print(f"   ✅ On-time completion: {user_stat['tasks_completed_on_time']}")
            return True
        
        return False

def main():
    print("🚀 Starting TripStars Task Management API Tests")
    print("=" * 60)
    
    tester = TripStarsAPITester()
    
    # Test sequence
    tests = [
        ("Root Endpoint", tester.test_root_endpoint),
        ("Login All Users", tester.test_login_all_users),
        ("Auth Me Endpoint", tester.test_auth_me),
        ("User Management (Admin)", tester.test_user_management_admin),
        ("User Management Unauthorized", tester.test_user_management_unauthorized),
        ("Task Management", tester.test_task_management),
        ("Task Status Update", tester.test_task_status_update),
        ("Comments API", tester.test_comments_api),
        ("Comments Authorization", tester.test_comments_authorization),
        ("Stats Endpoint", tester.test_stats_endpoint),
        ("Role-based Access", tester.test_role_based_access),
    ]
    
    failed_tests = []
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            if not test_func():
                failed_tests.append(test_name)
        except Exception as e:
            print(f"❌ Test {test_name} crashed: {str(e)}")
            failed_tests.append(test_name)
    
    # Print final results
    print(f"\n{'='*60}")
    print(f"📊 FINAL RESULTS")
    print(f"{'='*60}")
    print(f"Tests passed: {tester.tests_passed}/{tester.tests_run}")
    print(f"Success rate: {(tester.tests_passed/tester.tests_run)*100:.1f}%")
    
    if failed_tests:
        print(f"\n❌ Failed test categories:")
        for test in failed_tests:
            print(f"   - {test}")
    else:
        print(f"\n✅ All test categories passed!")
    
    return 0 if len(failed_tests) == 0 else 1

if __name__ == "__main__":
    sys.exit(main())