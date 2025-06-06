import pandas as pd
import hashlib
import os
from .database import Database
from .github_storage import GitHubStorage

class Auth:
    def __init__(self):
        self.db = Database()
        self.github_storage = GitHubStorage()
        self.users_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "users.csv")
        self.progress_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "progress.csv")
        self._initialize_files()

    def _initialize_files(self):
        """Initialize CSV files with proper headers if they don't exist"""
        # Create data directory if it doesn't exist
        os.makedirs(os.path.dirname(self.users_file), exist_ok=True)
        
        # Initialize users.csv if it doesn't exist or is empty
        if not os.path.exists(self.users_file) or os.path.getsize(self.users_file) == 0:
            users_df = pd.DataFrame(columns=['username', 'password', 'name', 'email'])
            users_df.to_csv(self.users_file, index=False)

        # Initialize progress.csv if it doesn't exist or is empty
        if not os.path.exists(self.progress_file) or os.path.getsize(self.progress_file) == 0:
            progress_df = pd.DataFrame(columns=['username', 'feature', 'data', 'timestamp'])
            progress_df.to_csv(self.progress_file, index=False)

    def _hash_password(self, password):
        """Hash password using SHA-256"""
        return hashlib.sha256(password.encode()).hexdigest()

    def _user_exists(self, username):
        """Check if a user exists"""
        try:
            users_df = pd.read_csv(self.users_file)
            return username in users_df['username'].values
        except Exception as e:
            print(f"Error checking user existence: {str(e)}")
            return False

    def register_user(self, username, password, name, email):
        """Register a new user"""
        try:
            # Ensure data directory exists
            os.makedirs(os.path.dirname(self.users_file), exist_ok=True)
            
            # Create users file if it doesn't exist
            if not os.path.exists(self.users_file):
                pd.DataFrame(columns=['username', 'password', 'name', 'email']).to_csv(self.users_file, index=False)
            
            # Read existing users
            users_df = pd.read_csv(self.users_file)
            
            # Check if username already exists
            if username in users_df['username'].values:
                return False, "Username already exists"
            
            # Hash password
            hashed_password = self._hash_password(password)
            
            # Create new user entry
            new_user = pd.DataFrame({
                'username': [username],
                'password': [hashed_password],
                'name': [name],
                'email': [email]
            })
            
            # Append to existing users and save
            users_df = pd.concat([users_df, new_user], ignore_index=True)
            users_df.to_csv(self.users_file, index=False)
            
            # Local save successful
            return True, "Registration successful"
            
        except Exception as e:
            print(f"Registration error: {str(e)}")  # Add logging
            return False, f"Registration failed: {str(e)}"

    def login_user(self, username, password):
        """Authenticate a user"""
        try:
            users_df = pd.read_csv(self.users_file)
            hashed_password = self._hash_password(password)
            
            user = users_df[users_df['username'] == username]
            if not user.empty and user.iloc[0]['password'] == hashed_password:
                return True, "Login successful"
            return False, "Invalid username or password"
            
        except Exception as e:
            return False, f"Login failed: {str(e)}"

    def save_progress(self, username, feature, data):
        """Save user progress"""
        try:
            progress_df = pd.read_csv(self.progress_file)
            
            # Create new progress entry
            new_progress = pd.DataFrame({
                'username': [username],
                'feature': [feature],
                'data': [str(data)],
                'timestamp': [pd.Timestamp.now()]
            })
            
            # Append new progress and save
            progress_df = pd.concat([progress_df, new_progress], ignore_index=True)
            progress_df.to_csv(self.progress_file, index=False)
            return True
            
        except Exception as e:
            print(f"Error saving progress: {str(e)}")
            return False

    def get_user_progress(self, username, feature=None):
        """Get user progress, optionally filtered by feature"""
        try:
            progress_df = pd.read_csv(self.progress_file)
            user_progress = progress_df[progress_df['username'] == username]
            
            if feature:
                user_progress = user_progress[user_progress['feature'] == feature]
                
            return user_progress
            
        except Exception as e:
            print(f"Error getting progress: {str(e)}")
            return pd.DataFrame()

# Use db.save_user_progress(), db.get_user_stats(), etc.