from sqlalchemy.orm.scoping import ScopedSession

from narraint.backend.database import SessionExtended
from narrec.backend.models import Recommender
from narrec.config import BACKEND_CONFIG


class SessionRecommender(SessionExtended):
    is_sqlite = False
    is_postgres = False
    _instance_recommender = None

    @classmethod
    def get(cls, connection_config: str = BACKEND_CONFIG, declarative_base=Recommender,
            force_create=False) -> ScopedSession:
        if not SessionRecommender._instance_recommender:
            SessionRecommender._instance_recommender = SessionExtended.get(connection_config, declarative_base,
                                                                           force_create=True)
            SessionRecommender.is_postgres = cls._instance.is_postgres
            SessionRecommender.is_sqlite = cls._instance.is_sqlite
        return SessionRecommender._instance_recommender
