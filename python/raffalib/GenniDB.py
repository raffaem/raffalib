#!/usr/bin/env python3
# Copyright 2023 Raffaele Mancuso
# SPDX-License-Identifier: GPL-2.0-or-later

class GenniDB:

    def __init__(self, dbfp):
        self.session = requests.Session()
        self.con = pysqlite3.connect(dbfp)
        self.con.row_factory = pysqlite3.Row
        self.cur = self.con.cursor()
        self.create_table()

    def __del__(self):
        self.con.close()

    def create_table(self):
        query = '''
        CREATE TABLE IF NOT EXISTS genni (
            id INTEGER PRIMARY KEY NOT NULL,
            ethnicity TEXT NOT NULL CHECK(LENGTH(ethnicity)>1),
            first_genni TEXT NOT NULL CHECK(LENGTH(first_genni)>0),
            first_in TEXT NOT NULL CHECK(LENGTH(first_in)>0),
            gender TEXT NOT NULL CHECK(LENGTH(gender)=1),
            last_genni TEXT NOT NULL CHECK(LENGTH(last_genni)>0),
            last_in TEXT NOT NULL CHECK(LENGTH(last_in)>0),
            timestamp TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            error VARCHAR(20),
            strip_accents INTEGER NOT NULL CHECK(strip_accents=0 OR strip_accents=1),
            manual INTEGER NOT NULL CHECK(manual=0 OR manual=1) DEFAULT 0,
            manual_full_search INTEGER NOT NULL CHECK(manual_full_search=0 OR manual_full_search=1) DEFAULT 0,
            UNIQUE(first_in, last_in)
        );
        '''
        self.cur.execute(query)

        query = '''
        CREATE TABLE IF NOT EXISTS proj2genni
        (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER NOT NULL,
            genni_id INTEGER NOT NULL,
            UNIQUE(project_id),
            FOREIGN KEY(genni_id) REFERENCES genni(id)
        );
        '''
        self.cur.execute(query)

    @staticmethod
    def proc_name(s):
        s = html.unescape(s)
        # Genni support names with no more than 4 words
        #if s.count(" ") > 3:
        #    s = s.split(" ")[:4]
        #    s = " ".join(s)
        return s

    @staticmethod
    def build_url(given_name, surname):
        return f"http://abel.lis.illinois.edu/cgi-bin/ethnea/" \
               f"search.py?Fname={given_name}&Lname={surname}&format=json"

    def get_response(self, url):
        resp = None

        for i in range(1,20):
            try:
                resp = self.session.get(url, stream=True, timeout=20)
            except Exception as e:
                logging.error("EXCEPTION:", e)
                logging.error("Sleeping and then re-trying..")
                time.sleep(10)
            else:
                break

        if not resp:
            return GenniResponse(None, "TooManyTrials")

        try:
            resp_data = resp.raw.data.decode("utf8").replace("'", '"').strip()
        except UnicodeDecodeError as e:
            logger.error(f"UnicodeDecodeError for url '{url}'")
            return GenniResponse(None, "UnicodeDecodeError")

        try:
            resp_json = json.loads(resp_data)
        except JSONDecodeError as e:
            logger.error(f"JSONDecodeError for url '{url}'")
            return GenniResponse(None, "JSONDecodeError")

        return GenniResponse(resp_json, None)

    def insert(self, resp, first_in, last_in, project_id, strip_accents):

        # Insert into genni table
        query = f"""
                INSERT INTO genni
                (ethnicity, first_genni, first_in,
                gender, last_genni, last_in, error, strip_accents)
                VALUES
                (:ethnicity, :first_genni, :first_in,
                :gender, :last_genni, :last_in, :error, :strip_accents)
                """
        d = {
            "ethnicity": resp.ethnicity,
            "first_genni": resp.first,
            "first_in": first_in,
            "gender": resp.gender,
            "last_genni": resp.last,
            "last_in": last_in,
            "error": resp.error,
            "strip_accents": strip_accents
            }

        try:
            self.cur.execute(query, d)
        except IntegrityError as e:
            msg = "IntegrityError while inserting into db\n"
            msg += f"first_in={first_in}; last_in={last_in}; project_id={project_id}\n"
            msg += str(e)
            raise Exception(msg)

        # Get max genni_id
        query = "SELECT MAX(id) AS genni_id FROM genni"
        genni_id = self.cur.execute(query).fetchone()["genni_id"]

        # Insert into proj2genni table
        query = "INSERT INTO proj2genni (project_id, genni_id) VALUES (:project_id, :genni_id)"
        d = {
            "project_id": project_id,
            "genni_id": genni_id
        }
        self.cur.execute(query, d)
        self.commit()

    def scrape(self, first_in, last_in, project_id):

        # Check if this project_id is already in the db
        query = "SELECT project_id FROM proj2genni WHERE project_id=?"
        row = self.cur.execute(query, [project_id]).fetchone()
        if row:
            return

        # Strip accents
        first_in_old = first_in
        last_in_old = last_in
        first_in = strip_accents_ascii(first_in)
        last_in = strip_accents_ascii(last_in)
        strip_accents = (first_in != first_in_old) or (last_in != last_in_old)

        # Check if name and surname are already in the db
        query = "SELECT id AS genni_id, gender, ethnicity, error FROM genni WHERE first_in=? AND last_in=?"
        row = self.cur.execute(query, [first_in, last_in]).fetchone()
        if row:
            logging.info(f"Value already present for project_id={project_id}")
            query = "INSERT INTO proj2genni (project_id, genni_id) VALUES (:project_id, :genni_id)"
            d = {
                "project_id": project_id,
                "genni_id": row["genni_id"]
            }
            self.cur.execute(query, d)
            self.commit()
            return None
        else:
            #logging.info(f"Scraping first_in={first_in}, last_in={last_in}, project_id={project_id}")
            url = GenniDB.build_url(first_in, last_in)
            #logging.info(f"Scraping url={url}")
            resp:GenniResponse = self.get_response(url)
            #logging.info(f"Scraping resp.gender={resp.gender}, resp.gender={resp.ethnicity}")

        # Insert GenniResponse into the db
        if resp:
            self.insert(resp, first_in, last_in, project_id, strip_accents)
            self.commit()
        return resp

    def commit(self):
        self.con.commit()

    def close(self):
        self.con.close()

