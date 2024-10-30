import os
import json
import ctypes
from datetime import datetime
import sys

class ProjectManager:
    def __init__(self, folder_dialog, file_explorer):
        self.folder_dialog = folder_dialog
        self.file_explorer = file_explorer
        self.projects_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "my-projects.aide.json")

    def open_project(self, parent=None):
        """
        Opens a project folder and manages project metadata.
        Creates or updates project information in my-projects.aide.json.
        """
        project_folder = self.folder_dialog.getExistingDirectory(parent, "Open Project", "/")
        if not project_folder:
            return

        project_name = os.path.basename(project_folder)
        timestamp = datetime.now().timestamp()
        if(not self.isProject(project_folder)):
                print("Is a not a project")
                # Prepare new project data
                new_project = {
                "name": project_name,
                "path": project_folder,
                "timestamp": timestamp,
                }

                # Load or create projects list
                if os.path.isfile(self.projects_file):
                        with open(self.projects_file) as file:
                                all_projects = json.load(file)
                else:
                        all_projects = {"projects": []}

                # Ensure all_projects has the correct structure
                if isinstance(all_projects, dict):
                        all_projects.setdefault("projects", [])
                        all_projects["projects"].append(new_project)
                else:
                        all_projects = {"projects": [new_project]}

                # Save updated projects list
                with open(self.projects_file, 'w') as file:
                        json.dump(all_projects, file, indent=4, separators=(',', ': '))
        else:
              print("Is a project")
              self.updateTimestamp(project_folder)
        # Update UI and project configuration
        self.file_explorer.update_ui(project_folder)
        json_data = {"project_name": project_name}
        self.update_project_json(project_folder, json_data)

    def update_project_json(self, path, data):
        """
        Creates or updates the project.aide.json file in the project directory.
        Makes the file hidden on Windows systems.
        
        Args:
            path (str): Project directory path
            data (dict): Project configuration data
        """
        filename = "project.aide.json"
        full_path = os.path.join(path, filename)

        # On Windows, remove hidden attribute if file exists
        if sys.platform == "win32" and os.path.exists(full_path):
            FILE_ATTRIBUTE_NORMAL = 0x80
            ctypes.windll.kernel32.SetFileAttributesW(full_path, FILE_ATTRIBUTE_NORMAL)

        # Write project configuration
        with open(full_path, 'w') as f:
            json.dump(data, f, indent=4)

        # Make file hidden on Windows
        if sys.platform == "win32":
            FILE_ATTRIBUTE_HIDDEN = 0x02
            ctypes.windll.kernel32.SetFileAttributesW(full_path, FILE_ATTRIBUTE_HIDDEN)
    def create_new_project(self, project_path):
        """
        Creates a new project entry with the given path.
        If a project with the same path exists, it updates its timestamp.
        
        Args:
                project_path (str): Full path to the project directory
                
        Returns:
                dict: The created/updated project entry
        """
        if not os.path.isdir(project_path):
                raise ValueError("Invalid project directory path")
                
        project_name = os.path.basename(project_path)
        timestamp = datetime.now().timestamp()
        
        
        new_project = {
                "name": project_name,
                "path": project_path,
                "timestamp": timestamp
        }
        
        # Load or create projects list
        if os.path.isfile(self.projects_file):
                with open(self.projects_file) as file:
                        data = json.load(file)
        else:
                data = {"projects": []}
                
        # Remove any existing project with the same path
        data["projects"] = [p for p in data["projects"] if p["path"] != project_path]
        # Add the new/updated project
        data["projects"].append(new_project)
        
        # Save updated projects list
        with open(self.projects_file, 'w') as file:
                json.dump(data, file, indent=4, separators=(',', ': '))

        # Create/update project configuration
        json_data = {"project_name": project_name}
        self.update_project_json(project_path, json_data)
        
        return new_project

    def isProject(self, project_path):
        """
        Check if a project with the given path exists.
        
        Args:
                project_path (str): Path of the project to check
                
        Returns:
                bool: True if project exists, False otherwise
        """
        if os.path.isfile(self.projects_file):
                with open(self.projects_file) as file:
                        data = json.load(file)
                return any(project["path"] == project_path for project in data.get("projects", []))
        return False

    def deleteProject(self, project_path):
        """
        Delete the project with the given path.
        
        Args:
                project_path (str): Path of the project to delete
        """
        if os.path.isfile(self.projects_file):
                with open(self.projects_file) as file:
                        data = json.load(file)
                
                # Remove project with matching path
                data["projects"] = [
                project for project in data.get("projects", [])
                if project["path"] != project_path
                ]
                
                with open(self.projects_file, 'w') as file:
                        json.dump(data, file, indent=4, separators=(',', ': '))
                
                # Optionally, remove the project.aide.json file from the project directory
                project_config = os.path.join(project_path, "project.aide.json")
                if os.path.exists(project_config):
                        os.remove(project_config)

    def updateTimestamp(self, project_path):
        """
        Update the timestamp of the project with the given path to current time.
        
        Args:
                project_path (str): Path of the project to update
                
        Returns:
                bool: True if project was found and updated, False otherwise
        """
        print("changing timestamps")
        if os.path.isfile(self.projects_file):
                current_timestamp = datetime.now().timestamp()
                with open(self.projects_file) as file:
                        data = json.load(file)
                
                updated = False
                for project in data.get("projects", []):
                        if project["path"] == project_path:
                                project["timestamp"] = current_timestamp
                                updated = True
                                break
                        
                if updated:
                        with open(self.projects_file, 'w') as file:
                                json.dump(data, file, indent=4, separators=(',', ': '))
                        return True
        return False

    def getTodayProjects(self):
        """
        Get list of all projects created/updated today.
        
        Returns:
                list: List of project dictionaries from today
        """
        if os.path.isfile(self.projects_file):
                with open(self.projects_file) as file:
                        data = json.load(file)
                
                today = datetime.now().date()
                return [
                project for project in data.get("projects", [])
                if datetime.fromtimestamp(project["timestamp"]).date() == today
                ]
        return []

    def getMonthProjects(self):
        """
        Get list of all projects created/updated this month.
        
        Returns:
                list: List of project dictionaries from this month
        """
        if os.path.isfile(self.projects_file):
                with open(self.projects_file) as file:
                        data = json.load(file)
                
                current = datetime.now()
                return [
                project for project in data.get("projects", [])
                if datetime.fromtimestamp(project["timestamp"]).year == current.year
                and datetime.fromtimestamp(project["timestamp"]).month == current.month
                ]
        return []

    def getAllProjects(self):
        """
        Get list of all projects.

        Returns:
                list: List of all project dictionaries
        """
        if os.path.isfile(self.projects_file):
                with open(self.projects_file) as file:
                        data = json.load(file)
                return data.get("projects", [])
        return []
    def searchProjects(self, search_term, threshold=0.6):
        """
        Search for projects whose names are similar to the given search term.
        Uses fuzzy string matching to find close matches.
        
        Args:
                search_term (str): The name or partial name to search for
                threshold (float): Similarity threshold between 0 and 1 (default: 0.6)
                                Higher values require closer matches
                                
        Returns:
                list: List of projects sorted by relevance (closest matches first)
        """
        from difflib import SequenceMatcher
        
        def similarity_score(project_name):
                # Calculate similarity ratio between search term and project name
                # Convert both to lowercase for case-insensitive comparison
                return SequenceMatcher(
                        None, 
                        search_term.lower(), 
                        project_name.lower()
                ).ratio()
        
        def name_contains_term(project_name):
                # Check if search term is contained within project name
                return search_term.lower() in project_name.lower()
        
        if not os.path.isfile(self.projects_file):
                return []
                
        with open(self.projects_file) as file:
                data = json.load(file)
        
        matching_projects = []
        
        for project in data.get("projects", []):
                project_name = project["name"]
                
                # If the search term is directly contained in the project name,
                # consider it a perfect match (score = 1.0)
                if name_contains_term(project_name):
                        matching_projects.append((1.0, project))
                        continue
                
                # Calculate similarity score for fuzzy matching
                score = similarity_score(project_name)
                
                # Add project to results if score exceeds threshold
                if score >= threshold: 
                        matching_projects.append((score, project))
        
        # Sort by similarity score (highest first) and remove scores from final result
        matching_projects.sort(reverse=True, key=lambda x: x[0])
        return [project for score, project in matching_projects]