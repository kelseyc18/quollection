from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy import create_engine, func
from passlib.apps import custom_app_context as pwd_context
import random, string

Base = declarative_base()
engine = create_engine('sqlite:///quollection.db')
Base.metadata.create_all(engine)

class User(Base):
    __tablename__ = 'user'
    id = Column(Integer, primary_key=True)
    name = Column(String(255))
    email = Column(String(255), unique=True)
    password_hash = Column(String(255))
    quotes = relationship("Quote", back_populates="user")
    moods = relationship("Mood", back_populates="user")

    def hash_password(self, password):
        self.password_hash = pwd_context.encrypt(password)

    def verify_password(self, password):
        return pwd_context.verify(password, self.password_hash)

class Quote(Base):
    __tablename__ = 'quote'
    id = Column(Integer, primary_key=True)
    text = Column(String(255))
    source = Column(String(255))
    quote_source = Column(String(255))
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship("User", uselist=False, back_populates="quotes")
    moods = relationship("MoodAssociation", back_populates="quote")

class Mood(Base):
    __tablename__ = 'mood'
    id = Column(Integer, primary_key=True)
    description = Column(String(255))
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship("User", uselist=False, back_populates="moods")
    quotes = relationship("MoodAssociation", back_populates="mood")

class MoodAssociation(Base):
    __tablename__ = 'moodAssociation'
    quote_id = Column(Integer, ForeignKey('quote.id'), primary_key=True)
    mood_id = Column(Integer, ForeignKey('mood.id'), primary_key=True)
    quote = relationship("Quote", back_populates="moods")
    mood = relationship("Mood", back_populates="quotes")
