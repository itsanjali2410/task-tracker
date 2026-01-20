import requests
import sys
from datetime import datetime, timedelta
import json

class TripStarsAPITester:
    def __init__(self, base_url="https://tripstars-tracker.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tokens = {}
        self.users = {}
        self.tasks = []
        self.comments = []
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
            200,
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
            200,
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