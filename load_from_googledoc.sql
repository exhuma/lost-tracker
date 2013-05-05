BEGIN;

    CREATE TEMPORARY TABLE googledoc (
        time text,
        name text,
        num_people integer,
        head text,
        phone text,
        email text,
        equipe text,
        gone text,
        back text);

    \copy googledoc FROM 'my__.groups.csv' WITH DELIMITER ',' CSV HEADER;

    INSERT INTO "group" (name, contact, phone, start_time)
    SELECT "name", email, phone, time FROM googledoc;

COMMIT;
