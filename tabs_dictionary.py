class tabs_dictionary:
    def __init__(self):
        self.tabs = {}
        self.index_counter = 0  # To track the order of the tabs

    def add_tab(self, key, **data):
        """Add a new tab or update an existing one, with an internal index"""
        self.tabs[key] = {"index": self.index_counter, **data}
        self.index_counter += 1  # Increment index for the next tab

    def remove_tab(self, key):
        """Remove a tab if it exists and update the indices of remaining tabs"""
        if key in self.tabs:
            print(f"removing tab: {key}")
            removed_index = self.tabs[key]["index"]
            del self.tabs[key]
            self._update_indices(removed_index)  # Recalculate indices after removal
            return True
        return False

    def update_tab(self, key, **new_data):
        """Update data for an existing tab"""
        if key in self.tabs:
            self.tabs[key].update(new_data)
            return True
        return False

    def change_key(self, old_key, new_key):
        """Change the key of a tab"""
        if old_key in self.tabs:
            self.tabs[new_key] = self.tabs.pop(old_key)
            return True
        return False

    def get_tab(self, key):
        """Get tab data safely using get()"""
        return self.tabs.get(key)

    def tab_exists(self, key):
        """Check if a tab exists"""
        return key in self.tabs

    def get_all_tabs(self):
        """Return all tabs"""
        return self.tabs

    def clear_tabs(self):
        """Remove all tabs"""
        self.tabs.clear()
        self.index_counter = 0  # Reset the index counter

    def get_tab_by_index(self, index):
        """Get tab key by the internal index value"""
        for key, data in self.tabs.items():
            if data.get("index") == index:
                return key
        raise IndexError("Tab index out of range")

    def _update_indices(self, removed_index): 
        """Private method to recalculate the indices of the remaining tabs"""
        # Loop through the dictionary and update indices of items with index > removed_index
        for key, data in self.tabs.items():
                current_index = data.get("index")
                if current_index > removed_index:
                        self.tabs[key]["index"] = current_index - 1