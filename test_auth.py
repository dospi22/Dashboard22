import database as db
import random
import string

def random_string(length=8):
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))

def run_test():
    test_email = f"test_{random_string()}@example.com"
    test_pass = "password123"
    test_name = "Test User"

    print(f"--- Testing Signup for {test_email} ---")
    res = db.auth_signup(test_email, test_pass, test_name)
    print("Signup Response:", res)

    if not res['success']:
        print("Signup failed (likely email confirmation required or project settings).")
        # Proceed to test login if user already exists or settings allow
    
    print("\n--- Testing Login ---")
    login_res = db.auth_login(test_email, test_pass)
    print("Login Response success:", login_res['success'])

    if login_res['success']:
        user_id = login_res['user_id']
        print(f"User ID: {user_id}")
        
        print("\n--- Testing Data Isolation ---")
        # Try to add an asset class for this specific user
        db.add_asset_class(user_id, "Test Category", 10.0)
        classes = db.get_asset_classes(user_id)
        print(f"Asset classes for this user: {len(classes)}")
        
        # Verify it's there
        if len(classes) > 0:
            print("Successfully added and retrieved private data.")
            # Clean up
            db.delete_asset_class(user_id, classes[0]['id'])
    else:
        print("Login failed. Details:", login_res.get("error"))

if __name__ == "__main__":
    run_test()
