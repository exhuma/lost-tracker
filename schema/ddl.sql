CREATE TABLE "group" (
    id SERIAL NOT NULL PRIMARY KEY,
    name character varying(50) UNIQUE,
    "order" integer,
    cancelled boolean DEFAULT false
);

CREATE TABLE group_station_state (
    group_id integer
        REFERENCES "group"(id)
            ON UPDATE CASCADE
            ON DELETE CASCADE,
    station_id integer
        REFERENCES station(id)
            ON UPDATE CASCADE
            ON DELETE CASCADE,
    state integer
);


CREATE TABLE station (
    id SERIAL NOT NULL PRIMARY KEY,
    name character varying(50) UNIQUE,
    "order" integer
);
