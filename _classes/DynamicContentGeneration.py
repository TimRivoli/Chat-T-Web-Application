class DynamicContentGeneration:
    @staticmethod
    def generate_default_note_categories():
        StorageManager.create_note_category("General", 0)
        StorageManager.create_note_category("To-Do", 1)
        StorageManager.create_note_category("Building Stuff", 2)
        StorageManager.create_note_category("Ideas", 3)
        StorageManager.create_note_category("Family", 4)
        StorageManager.create_note_category("Investing", 5)
        StorageManager.create_note_category("Personal Development", 6)
        StorageManager.create_note_category("Professional Development", 7)
        StorageManager.create_note_category("Takeout Orders", 8)
        StorageManager.create_note_category("Recipies", 9)
        StorageManager.create_note_category("Reference", 10)
        StorageManager.create_note_category("Writing", 11)