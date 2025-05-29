from sqlalchemy import Column, Integer, BigInteger, String, ForeignKey, Text
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

class Profile(Base):
    __tablename__ = "profiles"

    id = Column(Integer, primary_key=True)
    telegram_id = Column(BigInteger, unique=True, nullable=False)
    name = Column(String, nullable=False)
    company = Column(String)
    position = Column(String)
    role = Column(String)

class Questionnaire(Base):
    __tablename__ = "questionnaires"

    id = Column(Integer, primary_key=True)
    recruiter_id = Column(Integer, nullable=False)
    title = Column(String(255), nullable=False)
    code = Column(String(10), unique=True, nullable=False)

    questions = relationship("Question", back_populates="questionnaire", cascade="all, delete")

class Question(Base):
    __tablename__ = "questions"

    id = Column(Integer, primary_key=True)
    questionnaire_id = Column(Integer, ForeignKey("questionnaires.id", ondelete="CASCADE"))
    text = Column(Text, nullable=False)

    questionnaire = relationship("Questionnaire", back_populates="questions")

class Answer(Base):
    __tablename__ = "answers"

    id = Column(Integer, primary_key=True)
    questionnaire_id = Column(Integer, ForeignKey("questionnaires.id"))
    question_id = Column(Integer, ForeignKey("questions.id"))
    respondent_id = Column(BigInteger)
    answer_text = Column(Text)

class InterviewAnalysisResult(Base):
    __tablename__ = "interview_analysis_results"

    id = Column(Integer, primary_key=True)
    title = Column(String(255), nullable=False)
    telegram_id = Column(BigInteger, nullable=False)
    total_sentences = Column(Integer, nullable=False)
    general_count = Column(Integer, nullable=False)
    specific_count = Column(Integer, nullable=False)
    majority = Column(String(512), nullable=False)
    full_text = Column(Text, nullable=False)