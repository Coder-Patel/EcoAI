import pandas as pd
import hashlib
import os
import io
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
        os.makedirs(os.path.dirname(self.users_file), exist_ok=True)
        if not os.path.exists(self.users_file) or os.path.getsize(self.users_file) == 0:
            users_df = pd.DataFrame(columns=['username', 'password', 'name', 'email'])
            users_df.to_csv(self.users_file, index=False)
        if not os.path.exists(self.progress_file) or os.path.getsize(self.progress_file) == 0:
            progress_df = pd.DataFrame(columns=['username', 'feature', 'data', 'timestamp'])
            progress_df.to_csv(self.progress_file, index=False)

    def _hash_password(self, password):
        """Hash password using SHA-256"""
        return hashlib.sha256(password.encode()).hexdigest()

    def _get_github_users_df(self):
        """Fetch users.csv from GitHub and return as DataFrame"""
        if not self.github_storage.repo:
            return pd.DataFrame(columns=['username', 'password', 'name', 'email'])
        try:
            file = self.github_storage.repo.get_contents("data/users.csv")
            content = file.decoded_content.decode()
            users_df = pd.read_csv(io.StringIO(content))
            return users_df
        except Exception as e:
            print(f"Error fetching users.csv from GitHub: {e}")
            return pd.DataFrame(columns=['username', 'password', 'name', 'email'])

    def register_user(self, username, password, name, email):
        """Register a new user (save to GitHub users.csv and local)"""
        if not self.github_storage.repo:
            return False, "GitHub connection failed. Please contact the administrator."
        try:
            users_df = self._get_github_users_df()
            if username in users_df['username'].values:
                return False, "Username already exists"

            hashed_password = self._hash_password(password)
            new_user = pd.DataFrame({
                'username': [username],
                'password': [hashed_password],
                'name': [name],
                'email': [email]
            })

            # Append new user and upload to GitHub
            users_df = pd.concat([users_df, new_user], ignore_index=True)
            csv_buffer = io.StringIO()
            users_df.to_csv(csv_buffer, index=False)
            csv_content = csv_buffer.getvalue()

            # Update users.csv on GitHub
            file = self.github_storage.repo.get_contents("data/users.csv")
            self.github_storage.repo.update_file(
                path="data/users.csv",
                message=f"Add new user: {username}",
                content=csv_content,
                sha=file.sha
            )

            # Also save locally for backup/compatibility
            users_df.to_csv(self.users_file, index=False)

            return True, "Registration successful"
        except Exception as e:
            print(f"Registration error: {str(e)}")
            return False, f"Registration failed: {str(e)}"

    def login_user(self, username, password):
        """Authenticate a user (check from GitHub users.csv)"""
        try:
            users_df = self._get_github_users_df()
            hashed_password = self._hash_password(password)
            user = users_df[users_df['username'] == username]
            if not user.empty and user.iloc[0]['password'] == hashed_password:
                return True, "Login successful"
            return False, "Invalid username or password"
        except Exception as e:
            return False, f"Login failed: {str(e)}"

    def save_progress(self, username, feature, data):
        """Save user progress locally and to GitHub"""
        try:
            progress_df = pd.read_csv(self.progress_file)
            timestamp = pd.Timestamp.now()
            new_progress = pd.DataFrame({
                'username': [username],
                'feature': [feature],
                'data': [str(data)],
                'timestamp': [timestamp]
            })
            progress_df = pd.concat([progress_df, new_progress], ignore_index=True)
            progress_df.to_csv(self.progress_file, index=False)

            # --- Save to GitHub ---
            if self.github_storage.repo:
                self.github_storage.update_progress_csv(
                    username,
                    feature,
                    str(data),
                    str(timestamp)
                )
            return True
        except Exception as e:
            print(f"Error saving progress: {e}")
            return False

    def get_user_progress(self, username, feature=None):
        """Get user progress locally (unchanged)"""
        try:
            progress_df = pd.read_csv(self.progress_file)
            user_progress = progress_df[progress_df['username'] == username]
            if feature:
                user_progress = user_progress[user_progress['feature'] == feature]
            return user_progress
        except Exception as e:
            print(f"Error getting progress: {str(e)}")
            return pd.DataFrame()