from sqlalchemy import (
    Column,
    Integer,
    Text,
    ForeignKey,
)

from .meta import Base
from sqlalchemy.orm import relationship


class Page(Base):
    __tablename__ = 'pages'
    id = Column(Integer, primary_key=True)
    name = Column(Text, nullable=False, unique=True)
    data = Column(Text, nullable=False)
    creator_id = Column(ForeignKey('users.id'), nullable=False)
    creator = relationship('User', backref='created_pages')

    def _to_dict(self):
        return dict(
            name=self.name,
            data=self.data,
            creator=self.creator._to_dict()
        )
