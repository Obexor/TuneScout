import os
from tinydb import TinyDB, Query
from pipeline.utils import serializer

class DatabaseManager:
    def __init__(self, db_path):
        # Initialize the DatabaseManager with the path to the database file
        self.db_path = db_path
        
        # Create or open a TinyDB table for storing song metadata
        self.songs_table = TinyDB(self.db_path, storage=serializer).table('songs')
        
        # Create or open a TinyDB table for storing audio hashes
        self.hashes_table = TinyDB(self.db_path, storage=serializer).table('hashes')

    def store_song(self, song_data, hashes):
        # Check if the song already exists in the database using its song_id
        song_query = Query()
        if not self.songs_table.search(song_query.song_id == song_data['song_id']):
            # If the song does not exist, insert its metadata into the songs table
            self.songs_table.insert(song_data)
            
            # Store the associated hashes in the hashes table
            self.store_hashes(hashes)
            return True  # Return True to indicate the song was successfully stored
        return False  # Return False if the song already exists

    def store_hashes(self, hashes):
        # Insert multiple hashes into the hashes table
        self.hashes_table.insert_multiple(hashes)

    def find_song_by_hashes(self, hashes):
        # Search for a song by matching hashes in the hashes table
        song_query = Query()
        for hash_item in hashes:
            # Look for a matching hash in the hashes table
            result = self.hashes_table.search(song_query.hash == hash_item)
            if result:
                # If a matching hash is found, return the associated song_id
                return result[0].get("song_id", None)
        return None  # Return None if no match is found
