from src.common.data_models.models import db


class DBConnectionMiddleware(object):
    def process_request(self, req, resp):
        # No database connection initialization here to avoid additional latency on each API call.
        # Relying on PeeWee's default 'autoconnect' feature for seamless database connectivity.
        # Reference :
        # https://docs.peewee-orm.com/en/latest/peewee/database.html#using-autoconnect
        pass

    def process_response(self, req, resp, resource, req_succeeded):
        # Ensuring all database connections are properly closed after each request.
        # This returns the connections back to the pool for efficient reuse.
        # Reference :
        # https://docs.peewee-orm.com/en/latest/peewee/playhouse.html#connection-pool
        if not db.is_closed():
            db.close()
