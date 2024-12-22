import os
from tinydb import TinyDB, Query
from pipeline.utils import serializer


class DatabaseManager:
    def __init__(self, db_path):
        self.db_path = db_path
        self.songs_table = TinyDB(self.db_path, storage=serializer).table('songs')
        self.hashes_table = TinyDB(self.db_path, storage=serializer).table('hashes')

    def store_song(self, song_data, hashes):
        song_query = Query()
        if not self.songs_table.search(song_query.song_id == song_data['song_id']):
            self.songs_table.insert(song_data)
            self.store_hashes(hashes)
            return True
        return False

    def store_hashes(self, hashes):
        self.hashes_table.insert_multiple(hashes)

    def find_song_by_hashes(self, hashes):
        song_query = Query()
        for hash_item in hashes:
            result = self.hashes_table.search(song_query.hash == hash_item)
            if result:
                return result[0].get("song_id", None)
        return None
