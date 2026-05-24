-- PostgreSQL migration:
-- Make room_participants.room_id cascade when a room is deleted.
-- Run this once before enabling the external cleanup job.

ALTER TABLE room_participants
  DROP CONSTRAINT IF EXISTS room_participants_room_id_fkey;

ALTER TABLE room_participants
  ADD CONSTRAINT room_participants_room_id_fkey
  FOREIGN KEY (room_id)
  REFERENCES rooms(id)
  ON DELETE CASCADE;

