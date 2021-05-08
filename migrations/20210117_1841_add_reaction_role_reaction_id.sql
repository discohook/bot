ALTER TABLE reaction_role
ADD emoji_id TEXT;

UPDATE reaction_role
SET emoji_id = regexp_replace(reaction, '<a?:\w+:(\d+)>', '\1');

ALTER TABLE reaction_role
ALTER COLUMN emoji_id SET NOT NULL;
